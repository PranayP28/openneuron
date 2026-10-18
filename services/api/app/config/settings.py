from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "ZeroDay PS2"
    DEBUG: bool = False

    # Privacy & Local Constraints
    BIND_ADDRESS: str = "127.0.0.1"
    BIND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Local storage
    UPLOAD_DIR: str = "uploads"
    MANIFEST_DIR: str = "manifests"
    METRICS_DB_PATH: str = "metrics.db"
    MAX_UPLOAD_MB: int = 20

    # Ollama Config
    OLLAMA_MODEL: str = "gemma3:4b"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    LLM_TEMPERATURE: float = 0.0
    LLM_SEED: int = 42
    LLM_CONTEXT_WINDOW: int = 4096
    LLM_MAX_TOKENS: int = 400
    LLM_KEEP_ALIVE: str = "30m"
    LLM_TIMEOUT_SECONDS: float = 120.0
    # Concurrent model calls; match OLLAMA_NUM_PARALLEL so queued calls do not hit the timeout.
    LLM_MAX_PARALLEL: int = 1
    WARMUP_ON_STARTUP: bool = True

    # RAG Config
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_K: int = 4

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")


settings = Settings()
