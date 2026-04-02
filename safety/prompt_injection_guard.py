"""Detecta e bloqueia tentativas de prompt injection."""
import re
from typing import Tuple

# Padrões comuns de injection
_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if\s+you\s+are",
    r"jailbreak",
    r"DAN\s+mode",
    r"do\s+anything\s+now",
    r"system\s*:\s*you\s+are",
    r"<\s*system\s*>",
    r"\[INST\].*override",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]


def check_injection(text: str) -> Tuple[bool, str]:
    """
    Verifica se o texto contém tentativas de prompt injection.
    Retorna (is_safe, reason).
    """
    for pattern in _COMPILED:
        if pattern.search(text):
            return False, f"Padrão suspeito detectado: '{pattern.pattern}'"
    return True, "ok"


class PromptInjectionGuard:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.blocked_count = 0

    def guard(self, text: str) -> dict:
        is_safe, reason = check_injection(text)
        if not is_safe:
            self.blocked_count += 1
        return {
            "safe": is_safe,
            "reason": reason,
            "text": text if is_safe else "[BLOQUEADO]",
            "original": text,
        }

    def assert_safe(self, text: str) -> str:
        result = self.guard(text)
        if not result["safe"]:
            raise ValueError(f"Prompt injection detectado: {result['reason']}")
        return text
