"""
Rotas adicionais da API AIOS.
"""
from fastapi import APIRouter, Query
from core.agent_runtime import AgentRuntime
from core.config import get_active_llm_provider, OLLAMA_DEFAULT_MODEL

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "provider": get_active_llm_provider()}


@router.post("/ask")
def ask(
    question: str,
    provider: str = Query(default=None),
    model: str = Query(default=None),
):
    prov = provider or get_active_llm_provider()
    mdl = model or ("gpt-4o-mini" if prov == "openai" else OLLAMA_DEFAULT_MODEL)
    runtime = AgentRuntime(provider=prov, model=mdl)
    result = runtime.run(question)
    return {
        "answer": result.get("answer", ""),
        "provider": prov,
        "model": mdl,
        "latency_ms": result.get("latency_ms", 0),
    }


@router.get("/providers")
def list_providers():
    return {
        "available": ["openai", "anthropic", "ollama"],
        "models": {
            "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            "anthropic": ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"],
            "ollama": ["mistral", "llava:7b", "llama3"],
        },
    }
