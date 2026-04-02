"""Configurações centrais do AIOS — carregadas do .env."""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Ollama (local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "mistral")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava:7b")

# RAG
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "vector_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "3"))

# Audio / Vídeo
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# Observabilidade
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Guardrails
MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "4000"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2000"))


def get_active_llm_provider() -> str:
    """Retorna o provedor LLM ativo baseado nas chaves disponíveis."""
    if OPENAI_API_KEY:
        return "openai"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return "ollama"
