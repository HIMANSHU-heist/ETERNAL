"""
Analyst node.

This is the "no hallucination" guarantee of the system: every number in the
final report traces back to an actual pandas computation done here, not an
LLM guess. If a planned step references a column that doesn't exist or the
computation fails, we record the error per-step and keep going — one bad
step shouldn't kill the whole analysis.
"""

from app.core.file_loader import load_dataframe
from app.core.registry import get_file_context


def _execute_step(df, step: dict):
    step_type = step.get("type")

    if step_type == "missing_report":
        return df.isna().sum().to_dict()

    if step_type == "describe":
        return df.describe(include="all").fillna("").astype(str).to_dict()

    if step_type == "value_counts":
        col = step.get("column")
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in dataset")
        return df[col].value_counts().to_dict()

    if step_type == "correlation":
        cols = step.get("columns") or []
        cols = [c for c in cols if c in df.columns]
        if len(cols) < 2:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            cols = numeric_cols[:6]  # fallback: cap to keep result readable
        return df[cols].corr(numeric_only=True).round(3).to_dict()

    if step_type == "groupby_mean":
        group_col = step.get("group_col")
        target_col = step.get("target_col")
        if group_col not in df.columns or target_col not in df.columns:
            raise ValueError(
                f"group_col='{group_col}' or target_col='{target_col}' not found in dataset"
            )
        return df.groupby(group_col)[target_col].mean().round(3).to_dict()

    raise ValueError(f"Unknown step type: {step_type}")


def analyst_node(state: dict) -> dict:
    dataset_id = state["dataset_id"]
    context = get_file_context(dataset_id)
    if not context:
        return {"error": f"dataset_id {dataset_id} not found in registry", "analysis_results": []}

    df = load_dataframe(context["filepath"])
    plan = state.get("plan", [])

    results = []
    for step in plan:
        try:
            result = _execute_step(df, step)
            results.append({"step": step, "status": "ok", "result": result})
        except Exception as exc:
            results.append({"step": step, "status": "error", "error": str(exc)})

    return {"analysis_results": results}
