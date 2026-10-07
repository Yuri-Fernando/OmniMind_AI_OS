"""Testes de `evaluation/real_pipeline.py`.

A chamada cara/externa ao LLM é a única coisa mockada aqui (autorizado:
"pode mockar chamada de LLM externa cara"). A recuperação de contexto
(TF-IDF real sobre os documentos reais do repo), a montagem dos
`EvalRecord` e a lógica de fallback/erro são exercitadas de verdade."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.real_pipeline import build_retriever, generate_eval_records
from evaluation.golden_dataset import GOLDEN_SET


def test_build_retriever_indexes_real_repo_corpus():
    retriever = build_retriever()
    # pelo menos uma pergunta do golden-set deve recuperar contexto não-vazio
    hit = retriever.search(GOLDEN_SET[0].question, k=3)
    assert hit, "retriever real não encontrou nenhum contexto para a 1a pergunta do golden-set"


def test_generate_eval_records_offline_mode_is_fully_deterministic():
    records_a = generate_eval_records(force_offline=True)
    records_b = generate_eval_records(force_offline=True)

    assert len(records_a) == len(GOLDEN_SET)
    assert all(r.mode == "offline" for r in records_a)
    assert [r.answer for r in records_a] == [r.answer for r in records_b]
    assert [r.contexts for r in records_a] == [r.contexts for r in records_b]
    assert all(r.prompt_tokens == 0 and r.completion_tokens == 0 for r in records_a)


def test_generate_eval_records_offline_answer_is_extractive_from_real_context():
    records = generate_eval_records(force_offline=True)
    for r in records:
        if r.contexts:
            assert r.answer == r.contexts[0][:300]
        else:
            assert "Não sei" in r.answer


@patch("evaluation.real_pipeline.OPENAI_API_KEY", "fake-key-for-test")
@patch("evaluation.real_pipeline._answer_openai")
def test_generate_eval_records_uses_llm_mode_and_records_usage_when_key_present(mock_answer):
    mock_answer.return_value = ("resposta simulada", 42, 7)

    records = generate_eval_records(model="gpt-4o-mini")

    assert len(records) == len(GOLDEN_SET)
    assert all(r.mode == "llm" for r in records)
    assert all(r.answer == "resposta simulada" for r in records)
    assert all(r.prompt_tokens == 42 and r.completion_tokens == 7 for r in records)
    assert mock_answer.call_count == len(GOLDEN_SET)


@patch("evaluation.real_pipeline.OPENAI_API_KEY", "fake-key-for-test")
@patch("evaluation.real_pipeline._answer_openai")
def test_generate_eval_records_falls_back_to_offline_on_llm_error(mock_answer):
    mock_answer.side_effect = RuntimeError("401 invalid_api_key")

    records = generate_eval_records(model="gpt-4o-mini")

    assert all(r.mode == "llm_error_fallback_offline" for r in records)
    assert all("401 invalid_api_key" in r.answer for r in records)
    assert all(r.prompt_tokens == 0 for r in records)
