"""
Grafo de orquestração com suporte a múltiplos provedores LLM.
Wrapper sobre orchestration_graph.py com roteamento dinâmico.
"""
from core.orchestration_graph import build_graph
from core.router import route_question


def build_dynamic_graph(provider: str = "openai", model: str = "gpt-4o-mini"):
    """
    Constrói o grafo do agente para o provedor especificado.

    Args:
        provider: 'openai' | 'anthropic' | 'ollama'
        model: nome do modelo (ex: 'gpt-4o-mini', 'mistral', 'claude-haiku-4-5-20251001')
    """
    return build_graph(provider=provider, model=model)
