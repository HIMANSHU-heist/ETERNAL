from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.fe_planner import fe_plan_node
from app.core.dataset_registry_store import get_dataset_meta, register_dataset, set_dataset_flags
from app.core.feature_engineering import FeatureStepError, apply_plan
from app.core.file_loader import get_schema_summary, load_dataframe
from app.core.registry import get_file_context, update_dataset_file
from app.routers.upload import DATASET_REGISTRY

router = APIRouter()


class FeaturePlanRequest(BaseModel):
    dataset_id: str


class FeatureApplyRequest(BaseModel):
    dataset_id: str
    steps: list[dict]


@router.post("/feature-plan")
def get_feature_plan(payload: FeaturePlanRequest):
    context = get_file_context(payload.dataset_id)
    if not context:
        raise HTTPException(404, "dataset_id not found")
    steps = fe_plan_node(context["schema_summary"])
    return {"dataset_id": payload.dataset_id, "proposed_steps": steps}


@router.post("/feature-apply")
def apply_feature_plan(payload: FeatureApplyRequest):
    """
    Applies the APPROVED steps directly to the dataset's own CSV file
    (same dataset_id, same file on disk) — this is a real, permanent
    change to the uploaded data, not a preview and not a copy.
    """
    context = get_file_context(payload.dataset_id)
    if not context or payload.dataset_id not in DATASET_REGISTRY:
        raise HTTPException(404, "dataset_id not found")

    if not payload.steps:
        raise HTTPException(422, "No steps to apply.")

    before_schema = context["schema_summary"]
    path = DATASET_REGISTRY[payload.dataset_id]
    df = load_dataframe(path)

    try:
        df = apply_plan(df, payload.steps)
    except FeatureStepError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid feature-engineering step: {e}",
        )

    # Overwrite the SAME file — same dataset_id everywhere downstream
    # (sidebar entry, chat history, /dataset/{id}/csv all keep working).
    df.to_csv(path, index=False)

    after_schema = get_schema_summary(df)
    update_dataset_file(payload.dataset_id, path, after_schema)

    existing_meta = get_dataset_meta(payload.dataset_id) or {}
    register_dataset(
        file_id=payload.dataset_id,
        filename=existing_meta.get("filename", "dataset.csv"),
        num_rows=after_schema.get("num_rows"),
        num_columns=after_schema.get("num_columns"),
    )
    # dataset just changed -> old report is stale, needs a fresh /analyze
    set_dataset_flags(payload.dataset_id, dirty=True)

    return {
        "dataset_id": payload.dataset_id,
        "before_schema": before_schema,
        "after_schema": after_schema,
        "applied_steps": payload.steps,
    }