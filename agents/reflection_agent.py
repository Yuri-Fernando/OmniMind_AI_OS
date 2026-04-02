"""Agente de reflexão — avalia e melhora a resposta gerada."""
from agents._llm_factory import get_llm


def make_reflection(provider: str = "openai", model: str = "gpt-4o-mini"):
    llm = get_llm(provider, model)

    def reflection(state):
        question = state.get("question", "")
        answer = state.get("answer", "")
        prompt = (
            f"Avalie se a resposta abaixo responde adequadamente à pergunta.\n\n"
            f"Pergunta: {question}\n\n"
            f"Resposta atual: {answer}\n\n"
            f"Se estiver boa, retorne-a sem alterações. "
            f"Se puder melhorar, retorne a versão melhorada."
        )
        response = llm.invoke(prompt)
        state["answer"] = response.content if hasattr(response, "content") else str(response)
        state["iterations"] = state.get("iterations", 0) + 1
        return state

    return reflection


def reflection(state):
    return make_reflection()(state)
