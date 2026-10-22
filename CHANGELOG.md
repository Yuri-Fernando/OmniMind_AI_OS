# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [1.2.0] — 2026-10-21 — Adaptação de modelo, harness de avaliação e tracing do agente

### Added
- `model_adaptation/`: dataset sintético de tool-calling (460/57/114) determinístico e validado contra
  vazamento (entidades particionadas antes da geração, template holdout só no teste); treino LoRA, QLoRA
  (4-bit NF4 + double quant) e ajuste completo sobre `Qwen2.5-0.5B-Instruct`; inferência com adapter PEFT;
  `run_experiment` mede qualidade, VRAM, tempo, adapter em disco, latência e tokens/s; 3 seeds executadas
  de verdade (resultados em `model_adaptation/results/`).
- `evaluation/harness.py`: harness único (juiz, métricas determinísticas, tool-call accuracy, fila de
  avaliação humana, RAGAS/DeepEval opcionais — `NOT_RUN` sem chave) com relatório JSON/Markdown.
- `evaluation/tool_call_accuracy.py` (ferramenta, argumentos válidos/corretos, resultado usado, resposta
  ancorada), `evaluation/llm_judge.py` (juiz determinístico por padrão; `ClaudeJudge` só com opt-in),
  `evaluation/human_eval.py` (fila JSON, aprovar/reprovar com comentário, agregação, CLI),
  `evaluation/agent_golden.py` (5 casos positivos, 7 negativos).
- `observability/agent_tracing.py`: trace do fluxo planner → retriever → tool → LLM → reflection →
  resposta → scores de avaliação; sinks JSONL local e Langfuse (SDK v3); mascara segredos.
- `docker-compose.langfuse.yml` e `.env.langfuse.example` (stack self-host; **nunca executada**).
- ADR `docs/adr/0003-model-adaptation.md`; 86 testes novos.

### Fixed / Notes
- `.gitignore`: `.env.langfuse` e pesos (`*.safetensors|bin|pt` em `model_adaptation/`) agora ignorados.
- Descoberto (não alterado): `observability/langfuse_tracing.trace_run` chama `Langfuse.trace()`, inexistente no
  SDK v3 instalado (3.12.1); com chaves configuradas cairia sempre no arquivo local. O caminho novo usa a API v3.

### Status honesto
- Langfuse real: **BLOCKED_BY_CONFIGURATION**. RAGAS/DeepEval: sem scores (sem `OPENAI_API_KEY`).
- LoRA, QLoRA e ajuste completo: diferenças dentro do desvio entre seeds; tempos/latências ruidosos.

## [1.1.0] — 2026-10-20 — Software Factory SDD

### Added
- Módulo `software_factory/`: desenvolvimento orientado por especificação com agentes — brief
  versionado → ambiguidades → spec R-### → design → DAG de tarefas → implementação em `git worktree`
  por tarefa → pytest por runner externo → revisão independente → PR simulado sem merge.
- Máquina de estados com gates G0–G7 determinísticos, aprovações humanas vinculadas ao SHA-256 do
  artefato (expiram se editado), budget de tokens/chamadas e retrabalho limitado.
- Guardrails: scanner de injection em conteúdo não confiável (reusa `safety/prompt_injection_guard.py`),
  classificação de comandos (destrutivo encerra o run), allowlist de escrita por tarefa, scanner de
  segredos, checagem de sintaxe e de `git status` real do worktree.
- Provedores LLM: `MockLLM` determinístico (CI sem rede/chave) e `ClaudeProvider` opcional (chave só
  por variável de ambiente).
- Cenário `samples/engineering-intake/`: brief, 10 golden tests escritos antes do código,
  repositório-semente FastAPI e respostas roteirizadas; CLI `python -m software_factory`.
- 53 testes (`software_factory/tests/`): unitários, adversariais (injection no PRD, R-ID sem origem,
  DAG cíclico, colisão de owned_path, comando destrutivo, escrita fora da allowlist, relato falso de
  testes, rate limit, SHA stale, aprovação ausente/expirada, budget, input adulterado) e e2e com git e
  pytest reais.
- ADRs `docs/adr/0001` (destino do módulo) e `docs/adr/0002` (gates, isolamento e limites).

### Notes
- As entradas de `[Unreleased]` abaixo (avaliação real RAGAS/DeepEval) são anteriores e continuam sem tag.

## [Unreleased]

### Added
- Golden-set reprodutível (`evaluation/golden_dataset.py`) com 8 perguntas e
  respostas de referência extraídas do conteúdo real do próprio repositório
  (README.md, rag/GRAPH_RAG.md, architecture_readme.md).
- Retriever TF-IDF determinístico (`evaluation/tfidf_retriever.py`) usado
  como camada de recuperação real do harness de avaliação, sem depender de
  download de modelo nem de rede.
- Pipeline real de geração de respostas (`evaluation/real_pipeline.py`):
  contexto real (TF-IDF) + resposta real via OpenAI (gpt-4o-mini), com
  fallback offline determinístico documentado quando não há chave de API.
- Execução real de RAGAS (`evaluation/ragas_eval.run_ragas_on_golden`) sobre
  o golden-set, com relatório numérico salvo em `evaluation/reports/`.
- Execução real de DeepEval (`evaluation/deepeval_tests.run_deepeval_on_golden`)
  sobre o golden-set.
- Fallback local de tracing (`observability/langfuse_tracing.read_local_traces`,
  `active_backend`) que grava traces reais em
  `observability/traces/traces.jsonl` quando não há Langfuse Cloud/self-host
  configurado — documentado como limitação honesta, não como Langfuse real.
- Ponto de entrada único e reprodutível `python -m evaluation.run_all`, que
  gera `evaluation/reports/eval_<timestamp>.json` e `.md` com números medidos
  de verdade (não estimados).
- Suíte de testes para o novo código (`evaluation/tests/`): golden dataset,
  retriever TF-IDF, métricas puras, agregação do relatório.

### Fixed
- `evaluation/deepeval_tests.run_deepeval`: `HallucinationMetric` lê
  `test_case.context`, mas a função só preenchia `retrieval_context` — a
  métrica de hallucination nunca tinha dado reais para avaliar (campo
  obrigatório ausente). Corrigido para preencher os dois campos.
- `evaluation/deepeval_tests.run_deepeval`: lia `tc.relevancy_score`/
  `tc.hallucination_score` do `LLMTestCase`, atributos que o DeepEval nunca
  cria (o score é retornado por `metric.measure(tc)` e fica no objeto da
  métrica). Corrigido.
- `evaluation/ragas_eval.run_ragas_on_golden`: quando todas as chamadas ao
  LLM-juiz do RAGAS falham, `evaluate()` não propaga a exceção e
  `dict(eval_result)` lançava um `KeyError: 0` opaco ao tentar agregar um
  resultado vazio. Adicionada detecção explícita desse caso com mensagem
  de erro legível.

### Changed
- `evaluation/ragas_eval.py` e `evaluation/deepeval_tests.py` passam a ter,
  além das funções originais (mantidas por compatibilidade), uma função
  "on_golden" que de fato invoca essas avaliações com dados reais — até esta
  versão, nada no repositório chamava essas funções (não havia golden-set,
  script ou CI que as executasse).

### Known limitations
- `OPENAI_API_KEY` e `ANTHROPIC_API_KEY` no `.env` deste projeto estavam
  inválidas/expiradas nesta sessão (testado com chamada mínima real a cada
  provedor) — por isso os scores reais de RAGAS/DeepEval desta execução
  vieram como erro de autenticação, não como número. A infraestrutura está
  pronta e vai produzir números reais assim que uma chave válida estiver
  configurada; ver `WORKLOG.md` para o relato completo.
- Langfuse Cloud/self-host não configurado nesta sessão; tracing real cai
  no fallback local em arquivo (`observability/traces/traces.jsonl`).

## Contexto da auditoria

Item da auditoria de portfólio (seção "Agentic AI / RAG / LLMOps"):
"OmniMind: tornar RAGAS/DeepEval/Langfuse mensurados e reproduzíveis."

Estado anterior: README.md listava RAGAS, DeepEval e Langfuse como
funcionalidades do projeto; o código (`evaluation/ragas_eval.py`,
`evaluation/deepeval_tests.py`, `observability/langfuse_tracing.py`) existia
mas nunca era invocado por nada — sem golden-set, sem relatório gerado, sem
integração real de RAGAS/DeepEval, sem chaves de Langfuse configuradas.
As três bibliotecas (ragas, deepeval, langfuse) já estavam instaladas no
ambiente Python, mas isso não equivale a "mensurado e reproduzível".

Ver `WORKLOG.md` para o relato completo de execução desta tarefa, incluindo
o que rodou de verdade e o que ficou documentado como limitação.
