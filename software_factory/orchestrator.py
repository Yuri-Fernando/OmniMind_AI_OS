"""A0 ORCHESTRATOR — máquina de estados determinística (não é LLM).

Cada chamada a `advance()` avança o run até o próximo gate humano, um estado
terminal ou um bloqueio. O estado é persistido em runs/{run_id}/run_state.json
depois de cada transição, então o run pode ser retomado em outro processo.

Gates:
  G0 input       arquivos existem, não vazios, hashes conferem, repo-base fixado
  G1 assessment  nenhuma ambiguidade bloqueante sem decisão humana
  G2 spec        todo requisito com origem; todo MUST com teste golden existente; aprovação humana
  G3 plan        DAG válido (ids, R-IDs, ciclo, owned_paths, colisão); aprovação humana
  G4 implement   escrita só em owned_paths, sem segredo, compila, sem comando destrutivo
  G5 verify      runner externo: todos os testes da spec PASS (relato do agente é ignorado)
  G6 review      MUST rastreáveis e cobertos + revisor independente sem blocker
  G7 delivery    PR aberto em modo simulado; merge e COMPLETE só por humano
"""
from __future__ import annotations

import ast
import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from safety.policy_engine import PolicyEngine  # políticas de entrada já existentes no OmniMind

from . import git_ops
from .approvals import ApprovalStore
from .budget import Budget, BudgetExceeded
from .dag import DAGError, topological_order, validate_dag
from .delivery import (MockPullRequestClient, build_traceability, coverage, pr_body,
                       write_traceability_csv)
from .guardrails import check_write_path, classify_command, scan_secrets, scan_untrusted_text
from .hashing import sha256_bytes, sha256_file
from .llm.provider import LLMProvider
from .roles import InvalidLLMOutput, LLMUnavailable, RoleRunner
from .runner import run_pytest
from .schemas import (Ambiguity, Assessment, Decision, Design, InputFile, InputManifest, RepoRef,
                      Resolution, RunReport, Spec, StageUsage, TaskDAG, TaskResult, TestOutcome, TestRunResult,
                      utc_now)
from .state_machine import TERMINAL, RunState, transition

ARTIFACTS = {
    "spec": "02_spec/spec.json",
    "design": "03_design/design.json",
    "tasks": "04_tasks/tasks.json",
    "pr": "08_delivery/PR_BODY.md",
}
DEFAULT_PROTECTED = ("brief", "golden_tests", ".git", ".github", ".gitignore")


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "model_dump_json"):
        text = value.model_dump_json(indent=2)
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def _snapshot(src: Path, dst: Path, prefix: str) -> List[InputFile]:
    files = []
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            rel = p.relative_to(src).as_posix()
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            files.append(InputFile(source_id=f"{prefix}/{rel}", sha256=sha256_file(target), size=target.stat().st_size))
    return files


class Orchestrator:
    def __init__(self, run_dir: Path, provider: LLMProvider, budget: Optional[Budget] = None,
                 require_approval: Iterable[str] = ("spec", "tasks"), backoff_s: float = 0.0,
                 test_timeout_s: float = 180.0):
        self.run_dir = Path(run_dir)
        self.provider = provider
        self.budget = budget or Budget()
        self.require_approval = set(require_approval)
        self.test_timeout_s = test_timeout_s
        self.events: list = []
        self.roles = RoleRunner(provider, self.budget, backoff_s=backoff_s, events=self.events)
        self.approvals = ApprovalStore(self.run_dir / "approvals.json")
        self.st = json.loads((self.run_dir / "run_state.json").read_text(encoding="utf-8"))
        for u in self.st.get("usage", []):  # budget sobrevive a retomadas em outro processo
            self.budget.usage[u["stage"]] = StageUsage(**u)

    # ------------------------------------------------------------ criação
    @classmethod
    def create(cls, runs_root: Path, project: str, brief_dir: Path, golden_dir: Path, repo_path: Path,
               base_commit_sha: str, provider: LLMProvider, main_branch: str = "main",
               extra_protected: Iterable[str] = (), run_id: Optional[str] = None, **kw) -> "Orchestrator":
        run_id = run_id or "run-" + uuid.uuid4().hex[:10]
        run_dir = Path(runs_root) / run_id
        if run_dir.exists():
            raise FileExistsError(run_dir)
        files = _snapshot(Path(brief_dir), run_dir / "input" / "brief", "brief")
        golden = _snapshot(Path(golden_dir), run_dir / "input" / "golden_tests", "golden_tests")
        manifest = InputManifest(run_id=run_id, project=project, files=files, golden_tests=golden,
                                 repo=RepoRef(path=str(Path(repo_path).resolve()), base_commit_sha=base_commit_sha,
                                              main_branch=main_branch))
        _write_json(run_dir / "input_manifest.json", manifest)
        _write_json(run_dir / "run_state.json", {
            "run_id": run_id, "project": project, "state": RunState.CREATED.value, "blocked_reason": None,
            "attempt": 0, "history": [], "protected": list(DEFAULT_PROTECTED) + list(extra_protected),
            "integration_branch": None, "integration_commit": None, "verification": None})
        return cls(run_dir, provider, **kw)

    # ------------------------------------------------------------ util
    @property
    def state(self) -> RunState:
        return RunState(self.st["state"])

    @property
    def manifest(self) -> InputManifest:
        return InputManifest.model_validate_json((self.run_dir / "input_manifest.json").read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.st["usage"] = [u.model_dump() for u in self.budget.usage.values()]
        _write_json(self.run_dir / "run_state.json", self.st)

    def _to(self, dst: RunState, reason: str = "") -> None:
        src = self.state
        transition(src, dst)
        self.st["state"] = dst.value
        self.st["blocked_reason"] = reason if dst in TERMINAL else None
        self.st["history"].append({"from": src.value, "to": dst.value, "at": utc_now(), "reason": reason})
        self._save()

    def _block(self, reason: str) -> bool:
        self.st["blocked_reason"] = reason
        self._save()
        return False

    def _read(self, rel: str, model):
        return model.model_validate_json((self.run_dir / rel).read_text(encoding="utf-8"))

    def _docs(self) -> Dict[str, str]:
        base = self.run_dir / "input"
        return {f.source_id: (base / f.source_id).read_text(encoding="utf-8") for f in self.manifest.files}

    def _golden_index(self) -> Dict[str, List[str]]:
        idx = {}
        for f in self.manifest.golden_tests:
            if f.source_id.endswith(".py"):
                tree = ast.parse((self.run_dir / "input" / f.source_id).read_text(encoding="utf-8"))
                idx[f.source_id] = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                                    and n.name.startswith("test_")]
        return idx

    def _approval_ok(self, artifact: str) -> Optional[str]:
        """None se OK; senão o motivo de bloqueio."""
        if artifact not in self.require_approval:
            return None
        path = self.run_dir / ARTIFACTS[artifact]
        status = self.approvals.status(artifact, sha256_file(path))
        if status == "VALID":
            return None
        return f"AWAITING_APPROVAL:{artifact}" if status == "MISSING" else f"APPROVAL_EXPIRED:{artifact}"

    def _repo(self) -> Path:
        return Path(self.manifest.repo.path)

    # ------------------------------------------------------------ API humana
    def approve(self, artifact: str, approver: str, reason: str = "") -> dict:
        path = self.run_dir / ARTIFACTS[artifact]
        if not path.exists():
            raise FileNotFoundError(f"artefato {artifact} ainda não existe")
        return self.approvals.approve(artifact, sha256_file(path), approver, reason)

    def resolve(self, decisions: List[dict]) -> Resolution:
        assessment = self._read("00_assessment/ambiguities.json", Assessment)
        known = {a.id for a in assessment.ambiguities}
        res = Resolution(decisions=[Decision(**d) for d in decisions])
        unknown = {d.ambiguity_id for d in res.decisions} - known
        if unknown:
            raise ValueError(f"UNKNOWN_AMBIGUITY:{','.join(sorted(unknown))}")
        _write_json(self.run_dir / "01_resolution/decisions.json", res)
        md = ["# Decisões humanas", ""] + [f"- **{d.ambiguity_id}** ({d.decided_by}): {d.answer}" for d in res.decisions]
        (self.run_dir / "01_resolution/decisions.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        return res

    def cancel(self, reason: str = "cancelado por humano") -> None:
        self._to(RunState.CANCELLED, reason)

    # ------------------------------------------------------------ loop
    def advance(self) -> dict:
        while self.state not in TERMINAL:
            try:
                progressed = self._step()
            except BudgetExceeded as exc:
                self._to(RunState.BUDGET_EXCEEDED, str(exc))
                break
            except LLMUnavailable as exc:
                self._to(RunState.FAILED, f"LLM_UNAVAILABLE:{exc}")
                break
            except InvalidLLMOutput as exc:
                self._to(RunState.FAILED, f"INVALID_LLM_OUTPUT:{exc}")
                break
            if not progressed:
                break
        self._write_events()
        report = self._report()
        return {"run_id": self.st["run_id"], "state": self.state.value,
                "blocked_reason": self.st["blocked_reason"], "verification": report.verification,
                "run_dir": str(self.run_dir)}

    def _step(self) -> bool:
        return getattr(self, f"_on_{self.state.value.lower()}")()

    # ------------------------------------------------------------ G0
    def _on_created(self) -> bool:
        m = self.manifest
        policy = PolicyEngine()
        if not m.files:
            self._to(RunState.FAILED, "G0:NO_INPUT_FILES")
            return True
        for f in m.files + m.golden_tests:
            p = self.run_dir / "input" / f.source_id
            if not p.exists() or sha256_file(p) != f.sha256:
                self._to(RunState.FAILED, f"G0:INPUT_TAMPERED:{f.source_id}")
                return True
        for f in m.files:
            if policy.evaluate((self.run_dir / "input" / f.source_id).read_text(encoding="utf-8"))["blocked"]:
                self._to(RunState.FAILED, f"G0:INPUT_POLICY:{f.source_id}")
                return True
        try:
            git_ops.git(self._repo(), "cat-file", "-e", f"{m.repo.base_commit_sha}^{{commit}}")
            head = git_ops.head_sha(self._repo(), m.repo.main_branch)
        except git_ops.GitError as exc:
            self._to(RunState.FAILED, f"G0:REPO_INVALID:{exc}")
            return True
        if head != m.repo.base_commit_sha:
            self._to(RunState.FAILED, f"G0:STALE_BASE:{head[:12]}!={m.repo.base_commit_sha[:12]}")
            return True
        self._to(RunState.INPUT_VALIDATED)
        return True

    # ------------------------------------------------------------ assessment (A1)
    def _on_input_validated(self) -> bool:
        docs = self._docs()
        security = []
        for sid, text in docs.items():
            findings = scan_untrusted_text(text)
            if findings:
                security.append(Ambiguity(
                    id=f"S-{len(security) + 1:03d}", evidence_source_id=sid, category="security", blocking=True,
                    question="Documento contém instruções dirigidas ao agente; confirme que é só conteúdo e "
                             "que nenhuma ação embutida deve ser executada.",
                    impact="; ".join(findings)[:400]))
        assessment = self.roles.assess(docs)
        merged = Assessment(ambiguities=security + assessment.ambiguities)
        _write_json(self.run_dir / "00_assessment/ambiguities.json", merged)
        self._to(RunState.ASSESSED)
        return True

    # ------------------------------------------------------------ G1 + G2 (A3)
    def _decisions(self) -> List[Decision]:
        p = self.run_dir / "01_resolution/decisions.json"
        return self._read("01_resolution/decisions.json", Resolution).decisions if p.exists() else []

    def _on_assessed(self) -> bool:
        assessment = self._read("00_assessment/ambiguities.json", Assessment)
        decided = {d.ambiguity_id for d in self._decisions()}
        pending = [a.id for a in assessment.ambiguities if a.blocking and a.id not in decided]
        if pending:
            if self.state == RunState.ASSESSED:
                self._to(RunState.RESOLUTION_PENDING)
            return self._block("HUMAN_REQUIRED:" + ",".join(pending))
        spec_path = self.run_dir / ARTIFACTS["spec"]
        if not spec_path.exists():
            spec = self.roles.specify(self._docs(), [d.model_dump() for d in self._decisions()], self._golden_index())
            error = self._spec_gate(spec)
            if error:
                _write_json(self.run_dir / "02_spec/rejected_spec.json", spec)
                self._to(RunState.FAILED, f"G2:{error}")
                return True
            if spec.unresolved:
                _write_json(self.run_dir / "02_spec/unresolved_spec.json", spec)
                if self.state == RunState.ASSESSED:
                    self._to(RunState.RESOLUTION_PENDING)
                return self._block("SPEC_UNRESOLVED:" + " | ".join(spec.unresolved)[:300])
            _write_json(spec_path, spec)
            self._write_feature(spec)
        blocked = self._approval_ok("spec")
        if blocked:
            return self._block(blocked)
        self._to(RunState.SPEC_APPROVED)
        return True

    _on_resolution_pending = _on_assessed

    def _spec_gate(self, spec: Spec) -> Optional[str]:
        sources = {f.source_id for f in self.manifest.files}
        decided = {f"decision:{d.ambiguity_id}" for d in self._decisions()}
        golden = self._golden_index()
        ids = [r.id for r in spec.requirements]
        if len(ids) != len(set(ids)):
            return "DUPLICATE_R_ID"
        for r in spec.requirements:
            if r.trace_source not in sources | decided:
                return f"UNTRACEABLE_REQUIREMENT:{r.id}:{r.trace_source}"
            for ac in r.acceptance:
                file_part, _, name = ac.test_id.partition("::")
                if r.level == "MUST" and name not in golden.get(file_part, []):
                    return f"MUST_WITHOUT_GOLDEN_TEST:{r.id}:{ac.test_id}"
        return None

    def _write_feature(self, spec: Spec) -> None:
        lines = [f"Feature: {spec.scope}", ""]
        for r in spec.requirements:
            for ac in r.acceptance:
                lines += [f"  # {r.id} ({r.level}) — {r.text}", f"  Scenario: {ac.id} [{ac.test_id}]",
                          f"    Given {ac.given}", f"    When {ac.when}", f"    Then {ac.then}", ""]
        (self.run_dir / "02_spec/acceptance.feature").write_text("\n".join(lines), encoding="utf-8")

    # ------------------------------------------------------------ design (A4)
    def _on_spec_approved(self) -> bool:
        blocked = self._approval_ok("spec")
        if blocked:
            return self._block(blocked)
        path = self.run_dir / ARTIFACTS["design"]
        if not path.exists():
            design = self.roles.design(self._read(ARTIFACTS["spec"], Spec))
            _write_json(path, design)
            md = ["# Arquitetura", "", design.architecture, "", "## Decisões", ""] + [f"- {d}" for d in design.decisions]
            (self.run_dir / "03_design/architecture.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        blocked = self._approval_ok("design")
        if blocked:
            return self._block(blocked)
        self._to(RunState.DESIGN_APPROVED)
        return True

    # ------------------------------------------------------------ G3 (A5)
    def _on_design_approved(self) -> bool:
        path = self.run_dir / ARTIFACTS["tasks"]
        spec = self._read(ARTIFACTS["spec"], Spec)
        if not path.exists():
            files = git_ops.git(self._repo(), "ls-files").splitlines()
            dag = self.roles.plan(spec, self._read(ARTIFACTS["design"], Design), files)
            try:
                layers = validate_dag(dag, [r.id for r in spec.requirements], self.st["protected"])
            except DAGError as exc:
                _write_json(self.run_dir / "04_tasks/rejected_tasks.json", dag)
                self._to(RunState.FAILED, f"G3:{exc}")
                return True
            _write_json(path, dag)
            _write_json(self.run_dir / "04_tasks/plan_digest.json",
                        {"tasks_sha256": sha256_file(path), "spec_sha256": sha256_file(self.run_dir / ARTIFACTS["spec"]),
                         "parallel_layers": layers, "order": topological_order(dag)})
        blocked = self._approval_ok("tasks")
        if blocked:
            return self._block(blocked)
        self._to(RunState.TASKS_APPROVED)
        return True

    def _on_tasks_approved(self) -> bool:
        for art in ("spec", "tasks"):
            blocked = self._approval_ok(art)
            if blocked:
                return self._block(blocked)
        self._to(RunState.IMPLEMENTING)
        return True

    # ------------------------------------------------------------ G4 (A6)
    def _on_implementing(self) -> bool:
        for art in ("spec", "tasks"):
            blocked = self._approval_ok(art)
            if blocked:
                return self._block(blocked)
        m = self.manifest
        head = git_ops.head_sha(self._repo(), m.repo.main_branch)
        if head != m.repo.base_commit_sha:
            self._to(RunState.FAILED, f"G4:STALE_BASE:{head[:12]}!={m.repo.base_commit_sha[:12]}")
            return True
        self.st["attempt"] += 1
        n = self.st["attempt"]
        run_id = self.st["run_id"]
        spec = self._read(ARTIFACTS["spec"], Spec)
        dag = self._read(ARTIFACTS["tasks"], TaskDAG)
        by_id = {t.id: t for t in dag.tasks}
        wt_root = self.run_dir / "worktrees" / f"a{n}"
        integ_branch = f"agent/{run_id}/integration-a{n}"
        integ = git_ops.add_worktree(self._repo(), wt_root / "integration", integ_branch, m.repo.base_commit_sha)
        self.st.update(integration_branch=integ_branch, integration_worktree=str(integ))
        feedback = self.st.get("feedback", "")
        results: Dict[str, TaskResult] = {}
        violations_all: List[str] = []
        for tid in topological_order(dag):
            task = by_id[tid]
            branch = f"agent/{run_id}/{tid}" + (f"-a{n}" if n > 1 else "")
            wt = git_ops.add_worktree(self._repo(), wt_root / tid, branch, integ_branch)
            current = {p: ((wt / p).read_text(encoding="utf-8") if (wt / p).is_file() else None)
                       for p in task.owned_paths}
            out = self.roles.implement(task, spec, current, feedback)
            violations: List[str] = []
            for cmd in out.commands:
                kind = classify_command(cmd)
                self.events.append({"task": tid, "event": "command_proposed", "command": cmd[:200],
                                    "classification": kind, "executed": False})
                if kind == "DESTRUCTIVE":
                    results[tid] = TaskResult(task_id=tid, branch=branch, status="REJECTED",
                                              violations=[f"DESTRUCTIVE_COMMAND:{cmd[:80]}"])
                    self._write_impl(results, integ)
                    self._to(RunState.REJECTED, f"G4:DESTRUCTIVE_COMMAND_BLOCKED:{tid}")
                    return True
            for fc in out.files:
                try:
                    norm = check_write_path(fc.path, task.owned_paths, self.st["protected"])
                except DAGError as exc:
                    violations.append(str(exc))
                    continue
                if scan_secrets(fc.content):
                    violations.append(f"SECRET_IN_CONTENT:{norm}")
                    continue
                if norm.endswith(".py"):
                    try:
                        compile(fc.content, norm, "exec")
                    except SyntaxError as exc:
                        violations.append(f"SYNTAX_ERROR:{norm}:{exc.lineno}")
                        continue
                target = wt / norm
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(fc.content, encoding="utf-8", newline="\n")
            changed = git_ops.changed_files(wt)
            outside = [c for c in changed if not any(c == p or c.startswith(p.rstrip("/") + "/") for p in task.owned_paths)]
            violations += [f"DIFF_OUTSIDE_OWNED:{c}" for c in outside]
            if violations:
                results[tid] = TaskResult(task_id=tid, branch=branch, status="REJECTED", violations=violations,
                                          claimed_tests_passed=out.claimed_tests_passed)
                violations_all += violations
                break
            sha = git_ops.commit_all(wt, f"{tid}: {task.title} [{', '.join(task.req_ids)}]")
            if sha:
                git_ops.merge_into(integ, branch, f"merge {tid} into {integ_branch}")
            results[tid] = TaskResult(task_id=tid, branch=branch, commit_sha=sha, files_changed=changed,
                                      status="COMMITTED", claimed_tests_passed=out.claimed_tests_passed)
        self._write_impl(results, integ)
        if violations_all:
            return self._rework_or(RunState.REJECTED, "G4:POLICY_VIOLATION", "\n".join(violations_all))
        self.st["integration_commit"] = git_ops.head_sha(integ)
        self._to(RunState.VERIFYING)
        return True

    def _write_impl(self, results: Dict[str, TaskResult], integ: Path) -> None:
        _write_json(self.run_dir / "05_implementation/task_results.json",
                    {k: v.model_dump(mode="json") for k, v in results.items()})
        commits = [{"task_id": r.task_id, "branch": r.branch, "commit": r.commit_sha} for r in results.values()]
        _write_json(self.run_dir / "05_implementation/commits.json", commits)
        patch = git_ops.diff(self._repo(), self.manifest.repo.base_commit_sha, git_ops.head_sha(integ))
        (self.run_dir / "05_implementation/patch.diff").write_text(patch + "\n", encoding="utf-8")

    def _rework_or(self, terminal: RunState, reason: str, feedback: str) -> bool:
        if self.st["attempt"] < 1 + self.budget.max_rework_attempts:
            self.st["feedback"] = f"{reason}\n{feedback}"[:4000]
            self.st["history"].append({"from": self.state.value, "to": "REWORK", "at": utc_now(), "reason": reason})
            if self.state != RunState.IMPLEMENTING:
                self._to(RunState.IMPLEMENTING, reason)
            else:
                self._save()
            return True
        self._to(terminal, f"{reason}:attempts={self.st['attempt']}")
        return True

    # ------------------------------------------------------------ G5 (A7 runner)
    def _on_verifying(self) -> bool:
        integ = Path(self.st["integration_worktree"])
        golden_dst = integ / "golden_tests"
        shutil.copytree(self.run_dir / "input" / "golden_tests", golden_dst, dirs_exist_ok=True)
        try:
            tests = run_pytest(integ, ["tests", "golden_tests"], self.run_dir / "06_verification/junit.xml",
                               timeout_s=self.test_timeout_s)
        finally:
            shutil.rmtree(golden_dst, ignore_errors=True)
        spec = self._read(ARTIFACTS["spec"], Spec)
        required = {ac.test_id for r in spec.requirements for ac in r.acceptance}
        seen = {c.test_id: c.outcome for c in tests.cases}
        missing = sorted(t for t in required if t not in seen)
        failing = sorted(c.test_id for c in tests.cases if c.outcome != TestOutcome.PASS)
        ok = tests.passed and not missing
        results = json.loads((self.run_dir / "05_implementation/task_results.json").read_text(encoding="utf-8"))
        false_claims = [tid for tid, r in results.items() if r.get("claimed_tests_passed") is True and not ok]
        _write_json(self.run_dir / "06_verification/test_results.json", tests)
        _write_json(self.run_dir / "06_verification/verification_report.json", {
            "verdict": "PASS" if ok else "FAIL", "required_tests": sorted(required), "missing_required": missing,
            "failing": failing, "timed_out": tests.timed_out, "false_test_claims": false_claims,
            "note": "Veredito vem só do runner externo; claimed_tests_passed do implementer é ignorado."})
        self.st["verification"] = "PASS" if ok else "FAIL"
        if not ok:
            detail = "\n".join([f"FAIL {t}" for t in failing] + [f"MISSING {t}" for t in missing])
            if tests.timed_out:
                detail += "\nTIMEOUT"
            return self._rework_or(RunState.FAILED, "G5:VERIFICATION_FAILED", detail + "\n" + tests.stdout_tail[-1500:])
        self._to(RunState.REVIEWING)
        return True

    # ------------------------------------------------------------ G6 (A8)
    def _on_reviewing(self) -> bool:
        spec = self._read(ARTIFACTS["spec"], Spec)
        dag = self._read(ARTIFACTS["tasks"], TaskDAG)
        results = {k: TaskResult(**v) for k, v in json.loads(
            (self.run_dir / "05_implementation/task_results.json").read_text(encoding="utf-8")).items()}
        tests = self._read("06_verification/test_results.json", TestRunResult)
        rows = build_traceability(spec, dag, results, tests)
        write_traceability_csv(rows, self.run_dir / "07_review/traceability.csv")
        cov = coverage(rows)
        diff = (self.run_dir / "05_implementation/patch.diff").read_text(encoding="utf-8")
        review = self.roles.review(spec, diff, tests, rows)  # sem notas/claims do implementer
        _write_json(self.run_dir / "07_review/review.json", review)
        uncovered = [r.req_id for r in rows if r.level == "MUST" and not r.covered]
        blockers = [f.message for f in review.findings if f.severity == "blocker"]
        self.st["coverage"] = cov
        if uncovered or blockers or review.verdict != "APPROVE":
            fb = f"MUST sem evidência: {uncovered}\nBlockers: {blockers}"
            return self._rework_or(RunState.REJECTED, "G6:REVIEW_REJECTED", fb)
        body = pr_body(self.st["run_id"], spec, rows, tests, self.st["integration_branch"])
        (self.run_dir / ARTIFACTS["pr"]).parent.mkdir(parents=True, exist_ok=True)
        (self.run_dir / ARTIFACTS["pr"]).write_text(body, encoding="utf-8")
        MockPullRequestClient(self.run_dir / "08_delivery/pr_mock.json").create(
            title=f"[SDD {self.st['run_id']}] {spec.scope}", head=self.st["integration_branch"],
            base=self.manifest.repo.main_branch, body=body)
        notes = ["# Release notes (rascunho)", ""] + [f"- {r.id}: {r.text}" for r in spec.requirements]
        (self.run_dir / "08_delivery/release_notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
        self._to(RunState.PR_READY)
        return True

    # ------------------------------------------------------------ G7
    def _on_pr_ready(self) -> bool:
        path = self.run_dir / ARTIFACTS["pr"]
        if self.approvals.status("pr", sha256_file(path)) != "VALID":
            return self._block("AWAITING_HUMAN_PR_REVIEW (merge é manual, fora da fábrica)")
        self._to(RunState.COMPLETE, "PR aprovado por humano")
        return True

    # ------------------------------------------------------------ relatório
    def _write_events(self) -> None:
        p = self.run_dir / "05_implementation/tool_events.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            for e in self.events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        self.events.clear()

    def _report(self) -> RunReport:
        artifacts = {}
        for p in sorted(self.run_dir.glob("0*/*")):
            if p.is_file():
                artifacts[p.relative_to(self.run_dir).as_posix()] = sha256_bytes(p.read_bytes())
        cov = self.st.get("coverage") or {}
        report = RunReport(
            run_id=self.st["run_id"], state=self.state.value, blocked_reason=self.st["blocked_reason"],
            provider=getattr(self.provider, "name", "?"), model=getattr(self.provider, "model", "?"),
            base_commit_sha=self.manifest.repo.base_commit_sha, integration_commit_sha=self.st.get("integration_commit"),
            verification=self.st.get("verification") or "NOT_RUN",
            requirement_coverage=cov.get("requirement_coverage"), trace_coverage=cov.get("trace_coverage"),
            usage=list(self.budget.usage.values()), estimated_cost_usd=self.budget.estimated_cost(),
            approvals=self.approvals.all(), artifacts=artifacts)
        _write_json(self.run_dir / "08_delivery/run_report.json", report)
        return report
