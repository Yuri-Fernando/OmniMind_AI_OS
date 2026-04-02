"""Chain of Thought (CoT): resolve problemas passo a passo."""
from agents._llm_factory import get_llm
from typing import List


class ChainOfThought:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)

    def reason(self, question: str, steps: int = 4) -> dict:
        prompt = (
            f"Resolva a questão abaixo usando raciocínio passo a passo.\n"
            f"Mostre claramente cada etapa numerada e ao final escreva 'Resposta final:'.\n\n"
            f"Questão: {question}"
        )
        response = self.llm.invoke(prompt)
        text = response.content
        # Extrai resposta final
        final = ""
        if "Resposta final:" in text:
            final = text.split("Resposta final:")[-1].strip()
        return {"question": question, "reasoning": text, "answer": final or text}

    def few_shot(self, question: str, examples: List[dict]) -> dict:
        """CoT com exemplos few-shot. examples: [{'q': ..., 'a': ...}]"""
        examples_text = "\n\n".join(
            f"Q: {ex['q']}\nA: {ex['a']}" for ex in examples
        )
        prompt = f"{examples_text}\n\nQ: {question}\nA:"
        response = self.llm.invoke(prompt)
        return {"question": question, "answer": response.content.strip()}
