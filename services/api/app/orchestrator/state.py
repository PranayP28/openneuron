from typing import List, Optional, TypedDict

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    category: str
    findings: List[str]
    evidence: List[str]
    risk_level: str = "low"
    grounded: bool = False
    status: str = "ok"  # ok | ungrounded | blocked | error
    elapsed_ms: int = 0


class GraphState(TypedDict, total=False):
    """State shared across the LangGraph nodes."""
    doc_id: str
    request_id: str
    user_query: str
    full_text: str
    chunks: List[str]
    retrieved_context: List[str]

    # Parallel analysis results
    clause_analysis: Optional[AnalysisResult]
    risk_analysis: Optional[AnalysisResult]
    obligation_analysis: Optional[AnalysisResult]
    deadline_analysis: Optional[AnalysisResult]

    # Final response
    final_response: Optional[str]
    is_legal_doc: bool
    routing_decision: Optional[str]
