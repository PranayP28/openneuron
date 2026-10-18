import hashlib
import json
import logging
import os
import time
from typing import Any, Dict

from services.api.app.config.settings import settings

logger = logging.getLogger(__name__)


class ManifestService:
    """Creates a reproduction manifest for every LLM request."""

    def __init__(self, directory: str = None):
        self.directory = directory or settings.MANIFEST_DIR
        os.makedirs(self.directory, exist_ok=True)

    def create_manifest(self, request_id: str, prompt: str, model_tag: str, config: Dict[str, Any]) -> str:
        """Generates a JSON manifest for reproducibility (stores a prompt hash, never the prompt)."""
        manifest = {
            "request_id": request_id,
            "timestamp": time.time(),
            "model": model_tag,
            # sha256 is stable across processes, unlike Python's salted hash().
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "config": config,
            "seed": settings.LLM_SEED,
            "temperature": settings.LLM_TEMPERATURE,
        }

        file_path = os.path.join(self.directory, f"{request_id}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(manifest, f)
        except OSError as e:
            logger.warning("Failed to write manifest: %s", e)
        return file_path


manifest_service = ManifestService()
