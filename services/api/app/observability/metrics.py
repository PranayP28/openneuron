import logging
import sqlite3
import threading
import time

from services.api.app.config.settings import settings

logger = logging.getLogger(__name__)


class MetricsService:
    """Local SQLite-based metrics for privacy-preserving observability."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.METRICS_DB_PATH
        self._lock = threading.Lock()
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

    def log_request(self, request_id: str, doc_id: str, duration: float, is_legal: bool, outcome: str):
        """Logs request metadata without storing document text. Never raises."""
        try:
            with self._lock, sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO request_metrics VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (request_id, time.time(), doc_id, duration, is_legal, 0, outcome),
                )
        except sqlite3.Error as e:
            logger.warning("Failed to log metrics: %s", e)


metrics_service = MetricsService()
