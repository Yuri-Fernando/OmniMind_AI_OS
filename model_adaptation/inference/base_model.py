"""Carregamento do modelo base (bf16 ou quantizado 4/8 bit via bitsandbytes) e geração."""
from __future__ import annotations

import gc
import time
from typing import Any, Dict, List, Optional, Tuple

from model_adaptation.common import DEFAULT_BASE_MODEL, build_messages


def resolve_dtype(name: str):
    import torch
    return {"bf16": torch.bfloat16, "bfloat16": torch.bfloat16, "fp16": torch.float16,
            "float16": torch.float16, "fp32": torch.float32, "float32": torch.float32}[name]


def quantization_config(quant: Optional[str], compute_dtype: str = "bf16"):
    """`None`  → sem quantização; `'4bit'` → NF4 + double quant (QLoRA); `'8bit'` → LLM.int8()."""
    if not quant:
        return None
    from transformers import BitsAndBytesConfig
    if quant == "4bit":
        return BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=resolve_dtype(compute_dtype),
        )
    if quant == "8bit":
        return BitsAndBytesConfig(load_in_8bit=True)
    raise ValueError(f"quantização desconhecida: {quant!r}")


def load_tokenizer(model_id: str = DEFAULT_BASE_MODEL):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


def load_model(model_id: str = DEFAULT_BASE_MODEL, quant: Optional[str] = None,
               dtype: str = "bf16", device: str = "cuda"):
    """Carrega o modelo causal. Com quantização, o `device_map` fixa tudo na GPU 0."""
    import torch
    from transformers import AutoModelForCausalLM
    kwargs: Dict[str, Any] = {"dtype": resolve_dtype(dtype)}
    qc = quantization_config(quant, dtype)
    if qc is not None:
        kwargs["quantization_config"] = qc
        kwargs["device_map"] = {"": 0}
    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    if qc is None:
        model = model.to(device)
    model.eval()
    return model


def free_gpu() -> None:
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def count_params(model) -> Tuple[int, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def generate_one(model, tokenizer, user_text: str, max_new_tokens: int = 64) -> Dict[str, Any]:
    """Geração gulosa de UM pedido (batch=1) com tempo medido com sincronização de CUDA."""
    import torch
    prompt = tokenizer.apply_chat_template(build_messages(user_text), tokenize=False, add_generation_prompt=True)
    enc = tokenizer(prompt, return_tensors="pt").to(model.device)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tokenizer.pad_token_id)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    new_ids = out[0, enc["input_ids"].shape[1]:]
    text = tokenizer.decode(new_ids, skip_special_tokens=True)
    return {"text": text, "latency_s": dt, "prompt_tokens": int(enc["input_ids"].shape[1]),
            "new_tokens": int(new_ids.shape[0])}
