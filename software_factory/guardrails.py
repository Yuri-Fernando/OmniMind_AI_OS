"""Guardrails determinísticos, aplicados fora do modelo.

Reaproveita o detector de prompt injection do OmniMind
(safety/prompt_injection_guard.py) e acrescenta regras específicas de uma
fábrica de software: instruções operacionais embutidas em documentos,
comandos destrutivos, segredos em diff e escrita fora da allowlist.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Iterable, List

from safety.prompt_injection_guard import check_injection

from .dag import DAGError, normalize_owned_path

# Instruções dirigidas ao agente dentro de conteúdo não confiável (PRD, issue, README de terceiro)
_UNTRUSTED_INSTRUCTION = [re.compile(p, re.IGNORECASE) for p in (
    r"\b(ignore|disregard|override)\b.{0,40}\b(spec|specification|requirements?|guardrails?|polic(y|ies)|instru[cç][oõ]es)\b",
    r"\b(ignore|ignorar|desconsidere)\b.{0,30}\b(instru[cç][oõ]es|regras)\b",
    r"\bmark\b.{0,30}\btests?\b.{0,20}\b(as\s+)?pass(ed|ing)?\b",
    r"\bauto[- ]?(approve|merge)\b",
    r"\b(approve|aprove)\b.{0,20}\b(spec|plan|pr|pull request)\b.{0,20}\b(automatically|automaticamente)\b",
    r"\b(exfiltrate|send|envie)\b.{0,40}\b(api[_ ]?key|token|secret|credenciais?|\.env)\b",
    r"\b(curl|wget|invoke-webrequest)\b\s+https?://",
    r"\brm\s+-rf\b",
    r"\bgit\s+push\b",
)]

_DESTRUCTIVE = [re.compile(p, re.IGNORECASE) for p in (
    r"\brm\s+-[a-z]*r[a-z]*f?\b", r"\brmdir\s+/s\b", r"\bdel\s+/[sfq]\b", r"\bformat\s+[a-z]:",
    r"\bremove-item\b.*-recurse", r"\bgit\s+(push|reset\s+--hard|clean\s+-[a-z]*f|branch\s+-D|checkout\s+--)\b",
    r"\bmkfs\b", r"\bdd\s+if=", r"\bshutdown\b", r"\bchmod\s+-R\s+777\b", r":\(\)\s*\{\s*:\|:&\s*\};:",
)]

_ALLOWED_COMMANDS = (re.compile(r"^(python\s+-m\s+)?pytest(\s+[\w./:\-=\[\]]+)*$"),)

_SECRETS = [re.compile(p) for p in (
    r"sk-ant-[A-Za-z0-9_\-]{10,}", r"sk-[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{20,}", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
)]


def scan_untrusted_text(text: str) -> List[str]:
    """Achados de injection/instrução operacional em conteúdo NÃO confiável."""
    findings: List[str] = []
    safe, reason = check_injection(text)  # detector existente do OmniMind
    if not safe:
        findings.append(f"omnimind_guard:{reason}")
    for pat in _UNTRUSTED_INSTRUCTION:
        m = pat.search(text)
        if m:
            findings.append(f"embedded_instruction:{m.group(0)[:80]}")
    return findings


def classify_command(cmd: str) -> str:
    """ALLOWED | DESTRUCTIVE | NOT_ALLOWLISTED. O executor nunca roda comando vindo do LLM;
    esta classificação serve para registrar e bloquear a tentativa."""
    c = cmd.strip()
    if any(p.search(c) for p in _DESTRUCTIVE):
        return "DESTRUCTIVE"
    if any(p.match(c) for p in _ALLOWED_COMMANDS):
        return "ALLOWED"
    return "NOT_ALLOWLISTED"


def scan_secrets(text: str) -> List[str]:
    return [p.pattern for p in _SECRETS if p.search(text)]


def check_write_path(raw: str, owned_paths: Iterable[str], protected: Iterable[str]) -> str:
    """Normaliza e confere se o caminho está dentro de owned_paths e fora de protected.
    Devolve o caminho normalizado ou levanta DAGError com código estável."""
    norm = normalize_owned_path(raw)
    owned = [normalize_owned_path(p) for p in owned_paths]
    if any(norm == p or norm.startswith(p + "/") for p in (normalize_owned_path(x) for x in protected)):
        raise DAGError(f"WRITE_PROTECTED_PATH:{norm}")
    if not any(norm == p or norm.startswith(p + "/") for p in owned):
        raise DAGError(f"WRITE_OUTSIDE_OWNED_PATHS:{norm}")
    if PurePosixPath(norm).name.lower() in {".env", ".git", ".gitmodules"}:
        raise DAGError(f"WRITE_FORBIDDEN_FILE:{norm}")
    return norm
