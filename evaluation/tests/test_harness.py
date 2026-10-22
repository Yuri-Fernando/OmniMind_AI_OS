"""Harness unificado: o golden precisa separar positivos de negativos; RAGAS/DeepEval nunca são simulados."""
import pytest

from evaluation.agent_golden import golden_cases
from evaluation.harness import AgentCase, HarnessConfig, context_recall_gt, render_markdown, run_harness
from evaluation.human_eval import HumanEvalQueue


@pytest.fixture(scope="module")
def report():
    return run_harness(golden_cases())


def _row(report, cid):
    return next(c for c in report["cases"] if c["id"] == cid)


def test_all_positive_cases_complete_the_task(report):
    pos = [c for c in report["cases"] if c["label"] == "positive"]
    assert len(pos) == 5 and all(c["task_completion"] == 1.0 for c in pos)


def test_all_negative_cases_are_flagged(report):
    neg = [c for c in report["cases"] if c["label"].startswith("negative")]
    assert len(neg) == 7 and all(c["task_completion"] == 0.0 for c in neg)


@pytest.mark.parametrize("cid,check", [
    ("neg-wrong-tool", lambda t: not t["tool_match"]),
    ("neg-bad-args", lambda t: t["tool_match"] and not t["args_valid"]),
    ("neg-wrong-args", lambda t: t["args_valid"] and not t["args_match"]),
    ("neg-ignored-result", lambda t: t["correct_call"] and t["result_used"] is False),
    ("neg-ungrounded", lambda t: t["correct_call"] and t["grounded"] is False),
    ("neg-no-call", lambda t: not t["json_valid"]),
])
def test_each_negative_fails_for_its_own_reason(report, cid, check):
    assert check(_row(report, cid)["tool_call"])


def test_hallucinated_rag_answer_scores_low_faithfulness(report):
    assert _row(report, "pos-rag")["faithfulness"] > 0.9
    assert _row(report, "neg-hallucination")["faithfulness"] < 0.3
    assert _row(report, "neg-hallucination")["hallucination"] > 0.7


def test_summary_has_every_requested_metric_and_skips_inapplicable(report):
    s = report["summary"]
    for k in ("faithfulness", "answer_relevancy", "context_recall", "hallucination", "tool_correctness",
              "task_completion", "latency_ms", "input_tokens", "output_tokens", "cost_usd", "total_cost_usd"):
        assert k in s
    assert s["latency_ms"] is not None and s["latency_p95_ms"] is not None
    assert s["total_cost_usd"] == 0.0                       # modelo local → custo zero, não inventado
    assert 0.0 < s["task_completion"] < 1.0                 # golden misto


def test_cost_uses_prices_when_provided():
    c = AgentCase("x", "q", "a", input_tokens=1_000_000, output_tokens=500_000, model="m")
    rep = run_harness([c], HarnessConfig(price_in_per_mtok=3.0, price_out_per_mtok=15.0))
    assert rep["summary"]["total_cost_usd"] == pytest.approx(3.0 + 7.5)


def test_context_recall_is_ground_truth_coverage():
    assert context_recall_gt("RAGAS e DeepEval", ["usa RAGAS e DeepEval"]) == 1.0
    assert context_recall_gt("Prometheus Grafana", ["usa RAGAS e DeepEval"]) == 0.0
    assert context_recall_gt(None, ["x"]) is None and context_recall_gt("x", []) is None


def test_ragas_and_deepeval_not_run_without_key(report, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    rep = run_harness(golden_cases(), HarnessConfig(use_ragas=True, use_deepeval=True))
    for k in ("ragas", "deepeval"):
        assert rep[k]["status"] == "NOT_RUN" and "OPENAI_API_KEY" in rep[k]["reason"]
    assert report["ragas"]["status"] == "NOT_RUN"           # desligado por padrão


def test_ragas_is_called_with_rag_cases_only_when_enabled():
    seen = {}

    def fake(q, a, ctx, gt):
        seen.update(q=q, ctx=ctx, gt=gt)
        return {"faithfulness": 0.5}
    rep = run_harness(golden_cases(), HarnessConfig(use_ragas=True, ragas_fn=fake))
    assert rep["ragas"]["status"] == "COMPLETED" and rep["ragas"]["n"] == 2 and len(seen["ctx"]) == 2
    assert all(c for c in seen["ctx"])


def test_external_failure_is_reported_not_raised():
    def boom(*a):
        raise RuntimeError("rede caiu")
    rep = run_harness(golden_cases(), HarnessConfig(use_deepeval=True, deepeval_fn=boom))
    assert rep["deepeval"]["status"] == "FAILED" and "rede caiu" in rep["deepeval"]["reason"]
    rep2 = run_harness(golden_cases(), HarnessConfig(use_ragas=True, ragas_fn=lambda *a: {"error": "sem chave"}))
    assert rep2["ragas"]["status"] == "FAILED"


def test_human_queue_is_filled_once(tmp_path):
    q = HumanEvalQueue(tmp_path / "q.json")
    run_harness(golden_cases(), HarnessConfig(human_queue=q))
    rep = run_harness(golden_cases(), HarnessConfig(human_queue=q))          # reexecução não duplica
    assert rep["human_eval"]["total"] == 12 and rep["human_eval"]["pending"] == 12


def test_markdown_report_renders(report):
    md = render_markdown(report)
    assert "Tool-call accuracy" in md and "NOT_RUN" in md and "faithfulness" in md
