"""Filtro de conteúdo: detecta e filtra saídas inadequadas."""
import re
from typing import List, Tuple

# Categorias e palavras-chave (exemplos básicos — expandir conforme necessário)
_CATEGORIES = {
    "violence": ["matar", "assassinar", "bomba", "explosivo", "arma", "kill", "murder", "weapon", "bomb"],
    "hate_speech": ["odeio", "racismo", "discriminação", "hate", "racist"],
    "personal_data": [r"\d{3}\.\d{3}\.\d{3}-\d{2}", r"\b\d{16}\b"],  # CPF, cartão
}


def _contains(text: str, terms: List[str]) -> bool:
    text_lower = text.lower()
    for t in terms:
        if re.search(t, text_lower):
            return True
    return False


def check_content(text: str) -> Tuple[bool, str, str]:
    """Retorna (is_safe, category, reason)."""
    for category, terms in _CATEGORIES.items():
        if _contains(text, terms):
            return False, category, f"Conteúdo '{category}' detectado"
    return True, "", "ok"


class ContentFilter:
    def __init__(self, block_on_flag: bool = True):
        self.block_on_flag = block_on_flag
        self.stats = {"checked": 0, "blocked": 0}

    def filter(self, text: str) -> dict:
        self.stats["checked"] += 1
        is_safe, category, reason = check_content(text)
        if not is_safe:
            self.stats["blocked"] += 1
        return {
            "safe": is_safe,
            "category": category,
            "reason": reason,
            "output": text if (is_safe or not self.block_on_flag) else "[CONTEÚDO FILTRADO]",
        }
