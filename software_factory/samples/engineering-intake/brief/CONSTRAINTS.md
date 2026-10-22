# Constraints

- Python 3.10+, FastAPI, Pydantic v2, SQLite (stdlib `sqlite3`), pytest.
- A aplicação expõe `create_app(data_dir: Path, idempotency_window_s: int = 86400)` em
  `app/main.py`; testes usam `fastapi.testclient.TestClient`.
- Erros de domínio respondem `{"detail": {"error_code": "<CODIGO>"}}`.
- Códigos: `UNSAFE_PATH`, `UNSUPPORTED_FORMAT`, `IDEMPOTENCY_KEY_MISMATCH`, `JOB_NOT_FOUND`.
- Sem segredos no repositório, sem rede nos testes, sem dependências novas.
- Não alterar `tests/test_health.py` nem o endpoint `/health`.
