"""Experimento real: base × (base 4-bit) × ajuste completo × LoRA × QLoRA.

Uso:
    python -m model_adaptation.run_experiment --seeds 0 [--variants base_bf16 base_4bit lora qlora full]

Cada variante grava `results/<variante>_seed<N>.json` (treino + avaliação medidos) e, ao final,
`results/REPORT.md` é regenerado a partir de TODOS os JSONs existentes. Pesos ficam em
`D:\\Claude Temp\\staging\\omnimind-adapt` (fora do Drive e do git).
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from model_adaptation.common import (DATA_DIR, DEFAULT_BASE_MODEL, MODEL_ADAPTATION_DIR, RESULTS_DIR,
                                     STAGING_DIR, load_jsonl, set_seed, write_json)
from model_adaptation.evaluation.benchmark import evaluate_model, render_report
from model_adaptation.inference.adapter_loader import load_with_adapter
from model_adaptation.inference.base_model import free_gpu, load_model, load_tokenizer
from model_adaptation.training.trainer import load_config, run_training

ALL_VARIANTS = ["base_bf16", "base_4bit", "lora", "qlora", "full"]
TRAINED = {"lora": "lora.yaml", "qlora": "qlora.yaml", "full": "full.yaml"}


def environment() -> Dict[str, Any]:
    import peft
    import torch
    import transformers
    try:
        import bitsandbytes
        bnb = bitsandbytes.__version__
    except Exception:
        bnb = None
    return {
        "python": platform.python_version(), "torch": torch.__version__, "transformers": transformers.__version__,
        "peft": peft.__version__, "bitsandbytes": bnb, "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0), "gpu_total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2),
        "os": platform.platform(),
    }


def _eval(loader, tokenizer, rows, max_new_tokens: int) -> Dict[str, Any]:
    import torch
    free_gpu()
    torch.cuda.reset_peak_memory_stats()
    model = loader()
    out = evaluate_model(model, tokenizer, rows, max_new_tokens=max_new_tokens)
    peak = round(torch.cuda.max_memory_allocated() / 1e9, 3)
    return {"eval": out, "eval_peak_vram_gb": peak}


def run_variant(variant: str, seed: int, rows, tokenizer, max_new_tokens: int) -> Dict[str, Any]:
    base = {"variant": variant, "seed": seed, "base_model": DEFAULT_BASE_MODEL, "status": "COMPLETED"}
    if variant == "base_bf16":
        base.update(_eval(lambda: load_model(DEFAULT_BASE_MODEL), tokenizer, rows, max_new_tokens))
        return base
    if variant == "base_4bit":
        base.update(_eval(lambda: load_model(DEFAULT_BASE_MODEL, quant="4bit"), tokenizer, rows, max_new_tokens))
        return base

    cfg = load_config(MODEL_ADAPTATION_DIR / "configs" / TRAINED[variant])
    train = run_training(cfg, seed=seed)
    base["train"] = {k: v for k, v in train.items() if k != "config"}
    base["status"] = train["status"]
    if train["status"] != "COMPLETED":
        return base
    art = train["artifact_dir"]
    if variant == "lora":
        loader = lambda: load_with_adapter(art, DEFAULT_BASE_MODEL, quant=None)
    elif variant == "qlora":
        loader = lambda: load_with_adapter(art, DEFAULT_BASE_MODEL, quant="4bit")
    else:                                              # full: o diretório contém o modelo inteiro
        loader = lambda: load_model(art)
    base.update(_eval(loader, tokenizer, rows, max_new_tokens))
    return base


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--variants", nargs="+", default=ALL_VARIANTS, choices=ALL_VARIANTS)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ns = ap.parse_args(argv)

    rows = load_jsonl(DATA_DIR / "test.jsonl")
    tokenizer = load_tokenizer(DEFAULT_BASE_MODEL)
    env = environment()
    write_json(RESULTS_DIR / "environment.json", env)
    for seed in ns.seeds:
        for v in ns.variants:
            if v.startswith("base") and seed != ns.seeds[0]:
                continue                                # base é determinística (guloso): uma vez basta
            out_file = RESULTS_DIR / f"{v}_seed{seed}.json"
            print(f"== {v} seed={seed}", flush=True)
            res = run_variant(v, seed, rows, tokenizer, ns.max_new_tokens)
            res["environment"] = env
            write_json(out_file, res)
            q = res.get("eval", {}).get("quality", {})
            print(f"   status={res['status']} exact_match={q.get('correct_call')} strict={q.get('json_strict')}", flush=True)
            free_gpu()

    runs = []
    for p in sorted(RESULTS_DIR.glob("*_seed*.json")):
        if p.name.startswith("train_"):
            continue
        runs.append(json.loads(p.read_text(encoding="utf-8")))
    if runs:
        (RESULTS_DIR / "REPORT.md").write_text(render_report(runs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
