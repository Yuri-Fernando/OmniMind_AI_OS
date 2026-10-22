"""Rastreabilidade, corpo de PR e cliente de PR simulado (sem merge)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from .schemas import Spec, TaskDAG, TaskResult, TestOutcome, TestRunResult, TraceRow, utc_now


def build_traceability(spec: Spec, dag: TaskDAG, results: Dict[str, TaskResult],
                       tests: TestRunResult) -> List[TraceRow]:
    outcome = {c.test_id: c.outcome.value for c in tests.cases}
    rows = []
    for r in spec.requirements:
        task_ids = [t.id for t in dag.tasks if r.id in t.req_ids]
        commits = [results[t].commit_sha for t in task_ids if t in results and results[t].commit_sha]
        test_ids = [a.test_id for a in r.acceptance]
        outs = [outcome.get(t, TestOutcome.NOT_RUN.value) for t in test_ids]
        rows.append(TraceRow(req_id=r.id, level=r.level, trace_source=r.trace_source, task_ids=task_ids,
                             commits=commits, test_ids=test_ids, outcomes=outs,
                             covered=bool(task_ids) and bool(commits) and all(o == "PASS" for o in outs)))
    return rows


def write_traceability_csv(rows: List[TraceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["req_id", "level", "trace_source", "task_ids", "commits", "test_ids", "outcomes", "covered"])
        for r in rows:
            w.writerow([r.req_id, r.level, r.trace_source, ";".join(r.task_ids), ";".join(c[:12] for c in r.commits),
                        ";".join(r.test_ids), ";".join(r.outcomes), r.covered])


def coverage(rows: List[TraceRow]) -> Dict[str, float]:
    must = [r for r in rows if r.level == "MUST"]
    req_cov = sum(1 for r in must if all(o == "PASS" for o in r.outcomes)) / len(must) if must else 0.0
    trace_cov = sum(1 for r in rows if r.trace_source and r.task_ids and r.commits) / len(rows) if rows else 0.0
    return {"requirement_coverage": round(req_cov, 4), "trace_coverage": round(trace_cov, 4)}


def pr_body(run_id: str, spec: Spec, rows: List[TraceRow], tests: TestRunResult, branch: str) -> str:
    lines = [f"# [SDD {run_id}] {spec.scope}", "", f"Branch: `{branch}` — **merge somente humano, após CI.**", "",
             "## Requisitos e evidências", "", "| R-ID | Nível | Tarefas | Testes | Resultado |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.req_id} | {r.level} | {', '.join(r.task_ids)} | {len(r.test_ids)} | "
                     f"{'PASS' if r.covered else ', '.join(sorted(set(r.outcomes)))} |")
    passed = sum(1 for c in tests.cases if c.outcome == TestOutcome.PASS)
    lines += ["", "## Verificação (runner externo)", "",
              f"- `{' '.join(tests.command)}` → returncode {tests.returncode}, {passed}/{len(tests.cases)} PASS, "
              f"{tests.duration_s}s", "", "## Checklist do revisor humano", "",
              "- [ ] Diff lido por completo", "- [ ] CI externo verde", "- [ ] Rastreabilidade conferida"]
    return "\n".join(lines) + "\n"


class MockPullRequestClient:
    """Registra o PR em arquivo. Não existe caminho de merge nem deploy."""

    def __init__(self, out_path: Path):
        self.out_path = Path(out_path)

    def create(self, title: str, head: str, base: str, body: str) -> dict:
        pr = {"number": 1, "title": title, "head": head, "base": base, "state": "open",
              "mergeable_by_agent": False, "created_at": utc_now(), "body_chars": len(body)}
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text(json.dumps(pr, ensure_ascii=False, indent=2), encoding="utf-8")
        return pr

    def merge(self, *_a, **_k):
        raise PermissionError("MERGE_FORBIDDEN: merge é exclusivamente humano")
