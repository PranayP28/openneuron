import logging
import os

import PyPDF2

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".pdf", ".txt")

class IngestionService:
    """Handles local extraction of text from legal documents."""

    def extract_text(self, file_path: str) -> str:
        """Extracts text from PDF or TXT files locally."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {ext}. Only .pdf and .txt are allowed.")
        if ext == '.pdf':
            return self._extract_pdf(file_path)
        return self._extract_txt(file_path)

    def _extract_pdf(self, file_path: str) -> str:
        pages = []
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
        except Exception as e:
            # Log only the error, not the file path if it contains sensitive info
            logger.error("Error extracting PDF: %s", e)
            raise
        return "\n".join(pages).strip()

    def _extract_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Fallback for other common encodings
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read().strip()

ingestion_service = IngestionService()
