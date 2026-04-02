"""Registro central de skills do agente."""
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional


@dataclass
class Skill:
    name: str
    description: str
    handler: Callable
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    enabled: bool = True


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, name: str, description: str, handler: Callable, tags: list = None):
        self._skills[name] = Skill(name=name, description=description, handler=handler, tags=tags or [])

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def execute(self, name: str, *args, **kwargs):
        skill = self.get(name)
        if not skill:
            raise KeyError(f"Skill '{name}' não encontrada.")
        if not skill.enabled:
            raise RuntimeError(f"Skill '{name}' está desabilitada.")
        skill.usage_count += 1
        return skill.handler(*args, **kwargs)

    def find_by_tag(self, tag: str) -> List[Skill]:
        return [s for s in self._skills.values() if tag in s.tags]

    def all(self) -> List[dict]:
        return [{"name": s.name, "description": s.description, "tags": s.tags,
                 "usage": s.usage_count, "enabled": s.enabled}
                for s in self._skills.values()]
