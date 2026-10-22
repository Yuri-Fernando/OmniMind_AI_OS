"""Carrega um adapter LoRA/QLoRA (PEFT) sobre o modelo base."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from model_adaptation.common import DEFAULT_BASE_MODEL
from model_adaptation.inference.base_model import load_model


def load_with_adapter(adapter_dir, model_id: str = DEFAULT_BASE_MODEL, quant: Optional[str] = None,
                      dtype: str = "bf16"):
    """Base (bf16 ou 4/8 bit) + adapter. NÃO faz merge — o adapter continua separável."""
    from peft import PeftModel
    adapter_dir = Path(adapter_dir)
    if not (adapter_dir / "adapter_config.json").exists():
        raise FileNotFoundError(f"adapter_config.json ausente em {adapter_dir}")
    base = load_model(model_id, quant=quant, dtype=dtype)
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    model.eval()
    return model


def dir_size_bytes(path) -> int:
    return sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file())
