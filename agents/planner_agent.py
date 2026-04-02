"""Agente planejador — gera um plano de resposta antes de executar."""
from agents._llm_factory import get_llm


def make_planner(provider: str = "openai", model: str = "gpt-4o-mini"):
    llm = get_llm(provider, model)

    def planner(state):
        question = state["question"]
        prompt = (
            f"Você é um planejador de tarefas AI. Dado o pedido abaixo, "
            f"escreva em 1-3 linhas qual estratégia usar para responder bem.\n\n"
            f"Pedido: {question}"
        )
        response = llm.invoke(prompt)
        state["plan"] = response.content if hasattr(response, "content") else str(response)
        return state

    return planner


# Backward-compat: instância padrão OpenAI
def planner(state):
    return make_planner()(state)
