"""Agente de auto-reflexão: avalia e melhora suas próprias respostas."""
from agents._llm_factory import get_llm
from reflection.answer_critic import AnswerCritic


class SelfReflectionAgent:
    def __init__(self, provider: str = "ollama", model: str = "mistral", max_iterations: int = 2):
        self.llm = get_llm(provider, model)
        self.critic = AnswerCritic(provider, model)
        self.max_iterations = max_iterations

    def _generate(self, question: str, context: str = "") -> str:
        prompt = f"{context}\n\nPergunta: {question}" if context else question
        return self.llm.invoke(prompt).content.strip()

    def _improve(self, question: str, answer: str, critique: str) -> str:
        prompt = (
            f"Melhore a resposta abaixo com base na crítica fornecida.\n\n"
            f"Pergunta: {question}\nResposta original: {answer}\nCrítica: {critique}\n\nResposta melhorada:"
        )
        return self.llm.invoke(prompt).content.strip()

    def reflect_and_answer(self, question: str, threshold: float = 7.0) -> dict:
        answer = self._generate(question)
        iterations = [{"iteration": 1, "answer": answer}]

        for i in range(self.max_iterations):
            eval_result = self.critic.critique(question, answer)
            iterations[-1]["score"] = eval_result["score"]
            iterations[-1]["critique"] = eval_result["critique"]

            if not self.critic.should_retry(eval_result["score"], threshold):
                break

            answer = self._improve(question, answer, eval_result["critique"])
            iterations.append({"iteration": i + 2, "answer": answer})

        return {
            "question": question,
            "final_answer": answer,
            "iterations": len(iterations),
            "history": iterations,
        }
