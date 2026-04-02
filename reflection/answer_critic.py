"""Crítico de respostas: avalia qualidade e sugere melhorias."""
from agents._llm_factory import get_llm


class AnswerCritic:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)

    def critique(self, question: str, answer: str) -> dict:
        prompt = (
            f"Avalie a resposta abaixo para a pergunta fornecida.\n"
            f"Dê uma nota de 1-10 e aponte pontos fortes e fracos em bullet points.\n\n"
            f"Pergunta: {question}\n\nResposta: {answer}\n\n"
            f"Formato: Nota: X/10\nPontos fortes:\n- ...\nPontos fracos:\n- ..."
        )
        result = self.llm.invoke(prompt).content
        # Extrai nota
        score = 5.0
        for line in result.split("\n"):
            if "nota:" in line.lower():
                try:
                    score = float(line.split(":")[-1].strip().split("/")[0])
                except ValueError:
                    pass
                break
        return {"question": question, "answer": answer, "critique": result, "score": score}

    def should_retry(self, score: float, threshold: float = 6.0) -> bool:
        return score < threshold
