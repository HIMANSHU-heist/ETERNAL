"""
Shared state that flows through the LangGraph graph.

Every node (planner, analyst, reporter) receives this dict and returns a
partial dict of updates — LangGraph merges updates into the running state
automatically (standard LangGraph reducer behavior for TypedDict state).
"""

from typing import Any, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    dataset_id: str
    goal: str
    schema_summary: dict

    plan: List[dict]              # produced by planner node
    analysis_results: List[dict]  # produced by analyst node (REAL computed values)
    report: str                   # produced by reporter node

    error: Optional[str]
