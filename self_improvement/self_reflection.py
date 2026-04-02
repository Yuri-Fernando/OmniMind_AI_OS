"""Auto-reflexão do sistema: avalia performance geral e sugere melhorias."""
from agents._llm_factory import get_llm
from typing import List


class SystemSelfReflection:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)
        self.session_log: List[dict] = []

    def log_interaction(self, question: str, answer: str, rating: float = None):
        self.session_log.append({"q": question, "a": answer, "rating": rating})

    def reflect(self) -> dict:
        if not self.session_log:
            return {"message": "Nenhuma interação registrada nesta sessão."}
        summary = "\n".join(
            f"Q: {i['q'][:80]}\nA: {i['a'][:100]}\nRating: {i.get('rating', 'N/A')}"
            for i in self.session_log[-5:]
        )
        prompt = (
            f"Analise as últimas interações do agente e identifique:\n"
            f"1. Pontos fortes\n2. Áreas de melhoria\n3. Padrões de erro\n\n{summary}"
        )
        reflection = self.llm.invoke(prompt).content.strip()
        rated = [i for i in self.session_log if i.get("rating") is not None]
        avg = sum(i["rating"] for i in rated) / len(rated) if rated else None
        return {
            "interactions": len(self.session_log),
            "avg_rating": avg,
            "reflection": reflection,
        }
