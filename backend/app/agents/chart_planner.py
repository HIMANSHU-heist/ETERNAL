"""
Parses a natural-language chart request ("make a pie chart of gender",
"scatter plot of bmi vs blood sugar") into a structured JSON chart spec
using the LLM — grounded strictly in the actual schema's column names.
The LLM only decides WHAT to chart; chart_builder.py computes the REAL
numbers via pandas.
"""

import json
import re

from app.services.llm_service import get_llm_provider

CHART_PLANNER_SYSTEM_PROMPT = """You turn a user's natural-language chart request into a structured JSON spec.

Return ONLY valid JSON, no prose, no markdown fences. Shape:
{
  "chart_type": "bar" | "pie" | "line" | "scatter" | "histogram" | "heatmap" | "grouped_bar",
  "column": "COLUMN_NAME or null",
  "column2": "COLUMN_NAME or null",
  "columns": ["COL1", "COL2"] or null,
  "bin_size": number or null,
  "title": "short human-readable chart title"
}

HOW TO REASON (apply every time, regardless of domain or column names):

1. Figure out how many variables are actually involved, even if the user didn't spell it out:
   - ONE column mentioned/implied → bar/pie/histogram/line depending on its data type.
   - TWO numeric columns, no grouping implied → "scatter".
   - ONE categorical + ONE numeric column, where the numeric one should be split into
     ranges/bins and compared ACROSS the categorical groups → "grouped_bar". Categorical
     column → "column", numeric column → "column2".
   - 3+ numeric columns, or "relationship between everything" / "correlation" → "heatmap".

2. The user will often be VAGUE or informal — they may not say "grouped", "bins", "compare",
   or name both columns explicitly. Read INTENT, not just keywords:
   - "show X by Y" / "X across Y" / "break down X by Y" / "split by Y" / "how does X differ for Y"
     all mean the same thing: X (numeric) vs Y (categorical) → likely grouped_bar or bar depending
     on whether X needs binning.
   - If the user names only ONE concept but that concept is clearly numeric and continuous
     (e.g. "show me blood sugar spread"), default to "histogram" — don't ask for more info.
   - If the user names a numeric concept AND casually mentions another attribute in the same
     breath ("blood sugar levels for each risk group", "spending across regions"), treat the
     second attribute as the grouping column even if they didn't say "compare" or "group by".
   - When truly ambiguous between two reasonable interpretations, pick the one that produces
     the MORE informative chart (e.g. prefer grouped_bar over a plain histogram if a categorical
     column is mentioned anywhere in the request, since it shows more relationships for the
     same information).

3. NEVER assume specific column names — match user's described concepts to whatever columns
   actually exist in the schema, by meaning, not by literally repeating example names.

4. Pick bin_size sensibly: if the user gives a number, use it. If not, look at the numeric
   column's actual range in the schema (min/max) and pick a bin width that yields roughly
   5-10 bins — never default blindly to 10 regardless of the column's scale.

5. ONLY use column names that literally exist in the schema provided. Never invent one.

6. If after all this reasoning nothing sensible can be built (e.g. user's request has no
   plottable concept at all), set "chart_type" to null rather than guessing wildly.
"""


def _extract_json(raw: str) -> dict:
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
        return {}


def plan_chart(schema_summary: dict, user_message: str) -> dict:
    llm = get_llm_provider()
    user_prompt = (
        f"Dataset schema (only use these exact column names):\n{json.dumps(schema_summary)}\n\n"
        f"User's chart request: {user_message}"
    )
    raw = llm.chat(CHART_PLANNER_SYSTEM_PROMPT, user_prompt)
    return _extract_json(raw)