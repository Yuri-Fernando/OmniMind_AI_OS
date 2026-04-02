"""Arena de agentes: compara múltiplos modelos nas mesmas tarefas."""
from typing import List, Dict, Callable
from arena.tasks_dataset import BenchmarkTask, get_tasks
import time


class AgentArena:
    def __init__(self):
        self.competitors: Dict[str, Callable] = {}
        self.results: List[dict] = []

    def register(self, name: str, agent_fn: Callable):
        """Registra um agente. agent_fn(question: str) -> str"""
        self.competitors[name] = agent_fn

    def _score(self, expected: str, actual: str) -> float:
        expected = expected.lower().strip()
        actual = actual.lower().strip()
        if expected in actual or actual in expected:
            return 1.0
        # Score parcial por palavras em comum
        words_exp = set(expected.split())
        words_act = set(actual.split())
        if not words_exp:
            return 0.0
        overlap = len(words_exp & words_act) / len(words_exp)
        return round(overlap, 2)

    def run(self, tasks: List[BenchmarkTask] = None) -> List[dict]:
        if tasks is None:
            tasks = get_tasks()
        self.results = []
        for task in tasks:
            task_result = {"task_id": task.id, "question": task.question,
                           "expected": task.expected_answer, "scores": {}}
            for agent_name, fn in self.competitors.items():
                start = time.time()
                try:
                    answer = fn(task.question)
                    latency = round((time.time() - start) * 1000, 1)
                    score = self._score(task.expected_answer, answer)
                    task_result["scores"][agent_name] = {
                        "answer": answer, "score": score, "latency_ms": latency, "ok": True
                    }
                except Exception as e:
                    task_result["scores"][agent_name] = {
                        "answer": "", "score": 0.0, "error": str(e), "ok": False
                    }
            self.results.append(task_result)
        return self.results
