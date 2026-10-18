import logging
import re
from typing import Optional

import ollama

from services.api.app.config.settings import settings

logger = logging.getLogger(__name__)


class InferenceError(RuntimeError):
    """Raised when the local model cannot produce a response."""


class InferenceClient:
    """Interface for Ollama inference to allow for easy mocking in tests."""

    def __init__(self):
        self._client = ollama.Client(host=settings.OLLAMA_BASE_URL, timeout=settings.LLM_TIMEOUT_SECONDS)

    def _options(self, max_tokens: Optional[int] = None) -> dict:
        return {
            "temperature": settings.LLM_TEMPERATURE,
            "seed": settings.LLM_SEED,
            "num_ctx": settings.LLM_CONTEXT_WINDOW,
            "num_predict": max_tokens or settings.LLM_MAX_TOKENS,
        }

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generates a response from the local Gemma model."""
        try:
            response = self._client.generate(
                model=settings.OLLAMA_MODEL,
                prompt=prompt,
                system=system_prompt or None,
                options=self._options(max_tokens),
                keep_alive=settings.LLM_KEEP_ALIVE,
            )
            return response["response"].strip()
        except Exception as e:
            logger.error("Inference error: %s", e)
            raise InferenceError(
                f"Local model '{settings.OLLAMA_MODEL}' is unavailable at {settings.OLLAMA_BASE_URL}: {e}"
            ) from e

    def warmup(self) -> None:
        """Loads the model into memory so the first real request is not slowed by a cold start."""
        self._client.generate(
            model=settings.OLLAMA_MODEL,
            prompt="",
            keep_alive=settings.LLM_KEEP_ALIVE,
        )


class MockInferenceClient:
    """Mock client for unit tests to avoid needing Ollama running."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        lowered = prompt.lower()
        # Simulate legal doc classification
        if "classify" in lowered or "category" in lowered:
            document = lowered.split("document text:")[-1]
            if "apples" in document or "weather" in document:
                return "non_legal"
            if any(word in document for word in ["agreement", "lease", "contract", "rental"]):
                return "rental"
            return "non_legal"

        # Echo the first retrieved sentence so the response stays grounded in the document.
        excerpt = ""
        match = re.search(r"Document excerpts:\s*(.+?)(?:\n\n|$)", prompt, re.S)
        if match:
            excerpt = re.split(r"(?<=[.!?])\s+", match.group(1).strip())[0]
        return f"MOCK_RESPONSE: {excerpt}".strip()

    def warmup(self) -> None:
        return None


# Singleton instance
inference_client = InferenceClient()
