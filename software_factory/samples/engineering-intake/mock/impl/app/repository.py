"""Persistência SQLite de jobs e eventos, com idempotência por chave + SHA-256."""
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    content_sha256 TEXT NOT NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    event TEXT NOT NULL,
    error_code TEXT,
    at TEXT NOT NULL
);
"""


class IdempotencyMismatch(Exception):
    def __init__(self, job_id: str):
        super().__init__(job_id)
        self.job_id = job_id


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobRepository:
    def __init__(self, db_path: Path, idempotency_window_s: int = 86400):
        self.db_path = Path(db_path)
        self.window = timedelta(seconds=idempotency_window_s)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except IdempotencyMismatch:
            conn.commit()  # o evento de conflito precisa ficar registrado
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_or_get(self, idempotency_key: str, content_sha256: str, filename: str) -> Tuple[str, bool]:
        """Devolve (job_id, replay). Levanta IdempotencyMismatch se a chave já existe com outro conteúdo."""
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
            if row is not None:
                created = datetime.fromisoformat(row["created_at"])
                if _now() - created <= self.window:
                    if row["content_sha256"] == content_sha256:
                        return row["job_id"], True
                    self._event(conn, row["job_id"], "IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_KEY_MISMATCH")
                    raise IdempotencyMismatch(row["job_id"])
                # fora da janela: a chave é liberada, o job antigo continua consultável
                conn.execute("UPDATE jobs SET idempotency_key = ? WHERE job_id = ?",
                             (f"expired:{row['job_id']}:{idempotency_key}", row["job_id"]))
            job_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO jobs (job_id, idempotency_key, content_sha256, filename, status, created_at)"
                " VALUES (?, ?, ?, ?, 'QUEUED', ?)",
                (job_id, idempotency_key, content_sha256, filename, _now().isoformat()))
            self._event(conn, job_id, "JOB_CREATED", None)
            return job_id, False

    def delete(self, job_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM job_events WHERE job_id = ?", (job_id,))
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))

    def get(self, job_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            events = conn.execute("SELECT event, error_code, at FROM job_events WHERE job_id = ? ORDER BY id",
                                  (job_id,)).fetchall()
            return {"job_id": row["job_id"], "status": row["status"], "filename": row["filename"],
                    "events": [dict(e) for e in events]}

    def count_jobs(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    @staticmethod
    def _event(conn: sqlite3.Connection, job_id: str, event: str, error_code: Optional[str]) -> None:
        conn.execute("INSERT INTO job_events (job_id, event, error_code, at) VALUES (?, ?, ?, ?)",
                     (job_id, event, error_code, _now().isoformat()))

    def events(self, job_id: str) -> List[dict]:
        job = self.get(job_id)
        return job["events"] if job else []
