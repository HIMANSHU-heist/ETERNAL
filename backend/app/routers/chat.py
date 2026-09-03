from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.chart_planner import plan_chart
from app.core import chart_memory, chat_history, vector_store
from app.core.chart_builder import build_chart_data
from app.core.chunking import build_chunks
from app.core.file_loader import load_dataframe
from app.core.registry import get_file_context
from app.services.llm_service import get_llm_provider

router = APIRouter()


class ChatRequest(BaseModel):
    file_id: str
    message: str


class ChatResponse(BaseModel):
    file_id: str
    answer: str
    chart_proposal: Optional[dict] = None


SYSTEM_PROMPT_TEMPLATE = """You are a data analyst having a normal back-and-forth conversation with someone
about their dataset. You are NOT writing a report — you're chatting, like a colleague would.

Here is the most relevant context retrieved for this specific question, out of everything known
about the dataset (schema, computed statistics, and any generated analysis):

{context_text}

How to respond:
- Answer ONLY what was actually asked. Don't dump every related insight you have — if they ask
  about one factor, talk about that one factor, not all five.
- Keep it short: 1-4 sentences for a simple question. No headers, no bullet-point essays, no
  markdown tables, unless the person specifically asks for a breakdown or comparison.
- Talk like a person, not a report generator. It's fine to say things plainly — "yeah, study time
  looks like the biggest factor here" rather than a formal write-up.
- If there's naturally a good follow-up worth offering, mention it briefly in passing ("want me to
  check how that interacts with attendance too?") instead of pre-emptively answering it.
- Use ONLY the context above plus general reasoning — never invent numbers not present there.
- If the retrieved context doesn't answer the question, say so plainly and suggest what to run
  next (via /analyze), rather than guessing or padding the answer.
- If the context above describes a chart that was just shown to the user, your answer
  MUST be about that specific chart's numbers only — not a general summary of the whole dataset.
"""

CHART_KEYWORDS = [
    "plot", "chart", "graph", "pie", "histogram", "scatter", "visuali",
    "draw", "bar chart", "line chart", "heatmap", "diagram", "show me a",
    "can you show", "distribution graph", "trend line",
]

# If the message is asking to INTERPRET/EXPLAIN something (likely about a
# chart already shown), never route it into chart-building — even if it
# happens to contain a chart-ish word like "graph". This is what was making
# the bot get "stuck" proposing charts instead of answering "what does this
# graph mean?" style follow-ups.
CHART_EXCLUDE_PHRASES = [
    "conclusion", "interpret", "explain", "what does", "what's the meaning",
    "means", "insight", "understand", "why is", "why does", "summar",
    "takeaway", "tell me about this",
]


def _looks_like_chart_request(message: str) -> bool:
    lowered = message.lower()
    if any(phrase in lowered for phrase in CHART_EXCLUDE_PHRASES):
        return False
    return any(keyword in lowered for keyword in CHART_KEYWORDS)


def _handle_chart_request(file_id: str, context: dict, message: str) -> Optional[ChatResponse]:
    """Try to build a chart proposal. Returns None if it can't (falls back to normal chat)."""
    try:
        spec = plan_chart(context["schema_summary"], message)
        if not spec.get("chart_type"):
            return None

        df = load_dataframe(context["filepath"])
        chart_data = build_chart_data(df, spec)

        title = spec.get("title") or f"{chart_data['chart_type'].title()} chart"
        proposal = {
            "chart_type": chart_data["chart_type"],
            "title": title,
            "data": chart_data,
        }

        chart_memory.set_last_chart(file_id, {
            "title": title,
            "chart_type": chart_data["chart_type"],
            "data": chart_data,
        })

        answer_text = f"Yeah, I can put that together — a {chart_data['chart_type']} chart for \"{title}\". Approve below and I'll draw it."

        chat_history.append(file_id, "user", message)
        chat_history.append(file_id, "assistant", f"[Proposed chart: {title}]")

        return ChatResponse(file_id=file_id, answer=answer_text, chart_proposal=proposal)
    except Exception as exc:
        import traceback
        print("CHART BUILD FAILED:", exc)
        traceback.print_exc()  # temporary debug logging
        # Chart parsing/building failed (e.g. LLM picked a bad column) — fall
        # back to a normal conversational answer instead of erroring out.
        return None


def _describe_chart_for_llm(chart_ctx: dict) -> str:
    """Turns the last shown chart's real numbers into plain text the LLM can reason over."""
    data = chart_ctx["data"]
    ctype = chart_ctx["chart_type"]
    title = chart_ctx["title"]

    if ctype in ("bar", "pie", "histogram"):
        pairs = ", ".join(f"{l}: {v}" for l, v in zip(data["labels"], data["values"]))
        return (
            f'The chart just shown to the user is a {ctype} chart titled "{title}" '
            f'({data["x_label"]} vs {data["y_label"]}). Values — {pairs}.')

    if ctype == "grouped_bar":
        lines = []
        for cat in data["categories"]:
            vals = ", ".join(f"{l}: {v}" for l, v in zip(data["labels"], data["series"][cat]))
            lines.append(f"{cat} → {vals}")
        return (
            f'The chart just shown is a grouped bar chart titled "{title}" comparing '
            f'{data["group_label"]} across {data["x_label"]} ranges. ' + " | ".join(lines))

    if ctype == "line":
        return f'The chart just shown is a line chart titled "{title}" of {data["y_label"]} over {data["x_label"]}.'

    if ctype == "scatter":
        return (
            f'The chart just shown is a scatter plot titled "{title}" of '
            f'{data["x_label"]} vs {data["y_label"]} with {len(data["points"])} points.')

    if ctype == "heatmap":
        return f'The chart just shown is a correlation heatmap titled "{title}". Matrix: {data["matrix"]}'

    return f'A {ctype} chart titled "{title}" was just shown.'


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    context = get_file_context(payload.file_id)
    if not context:
        raise HTTPException(
            status_code=404,
            detail="file_id not found. Upload a file first via /api/v1/upload.",
        )

    if _looks_like_chart_request(payload.message):
        chart_response = _handle_chart_request(payload.file_id, context, payload.message)
        if chart_response:
            return chart_response
        # falls through to normal chat if chart building failed

    if not vector_store.is_indexed(payload.file_id):
        schema_chunks = build_chunks(context["schema_summary"])
        vector_store.index_dataset(payload.file_id, schema_chunks)

    retrieved_chunks = vector_store.query_dataset(payload.file_id, payload.message, top_k=6)
    context_text = (
        "\n".join(f"- {chunk}" for chunk in retrieved_chunks)
        if retrieved_chunks
        else "No specific context could be retrieved for this dataset yet."
    )

    lowered_msg = payload.message.lower()
    last_chart = chart_memory.get_last_chart(payload.file_id)
    if last_chart and any(p in lowered_msg for p in CHART_EXCLUDE_PHRASES):
        context_text = _describe_chart_for_llm(last_chart) + "\n\n" + context_text

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_text=context_text)
    history = chat_history.get(payload.file_id)

    llm = get_llm_provider()
    try:
        answer = llm.chat(system_prompt, payload.message, history=history)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")

    chat_history.append(payload.file_id, "user", payload.message)
    chat_history.append(payload.file_id, "assistant", answer)

    return ChatResponse(file_id=payload.file_id, answer=answer)


@router.get("/chat/history")
def get_chat_history(file_id: str):
    msgs = chat_history.get(file_id)
    return {"file_id": file_id, "messages": msgs}


@router.post("/chat/reset")
def reset_chat(file_id: str):
    chat_history.clear(file_id)
    return {"status": "ok", "message": f"Chat history cleared for {file_id}"}