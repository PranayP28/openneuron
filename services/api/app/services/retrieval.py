import threading
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from services.api.app.config.settings import settings


class RetrievalService:
    """Handles local retrieval using an in-process ChromaDB collection."""

    def __init__(self):
        # Privacy: disable Chroma's anonymous usage telemetry.
        self.client = chromadb.Client(ChromaSettings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name="legal_docs",
            metadata={"hnsw:space": "cosine"},
        )
        self._chunk_counts: dict = {}
        self._lock = threading.Lock()

    def index_document(self, doc_id: str, chunks: List[str]):
        """Indexes document chunks, replacing any previous index for the same document."""
        with self._lock:
            if self._chunk_counts.get(doc_id):
                self.collection.delete(where={"doc_id": doc_id})
            if chunks:
                self.collection.add(
                    documents=chunks,
                    ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
                    metadatas=[{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))],
                )
            self._chunk_counts[doc_id] = len(chunks)

    def is_indexed(self, doc_id: str) -> bool:
        return self._chunk_counts.get(doc_id, 0) > 0

    def retrieve(self, query: str, doc_id: Optional[str] = None, k: Optional[int] = None) -> List[str]:
        """
        Retrieves the most relevant chunks, returned in document order.
        If doc_id is provided, results are filtered to that document.
        """
        n_results = k or settings.RETRIEVAL_K
        if doc_id is not None:
            n_results = min(n_results, self._chunk_counts.get(doc_id, 0))
        if n_results <= 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"doc_id": doc_id} if doc_id else None,
        )

        documents = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
        ordered = sorted(zip(documents, metadatas), key=lambda pair: (pair[1] or {}).get("chunk_index", 0))
        return [doc for doc, _ in ordered]

    def warmup(self) -> None:
        """Loads the embedding model so the first upload is not slowed by a cold start."""
        ef = getattr(self.collection, "_embedding_function", None)
        if ef is not None:
            ef(["warmup"])


retrieval_service = RetrievalService()
