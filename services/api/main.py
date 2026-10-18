import json
import logging
import os
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

# Allow `python services/api/main.py` from the repo root without setting PYTHONPATH.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from services.api.app.config.settings import settings  # noqa: E402
from services.api.app.orchestrator import nodes  # noqa: E402
from services.api.app.orchestrator.graph import legal_graph  # noqa: E402
from services.api.app.orchestrator.nodes import ANALYSIS_TYPES  # noqa: E402
from services.api.app.services.chunking import chunking_service  # noqa: E402
from services.api.app.services.inference import InferenceError  # noqa: E402
from services.api.app.services.ingestion import SUPPORTED_EXTENSIONS, ingestion_service  # noqa: E402
from services.api.app.services.retrieval import retrieval_service  # noqa: E402

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger("zeroday.api")

NON_LEGAL_MESSAGE = "This document does not appear to be a legal document and cannot be processed."
SECTION_TITLES = {
    "clause": "Clauses",
    "risk": "Risks",
    "obligation": "Obligations",
    "deadline": "Deadlines",
}


@dataclass
class DocumentRecord:
    doc_id: str
    path: str
    filename: str
    full_text: str
    chunks: List[str]
    category: str
    is_legal: bool


_documents: Dict[str, DocumentRecord] = {}
_documents_lock = threading.Lock()


def _warmup() -> None:
    for name, fn in (("embeddings", retrieval_service.warmup), ("model", nodes.inference_client.warmup)):
        try:
            start = time.perf_counter()
            fn()
            logger.info("Warmed up %s in %.1fs", name, time.perf_counter() - start)
        except Exception as e:  # warm-up is best effort
            logger.warning("Warm-up of %s failed: %s", name, e)


@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if settings.WARMUP_ON_STARTUP:
        threading.Thread(target=_warmup, daemon=True).start()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Privacy: Strict CORS for local-only operation
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _validate_doc_id(doc_id: str) -> str:
    try:
        return str(uuid.UUID(doc_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid document id.")


def _ingest(doc_id: str, path: str, filename: str) -> DocumentRecord:
    """Extracts, chunks, indexes and classifies a document once, so chat requests skip that work."""
    try:
        text = ingestion_service.extract_text(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {e}")
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. Scanned/image-only PDFs are not supported.",
        )

    chunks = chunking_service.chunk_text(text)
    retrieval_service.index_document(doc_id, chunks)
    try:
        category, is_legal = nodes.classify_document(doc_id, text)
    except InferenceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    record = DocumentRecord(doc_id, path, filename, text, chunks, category, is_legal)
    with _documents_lock:
        _documents[doc_id] = record
    return record


def _get_document(doc_id: str) -> DocumentRecord:
    doc_id = _validate_doc_id(doc_id)
    with _documents_lock:
        record = _documents.get(doc_id)
    if record:
        return record
    # Re-ingest lazily after a server restart.
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{ext}")
        if os.path.exists(path):
            return _ingest(doc_id, path, os.path.basename(path))
    raise HTTPException(status_code=404, detail="Document not found. Please upload it again.")


def _graph_inputs(record: DocumentRecord, query: str, request_id: Optional[str] = None) -> dict:
    return {
        "doc_id": record.doc_id,
        "request_id": request_id or str(uuid.uuid4()),
        "user_query": query,
        "full_text": record.full_text,
        "chunks": record.chunks,
        "is_legal_doc": record.is_legal,
        "routing_decision": record.category,
    }


def _section(result) -> dict:
    data = result.model_dump()
    data["title"] = SECTION_TITLES.get(result.category, result.category.title())
    return data


def _clean_query(query: str) -> str:
    query = (query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    return query[:2000]


@app.get("/health")
def health_check():
    return {"status": "healthy", "model": settings.OLLAMA_MODEL}


@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename or "document")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .pdf and .txt are allowed.")

    doc_id = str(uuid.uuid4())
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{ext}")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    size = 0
    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.")
            buffer.write(chunk)

    try:
        record = _ingest(doc_id, file_path, filename)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    return {
        "doc_id": doc_id,
        "filename": filename,
        "category": record.category,
        "is_legal": record.is_legal,
        "num_chunks": len(record.chunks),
        "num_chars": len(record.full_text),
    }


@app.post("/chat")
def chat(doc_id: str = Form(...), query: str = Form(...)):
    query = _clean_query(query)
    record = _get_document(doc_id)
    if not record.is_legal:
        return {"response": NON_LEGAL_MESSAGE, "sections": []}

    start = time.perf_counter()
    result = legal_graph.invoke(_graph_inputs(record, query))
    sections = [_section(result[f"{t}_analysis"]) for t in ANALYSIS_TYPES if result.get(f"{t}_analysis")]
    return {
        "response": result.get("final_response") or "No analysis could be generated.",
        "sections": sections,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }


def _ndjson(event: dict) -> str:
    return json.dumps(event) + "\n"


@app.post("/chat/stream")
def chat_stream(doc_id: str = Form(...), query: str = Form(...)):
    """Streams each analysis section as soon as it finishes (NDJSON), for lower perceived latency."""
    query = _clean_query(query)
    record = _get_document(doc_id)

    def events() -> Iterator[str]:
        start = time.perf_counter()
        if not record.is_legal:
            yield _ndjson({"type": "final", "response": NON_LEGAL_MESSAGE, "elapsed_ms": 0})
            return
        yield _ndjson({"type": "status", "stage": "retrieving"})
        final_response: Optional[str] = None
        request_id = str(uuid.uuid4())
        completed = False
        try:
            for update in legal_graph.stream(_graph_inputs(record, query, request_id), stream_mode="updates"):
                for node_name, values in update.items():
                    if not values:
                        continue
                    if node_name == "retrieval":
                        yield _ndjson({"type": "status", "stage": "analyzing"})
                    for t in ANALYSIS_TYPES:
                        if values.get(f"{t}_analysis"):
                            yield _ndjson({"type": "section", "section": _section(values[f"{t}_analysis"])})
                    if values.get("final_response"):
                        final_response = values["final_response"]
            completed = True
        except Exception as e:
            logger.exception("Chat stream failed")
            yield _ndjson({"type": "error", "message": f"Analysis failed: {e}"})
            return
        finally:
            # Client disconnected (e.g. pressed Stop): skip model calls still waiting for a slot.
            if not completed:
                nodes.cancel_request(request_id)
        yield _ndjson({
            "type": "final",
            "response": final_response or "No analysis could be generated.",
            "elapsed_ms": int((time.perf_counter() - start) * 1000),
        })

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.BIND_ADDRESS, port=settings.BIND_PORT)
