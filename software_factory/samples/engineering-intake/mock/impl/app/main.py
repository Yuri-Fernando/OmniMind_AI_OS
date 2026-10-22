"""Engineering Intake API — submissão e consulta de jobs."""
import hashlib
from pathlib import Path, PurePath

from fastapi import FastAPI, HTTPException

from app.repository import IdempotencyMismatch, JobRepository
from app.schemas import ALLOWED_EXTENSIONS, DocumentIn, JobAccepted, JobOut


def _safe_filename(filename: str) -> str:
    if (filename in {".", ".."} or "/" in filename or "\\" in filename or ".." in filename
            or ":" in filename or PurePath(filename).name != filename):
        raise HTTPException(status_code=422, detail={"error_code": "UNSAFE_PATH"})
    if PurePath(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail={"error_code": "UNSUPPORTED_FORMAT"})
    return filename


def create_app(data_dir: Path, idempotency_window_s: int = 86400) -> FastAPI:
    data_dir = Path(data_dir).resolve()
    storage_root = data_dir / "storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    repo = JobRepository(data_dir / "intake.db", idempotency_window_s)
    app = FastAPI(title="Engineering Intake API", version="0.1.0")
    app.state.repo = repo
    app.state.storage_root = storage_root

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/v1/documents", status_code=202, response_model=JobAccepted)
    def submit(doc: DocumentIn) -> JobAccepted:
        filename = _safe_filename(doc.filename)
        content = doc.content.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        try:
            job_id, replay = repo.create_or_get(doc.idempotency_key, digest, filename)
        except IdempotencyMismatch:
            raise HTTPException(status_code=409, detail={"error_code": "IDEMPOTENCY_KEY_MISMATCH"})
        if not replay:
            target = (storage_root / job_id / filename).resolve()
            if storage_root not in target.parents:
                repo.delete(job_id)
                raise HTTPException(status_code=422, detail={"error_code": "UNSAFE_PATH"})
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return JobAccepted(job_id=job_id, status="QUEUED", idempotent_replay=replay)

    @app.get("/v1/jobs/{job_id}", response_model=JobOut)
    def get_job(job_id: str) -> JobOut:
        job = repo.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND"})
        return JobOut(**job)

    return app
