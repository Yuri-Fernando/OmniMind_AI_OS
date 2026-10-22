"""Constantes e utilitários compartilhados do experimento de adaptação de modelo.

Tarefa: *tool-calling estruturado* — dado um pedido em português, o modelo
responde SOMENTE com um JSON `{"tool": ..., "args": {...}}` apontando uma das
ferramentas do agente (calculator, weather_api, web_search, file_reader) ou
`none` quando nenhuma ferramenta se aplica.

Escolha deliberada: é a tarefa que o agente OmniMind realmente executa
(seleção de ferramenta + argumentos), é verificável de forma determinística
(sem LLM-juiz) e cabe em um modelo <=1B numa GPU de 8 GB.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

MODEL_ADAPTATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODEL_ADAPTATION_DIR.parent
RESULTS_DIR = MODEL_ADAPTATION_DIR / "results"
DATA_DIR = MODEL_ADAPTATION_DIR / "datasets" / "data"

# Pesos/checkpoints NUNCA vão para o Drive (G:) nem para o git.
STAGING_DIR = Path(os.getenv("OMNIMIND_ADAPT_STAGING", r"D:\Claude Temp\staging\omnimind-adapt"))

DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"  # Apache-2.0

# Fonte única do esquema: evaluation/tool_call_accuracy.py (espelha tools/*.py). `none` = sem ferramenta.
from evaluation.tool_call_accuracy import DEFAULT_TOOL_SCHEMAS as TOOL_SCHEMAS  # noqa: E402
TOOL_NAMES = list(TOOL_SCHEMAS)

SYSTEM_PROMPT = (
    "Você é o roteador de ferramentas de um agente. Responda SOMENTE com um JSON "
    'no formato {"tool": <nome>, "args": {...}}, sem texto extra.\n'
    "Ferramentas:\n"
    '- calculator: args {"expression": "<expressão aritmética, ex. 12*7>"}\n'
    '- weather_api: args {"city": "<cidade>"}\n'
    '- web_search: args {"query": "<assunto pesquisado>"}\n'
    '- file_reader: args {"path": "<caminho do arquivo>"}\n'
    '- none: args {} (conversa sem ferramenta)'
)


def set_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def canonical_target(tool: str, args: Dict[str, Any]) -> str:
    """Resposta-alvo canônica (JSON compacto, chaves ordenadas)."""
    return json.dumps({"tool": tool, "args": args}, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_messages(user_text: str, assistant_text: Optional[str] = None) -> List[Dict[str, str]]:
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    if assistant_text is not None:
        msgs.append({"role": "assistant", "content": assistant_text})
    return msgs


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
