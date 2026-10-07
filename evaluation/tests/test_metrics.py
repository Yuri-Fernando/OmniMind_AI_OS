"""Testes das métricas puras (sem LLM, sem rede) de evaluation/metrics.py —
lógica real de cálculo, nunca mockada."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.metrics import (
    aggregate_scores,
    answer_relevance,
    context_recall,
    exact_match,
    length_score,
    token_overlap_f1,
)


def test_exact_match_is_case_and_whitespace_insensitive():
    assert exact_match("  Brasília  ", "brasília") == 1.0
    assert exact_match("Rio de Janeiro", "Brasília") == 0.0


def test_token_overlap_f1_perfect_match():
    assert token_overlap_f1("gato preto", "gato preto") == 1.0


def test_token_overlap_f1_partial_overlap_is_between_0_and_1():
    score = token_overlap_f1("o gato é preto", "o cão é preto")
    assert 0.0 < score < 1.0


def test_token_overlap_f1_no_overlap_is_zero():
    assert token_overlap_f1("abacate", "cachorro") == 0.0


def test_token_overlap_f1_empty_prediction_is_zero():
    assert token_overlap_f1("", "qualquer coisa") == 0.0


def test_answer_relevance_counts_shared_question_tokens():
    # resposta repete 2 das 3 palavras-chave da pergunta
    score = answer_relevance("A capital é Brasília.", "Qual a capital do Brasil?")
    assert 0.0 < score <= 1.0


def test_answer_relevance_empty_question_is_zero():
    assert answer_relevance("qualquer resposta", "") == 0.0


def test_context_recall_full_usage_is_one():
    assert context_recall("gato preto corre", "gato preto corre") == 1.0


def test_context_recall_unused_context_is_low():
    score = context_recall("resposta nada a ver", "contexto totalmente diferente sobre física")
    assert score < 0.5


def test_length_score_penalizes_short_answers():
    assert length_score("uma duas", min_words=10) == 2 / 10


def test_length_score_penalizes_long_answers():
    long_answer = " ".join(["palavra"] * 600)
    assert length_score(long_answer, max_words=500) == 500 / 600


def test_length_score_full_score_in_range():
    answer = " ".join(["palavra"] * 50)
    assert length_score(answer, min_words=10, max_words=500) == 1.0


def test_aggregate_scores_rounds_to_4_decimals():
    assert aggregate_scores([1.0, 0.0, 0.5]) == 0.5
    assert aggregate_scores([1 / 3, 1 / 3, 1 / 3]) == round(1 / 3, 4)


def test_aggregate_scores_empty_list_is_zero():
    assert aggregate_scores([]) == 0.0
