"""Benchmark do roteador de ferramentas: qualidade, latência, tokens/s e memória.

`evaluate_model` roda o split de teste em batch=1 (latência de requisição única) com geração
gulosa — determinística — e aplica `evaluation.tool_call_accuracy` a cada saída.
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List

from evaluation.tool_call_accuracy import aggregate, extract_json_object, score_tool_call
from model_adaptation.inference.base_model import generate_one


def _pct(values: List[float], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def evaluate_model(model, tokenizer, rows: List[Dict[str, Any]], max_new_tokens: int = 64,
                   warmup: int = 3) -> Dict[str, Any]:
    for r in rows[:warmup]:                       # aquece kernels/cache; fora das métricas
        generate_one(model, tokenizer, r["prompt"], max_new_tokens)

    scores, lat, new_toks, fails = [], [], [], []
    by_tool: Dict[str, list] = {}
    by_tmpl: Dict[str, list] = {"holdout": [], "visto": []}
    for r in rows:
        g = generate_one(model, tokenizer, r["prompt"], max_new_tokens)
        obj, strict = extract_json_object(g["text"])
        sc = score_tool_call({"tool": r["tool"], "args": r["args"]}, obj, strict_json=strict)
        scores.append(sc)
        lat.append(g["latency_s"])
        new_toks.append(g["new_tokens"])
        by_tool.setdefault(r["tool"], []).append(sc)
        holdout = r["tool"] != "none" and r["template_id"] == 4
        by_tmpl["holdout" if holdout else "visto"].append(sc)
        if not sc.correct_call and len(fails) < 8:
            fails.append({"id": r["id"], "prompt": r["prompt"], "esperado": r["target"],
                          "saida": g["text"][:200], "erros": sc.errors})

    total_time = sum(lat)
    return {
        "n_test": len(rows),
        "quality": aggregate(scores),
        "quality_by_tool": {k: aggregate(v) for k, v in sorted(by_tool.items())},
        "quality_by_template": {k: aggregate(v) for k, v in by_tmpl.items() if v},
        "latency_ms": {"p50": round(_pct(lat, 0.5) * 1000, 1), "p95": round(_pct(lat, 0.95) * 1000, 1),
                       "mean": round(statistics.mean(lat) * 1000, 1)},
        "tokens_per_s": round(sum(new_toks) / total_time, 2) if total_time else 0.0,
        "mean_new_tokens": round(statistics.mean(new_toks), 2),
        "failures_sample": fails,
    }


# ------------------------------------------------------------------ relatório
_ORDER = ["base_bf16", "base_4bit", "full", "lora", "qlora"]
_LABEL = {"base_bf16": "Base (bf16)", "base_4bit": "Base (4-bit NF4)", "full": "Ajuste fino completo",
          "lora": "LoRA (bf16)", "qlora": "QLoRA (4-bit NF4)"}


def _fmt(vals: List[float], nd: int = 3) -> str:
    vals = [v for v in vals if v is not None]
    if not vals:
        return "—"
    if len(vals) == 1:
        return f"{vals[0]:.{nd}f}"
    return f"{statistics.mean(vals):.{nd}f} ± {statistics.pstdev(vals):.{nd}f}"


def render_report(runs: List[Dict[str, Any]]) -> str:
    """Tabela comparativa a partir dos JSONs reais (nunca de números digitados à mão)."""
    by_variant: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        by_variant.setdefault(r["variant"], []).append(r)
    lines = ["# Resultados — roteador de ferramentas (base × LoRA × QLoRA)", "",
             f"Modelo base: `{runs[0].get('base_model', '?')}` · test = {runs[0].get('eval', {}).get('n_test', '?')} pedidos "
             "(inclui template nunca visto no treino). Valores = média ± desvio entre seeds quando há mais de uma.", "",
             "| Variante | status | seeds | exact match | JSON estrito | holdout EM | VRAM treino (GB) | tempo treino (s) | "
             "adapter (MB) | treináveis (%) | lat. p50 (ms) | lat. p95 (ms) | tokens/s | VRAM infer. (GB) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in [x for x in _ORDER if x in by_variant]:
        rs = by_variant[v]
        done = [r for r in rs if r.get("eval")]
        if not done:
            tr = rs[0].get("train", {})
            lines.append(f"| {_LABEL[v]} | **{rs[0].get('status')}** | {len(rs)} | — | — | — | "
                         f"{tr.get('peak_vram_train_gb', '—')} | — | — | — | — | — | — | — |")
            continue
        g = lambda f: [f(r) for r in done]
        tr = lambda k: [r.get("train", {}).get(k) for r in done]
        lines.append(
            f"| {_LABEL[v]} | {done[0]['status']} | {len(done)} | "
            f"{_fmt(g(lambda r: r['eval']['quality']['correct_call']))} | "
            f"{_fmt(g(lambda r: r['eval']['quality']['json_strict']))} | "
            f"{_fmt(g(lambda r: r['eval']['quality_by_template'].get('holdout', {}).get('correct_call')))} | "
            f"{_fmt(tr('peak_vram_train_gb'))} | {_fmt(tr('train_time_s'), 1)} | {_fmt(tr('artifact_size_mb'), 1)} | "
            f"{_fmt(tr('trainable_pct'), 2)} | {_fmt(g(lambda r: r['eval']['latency_ms']['p50']), 0)} | "
            f"{_fmt(g(lambda r: r['eval']['latency_ms']['p95']), 0)} | {_fmt(g(lambda r: r['eval']['tokens_per_s']), 1)} | "
            f"{_fmt(g(lambda r: r['eval_peak_vram_gb']))} |")
    lines += ["", "Notas: VRAM = `torch.cuda.max_memory_allocated` (inclui pesos); latência em batch=1, geração gulosa, "
              "`max_new_tokens=64`; “exact match” = ferramenta correta + argumentos corretos (normalizados); "
              "“JSON estrito” = a saída inteira é só o JSON.", ""]
    return "\n".join(lines)
