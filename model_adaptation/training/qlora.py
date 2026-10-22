"""QLoRA (base 4-bit NF4 + adapter LoRA) — ponto de entrada fino sobre `training.trainer`.

Uso:  python -m model_adaptation.training.qlora [--seed 0] [--config configs/qlora.yaml]
"""
from __future__ import annotations

import argparse
import json

from model_adaptation.common import MODEL_ADAPTATION_DIR, RESULTS_DIR, write_json
from model_adaptation.training.trainer import load_config, run_training

DEFAULT_CONFIG = MODEL_ADAPTATION_DIR / "configs" / "qlora.yaml"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ns = ap.parse_args(argv)
    res = run_training(load_config(ns.config), seed=ns.seed)
    write_json(RESULTS_DIR / f"train_{res['name']}_seed{ns.seed}.json", res)
    print(json.dumps({k: res.get(k) for k in ("name", "status", "train_time_s", "peak_vram_train_gb", "artifact_size_mb", "val_loss")}))
    return 0 if res["status"] in {"COMPLETED", "OOM"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
