"""Contexto do ambiente: agrega informações do mundo e do agente."""
import time
from cognition.world_model import WorldModel
from cognition.belief_state import BeliefState


class EnvironmentContext:
    def __init__(self):
        self.world = WorldModel()
        self.beliefs = BeliefState()
        self.agent_goals: list = []
        self.session_start: float = time.time()
        self.turn_count: int = 0

    def observe(self, observation: dict):
        """Incorpora uma observação ao modelo de mundo."""
        for k, v in observation.items():
            self.world.update(k, v, source="observation")
        self.turn_count += 1

    def add_goal(self, goal: str, priority: int = 1):
        self.agent_goals.append({"goal": goal, "priority": priority, "ts": time.time()})

    def build_prompt_context(self) -> str:
        """Gera contexto formatado para incluir em prompts."""
        parts = [self.world.summarize()]
        top = self.beliefs.most_likely()
        if top:
            parts.append(f"Hipótese mais provável: {top} ({self.beliefs.get(top):.1%})")
        if self.agent_goals:
            goals_str = "; ".join(g["goal"] for g in sorted(self.agent_goals, key=lambda x: -x["priority"])[:3])
            parts.append(f"Objetivos ativos: {goals_str}")
        return "\n".join(parts)
