import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Tuple, Optional
from services.api.app.config.settings import settings

class RetrievalService:
    """Handles local hybrid retrieval using ChromaDB."""

    def __init__(self):
        # Initialize local persistent client
        # In a real app, this would be a persistent directory. For now, ephemeral or local.
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="legal_docs",
            metadata={"hnsw:space": "cosine"}
        )

    def index_document(self, doc_id: str, chunks: List[str]):
        """Indexes document chunks into the vector store."""
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    def retrieve(self, query: str, doc_id: Optional[str] = None) -> List[str]:
        """
        Retrieves the most relevant chunks.
        If doc_id is provided, it filters results to that document.
        """
        where_filter = {"doc_id": doc_id} if doc_id else None

        results = self.collection.query(
            query_texts=[query],
            n_results=settings.RETRIEVAL_K,
            where=where_filter
        )

        # Return flattened list of documents from the first query result
        return results['documents'][0] if results['documents'] else []

retrieval_service = RetrievalService()
