from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.fe_planner import fe_plan_node
from app.core.feature_engineering import FeatureStepError, apply_plan
from app.core.file_loader import load_dataframe, get_schema_summary
from app.core.registry import get_file_context, register_file
from app.routers.upload import DATASET_REGISTRY, UPLOAD_DIR

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
    import uuid

    if payload.dataset_id not in DATASET_REGISTRY:
        raise HTTPException(404, "dataset_id not found")

    df = load_dataframe(DATASET_REGISTRY[payload.dataset_id])

    try:
        df = apply_plan(df, payload.steps)
    except FeatureStepError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid feature-engineering step: {e}",
        )

    new_id = str(uuid.uuid4())
    new_path = UPLOAD_DIR / f"{new_id}.csv"
    df.to_csv(new_path, index=False)
    DATASET_REGISTRY[new_id] = str(new_path)
    schema = get_schema_summary(df)
    register_file(new_id, filepath=str(new_path), schema_summary=schema)
    return {"new_dataset_id": new_id, "schema": schema}
