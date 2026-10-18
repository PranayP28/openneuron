import sqlite3
import time
import json
from services.api.app.config.settings import settings

class MetricsService:
    """Local SQLite-based metrics for privacy-preserving observability."""

    def __init__(self):
        self.db_path = "metrics.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS request_metrics (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    doc_id TEXT,
                    processing_time REAL,
                    is_legal BOOLEAN,
                    token_count INTEGER,
                    outcome TEXT
                )
            """)
            conn.commit()

    def log_request(self, request_id: str, doc_id: str, duration: float, is_legal: bool, outcome: str):
        """Logs request metadata without storing document text."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO request_metrics VALUES (?, ?, ?, ?, ?, ?, ?)",
                (request_id, time.time(), doc_id, duration, is_legal, 0, outcome)
            )
            conn.commit()

metrics_service = MetricsService()
