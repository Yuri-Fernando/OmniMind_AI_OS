# ADR 0001 — Software Factory SDD como módulo do OmniMind AI OS

- **Status:** aceito (2026-10-20)
- **Contexto:** precisávamos de um ciclo de desenvolvimento orientado por especificação (SDD) com
  agentes: brief → ambiguidades → spec com R-IDs → design → DAG de tarefas → implementação isolada →
  testes por runner externo → revisão independente → PR para revisão humana.

## Opções avaliadas

| Opção | Prós | Contras |
|---|---|---|
| Repositório novo e independente | Isolamento total; nome próprio | Duplicaria runtime que já existe aqui (planejamento, guardrails, tracing, avaliação); mais um repo sem integração |
| Módulo no `IA_Agentica` | Repositório já é sobre desenvolvimento com IA agentiva | É agregador de submódulos e skills, sem runtime Python próprio para hospedar uma máquina de estados testada |
| **Módulo `software_factory/` no OmniMind** | Reaproveita `safety/prompt_injection_guard`, `safety/policy_engine`, `observability/tracing`; mesmo Python 3.10, mesma convenção de pacotes de topo | Repositório já grande; exige que o módulo não importe nada pesado (LangChain, bancos) para continuar testável sem rede |

## Decisão

Módulo de topo `software_factory/`, com dependências mínimas (pydantic, fastapi/httpx só no
repositório-alvo de demonstração, `anthropic` opcional e importado tarde). Reuso por import:

- `safety.prompt_injection_guard.check_injection` — primeira camada do scanner de conteúdo não confiável;
- `safety.policy_engine.PolicyEngine` — política de entrada no gate G0 (documento vazio/longo demais);
- `observability.tracing.Tracer` — spans por papel LLM.

Não reaproveitado de propósito:

- `planning/task_decomposer.py` devolve lista numerada em texto livre, sem dependências tipadas nem
  ownership de arquivos; o planner da fábrica precisa de DAG validado por schema.
- `tools/code_executor.py` executa `exec()` no processo; a fábrica proíbe execução de código vindo do
  LLM fora do runner externo (ver ADR 0002).
- `observability/langfuse_tracing.py` cria cliente na importação; manter a fábrica livre desse efeito
  colateral. Pode ser plugado depois no `RoleRunner`.

## Consequências

- A fábrica roda e é testada sem chave de LLM e sem rede (`MockLLM`).
- O módulo pode ser extraído para repositório próprio sem reescrita: só importa três utilitários do
  OmniMind, todos sem dependências externas.
