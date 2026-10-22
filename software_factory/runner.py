"""Runner externo de testes: o único juiz de PASS/FAIL.

Roda pytest num subprocesso com timeout, ambiente sem segredos e proxy
apontado para endereço morto (rede bloqueada em melhor esforço — não é
sandbox de SO; ver ADR 0002). O resultado vem do JUnit XML gerado pelo
próprio pytest, não do relato de nenhum agente.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import TestCaseResult, TestOutcome, TestRunResult

_SECRET_ENV = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|COOKIE|SESSION)", re.IGNORECASE)
_KEEP_ENV = {"PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
             "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "HOME", "LANG", "LC_ALL", "NUMBER_OF_PROCESSORS",
             "PROCESSOR_ARCHITECTURE", "APPDATA", "LOCALAPPDATA"}


def sandbox_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() in _KEEP_ENV and not _SECRET_ENV.search(k)}
    dead = "http://127.0.0.1:9"
    env.update({"HTTP_PROXY": dead, "HTTPS_PROXY": dead, "http_proxy": dead, "https_proxy": dead,
                "NO_PROXY": "", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
                "PIP_NO_INDEX": "1",
                # plugins de terceiros instalados no Python global (ex.: deepeval) não entram no
                # processo de verificação: isolamento e sem telemetria batendo no proxy morto
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    env.update(extra or {})
    return env


def _parse_junit(xml_path: Path) -> List[TestCaseResult]:
    if not xml_path.exists():
        return []
    cases: List[TestCaseResult] = []
    for tc in ET.parse(xml_path).getroot().iter("testcase"):
        file_attr = tc.get("file")
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        if file_attr:
            module = file_attr.replace("\\", "/")
        else:
            module = classname.replace(".", "/") + ".py"
        test_id = f"{module}::{name}"
        if tc.find("failure") is not None or tc.find("error") is not None:
            node = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
            cases.append(TestCaseResult(test_id=test_id, outcome=TestOutcome.FAIL,
                                        message=(node.get("message") or "")[:300]))
        elif tc.find("skipped") is not None:
            cases.append(TestCaseResult(test_id=test_id, outcome=TestOutcome.NOT_RUN, message="skipped"))
        else:
            cases.append(TestCaseResult(test_id=test_id, outcome=TestOutcome.PASS))
    return cases


def run_pytest(worktree: Path, test_paths: List[str], junit_path: Path,
               timeout_s: float = 120.0) -> TestRunResult:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
           f"--junitxml={junit_path}", "-o", "junit_family=xunit1", *test_paths]
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    if junit_path.exists():
        junit_path.unlink()
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=str(worktree), env=sandbox_env(), capture_output=True,
                              text=True, timeout=timeout_s, check=False)
        rc, out, err, timed_out = proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        rc, timed_out = None, True
        out = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    return TestRunResult(command=[Path(cmd[0]).name, *cmd[1:]], returncode=rc, timed_out=timed_out,
                         duration_s=round(time.monotonic() - start, 3),
                         cases=_parse_junit(junit_path),
                         stdout_tail=out[-3000:], stderr_tail=err[-2000:])
