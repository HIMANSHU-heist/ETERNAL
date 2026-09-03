"""
Reporter node.

Turns the Analyst's raw computed results into a readable markdown report.
The system prompt explicitly forbids inventing numbers not present in the
results — the LLM's job here is synthesis and interpretation, not
computation.
"""

import json

from app.services.llm_service import get_llm_provider

REPORT_SYSTEM_PROMPT = """You are the Reporting agent in a multi-agent data analysis system.

You will receive REAL computed analysis results (not hypothetical) from an Analyst agent,
plus the user's original goal. Write a clear, structured markdown report:

1. **Summary** — what was analyzed, referencing actual numbers from the results provided.
2. **Key insights** — relevant to the user's stated goal.
3. **Data quality notes** — flag missing values or anything odd found in the results.
4. **Recommended next steps** — concrete (e.g. "this looks like a multiclass classification
   problem, try X model" or "investigate the correlation between A and B further").

Rules:
- Do NOT invent numbers that are not present in the provided results.
- If a step has status "error", mention it briefly in one line and move on — don't dwell on it.
- Be concrete and specific, not generic filler advice.
"""


def report_node(state: dict) -> dict:
    goal = state["goal"]
    results = state.get("analysis_results", [])

    llm = get_llm_provider()
    user_message = (
        f"User goal: {goal}\n\n"
        f"Computed analysis results (JSON):\n{json.dumps(results, default=str)}"
    )

    report = llm.chat(REPORT_SYSTEM_PROMPT, user_message)
    return {"report": report}
