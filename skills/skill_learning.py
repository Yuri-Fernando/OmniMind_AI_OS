"""Aprendizado de novas skills a partir de exemplos e feedback."""
import json, os, time
from typing import List
from agents._llm_factory import get_llm


class SkillLearner:
    def __init__(self, provider: str = "ollama", model: str = "mistral",
                 learned_path: str = "data/learned_skills.json"):
        self.llm = get_llm(provider, model)
        self.learned_path = learned_path
        self.learned: List[dict] = []
        self._load()

    def learn_from_example(self, task: str, input_example: str, output_example: str) -> dict:
        """Gera uma skill a partir de exemplo de input/output."""
        prompt = (
            f"Crie uma função Python que resolve a tarefa abaixo.\n"
            f"Tarefa: {task}\nExemplo de entrada: {input_example}\nExemplo de saída: {output_example}\n\n"
            f"Retorne apenas o código Python da função, sem explicações."
        )
        code = self.llm.invoke(prompt).content.strip()
        skill_entry = {
            "name": task.lower().replace(" ", "_")[:30],
            "task": task, "code": code,
            "input_example": input_example, "output_example": output_example,
            "learned_at": time.time(),
        }
        self.learned.append(skill_entry)
        self._save()
        return skill_entry

    def _save(self):
        os.makedirs(os.path.dirname(self.learned_path) or ".", exist_ok=True)
        with open(self.learned_path, "w") as f:
            json.dump(self.learned, f, indent=2)

    def _load(self):
        if os.path.exists(self.learned_path):
            with open(self.learned_path) as f:
                self.learned = json.load(f)
