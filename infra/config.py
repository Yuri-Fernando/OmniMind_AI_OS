"""Configurações de infraestrutura (Docker, portas, volumes)."""

API_PORT = 8000
API_HOST = "0.0.0.0"
VECTOR_DB_VOLUME = "/data/vector_db"
LOG_VOLUME = "/data/logs"
OLLAMA_SERVICE_URL = "http://ollama:11434"
