import os
from typing import List, Dict
import PyPDF2
from services.api.app.config.settings import settings

class IngestionService:
    """Handles local extraction of text from legal documents."""

    def extract_text(self, file_path: str) -> str:
        """Extracts text from PDF or TXT files locally."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return self._extract_pdf(file_path)
        elif ext == '.txt':
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Only .pdf and .txt are allowed.")

    def _extract_pdf(self, file_path: str) -> str:
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            # Log only the error, not the file path if it contains sensitive info
            print(f"Error extracting PDF: {str(e)}")
            raise
        return text.strip()

    def _extract_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Fallback for other common encodings
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read().strip()

ingestion_service = IngestionService()
