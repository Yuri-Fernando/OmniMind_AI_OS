from fastapi.testclient import TestClient

from app.main import create_app


def test_health(tmp_path):
    client = TestClient(create_app(tmp_path))
    assert client.get("/health").json() == {"status": "ok"}
