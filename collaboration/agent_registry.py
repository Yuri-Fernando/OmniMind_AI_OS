"""Registro de agentes disponíveis no sistema multi-agente."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import time


@dataclass
class AgentInfo:
    name: str
    capabilities: List[str]
    handler: Optional[Callable] = None
    status: str = "idle"  # idle | busy | offline
    last_active: float = field(default_factory=time.time)
    task_count: int = 0


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}

    def register(self, name: str, capabilities: List[str], handler: Callable = None):
        self._agents[name] = AgentInfo(name=name, capabilities=capabilities, handler=handler)

    def get(self, name: str) -> Optional[AgentInfo]:
        return self._agents.get(name)

    def all(self) -> List[AgentInfo]:
        return list(self._agents.values())

    def find_by_capability(self, capability: str) -> List[AgentInfo]:
        return [a for a in self._agents.values() if capability in a.capabilities]

    def set_status(self, name: str, status: str):
        if name in self._agents:
            self._agents[name].status = status
            self._agents[name].last_active = time.time()

    def available(self) -> List[AgentInfo]:
        return [a for a in self._agents.values() if a.status == "idle"]

    def summary(self) -> dict:
        return {
            "total": len(self._agents),
            "idle": sum(1 for a in self._agents.values() if a.status == "idle"),
            "busy": sum(1 for a in self._agents.values() if a.status == "busy"),
            "agents": [{"name": a.name, "status": a.status, "capabilities": a.capabilities}
                       for a in self._agents.values()],
        }
