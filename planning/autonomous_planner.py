"""Planejador autônomo: dado um objetivo, cria e executa um plano de tarefas."""
from planning.goal_manager import GoalManager, Goal
from planning.task_decomposer import TaskDecomposer, Task
from typing import List, Callable, Optional


class AutonomousPlanner:
    def __init__(self, provider: str = "ollama", model: str = "mistral"):
        self.decomposer = TaskDecomposer(provider=provider, model=model)
        self.goal_manager = GoalManager()

    def plan(self, objective: str, max_tasks: int = 5) -> dict:
        """Cria um plano de execução para o objetivo."""
        goal = self.goal_manager.add(objective)
        tasks = self.decomposer.decompose(objective, max_tasks=max_tasks)
        return {
            "goal_id": goal.id,
            "goal": objective,
            "tasks": self.decomposer.to_dict(tasks),
            "total": len(tasks),
        }

    def execute(
        self,
        objective: str,
        executor: Optional[Callable[[str], str]] = None,
        max_tasks: int = 5,
    ) -> dict:
        """Planeja e executa cada tarefa com um executor opcional."""
        plan = self.plan(objective, max_tasks)
        results = []
        for task in plan["tasks"]:
            if executor:
                try:
                    output = executor(task["description"])
                    task["status"] = "done"
                    task["output"] = output
                except Exception as e:
                    task["status"] = "failed"
                    task["output"] = str(e)
            else:
                task["status"] = "pending"
                task["output"] = "(sem executor)"
            results.append(task)
        self.goal_manager.complete(plan["goal_id"])
        plan["tasks"] = results
        plan["completed"] = all(t["status"] == "done" for t in results)
        return plan
