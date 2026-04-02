"""Agente executor — gera a resposta final usando contexto recuperado."""
from agents._llm_factory import get_llm


def make_executor(provider: str = "openai", model: str = "gpt-4o-mini"):
    llm = get_llm(provider, model)

    def executor(state):
        question = state["question"]
        context = state.get("context", "")
        plan = state.get("plan", "")
        prompt = (
            f"Plano: {plan}\n\n"
            f"Contexto:\n{context}\n\n"
            f"Pergunta: {question}\n\n"
            f"Responda de forma clara e completa em português."
        )
        response = llm.invoke(prompt)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
        return state

    return executor


def executor(state):
    return make_executor()(state)
