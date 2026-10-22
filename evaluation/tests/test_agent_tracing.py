"""Instrumentação do fluxo do agente: spans, scores, redação de segredos, sinks (cliente Langfuse falso + JSONL real)."""
import json

import pytest

from evaluation.harness import AgentCase, HarnessConfig, score_case
from observability import langfuse_tracing as lt
from observability.agent_tracing import (AgentTracer, LangfuseSDKSink, LocalFileSink, attach_eval_scores, redact,
                                         run_traced_agent)


class MemSink:
    name = "mem"

    def __init__(self):
        self.traces = []

    def emit(self, trace):
        self.traces.append(trace)


class FakeObs:
    def __init__(self, log, kind, kw):
        self.log, self.kind, self.kw = log, kind, kw
        log.append(("start", kind, kw))

    def start_observation(self, **kw):
        return FakeObs(self.log, "child", kw)

    def update(self, **kw):
        self.log.append(("update", self.kind, kw))

    def end(self):
        self.log.append(("end", self.kind, {}))


class FakeLangfuse:
    """Imita a parte da API do SDK v3 que o sink usa."""
    def __init__(self):
        self.log, self.scores, self.flushed = [], [], 0

    def create_trace_id(self, *, seed=None):
        return "t" * 8 + (seed or "")[:24].ljust(24, "0")

    def start_observation(self, **kw):
        return FakeObs(self.log, "root", kw)

    def create_score(self, **kw):
        self.scores.append(kw)

    def flush(self):
        self.flushed += 1


def _agent(tracer, tool_ok=True):
    def tool(expression):
        if not tool_ok:
            raise ZeroDivisionError("boom")
        return str(eval(expression, {"__builtins__": {}}))
    return run_traced_agent(
        "Quanto é 37 vezes 12?",
        planner=lambda q: {"tool": "calculator", "args": {"expression": "37*12"}, "needs_retrieval": True},
        retriever=lambda q: ["documento sobre aritmética"],
        tools={"calculator": tool},
        llm=lambda q, ctx, res: {"text": f"O resultado é {res}.", "model": "qwen-test", "prompt": "SYS+Q",
                                 "input_tokens": 120, "output_tokens": 9},
        reflector=lambda q, a: {"ok": True, "answer": a},
        tracer=tracer)


def test_full_flow_produces_all_span_kinds_in_order():
    sink = MemSink()
    out = _agent(AgentTracer("agent_run", "Quanto é 37 vezes 12?", sinks=[sink]))
    t = out["trace"]
    assert [s["kind"] for s in t["spans"]] == ["planner", "retriever", "tool", "llm", "reflection", "response"]
    assert out["answer"] == "O resultado é 444." and t["output"] == "O resultado é 444."
    llm = t["spans"][3]
    assert llm["model"] == "qwen-test" and llm["usage"] == {"input": 120, "output": 9} and llm["prompt"] == "SYS+Q"
    assert all(s["latency_ms"] is not None and s["status"] == "ok" for s in t["spans"])
    assert t["backends"] == ["mem"] and sink.traces == [t]


def test_error_in_tool_is_recorded_and_propagated():
    sink = MemSink()
    tr = AgentTracer("agent_run", "q", sinks=[sink])
    with pytest.raises(ZeroDivisionError):
        _agent(tr, tool_ok=False)
    bad = next(s for s in tr.spans if s["kind"] == "tool")
    assert bad["status"] == "error" and "ZeroDivisionError" in bad["error"]
    assert tr.finish("falhou")["spans"][2]["status"] == "error"          # trace parcial ainda é emitido


def test_eval_scores_attached_before_emit():
    sink = MemSink()
    tr = AgentTracer("agent_run", "Quanto é 37 vezes 12?", sinks=[sink])
    case_of = lambda ans, ctx, res: score_case(
        AgentCase("t1", "Quanto é 37 vezes 12?", ans, ctx, "444",
                  {"tool": "calculator", "args": {"expression": "37*12"}},
                  {"tool": "calculator", "args": {"expression": "37*12"}}, res), HarnessConfig())
    out = run_traced_agent(
        "Quanto é 37 vezes 12?", planner=lambda q: {"tool": "calculator", "args": {"expression": "37*12"}},
        tools={"calculator": lambda expression: "444"},
        llm=lambda q, c, r: {"text": "37 vezes 12 é 444.", "model": "m", "input_tokens": 1, "output_tokens": 1},
        score_fn=case_of, tracer=tr)
    names = {s["name"]: s["value"] for s in out["trace"]["scores"]}
    assert names["tool_correctness"] == 1.0 and names["task_completion"] == 1.0 and "answer_relevancy" in names
    assert sink.traces[0]["scores"] == out["trace"]["scores"]


def test_attach_scores_skips_missing_metrics():
    tr = AgentTracer("x", sinks=[])
    attach_eval_scores(tr, {"faithfulness": None, "answer_relevancy": 0.7, "judge": "deterministic"})
    assert [s["name"] for s in tr.scores] == ["answer_relevancy"]


def test_secrets_are_redacted_and_payloads_truncated():
    red = redact({"api_key": "sk-abcdefghijklmnop1234", "note": "usei sk-abcdefghijklmnop1234 aqui",
                  "nested": {"Authorization": "Bearer x", "ok": 1}, "big": "x" * 5000})
    assert red["api_key"] == "***" and "sk-abc" not in red["note"] and red["nested"]["Authorization"] == "***"
    assert red["nested"]["ok"] == 1 and len(red["big"]) < 2100 and "chars]" in red["big"]


def test_span_kind_validated():
    with pytest.raises(ValueError):
        with AgentTracer("x", sinks=[]).span("inventado"):
            pass


def test_finish_is_idempotent_and_failing_sink_does_not_break_agent():
    class Bad:
        name = "bad"

        def emit(self, trace):
            raise RuntimeError("rede")
    good = MemSink()
    tr = AgentTracer("x", "in", sinks=[Bad(), good])
    t1 = tr.finish("out")
    assert tr.finish("outro") is t1 and len(good.traces) == 1
    assert t1["backends"] == ["mem"] and "bad: RuntimeError" in t1["sink_errors"][0]


def test_langfuse_sink_uses_v3_api_with_generation_usage_and_scores():
    fake = FakeLangfuse()
    tr = AgentTracer("agent_run", "q", sinks=[LangfuseSDKSink(fake)], trace_id="abc123")
    with tr.span("planner", input="q") as s:
        s.set_output({"tool": None})
    with tr.span("llm", input="q") as s:
        s.set_output("resposta").set(model="qwen", prompt="P").set_usage(10, 3)
    tr.score("faithfulness", 0.8, "juiz=x")
    t = tr.finish("resposta")
    assert t["backends"] == ["langfuse"] and fake.flushed == 1
    starts = [e for e in fake.log if e[0] == "start"]
    assert starts[0][1] == "root" and starts[0][2]["trace_context"]["trace_id"].startswith("tttttttt")
    gen = next(e[2] for e in starts if e[2].get("as_type") == "generation")
    assert gen["model"] == "qwen" and gen["usage_details"] == {"input": 10, "output": 3} and gen["input"] == "P"
    assert [e[1] for e in fake.log if e[0] == "end"].count("child") == 2
    assert fake.scores[0]["name"] == "faithfulness" and fake.scores[0]["value"] == 0.8
    assert fake.scores[0]["trace_id"] == starts[0][2]["trace_context"]["trace_id"]


def test_local_file_sink_writes_real_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(lt, "_TRACE_DIR", tmp_path)
    monkeypatch.setattr(lt, "_TRACE_FILE", tmp_path / "traces.jsonl")
    monkeypatch.setattr(lt, "_LOCAL_FALLBACK_ENABLED", True)
    out = _agent(AgentTracer("agent_run", "Quanto é 37 vezes 12?", sinks=[LocalFileSink()]))
    recs = lt.read_local_traces()
    assert len(recs) == 1 and recs[0]["metadata"]["kind"] == "agent_trace/1.0"
    assert recs[0]["metadata"]["trace_id"] == out["trace"]["trace_id"]
    assert [s["kind"] for s in recs[0]["metadata"]["spans"]][-1] == "response"
    json.dumps(recs[0])                                                    # serializável


def test_local_sink_respects_disable_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(lt, "_TRACE_DIR", tmp_path)
    monkeypatch.setattr(lt, "_TRACE_FILE", tmp_path / "traces.jsonl")
    monkeypatch.setattr(lt, "_LOCAL_FALLBACK_ENABLED", False)
    AgentTracer("x", "in", sinks=[LocalFileSink()]).finish("out")
    assert not (tmp_path / "traces.jsonl").exists()
