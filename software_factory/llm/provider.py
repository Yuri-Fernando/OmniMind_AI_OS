"""Interface mínima de provedor LLM usada pelos papéis da fábrica."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMError(RuntimeError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, role: str, system: str, prompt: str) -> LLMResponse:
        """Devolve texto (esperado JSON) para o papel indicado."""
        ...
