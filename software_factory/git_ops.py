"""Operações git usadas pela fábrica — sempre lista de argumentos, nunca shell.

Cada tarefa roda num `git worktree` próprio, numa branch
`agent/{run_id}/{task_id}` criada a partir da branch de integração do run.
Nada aqui faz push, merge na branch principal, reset ou clean.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

_IDENTITY = ["-c", "user.name=sdd-factory", "-c", "user.email=sdd-factory@localhost",
             "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false"]


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str, timeout: float = 60.0) -> str:
    proc = subprocess.run(["git", *_IDENTITY, *args], cwd=str(repo), capture_output=True,
                          text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} -> {proc.returncode}: {proc.stderr.strip()[:500]}")
    return proc.stdout.rstrip()  # rstrip: --porcelain começa com espaço significativo


def head_sha(repo: Path, ref: str = "HEAD") -> str:
    return git(repo, "rev-parse", ref)


def init_repo(path: Path, branch: str = "main") -> str:
    """Inicializa um repositório com o conteúdo atual da pasta e devolve o SHA do commit."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "seed: estado inicial do repositório-alvo")
    return head_sha(path)


def create_branch(repo: Path, name: str, start: str) -> None:
    git(repo, "branch", name, start)


def add_worktree(repo: Path, worktree: Path, branch: str, start: str) -> Path:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-q", "-b", branch, str(worktree), start)
    return worktree


def add_worktree_existing(repo: Path, worktree: Path, branch: str) -> Path:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-q", str(worktree), branch)
    return worktree


def changed_files(worktree: Path) -> List[str]:
    """Arquivos alterados/novos no worktree (relativos, com '/')."""
    out = git(worktree, "status", "--porcelain", "--untracked-files=all")
    files = []
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path.replace("\\", "/"))
    return sorted(files)


def commit_all(worktree: Path, message: str) -> Optional[str]:
    git(worktree, "add", "-A")
    if not git(worktree, "status", "--porcelain"):
        return None
    git(worktree, "commit", "-q", "-m", message)
    return head_sha(worktree)


def merge_into(worktree: Path, branch: str, message: str) -> str:
    """Integra a branch de uma tarefa na branch de integração (sem fast-forward)."""
    git(worktree, "merge", "--no-ff", "-q", "-m", message, branch)
    return head_sha(worktree)


def diff(repo: Path, base: str, head: str) -> str:
    return git(repo, "diff", f"{base}..{head}")
