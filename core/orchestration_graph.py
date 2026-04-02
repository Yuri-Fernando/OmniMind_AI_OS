"""
Grafo de orquestração principal do AIOS.
Suporta múltiplos provedores: OpenAI, Anthropic, Ollama (local).
Fluxo: planner → router → [rag | tool] → executor → reflection
"""
from langgraph.graph import StateGraph, END

from agents.planner_agent import make_planner
from agents.rag_agent import rag_agent
from agents.tool_agent import tool_agent
from agents.executor_agent import make_executor
from agents.reflection_agent import make_reflection
from core.router import route_question


def build_graph(provider: str = "openai", model: str = "gpt-4o-mini"):
    """
    Monta e compila o grafo do agente AIOS.

    Args:
        provider: 'openai' | 'anthropic' | 'ollama'
        model: nome do modelo a usar
    """
    graph = StateGraph(dict)

    # Nós com provedor injetado
    graph.add_node("planner", make_planner(provider, model))
    graph.add_node("rag", rag_agent)
    graph.add_node("tool", tool_agent)
    graph.add_node("executor", make_executor(provider, model))
    graph.add_node("reflection", make_reflection(provider, model))

    # Ponto de entrada
    graph.set_entry_point("planner")

    # Roteamento dinâmico após o planejador
    graph.add_conditional_edges(
        "planner",
        route_question,
        {"rag": "rag", "tool": "tool"},
    )

    # Convergência para executor → reflection → END
    graph.add_edge("rag", "executor")
    graph.add_edge("tool", "executor")
    graph.add_edge("executor", "reflection")
    graph.add_edge("reflection", END)

    return graph.compile()
