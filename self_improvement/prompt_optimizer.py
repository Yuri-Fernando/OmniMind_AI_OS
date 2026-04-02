"""Otimizador de prompts: melhora prompts com base em resultados."""
from agents._llm_factory import get_llm
from typing import List


class PromptOptimizer:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)
        self.variants: List[dict] = []

    def optimize(self, original_prompt: str, task_description: str, example_output: str = "") -> dict:
        """Gera versão melhorada de um prompt."""
        examples_text = f"\nExemplo de output esperado: {example_output}" if example_output else ""
        meta_prompt = (
            f"Você é um especialista em engenharia de prompts.\n"
            f"Melhore o prompt abaixo para ser mais claro, específico e eficaz.\n"
            f"Tarefa: {task_description}{examples_text}\n\n"
            f"Prompt original:\n{original_prompt}\n\nPrompt melhorado:"
        )
        improved = self.llm.invoke(meta_prompt).content.strip()
        variant = {"original": original_prompt, "improved": improved, "task": task_description}
        self.variants.append(variant)
        return variant

    def ab_test(self, prompt_a: str, prompt_b: str, test_input: str) -> dict:
        """Compara duas variantes de prompt para o mesmo input."""
        response_a = self.llm.invoke(f"{prompt_a}\n\nInput: {test_input}").content.strip()
        response_b = self.llm.invoke(f"{prompt_b}\n\nInput: {test_input}").content.strip()
        # Pede ao LLM para julgar qual é melhor
        judge_prompt = (
            f"Compare as duas respostas para o input: '{test_input}'\n\n"
            f"Resposta A: {response_a}\n\nResposta B: {response_b}\n\n"
            f"Qual é melhor? Responda com 'A' ou 'B' e explique brevemente."
        )
        judgment = self.llm.invoke(judge_prompt).content.strip()
        winner = "A" if judgment.upper().startswith("A") else "B"
        return {"winner": winner, "response_a": response_a, "response_b": response_b, "judgment": judgment}
