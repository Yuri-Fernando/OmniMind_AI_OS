"""Papéis LLM (assessor, specifier, architect, planner, implementer, reviewer).

Cada papel é uma função: monta o prompt, chama o provider dentro do budget,
extrai JSON e valida com Pydantic. Saída inválida gera nova tentativa com o
erro de validação anexado (limitada); esgotou → InvalidLLMOutput.
Rate limit/timeout → retentativas limitadas; esgotou → LLMUnavailable.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from observability.tracing import Tracer  # tracer leve já existente no OmniMind

from .budget import Budget
from .llm.provider import LLMProvider, LLMRateLimitError, LLMTimeoutError
from .schemas import (Assessment, Design, ImplementerOutput, Review, Spec, Task, TaskDAG,
                      TestRunResult, TraceRow)

M = TypeVar("M", bound=BaseModel)
PROMPTS = Path(__file__).parent / "prompts"


class InvalidLLMOutput(RuntimeError):
    pass


class LLMUnavailable(RuntimeError):
    pass


def _prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def untrusted(source_id: str, text: str) -> str:
    safe = text.replace("</untrusted_document>", "</untrusted_document_>")
    return f'<untrusted_document source_id="{source_id}">\n{safe}\n</untrusted_document>'


def extract_json(text: str) -> object:
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if fence:
        t = fence.group(1).strip()
    start = min([i for i in (t.find("{"), t.find("[")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("nenhum JSON na resposta")
    return json.loads(t[start:])


class RoleRunner:
    def __init__(self, provider: LLMProvider, budget: Budget, tracer: Optional[Tracer] = None,
                 max_invalid_retries: int = 2, max_transient_retries: int = 3, backoff_s: float = 0.0,
                 events: Optional[list] = None):
        self.provider = provider
        self.budget = budget
        self.tracer = tracer or Tracer()
        self.max_invalid_retries = max_invalid_retries
        self.max_transient_retries = max_transient_retries
        self.backoff_s = backoff_s
        self.events = events if events is not None else []

    def _call(self, role: str, prompt: str):
        transient = 0
        while True:
            self.budget.check_call(role)
            start = time.monotonic()
            try:
                resp = self.provider.complete(role, _prompt("system") + "\n\n" + _prompt(role), prompt)
            except (LLMRateLimitError, LLMTimeoutError) as exc:
                self.budget.record(role, 0, 0, (time.monotonic() - start) * 1000)
                transient += 1
                self.events.append({"role": role, "event": "transient_error", "error": type(exc).__name__})
                if transient > self.max_transient_retries:
                    raise LLMUnavailable(f"{role}:{type(exc).__name__}") from exc
                time.sleep(self.backoff_s * transient)
                continue
            self.budget.record(role, resp.input_tokens, resp.output_tokens, (time.monotonic() - start) * 1000)
            return resp

    def run(self, role: str, prompt: str, model: Type[M]) -> M:
        span = self.tracer.start(f"role:{role}")
        last_error = ""
        for attempt in range(self.max_invalid_retries + 1):
            full = prompt if not last_error else (
                f"{prompt}\n\nSua resposta anterior foi rejeitada pela validação: {last_error}\n"
                "Responda novamente só com JSON válido no schema.")
            resp = self._call(role, full)
            try:
                obj = model.model_validate(extract_json(resp.text))
                self.tracer.finish(span.name, role=role, attempts=attempt + 1, ok=True)
                self.events.append({"role": role, "event": "ok", "attempts": attempt + 1})
                return obj
            except (ValueError, ValidationError) as exc:
                last_error = str(exc)[:800]
                self.events.append({"role": role, "event": "invalid_output", "attempt": attempt + 1})
        self.tracer.finish(span.name, role=role, ok=False)
        raise InvalidLLMOutput(f"{role}:{last_error[:300]}")

    # ------------------------------------------------------------ papéis
    def assess(self, docs: Dict[str, str]) -> Assessment:
        body = "\n\n".join(untrusted(k, v) for k, v in docs.items())
        return self.run("assessor", f"DOCUMENTOS:\n{body}", Assessment)

    def specify(self, docs: Dict[str, str], decisions: List[dict], golden: Dict[str, List[str]]) -> Spec:
        body = "\n\n".join(untrusted(k, v) for k, v in docs.items())
        prompt = (f"DOCUMENTOS:\n{body}\n\nDECISOES_HUMANAS:\n{json.dumps(decisions, ensure_ascii=False)}\n\n"
                  f"GOLDEN_TESTS_DISPONIVEIS:\n{json.dumps(golden, ensure_ascii=False)}")
        return self.run("specifier", prompt, Spec)

    def design(self, spec: Spec) -> Design:
        return self.run("architect", f"SPEC_APROVADA:\n{spec.model_dump_json(indent=1)}", Design)

    def plan(self, spec: Spec, design: Design, repo_files: List[str]) -> TaskDAG:
        prompt = (f"SPEC_APROVADA:\n{spec.model_dump_json(indent=1)}\n\nDESIGN:\n{design.model_dump_json(indent=1)}"
                  f"\n\nARQUIVOS_DO_REPO:\n{json.dumps(repo_files)}")
        return self.run("planner", prompt, TaskDAG)

    def implement(self, task: Task, spec: Spec, current: Dict[str, Optional[str]],
                  feedback: str = "") -> ImplementerOutput:
        reqs = [r.model_dump() for r in spec.requirements if r.id in task.req_ids]
        prompt = (f"TASK_ID: {task.id}\nTAREFA:\n{task.model_dump_json(indent=1)}\n\nREQUISITOS:\n"
                  f"{json.dumps(reqs, ensure_ascii=False, indent=1)}\n\nCONTEUDO_ATUAL_OWNED_PATHS:\n"
                  + "\n".join(untrusted(p, c if c is not None else "<arquivo novo>") for p, c in current.items())
                  + (f"\n\nFEEDBACK_DA_VERIFICACAO:\n{feedback}" if feedback else ""))
        out = self.run("implementer", prompt, ImplementerOutput)
        if out.task_id != task.id:
            raise InvalidLLMOutput(f"implementer:task_id {out.task_id!r} != {task.id!r}")
        return out

    def review(self, spec: Spec, diff: str, tests: TestRunResult, trace: List[TraceRow]) -> Review:
        prompt = (f"SPEC_APROVADA:\n{spec.model_dump_json(indent=1)}\n\nDIFF:\n{untrusted('diff', diff[:60000])}"
                  f"\n\nRESULTADO_DO_RUNNER_EXTERNO:\n{tests.model_dump_json(indent=1)}\n\nRASTREABILIDADE:\n"
                  + json.dumps([r.model_dump() for r in trace], ensure_ascii=False, indent=1))
        return self.run("reviewer", prompt, Review)
