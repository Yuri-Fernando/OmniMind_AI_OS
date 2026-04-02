"""
Memória de curto prazo — mantém o histórico da conversa atual em RAM.
Descartada quando a sessão termina.
"""
from collections import deque
from typing import List, Dict


class ShortTermMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._history: deque = deque(maxlen=max_turns)

    def add(self, role: str, content: str):
        self._history.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        return list(self._history)

    def get_context_string(self) -> str:
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self._history)

    def clear(self):
        self._history.clear()

    def __len__(self):
        return len(self._history)
