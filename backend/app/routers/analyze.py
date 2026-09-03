from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.graph import get_graph
from app.core import vector_store
from app.core.chunking import build_chunks
from app.core.registry import get_file_context

router = APIRouter()


class AnalyzeRequest(BaseModel):
    dataset_id: str
    goal: str


@router.post("/analyze")
def analyze(payload: AnalyzeRequest):
    context = get_file_context(payload.dataset_id)
    if not context:
        raise HTTPException(
            status_code=404,
            detail="dataset_id not found. Upload a file first via /api/v1/upload.",
        )

    graph = get_graph()
    initial_state = {
        "dataset_id": payload.dataset_id,
        "goal": payload.goal,
        "schema_summary": context["schema_summary"],
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent graph failed: {exc}")

    analysis_results = final_state.get("analysis_results", [])
    report = final_state.get("report", "")

    # Re-index this dataset's vector store with schema + REAL analysis results
    # + report, so future /chat questions retrieve grounded, up-to-date context
    # instead of just the raw schema.
    chunks = build_chunks(context["schema_summary"], analysis_results, report)
    vector_store.index_dataset(payload.dataset_id, chunks)

    return {
        "dataset_id": payload.dataset_id,
        "goal": payload.goal,
        "plan": final_state.get("plan", []),
        "analysis_results": analysis_results,
        "report": report,
    }
