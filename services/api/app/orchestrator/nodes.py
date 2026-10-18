import time
import uuid
from typing import Tuple

from services.api.app.config.settings import settings
from services.api.app.observability.manifest import manifest_service
from services.api.app.observability.metrics import metrics_service
from services.api.app.orchestrator.policy import safety_service
from services.api.app.orchestrator.state import AnalysisResult, GraphState
from services.api.app.prompts.templates import (
    NON_LEGAL_CATEGORY,
    PROMPT_VERSION,
    get_prompt,
    get_system_prompt,
    parse_category,
)
from services.api.app.services.chunking import chunking_service
from services.api.app.services.inference import InferenceError, inference_client
from services.api.app.services.ingestion import ingestion_service
from services.api.app.services.retrieval import retrieval_service
from services.api.app.services.verification import verification_service

ANALYSIS_TYPES = ("clause", "risk", "obligation", "deadline")
PROMPT_KEYS = {
    "clause": "clause_analysis",
    "risk": "risk_detection",
    "obligation": "obligation_extraction",
    "deadline": "deadline_extraction",
}
CLASSIFY_SAMPLE_CHARS = 2000
MAX_EVIDENCE = 3


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def classify_document(doc_id: str, text: str) -> Tuple[str, bool]:
    """Classifies a document with the local model. Returns (category, is_legal)."""
    start = time.perf_counter()
    prompt = get_prompt("classify_label", text=text[:CLASSIFY_SAMPLE_CHARS])
    category = parse_category(inference_client.generate(prompt, get_system_prompt("classify_label")))
    is_legal = category != NON_LEGAL_CATEGORY
    metrics_service.log_request(str(uuid.uuid4()), doc_id, time.perf_counter() - start, is_legal, category)
    return category, is_legal


def ingestion_node(state: GraphState):
    """Extracts text, chunks and indexes the document (skipped if already done)."""
    doc_id = state["doc_id"]
    if state.get("full_text") and state.get("chunks") and retrieval_service.is_indexed(doc_id):
        return {}

    text = ingestion_service.extract_text(doc_id)
    chunks = chunking_service.chunk_text(text)
    retrieval_service.index_document(doc_id, chunks)
    return {"full_text": text, "chunks": chunks}


def router_node(state: GraphState):
    """Classifies the document and decides if it's a legal document (skipped if already classified)."""
    if state.get("routing_decision"):
        return {}
    category, is_legal = classify_document(state["doc_id"], state.get("full_text", ""))
    return {"is_legal_doc": is_legal, "routing_decision": category}


def retrieval_node(state: GraphState):
    """Retrieves relevant context based on the user query."""
    context = retrieval_service.retrieve(state["user_query"], doc_id=state["doc_id"])
    return {"retrieved_context": context}


def analysis_node(state: GraphState, analysis_type: str):
    """Generic analysis node; the four instances run in parallel."""
    start = time.perf_counter()
    prompt_key = PROMPT_KEYS[analysis_type]
    context = "\n\n".join(state.get("retrieved_context") or [])
    prompt = get_prompt(prompt_key, question=state.get("user_query", ""), text=context)
    system = get_system_prompt(prompt_key)

    # Reproducibility: Create manifest
    manifest_service.create_manifest(
        str(uuid.uuid4()),
        prompt,
        settings.OLLAMA_MODEL,
        {"temp": settings.LLM_TEMPERATURE, "prompt_key": prompt_key, "prompt_version": PROMPT_VERSION},
    )

    try:
        response = inference_client.generate(prompt, system)
    except InferenceError as e:
        result = AnalysisResult(
            category=analysis_type, findings=[str(e)], evidence=[], status="error", elapsed_ms=_elapsed_ms(start)
        )
        return {f"{analysis_type}_analysis": result}

    # Verification Step: Grounding
    is_grounded, evidence = verification_service.verify_claim(response, context)
    status = "ok"
    if not is_grounded:
        finding = "Verification failed: Claim not grounded in text."
        status = "ungrounded"
    else:
        # Safety Validation per section so one unsafe finding doesn't hide the others.
        is_safe, error = safety_service.validate_response(response)
        finding = response if is_safe else f"Safety Error: {error}. Please consult a legal professional."
        status = "ok" if is_safe else "blocked"

    result = AnalysisResult(
        category=analysis_type,
        findings=[finding],
        evidence=evidence[:MAX_EVIDENCE],
        grounded=is_grounded,
        status=status,
        elapsed_ms=_elapsed_ms(start),
    )
    return {f"{analysis_type}_analysis": result}


# Wrappers for parallel execution
def analyze_clause(state: GraphState): return analysis_node(state, "clause")
def analyze_risk(state: GraphState): return analysis_node(state, "risk")
def analyze_obligation(state: GraphState): return analysis_node(state, "obligation")
def analyze_deadline(state: GraphState): return analysis_node(state, "deadline")


def merge_node(state: GraphState):
    """Merges results and applies a final safety validation."""
    findings = []
    for analysis_type in ANALYSIS_TYPES:
        res = state.get(f"{analysis_type}_analysis")
        if res:
            findings.append(f"[{res.category.upper()}] {res.findings[0]}")

    summary = "\n\n".join(findings)

    is_safe, error = safety_service.validate_response(summary)
    if not is_safe and "Safety Error" not in summary:
        summary = f"Safety Error: {error}. Please consult a legal professional."

    return {"final_response": summary}
