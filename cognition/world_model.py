"""Modelo de mundo: mantém representação do estado do ambiente."""
import time
from typing import Any, Dict, Optional


class WorldModel:
    def __init__(self):
        self._facts: Dict[str, Any] = {}
        self._history: list = []
        self._last_updated: float = time.time()

    def update(self, key: str, value: Any, source: str = "agent"):
        old = self._facts.get(key)
        self._facts[key] = value
        self._last_updated = time.time()
        self._history.append({
            "key": key, "old": old, "new": value,
            "source": source, "ts": self._last_updated
        })

    def get(self, key: str, default: Any = None) -> Any:
        return self._facts.get(key, default)

    def snapshot(self) -> dict:
        return dict(self._facts)

    def diff(self, since_steps: int = 5) -> list:
        return self._history[-since_steps:]

    def summarize(self) -> str:
        if not self._facts:
            return "Modelo de mundo vazio."
        lines = [f"  {k}: {v}" for k, v in self._facts.items()]
        return "Estado atual:\n" + "\n".join(lines)
