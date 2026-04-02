"""Tree of Thoughts (ToT): explora múltiplos ramos de raciocínio."""
from agents._llm_factory import get_llm
from typing import List


class TreeOfThoughts:
    def __init__(self, provider: str = "ollama", model: str = "mistral", branches: int = 3):
        self.llm = get_llm(provider, model)
        self.branches = branches

    def _generate_thoughts(self, question: str) -> List[str]:
        prompt = (
            f"Gere {self.branches} abordagens diferentes para resolver:\n{question}\n\n"
            f"Liste cada abordagem numerada em 1-2 frases."
        )
        response = self.llm.invoke(prompt)
        lines = [l.strip() for l in response.content.split("\n") if l.strip()]
        return [l.lstrip("0123456789.-) ") for l in lines if l][:self.branches]

    def _evaluate_thought(self, question: str, thought: str) -> float:
        prompt = (
            f"Para a questão: '{question}'\n"
            f"Avalie a abordagem a seguir de 0 a 10 (somente o número):\n{thought}"
        )
        response = self.llm.invoke(prompt)
        try:
            return float(response.content.strip().split()[0])
        except (ValueError, IndexError):
            return 5.0

    def _expand_best(self, question: str, thought: str) -> str:
        prompt = f"Questão: {question}\nAbordagem escolhida: {thought}\n\nExpanda esta abordagem em uma resposta completa:"
        return self.llm.invoke(prompt).content.strip()

    def solve(self, question: str) -> dict:
        thoughts = self._generate_thoughts(question)
        scored = [(t, self._evaluate_thought(question, t)) for t in thoughts]
        best_thought, best_score = max(scored, key=lambda x: x[1])
        answer = self._expand_best(question, best_thought)
        return {
            "question": question,
            "thoughts": [{"thought": t, "score": s} for t, s in scored],
            "best_thought": best_thought,
            "best_score": best_score,
            "answer": answer,
        }
