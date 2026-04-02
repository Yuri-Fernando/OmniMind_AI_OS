"""Aprendizado por reforço simplificado: Q-table para ações discretas."""
import json, os
from typing import Dict, List


class SimpleQLearner:
    def __init__(self, actions: List[str], alpha: float = 0.1, gamma: float = 0.9,
                 epsilon: float = 0.2, path: str = "data/q_table.json"):
        self.actions = actions
        self.alpha = alpha    # taxa de aprendizado
        self.gamma = gamma    # desconto futuro
        self.epsilon = epsilon  # exploração
        self.path = path
        self.q_table: Dict[str, Dict[str, float]] = {}
        self._load()

    def _init_state(self, state: str):
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}

    def choose_action(self, state: str) -> str:
        import random
        self._init_state(state)
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        return max(self.q_table[state], key=self.q_table[state].get)

    def learn(self, state: str, action: str, reward: float, next_state: str):
        self._init_state(state)
        self._init_state(next_state)
        best_next = max(self.q_table[next_state].values())
        current_q = self.q_table[state][action]
        self.q_table[state][action] = current_q + self.alpha * (
            reward + self.gamma * best_next - current_q
        )
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.q_table, f, indent=2)

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.q_table = json.load(f)
