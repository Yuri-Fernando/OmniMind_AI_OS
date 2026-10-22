# WORKLOG — OmniMind AI OS

Registro mestre de progresso do projeto, em ordem cronológica (mais recente
no topo). Formato livre — cada entrada descreve o que foi feito, o que
rodou de verdade (vs. o que ficou documentado como limitação) e os números
medidos quando houver.

---

## 2026-10-20 — Software Factory SDD (`software_factory/`, v1.1.0)

**Motivação:** levar o OmniMind de "agentes que planejam" para um ciclo de desenvolvimento de software
orientado por especificação, em que os gates são código e o PASS vem de um runner externo.

### Decisão de destino
Módulo de topo dentro do OmniMind (ADR 0001): reusa `safety/prompt_injection_guard.py`,
`safety/policy_engine.py` e `observability/tracing.py` por import. Não reusa `planning/task_decomposer.py`
(texto livre, sem DAG tipado) nem `tools/code_executor.py` (`exec()` no processo — exatamente o que a
fábrica proíbe).

### O que foi implementado
- Schemas Pydantic, máquina de estados, gates G0–G7, aprovações por hash, budget, papéis LLM com
  retry limitado, worktrees por tarefa, runner pytest com JUnit, rastreabilidade R-ID→tarefa→commit→teste,
  PR simulado, CLI e cenário `engineering-intake` com golden tests.

### Achados reais durante o desenvolvimento
- `git_ops.git()` fazia `.strip()` na saída; o `git status --porcelain` começa com espaço significativo
  (` M app/main.py`) e o caminho virava `pp/main.py` → falso `DIFF_OUTSIDE_OWNED` e REJECTED. Corrigido
  para `rstrip()`; coberto pelo e2e.
- O runner levava 108 s para 14 testes que rodam em ~6 s fora dele: plugins do pytest instalados no
  Python global (deepeval) eram carregados e tentavam telemetria pelo proxy morto. Com
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` caiu para 10,8 s — e o processo de verificação ficou mais isolado.
- No repositório-semente sem a feature, os golden tests falham 10 de 10; com a implementação de
  referência, 14/14 passam (10 golden + 4 do repo) — prova de que os golden tests têm dente.

### Números medidos
- `python -m pytest -q software_factory/tests` → **53 passed** (232 s).
- Regressão: `evaluation/tests` **35 passed**, `rag/tests` **5 passed** (iguais ao baseline medido antes
  da mudança).
- Demo `python -m software_factory demo --auto-approve` → `PR_READY`, 14/14 PASS, requirement_coverage
  1.0, trace_coverage 1.0. Fluxo manual `resolve → approve → resume` entre processos até `COMPLETE`.

### Limitações registradas
- Rede no runner bloqueada só em melhor esforço (proxy morto + env sem segredos); não é sandbox de SO.
- `ClaudeProvider` testado só com cliente falso; respostas da demo são fixtures (não é geração por IA).

---

## 2026-10-07 — Avaliação real e reprodutível (RAGAS/DeepEval/Langfuse)

**Motivação:** item da auditoria de portfólio, seção "Agentic AI / RAG /
LLMOps": *"OmniMind: tornar RAGAS/DeepEval/Langfuse mensurados e
reproduzíveis."*

### Estado encontrado (antes desta sessão)

- `evaluation/ragas_eval.py` e `evaluation/deepeval_tests.py` já existiam,
  com `try/except ImportError` em volta de código real de RAGAS/DeepEval —
  mas **nada no repositório as chamava**. `grep` confirmou zero referências
  a `run_ragas_eval`/`run_deepeval` fora dos próprios arquivos.
- `observability/langfuse_tracing.py` já tinha `trace_run`/`is_langfuse_active`
  com graceful degradation — mas `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`
  estavam vazias no `.env`, então nunca enviava nada de verdade.
- README.md já listava RAGAS, DeepEval e Langfuse na seção "Funcionalidades
  > Evaluation/Observabilidade" como se fossem capacidades entregues.
- Não havia golden-set, script de execução, relatório gerado nem
  `evaluation/reports/` com conteúdo.
- As 3 bibliotecas (`ragas==0.4.3`, `deepeval==3.8.9`, `langfuse==3.12.1`)
  já estavam **instaladas** no Python 3.10 canônico — não era um problema de
  dependência faltando, era de nunca terem sido executadas de verdade.
- Encontrados 2 bugs reais em `run_deepeval` (nunca descobertos porque a
  função nunca rodava): (1) `HallucinationMetric` lê `test_case.context`,
  mas só `retrieval_context` era preenchido; (2) o código lia
  `tc.relevancy_score`/`tc.hallucination_score` do `LLMTestCase`, atributos
  que o DeepEval nunca cria (o score fica no objeto da métrica, não no test
  case).

### O que foi implementado

- `evaluation/golden_dataset.py` — golden-set fixo de 8 perguntas com
  ground_truth, usando README.md/GRAPH_RAG.md/architecture_readme.md (os
  próprios documentos reais do repo) como corpus.
- `evaluation/tfidf_retriever.py` — retriever TF-IDF real e determinístico
  (sem LLM, sem rede) para a camada de recuperação do harness de eval —
  decisão deliberada para não depender do download de modelo HuggingFace do
  backend de produção (`memory/vector_memory.py`) em um ambiente de CI/eval.
- `evaluation/real_pipeline.py` — gera contexto (TF-IDF real) + resposta
  (chamada real à API da OpenAI, `gpt-4o-mini`, temperatura 0) para cada
  item do golden-set; cai para um modo "offline" extrativo e claramente
  rotulado se não houver `OPENAI_API_KEY`.
- `evaluation/ragas_eval.run_ragas_on_golden` — roda RAGAS de verdade
  (faithfulness, answer_relevancy, context_recall) com LLM-juiz real.
- `evaluation/deepeval_tests.run_deepeval_on_golden` — roda DeepEval de
  verdade (AnswerRelevancyMetric, HallucinationMetric), com os 2 bugs acima
  corrigidos.
- `observability/langfuse_tracing.py` — adicionado fallback real de
  tracing em arquivo local (`observability/traces/traces.jsonl`) para quando
  não há Langfuse Cloud/self-host configurado, com `active_backend()`
  reportando honestamente qual dos dois está em uso.
- `evaluation/run_all.py` — `python -m evaluation.run_all`: ponto de entrada
  único, gera `evaluation/reports/eval_<timestamp>.{json,md}`.
- `evaluation/tests/` — testes reais (sem mock da lógica central) do golden
  dataset, do retriever TF-IDF e das métricas puras de `evaluation/metrics.py`.

### Langfuse — decisão sobre self-host

Self-host completo do Langfuse v3 exige um stack multi-container (web,
worker, Postgres, ClickHouse, Redis, MinIO). Docker Desktop estava
disponível nesta máquina, mas provisionar e validar esse stack dentro desta
sessão teria custado tempo desproporcional ao resto da tarefa e risco de
falha parcial não diagnosticável a tempo. Decisão: implementar o fallback
real em arquivo (acima) e documentar aqui o self-host completo como
próximo passo real — não fingido como feito.

### Números medidos (execução real, `python -m evaluation.run_all`)

Relatório completo: `evaluation/reports/eval_20261007_112831.{json,md}`.

- **Observabilidade**: 8 execuções reais do golden-set, 8 traces gravados em
  `observability/traces/traces.jsonl` (fallback local, backend `local_file`).
  Latência total real 15646.94 ms, média 1955.87 ms/execução.
- **RAGAS**: executou de verdade (import real da lib, LLM-juiz real
  instanciado via `ragas.llms.llm_factory`, 24 jobs = 8 perguntas × 3
  métricas submetidos ao executor do ragas) — mas **todas as 24 chamadas
  reais à API da OpenAI retornaram `401 invalid_api_key`**. Nenhum score
  de faithfulness/answer_relevancy/context_recall é real nesta sessão.
- **DeepEval**: mesma causa — `AnswerRelevancyMetric`/`HallucinationMetric`
  tentaram chamar a OpenAI de verdade e receberam o mesmo 401.
- **Achado real, fora do escopo original mas relevante**: tanto
  `OPENAI_API_KEY` quanto `ANTHROPIC_API_KEY` no `.env` deste projeto estão
  **inválidas/expiradas** (testado com uma chamada mínima real a cada
  provedor, fora do harness de avaliação, só para diagnosticar). Isso é uma
  ação para o usuário (rotacionar as chaves), não um bug do código desta
  tarefa — documentado aqui em vez de escondido.
- **Modo offline (sem LLM)**: validado como caminho reprodutível à parte —
  `generate_eval_records(force_offline=True)` produz exatamente os mesmos
  8 contextos (TF-IDF real sobre README.md/GRAPH_RAG.md/architecture_readme.md)
  e respostas extrativas em duas execuções consecutivas (testado em
  `evaluation/tests/test_real_pipeline.py`).

**Conclusão honesta:** a infraestrutura de RAGAS/DeepEval é real, está
corretamente conectada ao golden-set e ao pipeline de retrieval, e vai
produzir números reais de faithfulness/relevancy/hallucination no momento
em que uma `OPENAI_API_KEY` válida estiver no `.env` — não há mock entre o
golden-set e a chamada de API. O que não foi possível nesta sessão foi obter
os *números* em si, por falta de credencial válida, não por falta de
integração.

### Bugs reais encontrados e corrigidos (nunca detectados antes porque o código nunca rodava)

1. `evaluation/deepeval_tests.run_deepeval`: `HallucinationMetric` lê
   `test_case.context` (confirmado lendo
   `deepeval/metrics/hallucination/hallucination.py::_required_params`),
   mas só `retrieval_context` era preenchido — corrigido para preencher os
   dois campos.
2. Mesma função lia `tc.relevancy_score`/`tc.hallucination_score` do
   `LLMTestCase` — atributos que o DeepEval nunca cria (o score fica no
   objeto da métrica após `.measure()`, não no test case). Corrigido para
   ler `metric.measure(tc)` e o atributo `.reason` de cada métrica.
3. `evaluate()` do RAGAS, quando todos os jobs falham (ex.: credencial
   inválida), não propaga a exceção — captura por job e ainda assim tenta
   agregar um resultado vazio, o que gerava `KeyError: 0` opaco em
   `dict(eval_result)`. Adicionada detecção explícita de "todas as linhas
   falharam" antes de tentar extrair scores, com mensagem de erro real e
   legível em vez do `KeyError` interno da lib.

### Langfuse — decisão sobre self-host

Self-host completo do Langfuse v3 exige um stack multi-container (web,
worker, Postgres, ClickHouse, Redis, MinIO). Docker Desktop estava
disponível nesta máquina, mas provisionar e validar esse stack dentro desta
sessão teria custado tempo desproporcional ao resto da tarefa e risco de
falha parcial não diagnosticável a tempo. Decisão: implementar o fallback
real em arquivo (`observability/langfuse_tracing.py`, backend `local_file`,
validado com 8 traces reais gravados nesta sessão) e documentar aqui o
self-host completo como próximo passo real — não fingido como feito.

### Testes

`pytest evaluation/ rag/tests/` — **40 passed** (35 novos em
`evaluation/tests/` + 5 pré-existentes de GraphRAG, inalterados). Cobertura
dos testes novos: golden dataset (arquivos reais do corpus, perguntas
únicas), retriever TF-IDF (chunking, ranking, scores, casos de borda),
métricas puras de `evaluation/metrics.py` (13 testes), pipeline real com
chamada de LLM mockada (retrieval real + fallback de erro real) e a lógica
de agregação/renderização do relatório de `run_all.py`. Nenhum teste mocka
a lógica de cálculo de métrica ou de agregação — só a chamada cara de LLM
externa, como combinado.

---

## 2026-10-21 — OmniMind V2: adaptação de modelo, harness de avaliação e tracing do agente

**Pedido:** fechar as lacunas de Hugging Face/PEFT/LoRA/QLoRA, avaliação unificada (juiz, humano, tool-call
accuracy) e Langfuse, sem criar repositório novo.

**Já existia e foi reaproveitado:** `evaluation/` (RAGAS, DeepEval, golden, métricas) e
`observability/langfuse_tracing.py` (fallback JSONL).

**Feito e executado**
- Ambiente verificado antes de qualquer suposição: torch 2.13+cu126, transformers 5.16.1, peft 0.20.0,
  bitsandbytes 0.50.2, RTX 3060 Ti 8 GB; `trl` e `vllm` ausentes (não instalados).
- Modelo baixado para o cache `Q:\Hugginface` (≈1 GB). Dataset gerado e validado: 460/57/114, vazamento 0.
- Experimento: base bf16 e 4-bit, LoRA, QLoRA e ajuste completo; LoRA/QLoRA/completo × 3 seeds. O ajuste completo
  coube em bf16 puro (7,87 de 8,19 GB). Resultados e leitura honesta no README e em `model_adaptation/results/`.
- Harness, tool-call accuracy, juiz, fila humana e golden com casos negativos; tracing com spans por etapa.

**Problemas reais**
- O processo do experimento morreu na troca de sessão no meio do seed 1 e foi relançado só para o que faltava.
- Um teste meu falhou por premissa errada (resposta com números sem o contexto da pergunta não é "ancorada"); a
  métrica estava certa, corrigi o teste.
- `.env.langfuse` não estava no `.gitignore` apesar do comentário que eu escrevi — corrigido.
- `trace_run` antigo usa `Langfuse.trace()`, inexistente no SDK 3.12.1 (descoberto; legado intocado).

**Não feito:** Langfuse real (stack self-host escrita, não executada); RAGAS/DeepEval com scores (sem chave);
juiz Claude real (só cliente falso); merge do adapter e quantização de serving (fica para o RealTime-ML).

**Testes:** `model_adaptation/tests` 23 passed; `evaluation/tests` + `rag/tests` 103 passed (inclui os 40 anteriores).
