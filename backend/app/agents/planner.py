"""
Planner node.

Takes the dataset schema + the user's goal, and asks the LLM to produce a
STRUCTURED plan (JSON list of steps) — not prose. The Analyst node then
executes each step for real with pandas. This separation is what makes the
system trustworthy: the LLM decides *what* to analyze, but never fabricates
*results* — those come from actual code execution downstream.
"""

import json
import re

from app.services.llm_service import get_llm_provider

PLANNER_SYSTEM_PROMPT = """You are the Planner agent in a multi-agent data analysis system.

Given a dataset schema and a user's goal, produce a JSON analysis plan.
Return ONLY valid JSON, no markdown fences, no prose, no explanation — just the JSON object.

Shape (exact keys):
{
  "steps": [
    {"id": 1, "type": "missing_report", "description": "..."},
    {"id": 2, "type": "describe", "description": "..."},
    {"id": 3, "type": "value_counts", "column": "COLUMN_NAME", "description": "..."},
    {"id": 4, "type": "correlation", "columns": ["COL1", "COL2"], "description": "..."},
    {"id": 5, "type": "groupby_mean", "group_col": "COLUMN_NAME", "target_col": "COLUMN_NAME", "description": "..."}
  ]
}

Rules:
- Allowed "type" values ONLY: missing_report, describe, value_counts, correlation, groupby_mean
- ONLY reference column names that literally appear in the schema provided. Never invent a column name.
- "correlation" needs a "columns" list of NUMERIC columns only.
- "groupby_mean" needs "group_col" (usually categorical) and "target_col" (usually numeric).
- "value_counts" needs one "column" (usually categorical).
- Plan 3 to 6 steps, focused specifically on the user's stated goal. Don't pad with irrelevant steps.
"""


def _extract_json(raw: str) -> dict:
    """LLMs sometimes wrap JSON in markdown fences despite instructions — strip those defensively."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {"steps": []}


def plan_node(state: dict) -> dict:
    schema = state["schema_summary"]
    goal = state["goal"]

    llm = get_llm_provider()
    user_message = (
        f"Dataset schema (only use these exact column names):\n{json.dumps(schema)}\n\n"
        f"User goal: {goal}"
    )

    steps = []
    for attempt in range(2):  # try once, retry once if empty/malformed
        raw = llm.chat(PLANNER_SYSTEM_PROMPT, user_message)
        parsed = _extract_json(raw)
        steps = parsed.get("steps", [])

        if steps:
            break

        # Debug visibility: if this ever comes back empty again, you'll see
        # the raw LLM output in the uvicorn terminal to know exactly why
        # parsing failed (extra prose, wrong fence, truncated JSON, etc).
        print(f"[planner] attempt {attempt + 1} returned no usable steps. Raw LLM output:\n{raw}\n")

        if attempt == 0:
            user_message += (
                "\n\nYour previous response could not be parsed as valid JSON or had no steps. "
                "Return ONLY the JSON object described above, nothing else."
            )

    return {"plan": steps}