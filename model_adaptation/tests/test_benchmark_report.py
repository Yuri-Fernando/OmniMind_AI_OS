"""Relatório do experimento: agregação correta e consistência com os JSONs reais gerados."""
import json

import pytest

from model_adaptation.common import RESULTS_DIR
from model_adaptation.evaluation.benchmark import _pct, render_report


def _run(variant, em, seed=0, status="COMPLETED"):
    return {"variant": variant, "seed": seed, "status": status, "base_model": "m",
            "train": {"peak_vram_train_gb": 2.0, "train_time_s": 10.0, "artifact_size_mb": 35.0, "trainable_pct": 1.7},
            "eval": {"n_test": 10, "quality": {"correct_call": em, "json_strict": 1.0},
                     "quality_by_template": {"holdout": {"correct_call": em - 0.1}},
                     "latency_ms": {"p50": 100.0, "p95": 200.0}, "tokens_per_s": 9.0}, "eval_peak_vram_gb": 1.1}


def test_percentile_interpolates():
    assert _pct([1, 2, 3, 4], 0.5) == 2.5 and _pct([], 0.5) == 0.0 and _pct([7], 0.95) == 7


def test_report_has_mean_and_std_across_seeds():
    md = render_report([_run("lora", 0.9, 0), _run("lora", 0.8, 1)])
    assert "0.850 ± 0.050" in md and "LoRA (bf16)" in md


def test_report_shows_oom_instead_of_inventing_numbers():
    oom = {"variant": "full", "seed": 0, "status": "OOM", "base_model": "m", "train": {"peak_vram_train_gb": 7.9}}
    md = render_report([_run("lora", 0.9), oom])
    row = next(l for l in md.splitlines() if "Ajuste fino completo" in l)
    assert "**OOM**" in row and "7.9" in row and "0.9" not in row.replace("7.9", "")


def test_real_results_are_internally_consistent():
    files = [p for p in RESULTS_DIR.glob("*_seed*.json") if not p.name.startswith("train_")]
    if not files:
        pytest.skip("experimento ainda não executado")
    for p in files:
        r = json.loads(p.read_text(encoding="utf-8"))
        assert r["status"] in {"COMPLETED", "OOM"}
        if "eval" in r:
            q = r["eval"]["quality"]
            assert 0.0 <= q["correct_call"] <= q["tool_match"] <= 1.0
            assert q["n"] == r["eval"]["n_test"]
            assert r["eval"]["latency_ms"]["p95"] >= r["eval"]["latency_ms"]["p50"] > 0
        if r["variant"] in {"lora", "qlora"} and r["status"] == "COMPLETED":
            assert 0 < r["train"]["trainable_pct"] < 10          # adapter, não o modelo inteiro
            assert r["train"]["artifact_size_mb"] < 200
    md = render_report([json.loads(p.read_text(encoding="utf-8")) for p in files])
    assert md.startswith("# Resultados")
