"""
Métricas de avaliação de respostas — sem dependências externas.
"""
import re
from typing import List


def exact_match(prediction: str, reference: str) -> float:
    return 1.0 if prediction.strip().lower() == reference.strip().lower() else 0.0


def token_overlap_f1(prediction: str, reference: str) -> float:
    """F1 baseado em sobreposição de tokens (estilo SQuAD)."""
    pred_tokens = set(re.findall(r"\w+", prediction.lower()))
    ref_tokens = set(re.findall(r"\w+", reference.lower()))
    if not pred_tokens or not ref_tokens:
        return 0.0
    common = pred_tokens & ref_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def answer_relevance(answer: str, question: str) -> float:
    """Relevância heurística: quantos tokens da pergunta aparecem na resposta."""
    q_tokens = set(re.findall(r"\w+", question.lower()))
    a_tokens = set(re.findall(r"\w+", answer.lower()))
    if not q_tokens:
        return 0.0
    return len(q_tokens & a_tokens) / len(q_tokens)


def context_recall(answer: str, context: str) -> float:
    """Fração do contexto que foi usada na resposta."""
    ctx_tokens = set(re.findall(r"\w+", context.lower()))
    ans_tokens = set(re.findall(r"\w+", answer.lower()))
    if not ctx_tokens:
        return 0.0
    return len(ctx_tokens & ans_tokens) / len(ctx_tokens)


def length_score(answer: str, min_words: int = 10, max_words: int = 500) -> float:
    """Penaliza respostas muito curtas ou muito longas."""
    words = len(answer.split())
    if words < min_words:
        return words / min_words
    if words > max_words:
        return max_words / words
    return 1.0


def aggregate_scores(scores: List[float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)
