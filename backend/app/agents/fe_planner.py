import json

from app.agents.planner import _extract_json
from app.services.llm_service import get_llm_provider

FE_PLANNER_SYSTEM_PROMPT = """You are the Feature Engineering Planner.
Given a dataset schema, propose a JSON list of feature engineering steps.
Return ONLY valid JSON.

Shape:
{
  "steps": [
    {"id": 1, "type": "fillna", "column": "COL", "strategy": "mean|median|mode|constant", "value": null, "description": "..."},
    {"id": 2, "type": "drop_column", "column": "COL", "description": "..."},
    {"id": 3, "type": "encode_categorical", "column": "COL", "method": "onehot|label", "description": "..."},
    {"id": 4, "type": "create_ratio", "new_column": "NAME", "numerator": "COL", "denominator": "COL", "description": "..."},
    {"id": 5, "type": "bin_numeric", "column": "COL", "bins": 4, "new_column": "NAME", "description": "..."},
    {"id": 6, "type": "log_transform", "column": "COL", "description": "..."}
  ]
}

Rules:
- Only reference columns that exist in the schema. Never invent one.
- Only propose steps that make sense given dtypes and missing-value counts.
- Max 6 steps, prioritized by impact."""


def fe_plan_node(schema: dict) -> list[dict]:
    llm = get_llm_provider()
    user_message = f"Dataset schema:\n{json.dumps(schema)}"
    steps = []

    for attempt in range(2):
        raw = llm.chat(FE_PLANNER_SYSTEM_PROMPT, user_message)
        parsed = _extract_json(raw)
        steps = parsed.get("steps", [])

        if steps:
            break

        print(f"[fe_planner] attempt {attempt + 1} returned no usable steps. Raw LLM output:\n{raw}\n")

        if attempt == 0:
            user_message += (
                "\n\nYour previous response could not be parsed as valid JSON or had no steps. "
                "Return ONLY the JSON object described above, nothing else."
            )

    return steps
