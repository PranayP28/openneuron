import time
import json
import uuid
from typing import Any, Dict
from services.api.app.config.settings import settings

class ManifestService:
    """Creates a reproduction manifest for every LLM request."""

    def create_manifest(self, request_id: str, prompt: str, model_tag: str, config: Dict[str, Any]) -> str:
        """Generates a JSON manifest for reproducibility."""
        manifest = {
            "request_id": request_id,
            "timestamp": time.time(),
            "model": model_tag,
            "prompt_hash": hash(prompt),
            "config": config,
            "seed": settings.LLM_SEED,
            "temperature": settings.LLM_TEMPERATURE
        }

        file_path = f"manifests/{request_id}.json"
        # Ensure directory exists
        import os
        os.makedirs("manifests", exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return file_path

manifest_service = ManifestService()
