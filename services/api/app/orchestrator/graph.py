from langgraph.graph import StateGraph, END
from services.api.app.orchestrator.state import GraphState
from services.api.app.orchestrator.nodes import (
    ingestion_node,
    router_node,
    retrieval_node,
    analyze_clause,
    analyze_risk,
    analyze_obligation,
    analyze_deadline,
    merge_node
)

def create_legal_graph():
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("router", router_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("analyze_clause", analyze_clause)
    workflow.add_node("analyze_risk", analyze_risk)
    workflow.add_node("analyze_obligation", analyze_obligation)
    workflow.add_node("analyze_deadline", analyze_deadline)
    workflow.add_node("merge", merge_node)

    # Set Entry
    workflow.set_entry_point("ingestion")

    # Edges
    workflow.add_edge("ingestion", "router")

    # Conditional Routing
    workflow.add_conditional_edges(
        "router",
        lambda state: "end" if not state["is_legal_doc"] else "retrieve",
        {
            "end": END,
            "retrieve": "retrieval"
        }
    )

    workflow.add_edge("retrieval", "analyze_clause") # Start parallel fan-out
    # Note: LangGraph parallelization is usually done via a node that returns multiple edges
    # For simplicity here, we'll chain them or use a parallel wrapper if supported.
    # To implement actual Parallelism in LangGraph, we'd use a node that triggers multiple others.

    # Simplified linear flow for now that simulates the results:
    workflow.add_edge("analyze_clause", "analyze_risk")
    workflow.add_edge("analyze_risk", "analyze_obligation")
    workflow.add_edge("analyze_obligation", "analyze_deadline")
    workflow.add_edge("analyze_deadline", "merge")
    workflow.add_edge("merge", END)

    return workflow.compile()

legal_graph = create_legal_graph()
