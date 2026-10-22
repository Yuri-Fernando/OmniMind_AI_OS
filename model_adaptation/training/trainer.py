"""Loop de treino compartilhado por full/LoRA/QLoRA (PyTorch puro — `trl` não está instalado).

Mede, de verdade: pico de VRAM (`torch.cuda.max_memory_allocated`), tempo de treino,
loss por época, nº de parâmetros treináveis e tamanho do adapter em disco.
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

from model_adaptation.common import (DEFAULT_BASE_MODEL, DATA_DIR, STAGING_DIR, build_messages,
                                     load_jsonl, set_seed)
from model_adaptation.inference.adapter_loader import dir_size_bytes
from model_adaptation.inference.base_model import count_params, free_gpu, load_model, load_tokenizer


def load_config(path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    required = {"name", "mode", "train"}
    missing = required - set(cfg)
    if missing:
        raise ValueError(f"config sem chaves obrigatórias: {sorted(missing)}")
    if cfg["mode"] not in {"full", "lora", "qlora"}:
        raise ValueError(f"mode inválido: {cfg['mode']!r}")
    if cfg["mode"] in {"lora", "qlora"} and "lora" not in cfg:
        raise ValueError("modos lora/qlora exigem a seção 'lora'")
    if cfg["mode"] == "qlora" and cfg.get("quantization") != "4bit":
        raise ValueError("qlora exige quantization: 4bit")
    return cfg


def encode_example(tokenizer, user_text: str, target: str, max_len: int) -> Dict[str, List[int]]:
    """Tokeniza prompt+resposta; a loss só conta nos tokens da resposta (labels=-100 no prompt)."""
    prompt = tokenizer.apply_chat_template(build_messages(user_text), tokenize=False, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(build_messages(user_text, target), tokenize=False)
    assert full.startswith(prompt)
    p_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    f_ids = tokenizer(full, add_special_tokens=False)["input_ids"][:max_len]
    labels = [-100] * min(len(p_ids), len(f_ids)) + f_ids[len(p_ids):]
    return {"input_ids": f_ids, "labels": labels}


def collate(batch: List[Dict[str, List[int]]], pad_id: int):
    import torch
    n = max(len(b["input_ids"]) for b in batch)
    ids = torch.full((len(batch), n), pad_id, dtype=torch.long)
    lab = torch.full((len(batch), n), -100, dtype=torch.long)
    att = torch.zeros((len(batch), n), dtype=torch.long)
    for i, b in enumerate(batch):
        L = len(b["input_ids"])
        ids[i, :L] = torch.tensor(b["input_ids"])
        lab[i, :L] = torch.tensor(b["labels"])
        att[i, :L] = 1
    return {"input_ids": ids, "labels": lab, "attention_mask": att}


def _loss_on(model, batch, device, autocast: bool) -> "torch.Tensor":
    import torch
    batch = {k: v.to(device) for k, v in batch.items()}
    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=autocast):
        return model(**batch).loss


def _run_training(cfg: Dict[str, Any], data_dir, staging, seed: int) -> Dict[str, Any]:
    import random
    import torch
    set_seed(seed)
    mode, name = cfg["mode"], cfg["name"]
    tcfg = cfg["train"]
    model_id = cfg.get("base_model", DEFAULT_BASE_MODEL)
    quant = cfg.get("quantization") if mode == "qlora" else None
    out_dir = Path(staging) / "adapters" / f"{name}_seed{seed}"
    result: Dict[str, Any] = {"name": name, "mode": mode, "seed": seed, "base_model": model_id,
                              "quantization": quant, "config": cfg, "status": "RUNNING"}

    tokenizer = load_tokenizer(model_id)
    train_rows = load_jsonl(Path(data_dir) / "train.jsonl")
    val_rows = load_jsonl(Path(data_dir) / "val.jsonl")
    max_len = int(tcfg.get("max_seq_len", 384))
    train_enc = [encode_example(tokenizer, r["prompt"], r["target"], max_len) for r in train_rows]
    val_enc = [encode_example(tokenizer, r["prompt"], r["target"], max_len) for r in val_rows]
    result["train_examples"], result["val_examples"] = len(train_enc), len(val_enc)
    result["max_example_tokens"] = max(len(e["input_ids"]) for e in train_enc)

    free_gpu()
    torch.cuda.reset_peak_memory_stats()
    try:
        model = load_model(model_id, quant=quant, dtype=cfg.get("dtype", "bf16"))
        result["mem_after_load_gb"] = round(torch.cuda.memory_allocated() / 1e9, 3)

        if mode in {"lora", "qlora"}:
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
            if mode == "qlora":
                model = prepare_model_for_kbit_training(
                    model, use_gradient_checkpointing=bool(tcfg.get("gradient_checkpointing", False)))
            elif tcfg.get("gradient_checkpointing", False):
                model.gradient_checkpointing_enable()
                model.enable_input_require_grads()
            lc = cfg["lora"]
            model = get_peft_model(model, LoraConfig(
                r=int(lc["r"]), lora_alpha=int(lc["alpha"]), lora_dropout=float(lc.get("dropout", 0.05)),
                target_modules=list(lc["target_modules"]), bias="none", task_type="CAUSAL_LM"))
        else:
            for p in model.parameters():
                p.requires_grad_(True)
        model.config.use_cache = False
        total, trainable = count_params(model)
        result.update(params_total=total, params_trainable=trainable,
                      trainable_pct=round(100 * trainable / total, 4))

        params = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=float(tcfg["lr"]), weight_decay=float(tcfg.get("weight_decay", 0.0)))
        bs, epochs = int(tcfg["batch_size"]), int(tcfg["epochs"])
        steps_per_epoch = math.ceil(len(train_enc) / bs)
        total_steps, warmup = steps_per_epoch * epochs, max(1, int(0.05 * steps_per_epoch * epochs))
        sched = torch.optim.lr_scheduler.LambdaLR(
            opt, lambda s: (s + 1) / warmup if s < warmup else max(0.0, 0.5 * (1 + math.cos(math.pi * (s - warmup) / max(1, total_steps - warmup)))))
        autocast = mode != "full"          # full treina em bf16 puro; LoRA/QLoRA usam autocast bf16
        device = next(model.parameters()).device
        rng = random.Random(seed)

        epoch_losses: List[float] = []
        step_losses: List[float] = []
        model.train()
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for ep in range(epochs):
            order = list(range(len(train_enc)))
            rng.shuffle(order)
            running = []
            for s in range(steps_per_epoch):
                idx = order[s * bs:(s + 1) * bs]
                batch = collate([train_enc[i] for i in idx], tokenizer.pad_token_id)
                loss = _loss_on(model, batch, device, autocast)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, float(tcfg.get("max_grad_norm", 1.0)))
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                running.append(loss.item())
                step_losses.append(running[-1])
            epoch_losses.append(round(sum(running) / len(running), 5))
        torch.cuda.synchronize()
        result["train_time_s"] = round(time.perf_counter() - t0, 2)
        result["peak_vram_train_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 3)
        result["peak_vram_train_reserved_gb"] = round(torch.cuda.max_memory_reserved() / 1e9, 3)
        result["epoch_train_loss"] = epoch_losses
        result["first_steps_loss"] = [round(x, 4) for x in step_losses[:3]]
        result["last_steps_loss"] = [round(x, 4) for x in step_losses[-3:]]
        result["steps"] = total_steps

        model.eval()
        vl = []
        with torch.no_grad():
            for i in range(0, len(val_enc), bs):
                vl.append(_loss_on(model, collate(val_enc[i:i + bs], tokenizer.pad_token_id), device, autocast).item())
        result["val_loss"] = round(sum(vl) / len(vl), 5)

        out_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(out_dir))
        result["artifact_dir"] = str(out_dir)
        result["artifact_size_mb"] = round(dir_size_bytes(out_dir) / 1e6, 2)
        result["status"] = "COMPLETED"
    except torch.cuda.OutOfMemoryError as e:                       # limite real da GPU, registrado
        result["status"] = "OOM"
        result["error"] = str(e).splitlines()[0][:300]
        result["peak_vram_train_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 3)
    return result


def run_training(cfg: Dict[str, Any], data_dir=DATA_DIR, staging=STAGING_DIR, seed: int = 0) -> Dict[str, Any]:
    """Treina e devolve as métricas. A função interna retorna antes do `free_gpu()`,
    então modelo/otimizador já saíram de escopo e a VRAM é de fato liberada."""
    result = _run_training(cfg, data_dir, staging, seed)
    free_gpu()
    return result
