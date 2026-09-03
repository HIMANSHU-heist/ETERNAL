from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.graph import get_graph
from app.core import vector_store
from app.core.chunking import build_chunks
from app.core.dataset_registry_store import set_dataset_flags
from app.core.registry import get_file_context, save_analysis_result

router = APIRouter()


class AnalyzeRequest(BaseModel):
    dataset_id: str
    goal: str


@router.get("/analyze/{dataset_id}")
def get_cached_analysis(dataset_id: str):
    """
    Returns the last analysis for this dataset WITHOUT recomputing anything.
    404 if it has never been analyzed. `dirty=true` means the CSV changed
    (e.g. via feature engineering) since this report was generated, so the
    UI should offer a fresh "Re-analyze" instead of treating this as current.
    """
    context = get_file_context(dataset_id)
    if not context:
        raise HTTPException(status_code=404, detail="dataset_id not found.")
    if not context.get("analyzed"):
        raise HTTPException(status_code=404, detail="This dataset hasn't been analyzed yet.")

    return {
        "dataset_id": dataset_id,
        "plan": context.get("plan", []),
        "analysis_results": context.get("analysis_results", []),
        "report": context.get("report", ""),
        "dirty": context.get("dirty", False),
    }


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

    plan = final_state.get("plan", [])
    analysis_results = final_state.get("analysis_results", [])
    report = final_state.get("report", "")

    # Cache it: reopening this dataset won't force another /analyze click
    # unless the CSV changes again (feature engineering flips dirty=true).
    save_analysis_result(payload.dataset_id, analysis_results, report, plan)
    set_dataset_flags(payload.dataset_id, analyzed=True, dirty=False)

    # Re-index this dataset's vector store with schema + REAL analysis results
    # + report, so future /chat questions retrieve grounded, up-to-date context
    # instead of just the raw schema.
    chunks = build_chunks(context["schema_summary"], analysis_results, report)
    vector_store.index_dataset(payload.dataset_id, chunks)

    return {
        "dataset_id": payload.dataset_id,
        "goal": payload.goal,
        "plan": plan,
        "analysis_results": analysis_results,
        "report": report,
    }