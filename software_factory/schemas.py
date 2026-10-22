"""Contratos Pydantic de todos os artefatos da Software Factory.

Toda saída de LLM passa por estes modelos antes de ser usada; saída que não
valida é erro explícito (retry limitado), nunca coerção silenciosa.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

R_ID = re.compile(r"^R-\d{3}$")
T_ID = re.compile(r"^T\d+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- entrada
class InputFile(_Strict):
    source_id: str  # ex.: "brief/PRD.md"
    sha256: str
    size: int


class RepoRef(_Strict):
    path: str
    base_commit_sha: str
    main_branch: str = "main"


class InputManifest(_Strict):
    schema_version: Literal["sdd-input/1.0"] = "sdd-input/1.0"
    run_id: str
    project: str
    files: List[InputFile]
    repo: RepoRef
    golden_tests: List[InputFile] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


# ---------------------------------------------------------------- assessment
class Ambiguity(_Strict):
    id: str
    evidence_source_id: str
    question: str
    impact: str
    blocking: bool
    category: Literal["requirement", "contradiction", "missing", "security"] = "requirement"


class Assessment(_Strict):
    schema_version: Literal["sdd-assessment/1.0"] = "sdd-assessment/1.0"
    ambiguities: List[Ambiguity] = Field(default_factory=list)


class Decision(_Strict):
    ambiguity_id: str
    answer: str
    decided_by: str


class Resolution(_Strict):
    schema_version: Literal["sdd-resolution/1.0"] = "sdd-resolution/1.0"
    decisions: List[Decision] = Field(default_factory=list)


# ---------------------------------------------------------------- spec
class AcceptanceCriterion(_Strict):
    id: str
    given: str
    when: str
    then: str
    test_id: str  # nó pytest que prova o critério, ex.: "golden_tests/test_acceptance.py::test_x"


class Requirement(_Strict):
    id: str
    level: Literal["MUST", "SHOULD"]
    text: str
    trace_source: str  # source_id de um arquivo do input manifest ou "decision:A-001"
    acceptance: List[AcceptanceCriterion] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _rid(cls, v: str) -> str:
        if not R_ID.match(v):
            raise ValueError(f"R-ID inválido: {v!r} (esperado R-###)")
        return v


class Spec(_Strict):
    schema_version: Literal["sdd-spec/1.0"] = "sdd-spec/1.0"
    scope: str
    requirements: List[Requirement] = Field(min_length=1)
    unresolved: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------- design
class Design(_Strict):
    schema_version: Literal["sdd-design/1.0"] = "sdd-design/1.0"
    architecture: str
    decisions: List[str] = Field(default_factory=list)
    interfaces: Dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------- tasks
class Task(_Strict):
    id: str
    title: str
    requires: List[str] = Field(default_factory=list)
    req_ids: List[str] = Field(min_length=1)
    owned_paths: List[str] = Field(min_length=1)
    acceptance: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _tid(cls, v: str) -> str:
        if not T_ID.match(v):
            raise ValueError(f"task id inválido: {v!r} (esperado T<n>)")
        return v


class TaskDAG(_Strict):
    schema_version: Literal["task-dag/1.0.0"] = "task-dag/1.0.0"
    project: str
    tasks: List[Task] = Field(min_length=1)


# ---------------------------------------------------------------- implementação
class FileChange(_Strict):
    path: str
    content: str


class ImplementerOutput(_Strict):
    task_id: str
    files: List[FileChange] = Field(min_length=1)
    commands: List[str] = Field(default_factory=list)
    claimed_tests_passed: Optional[bool] = None  # registrado, nunca usado como evidência
    notes: str = ""


class TaskResult(_Strict):
    task_id: str
    branch: str
    commit_sha: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    status: Literal["COMMITTED", "REJECTED"]
    violations: List[str] = Field(default_factory=list)
    claimed_tests_passed: Optional[bool] = None


# ---------------------------------------------------------------- verificação
class TestOutcome(str, Enum):
    __test__ = False  # não é classe de teste do pytest
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class TestCaseResult(_Strict):
    __test__ = False
    test_id: str
    outcome: TestOutcome
    message: str = ""


class TestRunResult(_Strict):
    __test__ = False
    schema_version: Literal["sdd-test-run/1.0"] = "sdd-test-run/1.0"
    command: List[str]
    returncode: Optional[int]
    timed_out: bool = False
    duration_s: float
    cases: List[TestCaseResult] = Field(default_factory=list)
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def passed(self) -> bool:
        return (self.returncode == 0 and not self.timed_out and bool(self.cases)
                and all(c.outcome == TestOutcome.PASS for c in self.cases))


# ---------------------------------------------------------------- revisão
class ReviewFinding(_Strict):
    severity: Literal["blocker", "major", "minor", "info"]
    message: str
    req_id: Optional[str] = None


class Review(_Strict):
    schema_version: Literal["sdd-review/1.0"] = "sdd-review/1.0"
    verdict: Literal["APPROVE", "REQUEST_CHANGES"]
    findings: List[ReviewFinding] = Field(default_factory=list)


class TraceRow(_Strict):
    req_id: str
    level: str
    trace_source: str
    task_ids: List[str]
    commits: List[str]
    test_ids: List[str]
    outcomes: List[str]
    covered: bool


# ---------------------------------------------------------------- relatório
class StageUsage(_Strict):
    stage: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0


class RunReport(_Strict):
    schema_version: Literal["sdd-run-report/1.0"] = "sdd-run-report/1.0"
    run_id: str
    state: str
    blocked_reason: Optional[str] = None
    provider: str
    model: str
    base_commit_sha: str
    integration_commit_sha: Optional[str] = None
    verification: Optional[str] = None  # PASS | FAIL | NOT_RUN
    requirement_coverage: Optional[float] = None
    trace_coverage: Optional[float] = None
    usage: List[StageUsage] = Field(default_factory=list)
    estimated_cost_usd: Optional[float] = None
    approvals: List[dict] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)  # caminho relativo -> sha256
    created_at: str = Field(default_factory=utc_now)
