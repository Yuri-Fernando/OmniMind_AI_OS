"""Provedor Claude opcional (SDK `anthropic`).

A chave vem só de variável de ambiente (ANTHROPIC_API_KEY); nada é lido de
arquivo nem gravado em artefato. Os testes de CI não dependem deste módulo:
ele é exercitado com um cliente falso injetado. Execução real = suíte opt-in.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from .provider import LLMError, LLMRateLimitError, LLMResponse, LLMTimeoutError

DEFAULT_MODEL = "claude-sonnet-5-5"


class ClaudeProvider:
    name = "claude"

    def __init__(self, model: Optional[str] = None, max_tokens: int = 8000,
                 timeout_s: float = 120.0, client: Any = None):
        self.model = model or os.getenv("SDD_CLAUDE_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        if client is None:
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise LLMError("ANTHROPIC_API_KEY ausente — use o MockLLM ou exporte a chave no ambiente")
            import anthropic  # import tardio: CI não precisa do SDK
            client = anthropic.Anthropic(timeout=timeout_s, max_retries=0)
        self._client = client

    def complete(self, role: str, system: str, prompt: str) -> LLMResponse:
        try:
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # mapeia erros do SDK sem depender das classes dele
            kind = type(exc).__name__.lower()
            if "ratelimit" in kind or getattr(exc, "status_code", None) == 429:
                raise LLMRateLimitError(str(exc)) from exc
            if "timeout" in kind:
                raise LLMTimeoutError(str(exc)) from exc
            raise LLMError(f"{type(exc).__name__}: {exc}") from exc
        text = "".join(getattr(b, "text", "") for b in msg.content)
        usage = getattr(msg, "usage", None)
        return LLMResponse(text=text,
                           input_tokens=getattr(usage, "input_tokens", 0) or 0,
                           output_tokens=getattr(usage, "output_tokens", 0) or 0,
                           model=self.model)
