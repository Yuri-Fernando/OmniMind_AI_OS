"""Gerencia metas de alto nível e seu ciclo de vida."""
import json, os, time
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Goal:
    id: str
    description: str
    priority: int = 1  # 1=baixo, 5=crítico
    status: str = "active"  # active | paused | completed | cancelled
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    notes: str = ""


class GoalManager:
    def __init__(self, storage_path: str = "data/goals.json"):
        self.storage_path = storage_path
        self.goals: List[Goal] = []
        self._load()

    def add(self, description: str, priority: int = 1) -> Goal:
        gid = f"g{len(self.goals)+1:03d}"
        goal = Goal(id=gid, description=description, priority=priority)
        self.goals.append(goal)
        self._save()
        return goal

    def complete(self, goal_id: str):
        for g in self.goals:
            if g.id == goal_id:
                g.status = "completed"
                g.completed_at = time.time()
        self._save()

    def active(self) -> List[Goal]:
        return [g for g in self.goals if g.status == "active"]

    def top_priority(self) -> Optional[Goal]:
        active = self.active()
        return max(active, key=lambda g: g.priority) if active else None

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump([asdict(g) for g in self.goals], f, indent=2)

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                data = json.load(f)
            self.goals = [Goal(**d) for d in data]
