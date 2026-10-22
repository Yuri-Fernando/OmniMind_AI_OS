"""CLI da Software Factory.

  python -m software_factory demo --workspace "D:/Claude Temp/staging/sdd-runs"
  python -m software_factory status  --run-dir <runs/run-x>
  python -m software_factory approve --run-dir <...> --artifact spec --approver "Nome"
  python -m software_factory resolve --run-dir <...> --decisions decisions.json
  python -m software_factory resume  --run-dir <...> [--provider claude]

`demo` com --auto-approve simula as aprovações humanas (rotuladas como
"demo-approver" no approvals.json); sem a flag, o run para em cada gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import demo
from .orchestrator import Orchestrator


def _provider(name: str):
    if name == "claude":
        from .llm.claude_provider import ClaudeProvider
        return ClaudeProvider()
    return demo.mock_provider()


def cmd_demo(args) -> dict:
    ws = Path(args.workspace).resolve()
    if "google drive" in str(ws).lower() or str(ws)[:2].upper() == "G:":
        raise SystemExit("workspace precisa ficar fora do Google Drive (G:) — use D:/Claude Temp/staging/...")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    repo = ws / f"seed-{stamp}"
    base = demo.prepare_seed_repo(repo)
    orch = Orchestrator.create(ws / "runs", "engineering-intake-api", demo.SAMPLE / "brief",
                               demo.SAMPLE / "golden_tests", repo, base, _provider(args.provider),
                               run_id=f"run-{stamp}")
    status = orch.advance()
    if args.auto_approve:
        orch.resolve(demo.DECISIONS)
        for _ in range(6):
            reason = status["blocked_reason"] or ""
            if reason.startswith("AWAITING_APPROVAL:"):
                orch.approve(reason.split(":", 1)[1], "demo-approver", "aprovação simulada da demo")
            elif not reason.startswith("HUMAN_REQUIRED"):
                break
            status = orch.advance()
    return status


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows (cp1252) quebra acentos
    ap =argparse.ArgumentParser(prog="software_factory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo")
    d.add_argument("--workspace", default="D:/Claude Temp/staging/sdd-runs")
    d.add_argument("--provider", choices=["mock", "claude"], default="mock")
    d.add_argument("--auto-approve", action="store_true")
    for name in ("status", "approve", "resolve", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--run-dir", required=True)
        p.add_argument("--provider", choices=["mock", "claude"], default="mock")
        if name == "approve":
            p.add_argument("--artifact", required=True, choices=["spec", "design", "tasks", "pr"])
            p.add_argument("--approver", required=True)
            p.add_argument("--reason", default="")
        if name == "resolve":
            p.add_argument("--decisions", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "demo":
        out = cmd_demo(args)
    else:
        orch = Orchestrator(Path(args.run_dir), _provider(args.provider))
        if args.cmd == "approve":
            out = orch.approve(args.artifact, args.approver, args.reason)
        elif args.cmd == "resolve":
            out = orch.resolve(json.loads(Path(args.decisions).read_text(encoding="utf-8"))).model_dump()
        elif args.cmd == "resume":
            out = orch.advance()
        else:
            out = {"state": orch.state.value, "blocked_reason": orch.st["blocked_reason"],
                   "history": orch.st["history"]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
