"""
Ponto de entrada único e reprodutível para a avaliação real do OmniMind AI OS.

    python -m evaluation.run_all

Executa, sobre o golden-set fixo (`evaluation/golden_dataset.py`):
  1. RAGAS real (faithfulness, answer_relevancy, context_recall) — LLM-juiz
     OpenAI real se OPENAI_API_KEY estiver configurada.
  2. DeepEval real (answer relevancy, hallucination) — idem.
  3. Observabilidade: registra 1 trace por item do golden-set via
     `observability/langfuse_tracing.py` (Langfuse real se configurado,
     senão fallback local em arquivo — ver módulo para detalhes) e reporta
     latência/tokens agregados.

Salva um relatório JSON (dados completos) e um Markdown (resumo legível) em
`evaluation/reports/`, sempre com timestamp, e nunca sobrescreve relatórios
anteriores.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPORTS_DIR = Path(__file__).parent / "reports"


def _run_ragas(model: str) -> Dict[str, Any]:
    from evaluation.ragas_eval import run_ragas_on_golden

    try:
        return run_ragas_on_golden(model=model)
    except Exception as e:
        return {"error": f"falha ao rodar RAGAS: {e}"}


def _run_deepeval(model: str) -> Dict[str, Any]:
    from evaluation.deepeval_tests import run_deepeval_on_golden

    try:
        results = run_deepeval_on_golden(model=model)
        return {"items": results}
    except Exception as e:
        return {"error": f"falha ao rodar DeepEval: {e}"}


def _run_observability() -> Dict[str, Any]:
    """Gera traces reais (não mockados) de cada item do golden-set e resume
    o estado real de observabilidade (cloud Langfuse vs. fallback local)."""
    from evaluation.real_pipeline import generate_eval_records
    from observability.langfuse_tracing import active_backend, trace_run, read_local_traces

    records = generate_eval_records()
    for r in records:
        trace_run(
            name="eval.golden_set",
            input_text=r.question,
            output_text=r.answer,
            metadata={
                "mode": r.mode,
                "model": r.model,
                "latency_ms": r.latency_ms,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
            },
        )

    backend = active_backend()
    summary: Dict[str, Any] = {"backend": backend}
    if backend == "local_file":
        traces = read_local_traces()
        summary["local_trace_count"] = len(traces)
        summary["local_trace_file"] = "observability/traces/traces.jsonl"
        summary["note"] = (
            "Langfuse Cloud/self-host não configurado nesta sessão "
            "(LANGFUSE_PUBLIC_KEY/SECRET_KEY vazias e self-host via "
            "docker-compose não provisionado — ver WORKLOG.md). Traces "
            "reais gravados localmente em JSONL como fallback documentado."
        )

    total_latency = sum(r.latency_ms for r in records)
    total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in records)
    summary["aggregate"] = {
        "n_runs": len(records),
        "total_latency_ms": round(total_latency, 2),
        "avg_latency_ms": round(total_latency / len(records), 2) if records else 0,
        "total_tokens": total_tokens,
    }
    return summary


def run_all(model: str = "gpt-4o-mini", skip_ragas: bool = False, skip_deepeval: bool = False) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Importa core.config primeiro para garantir que load_dotenv() já rodou
    # antes de checar a env var (senão `openai_key_configured` reporta False
    # mesmo com a chave presente no .env, só porque nada tinha importado
    # core.config ainda neste processo).
    from core.config import OPENAI_API_KEY as _openai_key

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "openai_key_configured": bool(_openai_key),
    }

    report["observability"] = _run_observability()
    report["ragas"] = {} if skip_ragas else _run_ragas(model)
    report["deepeval"] = {} if skip_deepeval else _run_deepeval(model)

    json_path = REPORTS_DIR / f"eval_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    md_path = REPORTS_DIR / f"eval_{timestamp}.md"
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"Relatório JSON: {json_path}")
    print(f"Relatório Markdown: {md_path}")
    return json_path


def _render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Relatório de avaliação — {report['timestamp']}",
        "",
        f"Modelo: `{report['model']}` · OPENAI_API_KEY configurada: "
        f"{report['openai_key_configured']}",
        "",
        "## Observabilidade",
        f"Backend ativo: `{report['observability'].get('backend')}`",
    ]
    obs = report["observability"]
    if "note" in obs:
        lines.append(f"\n> {obs['note']}")
    agg = obs.get("aggregate", {})
    if agg:
        lines.append("")
        lines.append(
            f"- Execuções: {agg.get('n_runs')}\n"
            f"- Latência total: {agg.get('total_latency_ms')} ms\n"
            f"- Latência média: {agg.get('avg_latency_ms')} ms\n"
            f"- Tokens totais: {agg.get('total_tokens')}"
        )

    lines.append("\n## RAGAS")
    ragas = report.get("ragas", {})
    if not ragas:
        lines.append("(pulado)")
    elif "error" in ragas:
        lines.append(f"Erro: {ragas['error']}")
    else:
        lines.append(f"Degradado (sem LLM real em algum item): {ragas.get('degraded')}")
        for metric, score in ragas.get("scores", {}).items():
            lines.append(f"- **{metric}**: {score}")

    lines.append("\n## DeepEval")
    deepeval = report.get("deepeval", {})
    if not deepeval:
        lines.append("(pulado)")
    elif "error" in deepeval:
        lines.append(f"Erro: {deepeval['error']}")
    else:
        for item in deepeval.get("items", []):
            if "error" in item:
                lines.append(f"- Erro: {item['error']}")
                continue
            lines.append(
                f"- **{item['question'][:60]}...** — relevancy={item.get('relevancy')}, "
                f"hallucination={item.get('hallucination')} (mode={item.get('mode')})"
            )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avaliação real e reprodutível do OmniMind AI OS")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--skip-ragas", action="store_true")
    parser.add_argument("--skip-deepeval", action="store_true")
    args = parser.parse_args()
    run_all(model=args.model, skip_ragas=args.skip_ragas, skip_deepeval=args.skip_deepeval)
