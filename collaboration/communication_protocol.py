"""Protocolo de comunicação entre agentes — mensagens tipadas."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time, uuid


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    content: Any
    msg_type: str = "task"  # task | result | error | broadcast
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    reply_to: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.msg_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.msg_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
        }


class MessageBus:
    """Bus simples em memória para troca de mensagens entre agentes."""

    def __init__(self):
        self._queues: Dict[str, List[AgentMessage]] = {}
        self._history: List[AgentMessage] = []

    def send(self, msg: AgentMessage):
        if msg.recipient not in self._queues:
            self._queues[msg.recipient] = []
        self._queues[msg.recipient].append(msg)
        self._history.append(msg)

    def broadcast(self, sender: str, content: Any, recipients: List[str]):
        for r in recipients:
            self.send(AgentMessage(sender=sender, recipient=r, content=content, msg_type="broadcast"))

    def receive(self, agent_name: str) -> List[AgentMessage]:
        msgs = self._queues.pop(agent_name, [])
        return msgs

    def peek(self, agent_name: str) -> List[AgentMessage]:
        return self._queues.get(agent_name, [])

    def history(self, limit: int = 20) -> List[dict]:
        return [m.to_dict() for m in self._history[-limit:]]
