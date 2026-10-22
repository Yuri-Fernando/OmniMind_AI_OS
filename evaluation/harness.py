"""Evaluation harness único: Agent/RAG → resposta → {RAGAS, DeepEval, juiz, determinísticas, humano} → relatório.

    casos (AgentCase) ─┬─ métricas determinísticas (relevância, context recall, tool-call accuracy, task completion)
                       ├─ juiz (LLM-as-judge plugável: faithfulness, hallucination, correctness)
                       ├─ RAGAS / DeepEval (opcionais: exigem OPENAI_API_KEY; sem ela → NOT_RUN com motivo)
                       └─ fila de avaliação humana (HumanEvalQueue)
                                      ↓
                            HarnessReport (JSON + Markdown)

Princípios: métrica que não se aplica fica `None` e NÃO entra na média; nada é preenchido por padrão;
RAGAS/DeepEval nunca são simulados — ou rodam de verdade ou aparecem como NOT_RUN.
"""
from __future__ import annotations

import json
import os
import re
import statistics
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from evaluation.human_eval import HumanEvalQueue
from evaluation.llm_judge import DeterministicJudge, Judge
from evaluation.metrics import answer_relevance
from evaluation.tool_call_accuracy import DEFAULT_TOOL_SCHEMAS, score_tool_call


@dataclass
class AgentCase:
    id: str
    question: str
    answer: str
    contexts: List[str] = field(default_factory=list)
    ground_truth: Optional[str] = None
    expected_call: Optional[Dict[str, Any]] = None     # {"tool":..., "args": {...}}
    actual_call: Optional[Dict[str, Any]] = None
    tool_result: Any = None
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "unknown"
    label: str = ""


@dataclass
class HarnessConfig:
    judge: Judge = field(default_factory=DeterministicJudge)
    price_in_per_mtok: float = 0.0        # USD / 1M tokens de entrada (0 = modelo local)
    price_out_per_mtok: float = 0.0
    use_ragas: bool = False
    use_deepeval: bool = False
    ragas_fn: Optional[Any] = None        # injetável em testes; padrão = evaluation.ragas_eval.run_ragas_eval
    deepeval_fn: Optional[Any] = None
    human_queue: Optional[HumanEvalQueue] = None
    task_completion_threshold: float = 0.5
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=lambda: DEFAULT_TOOL_SCHEMAS)


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) >= 4 or t.isdigit()}


def context_recall_gt(ground_truth: Optional[str], contexts: List[str]) -> Optional[float]:
    """Fração do conteúdo da resposta de referência que o contexto recuperado cobre (recall de contexto)."""
    if not ground_truth or not contexts:
        return None
    gt = _tokens(ground_truth)
    if not gt:
        return None
    return round(len(gt & _tokens(" ".join(contexts))) / len(gt), 4)


def score_case(case: AgentCase, cfg: HarnessConfig) -> Dict[str, Any]:
    v = cfg.judge.judge(case.question, case.answer, case.ground_truth, case.contexts or None)
    row: Dict[str, Any] = {
        "id": case.id, "label": case.label, "model": case.model,
        "faithfulness": v.faithfulness, "hallucination": v.hallucination,
        "answer_relevancy": round(answer_relevance(case.answer, case.question), 4),
        "correctness": v.correctness, "context_recall": context_recall_gt(case.ground_truth, case.contexts),
        "judge": v.judge, "judge_rationale": v.rationale,
        "tool_correctness": None, "tool_call": None, "task_completion": None,
        "latency_ms": case.latency_ms or None, "input_tokens": case.input_tokens or None,
        "output_tokens": case.output_tokens or None,
    }
    cost = (case.input_tokens * cfg.price_in_per_mtok + case.output_tokens * cfg.price_out_per_mtok) / 1e6
    cost += (v.input_tokens * cfg.price_in_per_mtok + v.output_tokens * cfg.price_out_per_mtok) / 1e6
    row["cost_usd"] = round(cost, 8)

    if case.expected_call is not None:
        sc = score_tool_call(case.expected_call, case.actual_call, cfg.schemas, tool_result=case.tool_result,
                             final_answer=case.answer, context=case.question + " " + " ".join(case.contexts))
        row["tool_call"] = sc.to_dict()
        row["tool_correctness"] = float(sc.correct_call)
        row["task_completion"] = float(sc.overall)
    elif v.correctness is not None:
        row["task_completion"] = float(v.correctness >= cfg.task_completion_threshold)
    return row


_METRICS = ["faithfulness", "answer_relevancy", "context_recall", "hallucination", "correctness",
            "tool_correctness", "task_completion", "latency_ms", "input_tokens", "output_tokens", "cost_usd"]


def _mean(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(statistics.mean(vals), 4) if vals else None


def _external(name: str, fn, enabled: bool, cases: List[AgentCase]) -> Dict[str, Any]:
    if not enabled:
        return {"status": "NOT_RUN", "reason": "desligado na configuração"}
    if fn is None and not os.getenv("OPENAI_API_KEY"):
        return {"status": "NOT_RUN", "reason": "OPENAI_API_KEY ausente (RAGAS/DeepEval usam um LLM-juiz real)"}
    rag = [c for c in cases if c.contexts]
    if not rag:
        return {"status": "NOT_RUN", "reason": "nenhum caso com contexto recuperado"}
    q, a, ctx = [c.question for c in rag], [c.answer for c in rag], [c.contexts for c in rag]
    gt = [c.ground_truth or "" for c in rag] if all(c.ground_truth for c in rag) else None
    try:
        if name == "ragas":
            from evaluation.ragas_eval import run_ragas_eval
            out = (fn or run_ragas_eval)(q, a, ctx, gt)
        else:
            from evaluation.deepeval_tests import run_deepeval
            out = (fn or run_deepeval)(q, a, ctx, gt)
    except Exception as e:                                # nunca derruba o harness
        return {"status": "FAILED", "reason": str(e)[:300]}
    if isinstance(out, dict) and "error" in out:
        return {"status": "FAILED", "reason": str(out["error"])[:300]}
    return {"status": "COMPLETED", "n": len(rag), "result": out}


def run_harness(cases: List[AgentCase], cfg: Optional[HarnessConfig] = None) -> Dict[str, Any]:
    cfg = cfg or HarnessConfig()
    rows = [score_case(c, cfg) for c in cases]
    if cfg.human_queue is not None:
        for c in cases:
            cfg.human_queue.enqueue(c.id, c.question, c.answer, c.contexts, {"label": c.label})
    lat = sorted(r["latency_ms"] for r in rows if r["latency_ms"] is not None)
    summary = {m: _mean(rows, m) for m in _METRICS}
    summary["latency_p95_ms"] = round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 2) if lat else None
    summary["total_cost_usd"] = round(sum(r["cost_usd"] for r in rows), 8)
    tc = [r["tool_call"] for r in rows if r["tool_call"]]
    return {
        "schema_version": "harness-report/1.0", "n_cases": len(rows), "judge": cfg.judge.name,
        "summary": summary,
        "tool_call_accuracy": {
            k: round(sum(bool(t[k]) for t in tc if t[k] is not None) / max(1, len([t for t in tc if t[k] is not None])), 4)
            for k in ("tool_match", "args_valid", "args_match", "result_used", "grounded", "overall")
        } if tc else None,
        "ragas": _external("ragas", cfg.ragas_fn, cfg.use_ragas, cases),
        "deepeval": _external("deepeval", cfg.deepeval_fn, cfg.use_deepeval, cases),
        "human_eval": cfg.human_queue.aggregate() if cfg.human_queue is not None else None,
        "cases": rows,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    s = report["summary"]
    f = lambda x, nd=3: "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
    lines = [f"# Relatório do harness de avaliação ({report['n_cases']} casos, juiz: `{report['judge']}`)", "",
             "| Métrica | Valor |", "|---|---|"]
    for k in ("faithfulness", "answer_relevancy", "context_recall", "hallucination", "correctness",
              "tool_correctness", "task_completion"):
        lines.append(f"| {k} | {f(s[k])} |")
    lines += [f"| latência média (ms) | {f(s['latency_ms'], 1)} |", f"| latência p95 (ms) | {f(s['latency_p95_ms'], 1)} |",
              f"| tokens entrada (média) | {f(s['input_tokens'], 1)} |", f"| tokens saída (média) | {f(s['output_tokens'], 1)} |",
              f"| custo total (USD) | {f(s['total_cost_usd'], 6)} |", ""]
    if report["tool_call_accuracy"]:
        t = report["tool_call_accuracy"]
        lines += ["## Tool-call accuracy", "", "| " + " | ".join(t) + " |", "|" + "---|" * len(t),
                  "| " + " | ".join(f(v) for v in t.values()) + " |", ""]
    for name in ("ragas", "deepeval"):
        e = report[name]
        lines.append(f"- **{name}**: {e['status']}" + (f" — {e['reason']}" if e.get("reason") else ""))
    if report["human_eval"]:
        h = report["human_eval"]
        lines.append(f"- **avaliação humana**: {h['approved']} aprovados / {h['rejected']} reprovados / {h['pending']} pendentes")
    lines += ["", "> `—` = métrica não aplicável aos casos (não entra na média). Juiz determinístico = proxies lexicais.", ""]
    return "\n".join(lines)


if __name__ == "__main__":                                # python -m evaluation.harness [--out DIR]
    import argparse
    from pathlib import Path

    from evaluation.agent_golden import golden_cases
    ap = argparse.ArgumentParser(description="Roda o harness no golden de agentes (juiz determinístico).")
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    ns = ap.parse_args()
    rep = run_harness(golden_cases())
    md = render_markdown(rep)
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "harness_golden.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "harness_golden.md").write_text(md, encoding="utf-8")
    print(md)
