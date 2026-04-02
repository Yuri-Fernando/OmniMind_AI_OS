"""Motor de melhoria contínua: aprende com falhas e melhora prompts."""
import json, os
from typing import List
from agents._llm_factory import get_llm


class ImprovementEngine:
    def __init__(self, provider: str = "ollama", model: str = "mistral",
                 history_path: str = "data/improvement_history.json"):
        self.llm = get_llm(provider, model)
        self.history_path = history_path
        self.history: List[dict] = []
        self._load()

    def record_failure(self, task: str, attempt: str, error: str):
        entry = {"type": "failure", "task": task, "attempt": attempt, "error": error}
        self.history.append(entry)
        self._save()

    def record_success(self, task: str, solution: str):
        entry = {"type": "success", "task": task, "solution": solution}
        self.history.append(entry)
        self._save()

    def suggest_improvement(self, task: str) -> str:
        failures = [h for h in self.history if h.get("type") == "failure" and h.get("task") == task]
        if not failures:
            return "Nenhuma falha anterior para esta tarefa."
        context = "\n".join(f"- Tentativa: {f['attempt']}\n  Erro: {f['error']}" for f in failures[-3:])
        prompt = (
            f"Tarefa: {task}\n\nFalhas anteriores:\n{context}\n\n"
            f"Sugira uma abordagem melhorada para resolver esta tarefa:"
        )
        return self.llm.invoke(prompt).content.strip()

    def _save(self):
        os.makedirs(os.path.dirname(self.history_path) or ".", exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def _load(self):
        if os.path.exists(self.history_path):
            with open(self.history_path) as f:
                self.history = json.load(f)
