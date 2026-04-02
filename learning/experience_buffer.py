"""Buffer de experiências: armazena histórico de interações para aprendizado."""
import json, os, time
from dataclasses import dataclass, asdict, field
from typing import List, Optional


@dataclass
class Experience:
    state: str
    action: str
    result: str
    reward: float = 0.0
    timestamp: float = field(default_factory=time.time)
    episode: int = 0


class ExperienceBuffer:
    def __init__(self, max_size: int = 1000, path: str = "data/experience_buffer.json"):
        self.max_size = max_size
        self.path = path
        self.buffer: List[Experience] = []
        self._load()

    def add(self, state: str, action: str, result: str, reward: float = 0.0, episode: int = 0):
        exp = Experience(state=state, action=action, result=result, reward=reward, episode=episode)
        self.buffer.append(exp)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)
        self._save()

    def sample(self, n: int = 10) -> List[Experience]:
        import random
        return random.sample(self.buffer, min(n, len(self.buffer)))

    def best(self, n: int = 5) -> List[Experience]:
        return sorted(self.buffer, key=lambda x: x.reward, reverse=True)[:n]

    def stats(self) -> dict:
        if not self.buffer:
            return {"count": 0}
        rewards = [e.reward for e in self.buffer]
        return {
            "count": len(self.buffer),
            "avg_reward": sum(rewards) / len(rewards),
            "max_reward": max(rewards),
            "min_reward": min(rewards),
        }

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([asdict(e) for e in self.buffer], f, indent=2)

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                data = json.load(f)
            self.buffer = [Experience(**d) for d in data]
