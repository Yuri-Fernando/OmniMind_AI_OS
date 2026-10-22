"""Cenário de demonstração `engineering-intake` com MockLLM roteirizado.

As respostas do MockLLM são fixtures escritas à mão (não geradas por IA): o que
a demo prova é a mecânica da fábrica — gates, aprovação vinculada a hash, DAG,
worktrees isolados, runner externo, revisão e rastreabilidade — com o código
de verdade executado e testado pelo pytest dentro do worktree.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Callable, Dict, Optional

from . import git_ops
from .llm.mock_provider import MockLLM

SAMPLE = Path(__file__).parent / "samples" / "engineering-intake"
GOLDEN = "golden_tests/test_acceptance.py"


def _ac(rid: str, n: int, given: str, when: str, then: str, test: str) -> dict:
    return {"id": f"AC-{rid[2:]}-{n}", "given": given, "when": when, "then": then, "test_id": f"{GOLDEN}::{test}"}


ASSESSMENT = {"schema_version": "sdd-assessment/1.0", "ambiguities": [
    {"id": "A-001", "evidence_source_id": "brief/PRD.md", "category": "missing", "blocking": True,
     "question": "Qual é a 'janela configurada' de idempotência e o que acontece com a chave depois dela?",
     "impact": "Sem a janela, R-003 não é testável e o comportamento de reuso da chave fica indefinido."},
    {"id": "A-002", "evidence_source_id": "brief/PRD.md", "category": "missing", "blocking": False,
     "question": "Há autenticação nos endpoints?",
     "impact": "Não bloqueia o incremento local; afeta exposição em rede."},
]}

DECISIONS = [
    {"ambiguity_id": "A-001", "decided_by": "demo-human",
     "answer": "Janela configurável por create_app(idempotency_window_s), padrão 86400 s; fora da janela a "
               "chave é liberada e o job antigo continua consultável."},
    {"ambiguity_id": "A-002", "decided_by": "demo-human",
     "answer": "Sem autenticação neste incremento (execução local de demonstração)."},
]

SPEC = {"schema_version": "sdd-spec/1.0", "scope": "Engineering Intake API — submissão e consulta de jobs",
        "unresolved": [], "requirements": [
    {"id": "R-001", "level": "MUST", "trace_source": "brief/PRD.md",
     "text": "POST /v1/documents responde 202 com job_id e grava o conteúdo em storage/{job_id}/{filename}.",
     "acceptance": [_ac("R-001", 1, "payload válido", "POST /v1/documents", "202 com job_id e status QUEUED",
                        "test_post_returns_202_with_job_id"),
                    _ac("R-001", 2, "payload válido", "o job é criado", "o arquivo fica só em storage/{job_id}",
                        "test_file_stored_under_isolated_job_dir")]},
    {"id": "R-002", "level": "MUST", "trace_source": "brief/PRD.md",
     "text": "GET /v1/jobs/{id} retorna status QUEUED|RUNNING|COMPLETED|FAILED; job inexistente 404 JOB_NOT_FOUND.",
     "acceptance": [_ac("R-002", 1, "job criado", "GET /v1/jobs/{id}", "200 com status válido",
                        "test_get_job_returns_valid_status"),
                    _ac("R-002", 2, "id inexistente", "GET /v1/jobs/{id}", "404 JOB_NOT_FOUND",
                        "test_get_unknown_job_is_404")]},
    {"id": "R-003", "level": "MUST", "trace_source": "decision:A-001",
     "text": "Mesma idempotency_key + mesmo SHA-256 na janela devolve o job original; conteúdo diferente 409.",
     "acceptance": [_ac("R-003", 1, "job criado com chave k", "reenviar mesma chave e conteúdo", "mesmo job_id",
                        "test_same_key_same_content_returns_original_job"),
                    _ac("R-003", 2, "job criado com chave k", "reenviar k com outro conteúdo",
                        "409 IDEMPOTENCY_KEY_MISMATCH", "test_same_key_different_content_is_409")]},
    {"id": "R-004", "level": "MUST", "trace_source": "brief/PRD.md",
     "text": "Payload inválido ou extensão não suportada responde 422 sem criar job nem arquivo.",
     "acceptance": [_ac("R-004", 1, "payload inválido", "POST", "422 e nenhum efeito colateral",
                        "test_invalid_payload_is_422_without_side_effects")]},
    {"id": "R-005", "level": "MUST", "trace_source": "brief/SECURITY.md",
     "text": "Nomes com /, \\, .., ':' ou absolutos são recusados com 422 UNSAFE_PATH; nada é escrito fora do storage.",
     "acceptance": [_ac("R-005", 1, "filename malicioso", "POST", "422 UNSAFE_PATH e nenhum arquivo",
                        "test_path_traversal_is_rejected")]},
    {"id": "R-006", "level": "MUST", "trace_source": "brief/PRD.md",
     "text": "Todo job registra eventos (JOB_CREATED, conflitos com error_code) em SQLite.",
     "acceptance": [_ac("R-006", 1, "conflito de idempotência", "GET do job", "evento com error_code",
                        "test_events_recorded_with_error_code")]},
    {"id": "R-007", "level": "MUST", "trace_source": "brief/USER_STORIES.md",
     "text": "Requisições concorrentes com a mesma chave criam um único job.",
     "acceptance": [_ac("R-007", 1, "8 requisições simultâneas com a mesma chave", "POST em paralelo",
                        "um único job_id e um único arquivo", "test_concurrent_same_key_creates_single_job")]},
]}

DESIGN = {"schema_version": "sdd-design/1.0",
          "architecture": "FastAPI (app/main.py) -> JobRepository SQLite (app/repository.py); DTOs Pydantic em "
                          "app/schemas.py; armazenamento em data_dir/storage/{job_id}/{filename}.",
          "decisions": ["Idempotência resolvida dentro de um lock + UNIQUE(idempotency_key)",
                        "Validação de nome antes de qualquer escrita; caminho resolvido conferido contra a raiz",
                        "Evento de conflito persistido mesmo quando a requisição falha (409)"],
          "interfaces": {"create_app": "create_app(data_dir: Path, idempotency_window_s: int = 86400) -> FastAPI",
                         "JobRepository.create_or_get": "(key, sha256, filename) -> (job_id, replay)"}}

TASKS = {"schema_version": "task-dag/1.0.0", "project": "engineering-intake-api", "tasks": [
    {"id": "T1", "title": "DTOs", "requires": [], "req_ids": ["R-001", "R-004"],
     "owned_paths": ["app/schemas.py"], "acceptance": ["schema validado", "422 em payload inválido"]},
    {"id": "T2", "title": "Persistência", "requires": [], "req_ids": ["R-002", "R-003", "R-006", "R-007"],
     "owned_paths": ["app/repository.py"], "acceptance": ["SQLite", "mismatch -> 409", "eventos"]},
    {"id": "T3", "title": "Endpoints", "requires": ["T1", "T2"], "req_ids": ["R-001", "R-002", "R-005"],
     "owned_paths": ["app/main.py"], "acceptance": ["POST 202", "GET status", "traversal negado"]},
    {"id": "T4", "title": "Testes de integração", "requires": ["T3"], "req_ids": ["R-004", "R-005"],
     "owned_paths": ["tests/test_api.py"], "acceptance": ["pytest verde"]},
]}

REVIEW_OK = {"schema_version": "sdd-review/1.0", "verdict": "APPROVE", "findings": [
    {"severity": "info", "message": "Sem autenticação por decisão A-002; revisar antes de expor em rede."}]}


def impl_files(variant: str = "impl") -> Dict[str, str]:
    root = SAMPLE / "mock" / variant
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in root.rglob("*.py")}


def implementer_from(files: Dict[str, str], mutate: Optional[Callable[[str, str, str], str]] = None,
                     claimed: Optional[bool] = True):
    """Callable de MockLLM: lê TASK_ID do prompt e devolve os owned_paths daquela tarefa."""
    owned = {t["id"]: t["owned_paths"] for t in TASKS["tasks"]}

    def respond(prompt: str) -> dict:
        tid = re.search(r"TASK_ID: (T\d+)", prompt).group(1)
        out = []
        for p in owned[tid]:
            content = files[p]
            if mutate:
                content = mutate(tid, p, content)
            out.append({"path": p, "content": content})
        return {"task_id": tid, "files": out, "commands": [], "claimed_tests_passed": claimed,
                "notes": "resposta roteirizada (MockLLM)"}
    return respond


def mock_provider(implementer=None, review=None, spec=None, assessment=None, tasks=None) -> MockLLM:
    impl = implementer or implementer_from(impl_files())
    return MockLLM({
        "assessor": [assessment or ASSESSMENT],
        "specifier": [spec or SPEC],
        "architect": [DESIGN],
        "planner": [tasks or TASKS],
        "implementer": [impl] * 16,
        "reviewer": [review or REVIEW_OK] * 4,
    })


def prepare_seed_repo(dest: Path) -> str:
    """Copia o repositório-semente para fora do Drive e inicializa o git. Devolve o SHA base."""
    if dest.exists():
        raise FileExistsError(dest)
    shutil.copytree(SAMPLE / "seed_repo", dest, ignore=shutil.ignore_patterns("__pycache__"))
    return git_ops.init_repo(dest)
