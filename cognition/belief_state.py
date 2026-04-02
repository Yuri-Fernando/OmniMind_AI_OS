"""Estado de crença do agente: probabilidades sobre hipóteses."""
from typing import Dict


class BeliefState:
    def __init__(self):
        self._beliefs: Dict[str, float] = {}

    def set(self, hypothesis: str, probability: float):
        self._beliefs[hypothesis] = max(0.0, min(1.0, probability))

    def update(self, hypothesis: str, evidence_strength: float):
        """Atualiza crença usando regra de Bayes simplificada."""
        prior = self._beliefs.get(hypothesis, 0.5)
        # Atualização bayesiana simplificada
        posterior = prior * evidence_strength / (prior * evidence_strength + (1 - prior) * (1 - evidence_strength))
        self._beliefs[hypothesis] = posterior

    def get(self, hypothesis: str) -> float:
        return self._beliefs.get(hypothesis, 0.0)

    def most_likely(self) -> str:
        if not self._beliefs:
            return ""
        return max(self._beliefs, key=self._beliefs.get)

    def all_beliefs(self) -> Dict[str, float]:
        return dict(sorted(self._beliefs.items(), key=lambda x: x[1], reverse=True))

    def reset(self):
        self._beliefs.clear()
