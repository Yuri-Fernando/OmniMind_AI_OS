"""
Integração com Langfuse — tracing remoto de traces e spans.

Status honesto (ver evaluation/reports/ e WORKLOG.md para o registro
completo): nesta sessão não havia conta Langfuse Cloud configurada
(LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY vazias no .env) e o self-host
completo (langfuse + postgres + clickhouse + redis + minio via
docker-compose) não foi provisionado por ser pesado para o escopo desta
tarefa — fica documentado como próximo passo real, não fingido como feito.

Para ainda assim ter tracing real (não mockado) das execuções de avaliação,
este módulo tem 3 modos, sempre explícitos em `active_backend()`:

1. "cloud"   — Langfuse real, se LANGFUSE_PUBLIC_KEY/SECRET_KEY estiverem
               configuradas (cloud ou self-host via LANGFUSE_HOST). Usa o
               SDK oficial de verdade.
2. "local_file" — fallback real (não é Langfuse, não finge ser): cada
               trace é serializado como uma linha JSONL em
               `observability/traces/traces.jsonl`, com os mesmos campos que
               se mandaria para o Langfuse (name, input, output, metadata,
               timestamp). É uma gravação real em disco de dados reais de
               execução, não um mock de teste.
3. "none"    — Langfuse indisponível E escrita em arquivo desabilitada
               (ex.: `LANGFUSE_LOCAL_FALLBACK=0`); opera silenciosamente,
               igual ao comportamento original.

Graceful degradation preservada: nenhum destes modos derruba o chamador.
"""
import json
import os
import time
from pathlib import Path

from core.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST

_TRACE_DIR = Path(__file__).parent / "traces"
_TRACE_FILE = _TRACE_DIR / "traces.jsonl"
_LOCAL_FALLBACK_ENABLED = os.getenv("LANGFUSE_LOCAL_FALLBACK", "1") != "0"


def _get_langfuse():
    if not (LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY):
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
    except Exception:
        return None


_lf = _get_langfuse()


def active_backend() -> str:
    """Qual backend de tracing está realmente ativo — usado no relatório de
    eval para nunca alegar 'Langfuse real' quando na verdade foi o fallback
    local em arquivo."""
    if _lf is not None:
        return "cloud"
    if _LOCAL_FALLBACK_ENABLED:
        return "local_file"
    return "none"


def _write_local_trace(name: str, input_text: str, output_text: str, metadata: dict) -> None:
    _TRACE_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "name": name,
        "input": input_text,
        "output": output_text,
        "metadata": metadata,
        "timestamp": time.time(),
    }
    with open(_TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def trace_run(name: str, input_text: str, output_text: str, metadata: dict = None):
    """Registra uma execução. Usa Langfuse real se configurado; senão grava
    um trace real localmente (JSONL) se o fallback estiver habilitado."""
    metadata = metadata or {}
    if _lf is not None:
        try:
            return _lf.trace(name=name, input=input_text, output=output_text, metadata=metadata)
        except Exception:
            pass  # cai para o fallback local abaixo, não falha silenciosamente sem registrar nada

    if _LOCAL_FALLBACK_ENABLED:
        try:
            _write_local_trace(name, input_text, output_text, metadata)
        except Exception:
            return None
    return None


def is_langfuse_active() -> bool:
    """Mantido por compatibilidade: True apenas quando é o Langfuse de
    verdade (cloud/self-host), nunca para o fallback local em arquivo."""
    return _lf is not None


def read_local_traces() -> list:
    """Lê todos os traces gravados no fallback local — usado pelo relatório
    de eval para mostrar números reais mesmo sem Langfuse configurado."""
    if not _TRACE_FILE.exists():
        return []
    records = []
    with open(_TRACE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
