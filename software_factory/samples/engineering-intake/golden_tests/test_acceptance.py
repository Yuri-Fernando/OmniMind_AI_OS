"""Golden tests de aceitação — escritos por humano ANTES da implementação.

O implementer não pode editá-los (caminho protegido); o runner externo os
copia para o worktree de integração só na verificação. Cada teste cita os
R-IDs que prova.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _client(tmp_path, **kw):
    return TestClient(create_app(tmp_path, **kw))


def _post(client, filename="plate.dxf", content="0\nSECTION\n", key="key-1", **extra):
    body = {"filename": filename, "content": content, "idempotency_key": key, **extra}
    return client.post("/v1/documents", json=body)


def _files(root: Path):
    storage = root / "storage"
    return sorted(p for p in storage.rglob("*") if p.is_file()) if storage.exists() else []


def test_post_returns_202_with_job_id(tmp_path):
    """R-001"""
    r = _post(_client(tmp_path), metadata={"project": "demo"})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "QUEUED" and len(body["job_id"]) >= 16


def test_file_stored_under_isolated_job_dir(tmp_path):
    """R-001, R-005"""
    client = _client(tmp_path)
    job_id = _post(client, content="conteudo-original").json()["job_id"]
    stored = tmp_path / "storage" / job_id / "plate.dxf"
    assert stored.read_text(encoding="utf-8") == "conteudo-original"
    assert _files(tmp_path) == [stored]


def test_get_job_returns_valid_status(tmp_path):
    """R-002"""
    client = _client(tmp_path)
    job_id = _post(client).json()["job_id"]
    r = client.get(f"/v1/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["status"] in {"QUEUED", "RUNNING", "COMPLETED", "FAILED"}


def test_get_unknown_job_is_404(tmp_path):
    """R-002"""
    r = _client(tmp_path).get("/v1/jobs/does-not-exist")
    assert r.status_code == 404
    assert r.json()["detail"]["error_code"] == "JOB_NOT_FOUND"


def test_same_key_same_content_returns_original_job(tmp_path):
    """R-003"""
    client = _client(tmp_path)
    first = _post(client).json()["job_id"]
    second = _post(client)
    assert second.status_code == 202 and second.json()["job_id"] == first
    assert len(_files(tmp_path)) == 1


def test_same_key_different_content_is_409(tmp_path):
    """R-003"""
    client = _client(tmp_path)
    _post(client, content="A")
    r = _post(client, content="B")
    assert r.status_code == 409
    assert r.json()["detail"]["error_code"] == "IDEMPOTENCY_KEY_MISMATCH"


def test_invalid_payload_is_422_without_side_effects(tmp_path):
    """R-004"""
    client = _client(tmp_path)
    for body in ({"content": "x", "idempotency_key": "k"},
                 {"filename": "a.pdf", "content": 123, "idempotency_key": "k"},
                 {"filename": "a.exe", "content": "x", "idempotency_key": "k"}):
        assert client.post("/v1/documents", json=body).status_code == 422
    assert _files(tmp_path) == []
    db = tmp_path / "intake.db"
    if db.exists():
        with sqlite3.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0


def test_path_traversal_is_rejected(tmp_path):
    """R-005, R-007"""
    client = _client(tmp_path)
    for name in ("../evil.pdf", "..\\evil.pdf", "sub/evil.pdf", "/abs/evil.pdf", "C:evil.pdf", ".."):
        r = _post(client, filename=name, key=f"k-{name}")
        assert r.status_code == 422, name
        assert r.json()["detail"]["error_code"] == "UNSAFE_PATH", name
    assert _files(tmp_path) == []
    assert not (tmp_path / "evil.pdf").exists() and not (tmp_path.parent / "evil.pdf").exists()


def test_events_recorded_with_error_code(tmp_path):
    """R-006"""
    client = _client(tmp_path)
    job_id = _post(client, content="A").json()["job_id"]
    _post(client, content="B")
    events = client.get(f"/v1/jobs/{job_id}").json()["events"]
    names = [e["event"] for e in events]
    assert names[0] == "JOB_CREATED"
    assert any(e["error_code"] == "IDEMPOTENCY_KEY_MISMATCH" for e in events)


def test_concurrent_same_key_creates_single_job(tmp_path):
    """R-003, R-007"""
    client = _client(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: _post(client, key="race"), range(8)))
    assert {r.status_code for r in results} == {202}
    assert len({r.json()["job_id"] for r in results}) == 1
    assert len(_files(tmp_path)) == 1
