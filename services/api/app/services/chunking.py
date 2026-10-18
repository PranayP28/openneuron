from typing import List
from services.api.app.config.settings import settings

class ChunkingService:
    """Handles context-aware chunking for legal documents."""

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks based on settings.
        In a real legal app, this would be improved to split by clause boundaries.
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + settings.CHUNK_SIZE
            chunk = text[start:end]
            chunks.append(chunk)
            # Move start forward by chunk size minus overlap
            start += (settings.CHUNK_SIZE - settings.CHUNK_OVERLAP)

        return chunks

chunking_service = ChunkingService()
