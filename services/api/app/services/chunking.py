from typing import List

from services.api.app.config.settings import settings

_BOUNDARIES = ("\n\n", "\n", ". ", "; ", " ")


class ChunkingService:
    """Handles context-aware chunking for legal documents."""

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Splits text into overlapping chunks, preferring paragraph/sentence/word
        boundaries near the end of each window so clauses are not cut mid-word.
        """
        if not text:
            return []

        size = chunk_size or settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP if overlap is None else overlap
        # Guard against a non-advancing window (would loop forever).
        overlap = max(0, min(overlap, size - 1))

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + size, text_len)
            if end < text_len:
                min_end = start + int(size * 0.8)
                for boundary in _BOUNDARIES:
                    idx = text.rfind(boundary, min_end, end)
                    if idx != -1:
                        end = idx + len(boundary)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start = max(end - overlap, start + 1)

        return chunks


chunking_service = ChunkingService()
