"""Testes de integração escritos na tarefa T4 (complementam os golden tests)."""
from fastapi.testclient import TestClient

from app.main import create_app


def _client(tmp_path):
    return TestClient(create_app(tmp_path))


def test_submit_and_query_roundtrip(tmp_path):
    client = _client(tmp_path)
    r = client.post("/v1/documents", json={"filename": "plate.dxf", "content": "0\nSECTION",
                                           "idempotency_key": "k1"})
    assert r.status_code == 202
    job = client.get(f"/v1/jobs/{r.json()['job_id']}").json()
    assert job["status"] == "QUEUED" and job["filename"] == "plate.dxf"


def test_unsupported_extension(tmp_path):
    r = _client(tmp_path).post("/v1/documents", json={"filename": "run.exe", "content": "x",
                                                      "idempotency_key": "k2"})
    assert r.status_code == 422
    assert r.json()["detail"]["error_code"] == "UNSUPPORTED_FORMAT"


def test_extra_field_rejected(tmp_path):
    r = _client(tmp_path).post("/v1/documents", json={"filename": "a.pdf", "content": "x",
                                                      "idempotency_key": "k3", "shell": "rm -rf /"})
    assert r.status_code == 422
