"""Decompõe um objetivo em sub-tarefas executáveis."""
from dataclasses import dataclass, field
from typing import List
from agents._llm_factory import get_llm


@dataclass
class Task:
    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | done | failed


class TaskDecomposer:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.llm = get_llm(provider, model)

    def decompose(self, goal: str, max_tasks: int = 5) -> List[Task]:
        prompt = (
            f"Decompõe o seguinte objetivo em no máximo {max_tasks} sub-tarefas concretas.\n"
            f"Responda com uma lista numerada, uma tarefa por linha.\n\nObjetivo: {goal}"
        )
        response = self.llm.invoke(prompt)
        lines = [l.strip() for l in response.content.split("\n") if l.strip()]
        tasks = []
        for i, line in enumerate(lines[:max_tasks]):
            # Remove numeração
            desc = line.lstrip("0123456789.-) ").strip()
            if desc:
                tasks.append(Task(id=f"t{i+1}", description=desc))
        return tasks

    def to_dict(self, tasks: List[Task]) -> List[dict]:
        return [{"id": t.id, "description": t.description,
                 "dependencies": t.dependencies, "status": t.status} for t in tasks]
