"""
Wires the three agent nodes into a LangGraph StateGraph.

Current flow is linear: planner -> analyst -> reporter -> END.
This is intentionally simple for Step 3. A natural Step 4 extension is a
conditional edge after the planner (e.g. route to an "ml_agent" node when
the plan/goal implies prediction, skip it otherwise) — the graph structure
already supports that without restructuring anything above it.
"""

from langgraph.graph import END, StateGraph

from app.agents.analyst import analyst_node
from app.agents.planner import plan_node
from app.agents.reporting import report_node
from app.agents.state import AgentState

_compiled_graph = None


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("reporter", report_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "analyst")
    graph.add_edge("analyst", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


def get_graph():
    """Cache the compiled graph so we don't rebuild it on every request."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
