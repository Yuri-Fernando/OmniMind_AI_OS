"""Configs LoRA/QLoRA/full, quantização NF4 e preparação de exemplos (sem treinar nada, sem GPU)."""
import glob
import os

import pytest
import yaml

from model_adaptation.common import MODEL_ADAPTATION_DIR
from model_adaptation.training.trainer import collate, encode_example, load_config

CFG = MODEL_ADAPTATION_DIR / "configs"


def _write(tmp_path, d):
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(d), encoding="utf-8")
    return p


def test_shipped_configs_load():
    lora, qlora, full = (load_config(CFG / f"{n}.yaml") for n in ("lora", "qlora", "full"))
    assert lora["mode"] == "lora" and "quantization" not in lora
    assert qlora["mode"] == "qlora" and qlora["quantization"] == "4bit"
    assert full["mode"] == "full" and "lora" not in full
    # a comparação é justa: mesmos hiperparâmetros de adapter e de treino entre LoRA e QLoRA
    assert lora["lora"] == qlora["lora"] and lora["train"] == qlora["train"]


def test_qlora_requires_4bit(tmp_path):
    cfg = yaml.safe_load((CFG / "qlora.yaml").read_text(encoding="utf-8"))
    cfg["quantization"] = "8bit"
    with pytest.raises(ValueError, match="4bit"):
        load_config(_write(tmp_path, cfg))


def test_lora_modes_require_lora_section(tmp_path):
    cfg = yaml.safe_load((CFG / "lora.yaml").read_text(encoding="utf-8"))
    del cfg["lora"]
    with pytest.raises(ValueError, match="lora"):
        load_config(_write(tmp_path, cfg))


def test_invalid_mode_and_missing_keys(tmp_path):
    with pytest.raises(ValueError):
        load_config(_write(tmp_path, {"name": "x", "mode": "magia", "train": {}}))
    with pytest.raises(ValueError):
        load_config(_write(tmp_path, {"name": "x"}))


def test_quantization_config_is_nf4_double_quant_bf16():
    import torch
    from model_adaptation.inference.base_model import quantization_config
    q = quantization_config("4bit", "bf16")
    assert q.load_in_4bit and q.bnb_4bit_quant_type == "nf4" and q.bnb_4bit_use_double_quant
    assert q.bnb_4bit_compute_dtype == torch.bfloat16
    assert quantization_config(None) is None
    assert quantization_config("8bit").load_in_8bit
    with pytest.raises(ValueError):
        quantization_config("2bit")


def _tokenizer():
    hits = glob.glob(r"Q:\Hugginface\hub\models--Qwen--Qwen2.5-0.5B-Instruct\snapshots\*\tokenizer.json")
    if not hits:
        pytest.skip("tokenizer do modelo base não está no cache local")
    from model_adaptation.inference.base_model import load_tokenizer
    return load_tokenizer(os.path.dirname(hits[0]))


def test_labels_mask_prompt_and_supervise_only_the_answer():
    tok = _tokenizer()
    target = '{"args":{"city":"Recife"},"tool":"weather_api"}'
    enc = encode_example(tok, "Como está o tempo em Recife?", target, 384)
    ids, labels = enc["input_ids"], enc["labels"]
    assert len(ids) == len(labels)
    sup = [i for i, l in zip(ids, labels) if l != -100]
    assert sup and all(l == i for i, l in zip(ids, labels) if l != -100)
    decoded = tok.decode(sup)
    assert "weather_api" in decoded and "roteador" not in decoded      # nada do prompt/sistema supervisionado
    first_sup = next(k for k, l in enumerate(labels) if l != -100)
    assert all(l == -100 for l in labels[:first_sup]) and first_sup > 20


def test_collate_pads_right_with_ignore_index():
    batch = [{"input_ids": [5, 6, 7], "labels": [-100, 6, 7]}, {"input_ids": [8], "labels": [8]}]
    out = collate(batch, pad_id=0)
    assert out["input_ids"].shape == (2, 3) and out["attention_mask"].tolist() == [[1, 1, 1], [1, 0, 0]]
    assert out["labels"].tolist() == [[-100, 6, 7], [8, -100, -100]]


def test_lora_targets_cover_all_linear_projections():
    cfg = load_config(CFG / "lora.yaml")
    assert set(cfg["lora"]["target_modules"]) == {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
