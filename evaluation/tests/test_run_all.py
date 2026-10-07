"""Testes da lógica real de agregação/renderização do relatório em
`evaluation/run_all.py` — não mocka a lógica de relatório em si, só os dados
de entrada (que num run real viriam de RAGAS/DeepEval/observability)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.run_all import _render_markdown


def _base_report(**overrides):
    report = {
        "timestamp": "2026-01-01T00:00:00",
        "model": "gpt-4o-mini",
        "openai_key_configured": True,
        "observability": {
            "backend": "local_file",
            "aggregate": {
                "n_runs": 8,
                "total_latency_ms": 1234.5,
                "avg_latency_ms": 154.3,
                "total_tokens": 999,
            },
            "note": "Langfuse não configurado.",
        },
        "ragas": {},
        "deepeval": {},
    }
    report.update(overrides)
    return report


def test_render_markdown_includes_core_fields():
    md = _render_markdown(_base_report())
    assert "gpt-4o-mini" in md
    assert "local_file" in md
    assert "1234.5" in md
    assert "999" in md


def test_render_markdown_shows_ragas_error_when_present():
    md = _render_markdown(_base_report(ragas={"error": "401 invalid_api_key"}))
    assert "401 invalid_api_key" in md


def test_render_markdown_shows_ragas_scores_when_present():
    md = _render_markdown(
        _base_report(ragas={"degraded": False, "scores": {"faithfulness": 0.87}})
    )
    assert "faithfulness" in md
    assert "0.87" in md


def test_render_markdown_shows_deepeval_items():
    md = _render_markdown(
        _base_report(
            deepeval={
                "items": [
                    {
                        "question": "Pergunta de teste bem longa para truncar no render?",
                        "relevancy": 0.9,
                        "hallucination": 0.1,
                        "mode": "llm",
                    }
                ]
            }
        )
    )
    assert "relevancy=0.9" in md
    assert "hallucination=0.1" in md
    assert "mode=llm" in md


def test_render_markdown_handles_skipped_sections():
    md = _render_markdown(_base_report(ragas={}, deepeval={}))
    assert "(pulado)" in md
