"""Tracing ponta a ponta de uma execução de agente — com Langfuse REAL quando configurado.

    agent run → planner → retriever → tool calls → LLM → reflection → resposta final → scores de avaliação

Cada etapa vira um span com input/output/prompt/modelo/tokens/latência/status. Ao fim, o trace inteiro
é entregue a *sinks*:

  * `LocalFileSink`     — SEMPRE ativo por padrão: reaproveita o fallback JSONL de `langfuse_tracing`
                          (`observability/traces/traces.jsonl`). É gravação real em disco, não é Langfuse.
  * `LangfuseSDKSink`   — só quando o Langfuse está configurado (LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST).
                          Usa a API do SDK v3 (`start_observation`, `create_score`). NÃO foi exercitado contra
                          um servidor real nesta sessão (BLOCKED_BY_CONFIGURATION) — só contra um cliente falso.

Nota: o `langfuse_tracing.trace_run` antigo chama `Langfuse.trace()`, método que NÃO existe no SDK v3
instalado (3.12.1); com chaves configuradas ele cairia silenciosamente no arquivo local. Este módulo
usa a API v3 correta e informa em `backends` o que realmente recebeu o trace.

Segurança: chaves/tokens/segredos são mascarados e payloads são truncados antes de sair do processo.
"""
from __future__ import annotations

import re
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Protocol

_SECRET_KEY = re.compile(r"(key|token|secret|password|authorization|credential)", re.I)
_SECRET_VAL = re.compile(r"(sk-[A-Za-z0-9_\-]{12,}|sbp_[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{12,}|eyJ[A-Za-z0-9_\-\.]{20,})")
MAX_CHARS = 2000

SPAN_KINDS = {"planner": "chain", "retriever": "retriever", "tool": "tool", "llm": "generation",
              "reflection": "chain", "response": "span"}


def redact(value: Any, _depth: int = 0) -> Any:
    """Mascara segredos e trunca strings longas; tolera objetos arbitrários."""
    if _depth > 6:
        return "…"
    if isinstance(value, dict):
        return {str(k): ("***" if _SECRET_KEY.search(str(k)) else redact(v, _depth + 1)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, _depth + 1) for v in list(value)[:50]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    s = _SECRET_VAL.sub("***", str(value))
    return s if len(s) <= MAX_CHARS else s[:MAX_CHARS] + f"…[+{len(s) - MAX_CHARS} chars]"


class TraceSink(Protocol):
    name: str

    def emit(self, trace: Dict[str, Any]) -> None: ...


class LocalFileSink:
    """Grava o trace completo como 1 linha JSONL (respeita `LANGFUSE_LOCAL_FALLBACK=0`)."""
    name = "local_file"

    def emit(self, trace: Dict[str, Any]) -> None:
        from observability.langfuse_tracing import _LOCAL_FALLBACK_ENABLED, _write_local_trace
        if not _LOCAL_FALLBACK_ENABLED:
            return
        _write_local_trace(trace["name"], str(trace["input"]), str(trace["output"]),
                           {"trace_id": trace["trace_id"], "kind": "agent_trace/1.0", "spans": trace["spans"],
                            "scores": trace["scores"], "metadata": trace["metadata"], "backends": trace["backends"]})


class LangfuseSDKSink:
    """Envia o trace ao Langfuse via SDK v3. `client` é injetável (testes usam um cliente falso)."""
    name = "langfuse"

    def __init__(self, client: Any):
        self.client = client

    def emit(self, trace: Dict[str, Any]) -> None:
        tid = self.client.create_trace_id(seed=trace["trace_id"])
        root = self.client.start_observation(trace_context={"trace_id": tid}, name=trace["name"], as_type="span",
                                             input=trace["input"], metadata=trace["metadata"])
        for sp in trace["spans"]:
            kwargs: Dict[str, Any] = dict(
                name=sp["name"], as_type=SPAN_KINDS.get(sp["kind"], "span"), input=sp["input"], output=sp["output"],
                metadata={**sp["metadata"], "latency_ms": sp["latency_ms"], "status": sp["status"], "kind": sp["kind"]},
                level="ERROR" if sp["status"] == "error" else "DEFAULT", status_message=sp.get("error"))
            if sp["kind"] == "llm":
                kwargs["model"] = sp.get("model")
                if sp.get("usage"):
                    kwargs["usage_details"] = {"input": sp["usage"].get("input", 0), "output": sp["usage"].get("output", 0)}
                if sp.get("prompt") is not None:
                    kwargs["input"] = sp["prompt"]
            child = root.start_observation(**kwargs)
            child.end()
        root.update(output=trace["output"])
        root.end()
        for s in trace["scores"]:
            self.client.create_score(trace_id=tid, name=s["name"], value=float(s["value"]),
                                     data_type="NUMERIC", comment=s.get("comment"))
        self.client.flush()


def default_sinks() -> List[TraceSink]:
    """Local sempre; Langfuse real só se `langfuse_tracing` conseguiu criar um cliente."""
    sinks: List[TraceSink] = [LocalFileSink()]
    try:
        from observability import langfuse_tracing as lt
        if lt.is_langfuse_active():
            sinks.append(LangfuseSDKSink(lt._lf))
    except Exception:
        pass
    return sinks


class SpanHandle:
    def __init__(self, span: Dict[str, Any]):
        self._s = span

    def set_output(self, output: Any) -> "SpanHandle":
        self._s["output"] = redact(output)
        return self

    def set_usage(self, input_tokens: int, output_tokens: int) -> "SpanHandle":
        self._s["usage"] = {"input": int(input_tokens), "output": int(output_tokens)}
        return self

    def set(self, **meta: Any) -> "SpanHandle":
        for k in ("model", "prompt"):
            if k in meta:
                self._s[k] = redact(meta.pop(k))
        self._s["metadata"].update(redact(meta))
        return self


class AgentTracer:
    def __init__(self, name: str, input: Any = None, sinks: Optional[List[TraceSink]] = None,
                 trace_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.trace_id = trace_id or uuid.uuid4().hex
        self.input = redact(input)
        self.metadata = redact(metadata or {})
        self.sinks = default_sinks() if sinks is None else sinks
        self.spans: List[Dict[str, Any]] = []
        self.scores: List[Dict[str, Any]] = []
        self._t0 = time.perf_counter()
        self._finished: Optional[Dict[str, Any]] = None

    @contextmanager
    def span(self, kind: str, name: Optional[str] = None, input: Any = None, **meta: Any) -> Iterator[SpanHandle]:
        if kind not in SPAN_KINDS:
            raise ValueError(f"tipo de span desconhecido: {kind!r} (use {sorted(SPAN_KINDS)})")
        sp = {"id": uuid.uuid4().hex[:16], "kind": kind, "name": name or kind, "input": redact(input), "output": None,
              "model": None, "prompt": None, "usage": None, "latency_ms": None, "status": "ok", "error": None,
              "metadata": redact(meta)}
        self.spans.append(sp)
        t = time.perf_counter()
        try:
            yield SpanHandle(sp)
        except Exception as e:                       # registra e propaga: tracing nunca engole erro do agente
            sp["status"], sp["error"] = "error", redact(f"{type(e).__name__}: {e}")
            raise
        finally:
            sp["latency_ms"] = round((time.perf_counter() - t) * 1000, 3)

    def score(self, name: str, value: float, comment: Optional[str] = None) -> None:
        if value is None:
            return
        self.scores.append({"name": name, "value": float(value), "comment": comment})

    def finish(self, output: Any = None) -> Dict[str, Any]:
        if self._finished is not None:
            return self._finished
        trace = {"trace_id": self.trace_id, "name": self.name, "input": self.input, "output": redact(output),
                 "metadata": self.metadata, "spans": self.spans, "scores": self.scores,
                 "latency_ms": round((time.perf_counter() - self._t0) * 1000, 3), "backends": [], "sink_errors": []}
        for sink in self.sinks:
            try:
                sink.emit(trace)
                trace["backends"].append(sink.name)
            except Exception as e:                   # sink com defeito não derruba o agente
                trace["sink_errors"].append(f"{sink.name}: {type(e).__name__}: {str(e)[:160]}")
        self._finished = trace
        return trace


def attach_eval_scores(tracer: AgentTracer, row: Dict[str, Any]) -> None:
    """Anexa ao trace as métricas de uma linha do harness (`evaluation.harness.score_case`)."""
    for k in ("faithfulness", "answer_relevancy", "context_recall", "hallucination", "correctness",
              "tool_correctness", "task_completion"):
        if row.get(k) is not None:
            tracer.score(k, row[k], comment=f"juiz={row.get('judge')}")


def run_traced_agent(question: str, *, planner, retriever=None, tools: Optional[Dict[str, Any]] = None, llm,
                     reflector=None, score_fn=None, tracer: Optional[AgentTracer] = None) -> Dict[str, Any]:
    """Fluxo de referência do agente, totalmente instrumentado.

    planner(question) -> {"tool": str|None, "args": dict, "needs_retrieval": bool}
    retriever(question) -> List[str]                  (opcional)
    tools[name](**args) -> resultado                  (opcional)
    llm(question, contexts, tool_result) -> {"text", "model", "prompt", "input_tokens", "output_tokens"}
    reflector(question, answer) -> {"ok": bool, "answer": str}   (opcional)
    score_fn(answer, contexts, tool_result) -> linha do harness (opcional): vira scores do trace
    """
    tr = tracer or AgentTracer("agent_run", input=question)
    contexts: List[str] = []
    result = None
    with tr.span("planner", input=question) as sp:
        plan = planner(question)
        sp.set_output(plan)
    if retriever is not None and plan.get("needs_retrieval", True):
        with tr.span("retriever", input=question) as sp:
            contexts = retriever(question)
            sp.set_output(contexts).set(n_docs=len(contexts))
    if plan.get("tool") and tools and plan["tool"] in tools:
        with tr.span("tool", name=plan["tool"], input=plan.get("args")) as sp:
            result = tools[plan["tool"]](**plan.get("args", {}))
            sp.set_output(result)
    with tr.span("llm", input={"question": question, "n_contexts": len(contexts)}) as sp:
        out = llm(question, contexts, result)
        sp.set_output(out["text"]).set(model=out.get("model"), prompt=out.get("prompt"))
        sp.set_usage(out.get("input_tokens", 0), out.get("output_tokens", 0))
    answer = out["text"]
    if reflector is not None:
        with tr.span("reflection", input=answer) as sp:
            ref = reflector(question, answer)
            sp.set_output(ref)
            answer = ref.get("answer", answer)
    with tr.span("response", input=question) as sp:
        sp.set_output(answer)
    if score_fn is not None:
        attach_eval_scores(tr, score_fn(answer, contexts, result))
    trace = tr.finish(answer)
    return {"answer": answer, "contexts": contexts, "tool_result": result, "plan": plan, "trace": trace, "tracer": tr}
