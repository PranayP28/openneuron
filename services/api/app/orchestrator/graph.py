from langgraph.graph import END, StateGraph

from services.api.app.orchestrator.nodes import (
    analyze_clause,
    analyze_deadline,
    analyze_obligation,
    analyze_risk,
    ingestion_node,
    merge_node,
    retrieval_node,
    router_node,
)
from services.api.app.orchestrator.state import GraphState

ANALYSIS_NODES = {
    "analyze_clause": analyze_clause,
    "analyze_risk": analyze_risk,
    "analyze_obligation": analyze_obligation,
    "analyze_deadline": analyze_deadline,
}


def create_legal_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("router", router_node)
    workflow.add_node("retrieval", retrieval_node)
    for name, node in ANALYSIS_NODES.items():
        workflow.add_node(name, node)
    workflow.add_node("merge", merge_node)

    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "router")
    workflow.add_conditional_edges(
        "router",
        lambda state: "retrieve" if state.get("is_legal_doc") else "end",
        {"end": END, "retrieve": "retrieval"},
    )

    # Parallel fan-out: all analyses run in the same superstep, then fan in to merge.
    for name in ANALYSIS_NODES:
        workflow.add_edge("retrieval", name)
    workflow.add_edge(list(ANALYSIS_NODES), "merge")
    workflow.add_edge("merge", END)

    return workflow.compile()


legal_graph = create_legal_graph()
