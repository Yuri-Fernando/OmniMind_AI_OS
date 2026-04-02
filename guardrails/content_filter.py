"""
Filtro de conteúdo — bloqueia respostas com conteúdo inapropriado.
"""
import re
from typing import Tuple


BLOCKED_PATTERNS = [
    r"\b(hack|exploit|malware|ransomware)\b",
    r"\b(fabricar|sintetizar).*(droga|explosivo|veneno)\b",
    r"\b(como matar|como ferir|como machucar)\b",
]


def filter_output(text: str) -> Tuple[bool, str]:
    """
    Verifica se o texto viola as políticas.

    Returns:
        (blocked: bool, reason: str)
    """
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lower):
            return True, f"Conteúdo bloqueado: padrão '{pattern}' detectado."
    return False, ""


def sanitize_input(text: str, max_length: int = 4000) -> str:
    """Remove caracteres de controle e limita tamanho."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:max_length]
