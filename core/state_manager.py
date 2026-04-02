"""
Gerenciador de estado do AIOS.
Define o esquema do estado compartilhado entre todos os agentes.
"""
from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    question: str
    plan: str
    context: str
    source_documents: List[Dict[str, Any]]
    answer: str
    tool_used: str
    reflection_notes: str
    iterations: int
    history: List[Dict[str, str]]
    provider: str
    model: str
    latency_ms: float
    tokens_used: int


def new_state(question: str, provider: str = "openai", model: str = "gpt-4o-mini") -> AgentState:
    """Cria um estado inicial limpo para uma nova query."""
    return AgentState(
        question=question,
        plan="",
        context="",
        source_documents=[],
        answer="",
        tool_used="",
        reflection_notes="",
        iterations=0,
        history=[],
        provider=provider,
        model=model,
        latency_ms=0.0,
        tokens_used=0,
    )
