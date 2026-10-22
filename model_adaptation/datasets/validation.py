"""Validação do dataset: esquema, alvo canônico e vazamento entre splits."""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, List

from model_adaptation.common import TOOL_SCHEMAS, canonical_target

_TYPE = {"string": str}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def validate_record(rec: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    tool, args = rec.get("tool"), rec.get("args")
    if tool not in TOOL_SCHEMAS:
        return [f"{rec.get('id')}: ferramenta desconhecida {tool!r}"]
    if not isinstance(args, dict):
        return [f"{rec.get('id')}: args não é objeto"]
    required = TOOL_SCHEMAS[tool]["required"]
    if set(args) != set(required):
        errs.append(f"{rec['id']}: chaves {sorted(args)} != {sorted(required)}")
    for k, typ in required.items():
        if k in args and (not isinstance(args[k], _TYPE[typ]) or not args[k].strip()):
            errs.append(f"{rec['id']}: arg {k} inválido")
    if rec.get("target") != canonical_target(tool, args):
        errs.append(f"{rec['id']}: target não é canônico")
    try:
        json.loads(rec.get("target", ""))
    except Exception:
        errs.append(f"{rec['id']}: target não é JSON")
    if not rec.get("prompt", "").strip():
        errs.append(f"{rec['id']}: prompt vazio")
    return errs


def _entity(rec: Dict[str, Any]) -> str:
    return "" if rec["tool"] == "none" else f"{rec['tool']}::{json.dumps(rec['args'], sort_keys=True, ensure_ascii=False)}"


def validate_dataset(splits: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    errors: List[str] = []
    for rows in splits.values():
        for r in rows:
            errors += validate_record(r)

    names = list(splits)
    leaks: Dict[str, int] = {"prompt_exato": 0, "prompt_normalizado": 0, "tool_args": 0, "none_prompt": 0}
    detail: List[str] = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = {r["prompt"] for r in splits[a]}, {r["prompt"] for r in splits[b]}
            na, nb = {_norm(r["prompt"]) for r in splits[a]}, {_norm(r["prompt"]) for r in splits[b]}
            ea, eb = {_entity(r) for r in splits[a]} - {""}, {_entity(r) for r in splits[b]} - {""}
            leaks["prompt_exato"] += len(pa & pb)
            leaks["prompt_normalizado"] += len(na & nb)
            leaks["tool_args"] += len(ea & eb)
            if pa & pb or na & nb or ea & eb:
                detail.append(f"{a}×{b}: exato={len(pa & pb)} norm={len(na & nb)} tool_args={len(ea & eb)}")
    for name, rows in splits.items():
        if len({r["prompt"] for r in rows}) != len(rows):
            errors.append(f"{name}: prompts duplicados dentro do split")

    # template holdout (id máximo de cada ferramenta) só pode existir no test
    holdout_ids = {"calculator": 4, "weather_api": 4, "web_search": 4, "file_reader": 4}
    holdout_in_trainval = sum(
        1 for s in ("train", "val") for r in splits.get(s, [])
        if r["tool"] in holdout_ids and r["template_id"] == holdout_ids[r["tool"]]
    )
    holdout_in_test = sum(
        1 for r in splits.get("test", []) if r["tool"] in holdout_ids and r["template_id"] == holdout_ids[r["tool"]]
    )
    if holdout_in_trainval:
        errors.append(f"template holdout presente em train/val ({holdout_in_trainval})")

    dist = {s: {t: sum(1 for r in rows if r["tool"] == t) for t in TOOL_SCHEMAS} for s, rows in splits.items()}
    ok = not errors and not any(leaks.values())
    return {
        "ok": ok,
        "errors": errors[:50],
        "leakage": leaks,
        "leakage_detail": detail,
        "holdout_template": {"em_train_val": holdout_in_trainval, "em_test": holdout_in_test},
        "sizes": {s: len(rows) for s, rows in splits.items()},
        "distribution": dist,
    }
