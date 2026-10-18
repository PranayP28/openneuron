import ollama
from typing import Optional, Dict, Any
from services.api.app.config.settings import settings

class InferenceClient:
    """Interface for Ollama inference to allow for easy mocking in tests."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates a response from the local Gemma model."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"

        try:
            # Use ollama.generate directly
            response = ollama.generate(
                model=settings.OLLAMA_MODEL,
                prompt=full_prompt,
                options={
                    "temperature": settings.LLM_TEMPERATURE,
                    "seed": settings.LLM_SEED,
                    "num_ctx": settings.LLM_CONTEXT_WINDOW,
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Inference error: {str(e)}")
            raise

class MockInferenceClient:
    """Mock client for unit tests to avoid needing Ollama running."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Simulate legal doc classification
        if "classify" in prompt.lower() or "category" in prompt.lower():
            # Return non_legal if specifically mentioning apples or weather
            if "apples" in prompt.lower() or "weather" in prompt.lower():
                return "non_legal"
            # Otherwise, if it looks like a legal doc, return rental
            if any(word in prompt.lower() for word in ["agreement", "lease", "contract", "rental"]):
                return "rental"
            return "non_legal"

        return "MOCK_RESPONSE: This is a simulated response for testing purposes."




# Singleton instance
inference_client = InferenceClient()
