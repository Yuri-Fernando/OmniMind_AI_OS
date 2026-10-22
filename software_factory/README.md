# Software Factory SDD (`software_factory/`)

Módulo do OmniMind que transforma um **brief versionado** (PRD, user stories, constraints, guardrails)
num **PR pronto para revisão humana**, passando por especificação rastreável, plano em DAG,
implementação em `git worktree` isolado, testes executados por runner externo e revisão independente.
Os gates são código determinístico; o LLM só propõe artefatos que são validados por schema.

> SDD ≠ multiagente. O artefato central é a especificação; os agentes são um meio de executá-la.
> Um chat que escreve código não é SDD, e um plano que nunca roda testes não é validação.

## Fluxo e gates

```text
brief/ + golden_tests/ + repo@SHA
   │  G0 input: hashes, arquivos não vazios, SHA-base == main
   ▼
ASSESSOR ─► ambiguidades (+ scanner de injection)  ── bloqueante sem decisão ─► RESOLUTION_PENDING (humano)
   │  G1
   ▼
SPECIFIER ─► spec R-### + Given/When/Then          ── G2: origem rastreável, MUST→golden test, aprovação humana (hash)
   ▼
ARCHITECT ─► design + ADRs
   ▼
PLANNER ─► DAG de tarefas                            ── G3: ids, R-IDs, ciclo, owned_paths, colisão, aprovação humana (hash)
   ▼
IMPLEMENTER (por tarefa, worktree agent/{run}/{T}) ── G4: só owned_paths, sem segredo, compila, comando destrutivo = REJECTED
   ▼
RUNNER EXTERNO (pytest + JUnit, sem segredos)      ── G5: todos os testes da spec PASS (relato do agente ignorado)
   ▼
REVIEWER independente + rastreabilidade            ── G6: todo MUST coberto, sem blocker
   ▼
PR_READY (PR simulado, sem merge)                   ── G7: COMPLETE só com aprovação humana do PR
```

Retrabalho: falha em G4/G5/G6 volta a `IMPLEMENTING` com feedback, até `1 + max_rework_attempts`.
Terminais: `FAILED`, `CANCELLED`, `REJECTED`, `BUDGET_EXCEEDED`, `COMPLETE`.

## Artefatos por run (`runs/{run_id}/`)

| Pasta | Conteúdo |
|---|---|
| `input/`, `input_manifest.json` | snapshot imutável do brief e dos golden tests, com SHA-256 |
| `00_assessment/ambiguities.json` | ambiguidades do assessor + achados de segurança (`S-###`) |
| `01_resolution/decisions.{json,md}` | decisões humanas |
| `02_spec/spec.json`, `acceptance.feature` | requisitos R-### e cenários |
| `03_design/design.json`, `architecture.md` | arquitetura e decisões |
| `04_tasks/tasks.json`, `plan_digest.json` | DAG, camadas paralelas, ordem, hashes |
| `05_implementation/` | `task_results.json`, `commits.json`, `patch.diff`, `tool_events.jsonl` |
| `06_verification/` | `junit.xml`, `test_results.json`, `verification_report.json` |
| `07_review/` | `review.json`, `traceability.csv` (R-ID → tarefas → commits → testes) |
| `08_delivery/` | `PR_BODY.md`, `pr_mock.json`, `release_notes.md`, `run_report.json` |
| `approvals.json`, `run_state.json` | aprovações por hash; estado + histórico de transições + uso de tokens |

## Módulos

| Arquivo | Papel |
|---|---|
| `schemas.py` | contratos Pydantic (`extra="forbid"`) de todos os artefatos |
| `state_machine.py` | estados e transições permitidas |
| `orchestrator.py` | A0 — executa estágios, aplica gates, persiste e retoma |
| `roles.py` | papéis LLM com JSON validado, retry limitado, budget e tracing |
| `dag.py` | validação do plano (G3) |
| `guardrails.py` | injection (reusa `safety/prompt_injection_guard.py`), comandos, segredos, caminhos |
| `approvals.py`, `budget.py`, `hashing.py` | aprovação por hash, teto de tokens/chamadas, hash canônico |
| `git_ops.py` | worktrees e commits por lista de argumentos (sem shell, sem push) |
| `runner.py` | pytest em subprocesso com timeout, ambiente sem segredos, JUnit |
| `delivery.py` | rastreabilidade, cobertura, corpo de PR, cliente de PR simulado sem merge |
| `llm/` | `MockLLM` (CI sem rede) e `ClaudeProvider` opcional (chave só por ambiente) |
| `demo.py`, `cli.py` | cenário `engineering-intake` e linha de comando |
| `samples/engineering-intake/` | brief, golden tests, repositório-semente FastAPI e respostas roteirizadas |

## Rodar

```bash
# testes (sem rede, sem chave): unitários, adversariais e e2e com git + pytest reais
python -m pytest -q -p no:cacheprovider software_factory/tests

# demo ponta a ponta com aprovações simuladas (rotuladas "demo-approver")
python -m software_factory demo --workspace "D:/Claude Temp/staging/sdd-runs" --auto-approve

# fluxo com gates manuais
python -m software_factory demo --workspace <dir>                 # para em HUMAN_REQUIRED:A-001
python -m software_factory resolve --run-dir <dir>/runs/<run> --decisions decisions.json
python -m software_factory resume  --run-dir <dir>/runs/<run>     # para em AWAITING_APPROVAL:spec
python -m software_factory approve --run-dir <dir>/runs/<run> --artifact spec --approver "Nome"
python -m software_factory resume  --run-dir <dir>/runs/<run>     # ... tasks, depois PR_READY

# Claude real (opcional): exportar ANTHROPIC_API_KEY e usar --provider claude
```

O workspace precisa ficar fora de pastas sincronizadas (Drive/OneDrive): a CLI recusa `G:`.

## O que a demo prova e o que não prova

- **Prova:** gates, bloqueio por ambiguidade, aprovação por hash, DAG, isolamento por worktree,
  allowlist de escrita, runner externo decidindo PASS/FAIL, rastreabilidade e PR sem merge — com
  código real executado por pytest real no worktree.
- **Não prova:** geração autônoma de código por IA. As respostas do `MockLLM` são fixtures escritas à
  mão (`samples/engineering-intake/mock/`). Com `ClaudeProvider` o mesmo fluxo roda com um modelo real,
  mas isso não foi executado nesta revisão.
