"""Simulador de ambiente: cria cenários controlados para teste de agentes."""
import random
from typing import Dict, Any, List, Callable


class EnvironmentSimulator:
    def __init__(self, name: str = "default"):
        self.name = name
        self.state: Dict[str, Any] = {}
        self.step_count: int = 0
        self.history: List[dict] = []
        self._rules: List[Callable] = []

    def set_state(self, **kwargs):
        self.state.update(kwargs)

    def add_rule(self, rule: Callable):
        """Adiciona uma regra de transição de estado (state -> new_state)."""
        self._rules.append(rule)

    def step(self, action: str) -> dict:
        """Executa uma ação e avança o estado do ambiente."""
        old_state = dict(self.state)
        for rule in self._rules:
            try:
                self.state = rule(self.state, action) or self.state
            except Exception:
                pass
        self.step_count += 1
        reward = self._compute_reward(old_state, action, self.state)
        transition = {
            "step": self.step_count, "action": action,
            "state_before": old_state, "state_after": dict(self.state),
            "reward": reward,
        }
        self.history.append(transition)
        return transition

    def _compute_reward(self, state_before: dict, action: str, state_after: dict) -> float:
        """Recompensa padrão: +1 se estado mudou, 0 caso contrário."""
        return 1.0 if state_before != state_after else 0.0

    def reset(self):
        self.state = {}
        self.step_count = 0
        self.history = []

    def summary(self) -> dict:
        total_reward = sum(t["reward"] for t in self.history)
        return {
            "name": self.name, "steps": self.step_count,
            "total_reward": total_reward, "current_state": self.state,
        }
