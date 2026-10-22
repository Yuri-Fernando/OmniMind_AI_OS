"""Engineering Intake API — estado inicial (só healthcheck)."""
from pathlib import Path

from fastapi import FastAPI


def create_app(data_dir: Path, idempotency_window_s: int = 86400) -> FastAPI:
    app = FastAPI(title="Engineering Intake API", version="0.0.1")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
