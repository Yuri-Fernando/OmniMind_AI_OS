"""
Integração com Langfuse — tracing remoto de traces e spans.
Graceful degradation: se as chaves não estiverem configuradas, opera silenciosamente.
"""
from core.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST


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


def trace_run(name: str, input_text: str, output_text: str, metadata: dict = None):
    """Registra uma execução no Langfuse se disponível."""
    if _lf is None:
        return None
    try:
        t = _lf.trace(name=name, input=input_text, output=output_text, metadata=metadata or {})
        return t
    except Exception:
        return None


def is_langfuse_active() -> bool:
    return _lf is not None
