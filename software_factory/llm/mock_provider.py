"""MockLLM determinístico para CI sem rede e sem chave.

Não é IA: devolve respostas roteirizadas por papel (fixtures). Serve para
provar as partes que importam numa fábrica SDD — gates, DAG, isolamento,
runner externo, revisão e rastreabilidade — de forma reproduzível. Cada
roteiro é uma fila por papel; um item pode ser texto, dict (vira JSON),
uma exceção (simula 429/timeout) ou um callable(prompt) -> texto|dict.
"""
from __future__ import annotations

import json
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, Iterable, Union

from .provider import LLMResponse

ScriptItem = Union[str, dict, list, BaseException, Callable[[str], Any]]


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class MockLLM:
    name = "mock"

    def __init__(self, script: Dict[str, Iterable[ScriptItem]] | None = None, model: str = "mock-deterministic"):
        self.model = model
        self._queues: Dict[str, Deque[ScriptItem]] = defaultdict(deque)
        self.calls: list[dict] = []
        for role, items in (script or {}).items():
            self._queues[role].extend(items)

    def push(self, role: str, *items: ScriptItem) -> None:
        self._queues[role].extend(items)

    def complete(self, role: str, system: str, prompt: str) -> LLMResponse:
        self.calls.append({"role": role, "prompt_chars": len(prompt)})
        queue = self._queues.get(role)
        if not queue:
            raise LookupError(f"MockLLM sem resposta roteirizada para o papel {role!r}")
        item = queue.popleft()
        if isinstance(item, BaseException):
            raise item
        if callable(item):
            item = item(prompt)
        text = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        return LLMResponse(text=text, input_tokens=_approx_tokens(system + prompt),
                           output_tokens=_approx_tokens(text), model=self.model)
