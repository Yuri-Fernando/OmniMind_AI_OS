"""Configuração de ambiente e variáveis de infraestrutura do AIOS."""
import os
from dotenv import load_dotenv

load_dotenv()

class EnvConfig:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "mistral")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "vector_db")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @classmethod
    def validate(cls) -> dict:
        warnings = []
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            warnings.append("Nenhuma API key configurada — usando Ollama local.")
        if not cls.LANGFUSE_PUBLIC_KEY:
            warnings.append("LANGFUSE_PUBLIC_KEY ausente — tracing desabilitado.")
        return {"warnings": warnings, "ok": True}

    @classmethod
    def summary(cls) -> str:
        return (
            f"OpenAI: {'✅' if cls.OPENAI_API_KEY else '❌'} | "
            f"Anthropic: {'✅' if cls.ANTHROPIC_API_KEY else '❌'} | "
            f"Ollama: {cls.OLLAMA_BASE_URL}"
        )

env = EnvConfig()
