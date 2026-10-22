# 🤖 OmniMind AI OS — Plataforma Modular de Orquestração de Agentes de IA

### Python · LangChain · LangGraph · FastAPI · MongoDB · Postgres/pgvector · Neo4j · RAGAS · DeepEval · Langfuse

![versão](https://img.shields.io/badge/vers%C3%A3o-1.2-4a5563)
![python](https://img.shields.io/badge/python-3.10%2B-4a5563)
![testes](https://img.shields.io/badge/testes-179%2F179-0a8a0a)
![uso](https://img.shields.io/badge/uso-P%26D%20%2F%20portf%C3%B3lio-c8742a)

## Status

🟢 **Concluído no escopo do núcleo — Versão 1.2 / P&D em Agentic AI**

**Novo na v1.1:** módulo [`software_factory/`](software_factory/README.md) — Software Factory SDD:
brief versionado → spec com R-IDs → DAG de tarefas → implementação em `git worktree` isolado → testes
por runner externo → revisão independente → PR para revisão humana, com gates G0–G7 determinísticos.
53 testes próprios (unitários, adversariais e e2e com git/pytest reais), demo ponta a ponta em
`PR_READY` com 14/14 testes e cobertura de requisitos 1.0.

**Novo na v1.2:** [`model_adaptation/`](model_adaptation/README.md) — experimento **executado** de ajuste
fino de um modelo pequeno (`Qwen2.5-0.5B-Instruct`) para roteamento de ferramentas: base × LoRA × QLoRA
(4-bit NF4) × ajuste completo, 3 seeds, com VRAM/tempo/adapter/qualidade/latência medidos; um **harness de
avaliação único** (`evaluation/harness.py`: juiz, métricas determinísticas, tool-call accuracy, fila de
avaliação humana, RAGAS/DeepEval quando há chave) e **tracing ponta a ponta** do fluxo do agente
(`observability/agent_tracing.py`). 86 testes novos. O backend Langfuse real **continua
`BLOCKED_BY_CONFIGURATION`** (stack self-host escrita, nunca executada).

O núcleo de orquestração (planejamento autônomo, coordenação multiagente, RAG, ferramentas dinâmicas,
memória, reasoning, reflection, segurança e observabilidade) está implementado e documentado. Na
sessão mais recente, a camada de **Evaluation** (RAGAS/DeepEval) e a de **Observability** (tracing)
deixaram de ser código nunca executado e passaram a rodar de ponta a ponta contra um golden-set
reprodutível — **40/40 testes passando** (confirmado nesta revisão) e 8 execuções reais com tracing
real gravado em arquivo. Os *scores* numéricos de RAGAS/DeepEval desta sessão não puderam ser obtidos
porque as chaves `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` deste `.env` estão **expiradas** — isso é uma
dependência externa (rotação de credencial), não uma falha da integração, e está documentado como tal
em vez de ser escondido ou simulado.

| Área | Estado | Evidência |
|---|---|---|
| Orquestração multiagente, planejamento, RAG, ferramentas, memória V1 | 🟢 Concluído | Código em `core/`, `agents/`, `planning/`, `rag/`, `memory/` |
| GraphRAG (RAG + Knowledge Graph) | 🟢 Concluído | `rag/graph_rag.py`, 5 testes com fakes em `rag/tests/test_graph_rag.py` |
| Memory V2 (MongoDB + pgvector + Neo4j) | 🟡 Implementado, não validado contra bancos reais nesta sessão | `memory/*_v2.py`, mesma interface da V1 |
| Evaluation real (RAGAS/DeepEval sobre golden-set) | 🟡 Infra real e testada; scores bloqueados por chave de API expirada | `evaluation/run_all.py`, 35 testes novos, `evaluation/reports/eval_20261007_112831.*` |
| Observability (tracing) | 🟡 Fallback local real funcionando; Langfuse Cloud/self-host não configurado | `observability/langfuse_tracing.py`, `observability/traces/traces.jsonl` |
| Software Factory SDD (`software_factory/`) | 🟢 MVP com MockLLM / 🟡 Claude real não executado | 53 testes em `software_factory/tests/`; ADRs `docs/adr/0001` e `0002` |
| Adaptação de modelo (LoRA / QLoRA / completo) | 🟢 Executado e testado (modelo 0,5B, tarefa sintética, 1 GPU de 8 GB) | `model_adaptation/`, `model_adaptation/results/*.json` + `REPORT.md`, 23 testes, ADR `0003` |
| Harness de avaliação único (juiz + determinísticas + humano + tool-call accuracy) | 🟢 Implementado e testado / 🟡 RAGAS e DeepEval só rodam com `OPENAI_API_KEY` (senão `NOT_RUN`) | `evaluation/harness.py`, `evaluation/tool_call_accuracy.py`, `evaluation/reports/harness_golden.*`, 63 testes |
| Tracing do fluxo do agente | 🟢 JSONL local real; sink Langfuse testado só com cliente falso / 🔴 Langfuse real `BLOCKED_BY_CONFIGURATION` | `observability/agent_tracing.py`, `docker-compose.langfuse.yml` (nunca executado), `.env.langfuse.example` |

---

## Descrição / Contexto

O OmniMind AI OS é uma plataforma modular de orquestração de agentes de IA para resolução de tarefas
complexas por meio de planning automático, coordenação multiagente, RAG, ferramentas dinâmicas,
memória, avaliação, reflexão e observabilidade. O núcleo integra planejamento, execução, conhecimento,
ferramentas, memória, avaliação, segurança e observabilidade em uma única arquitetura modular.

```text
Goal → Plan → Execute → Learn → Improve → Final Answer
```

> Este é um projeto de P&D/portfólio pessoal. Números de latência, contagem de testes e resultados de
> avaliação citados abaixo foram medidos localmente nesta máquina; onde um resultado não pôde ser
> obtido (ex.: score de RAGAS por falta de credencial válida), isso está documentado como limitação,
> não como resultado.

## 🧭 Origem do Projeto

1. **Núcleo (versões anteriores)** — orquestração multiagente, planejamento autônomo, RAG, ferramentas
   dinâmicas, memória em três camadas (local), reasoning/reflection, segurança e observabilidade
   básica foram implementados e documentados como a "Versão 1.0" do projeto.
2. **Memory V2** — a V1 do Memory System roda inteira sobre armazenamento local (`LongTermMemory` em
   JSON, `VectorMemory` via Chroma/SQLite, `KnowledgeGraphBuilder` em dicionário Python perdido ao
   final do processo). Decisão: substituir os três backends por bancos de dados reais (MongoDB,
   Postgres+pgvector, Neo4j) **mantendo a mesma interface pública**, para não escalar para múltiplas
   instâncias nem perder estado fora do processo sem reescrever quem já consome `MemoryManager`.
3. **GraphRAG** — `rag/` (Chroma + embeddings) e `knowledge_graph/` (extração de entidades/relações
   via LLM + travessia em grafo) já existiam **separados**. Decisão: compor os dois de verdade em
   `rag/graph_rag.py`, porque busca vetorial sozinha falha em perguntas relacionais ("onde X
   trabalhou") quando as duas entidades não compartilham vocabulário.
4. **Avaliação real (sessão 2026-10-07)** — item de auditoria de portfólio: *"OmniMind: tornar
   RAGAS/DeepEval/Langfuse mensurados e reproduzíveis."* Estado encontrado antes desta sessão:
   `evaluation/ragas_eval.py` e `evaluation/deepeval_tests.py` já existiam com código real de
   RAGAS/DeepEval, mas **nada no repositório as chamava** (confirmado via grep: zero referências fora
   dos próprios arquivos); `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` vazias; sem golden-set, sem relatório.
   As 3 bibliotecas já estavam instaladas — o problema nunca foi dependência faltando, foi ausência de
   execução real. Esta sessão construiu o golden-set, o pipeline real e o ponto de entrada único (ver
   seção seguinte), e no processo encontrou e corrigiu 2 bugs reais em `run_deepeval` que nunca tinham
   sido detectados porque a função nunca rodava.

## 🎯 Objetivo

- Orquestrar múltiplos agentes especializados (RAG, ferramentas, execução) sob um planejador autônomo.
- Manter memória de curto, médio (vetorial) e longo prazo, com opção de backends locais ou bancos reais.
- Combinar busca vetorial e grafo de conhecimento para perguntas relacionais (GraphRAG).
- Medir a qualidade das respostas do próprio agente com RAGAS e DeepEval sobre um golden-set
  reprodutível, não apenas citar as bibliotecas como dependência instalada.
- Registrar tracing real de cada execução, com fallback honesto quando não há backend de observabilidade
  configurado.

## 🔬 Linha de Pesquisa / Desenvolvimento

- Multi-Agent Systems e Autonomous Planning.
- RAG, GraphRAG e Knowledge Graphs.
- Reasoning (CoT/ToT) e Reflection.
- Memória multi-tier (local e com bancos de dados reais).
- Evaluation de agentes de LLM (RAGAS, DeepEval) com golden-set reprodutível.
- Observabilidade e tracing de execução de agentes.

## 🏗️ Arquitetura

```text
                              USER
                                │
                                ▼
                       Interaction Layer
             ┌─────────────────────────────────┐
             │ API │ Notebook │ Voice │ CLI    │
             └────────────────┬────────────────┘
                              │
                              ▼
                      Goal Management Layer
             ┌─────────────────────────────────┐
             │ Goal Manager                     │
             │ Autonomous Planner                │
             │ Task Decomposer                   │
             └────────────────┬────────────────┘
                              │
                              ▼
                    Multi-Agent Coordination
             ┌─────────────────────────────────┐
             │ Agent Router                      │
             │ Agent Registry                    │
             │ Communication Protocol            │
             └────────────────┬────────────────┘
                              │
                              ▼
                      Agent Execution
             ┌─────────────────────────────────┐
             │ RAG Agent                         │
             │ Tool Agent                        │
             │ Executor Agent                    │
             └────────────────┬────────────────┘
                              │
                              ▼
                    Reasoning / Reflection
                              │
                              ▼
                    Self-Improvement Engine
                              │
                              ▼
                        Memory System
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
            Short-Term     Vector      Long-Term
              Memory       Memory         Memory
          (local / V2: MongoDB · pgvector · Neo4j)
                              │
                              ▼
                         World Model
                              │
                              ▼
                      Evaluation Layer
                (RAGAS · DeepEval sobre golden-set real)
                              │
                              ▼
                    Observability Layer
              (Langfuse ou fallback local JSONL)
```

| Módulo | Função | Teste |
|---|---|---|
| `core/agent_runtime.py`, `core/orchestration_graph.py` | Runtime e grafo de orquestração | — |
| `planning/` | Goal Manager, planejador autônomo, decomposição de tarefas | — |
| `rag/graph_rag.py` | Composição real de busca vetorial + grafo de conhecimento | `rag/tests/test_graph_rag.py` (5 testes com fakes) |
| `memory/*_v2.py` | Backends V2 (MongoDB, pgvector, Neo4j) atrás da mesma interface da V1 | `notebooks/memory_databases_v2.ipynb` |
| `evaluation/run_all.py` | Ponto de entrada único: golden-set → RAGAS/DeepEval reais → relatório | `evaluation/tests/` (35 testes) |
| `observability/langfuse_tracing.py` | Tracing real com fallback local em arquivo | 8 traces reais em `observability/traces/traces.jsonl` |
| `software_factory/` | Software Factory SDD: gates G0–G7, aprovação por hash, worktree por tarefa, runner externo, rastreabilidade | `software_factory/tests/` (53 testes) |

## ⚙️ Funcionamento

### Ciclo de execução do agente

```text
User Request → Goal Manager → Autonomous Planner → Task Decomposer → Multi-Agent Router
   ├── RAG Agent
   ├── Tool Agent
   └── Executor Agent
→ Reasoning Engine → Reflection Agent → Self-Improvement → Memory Update
→ Evaluation Pipeline → Observability → Final Answer
```

### Pipeline de avaliação real (`python -m evaluation.run_all`)

1. `evaluation/golden_dataset.py` fornece 8 perguntas com `ground_truth`, extraídas do conteúdo real
   do próprio repositório (README.md, `rag/GRAPH_RAG.md`, `architecture_readme.md`).
2. `evaluation/tfidf_retriever.py` recupera contexto por TF-IDF determinístico — real, sem download de
   modelo nem rede, para não depender do backend de produção em um harness de avaliação/CI.
3. `evaluation/real_pipeline.py` gera a resposta: contexto real (TF-IDF) + chamada real à API da
   OpenAI (`gpt-4o-mini`, temperatura 0); cai para um modo offline extrativo claramente rotulado se não
   houver `OPENAI_API_KEY`.
4. `evaluation/ragas_eval.run_ragas_on_golden` roda RAGAS de verdade (faithfulness, answer_relevancy,
   context_recall) com LLM-juiz real.
5. `evaluation/deepeval_tests.run_deepeval_on_golden` roda DeepEval de verdade
   (AnswerRelevancyMetric, HallucinationMetric).
6. Cada execução é traçada por `observability/langfuse_tracing.py` — Langfuse Cloud/self-host se
   configurado, senão fallback real em `observability/traces/traces.jsonl`.
7. `evaluation/run_all.py` consolida tudo em `evaluation/reports/eval_<timestamp>.{json,md}`.

### Software Factory SDD (`python -m software_factory`)

```text
brief + golden tests + repo@SHA
  → G0 input (hashes, SHA-base) → ASSESSOR (+ scanner de injection) → G1 decisões humanas
  → SPECIFIER (R-###, Given/When/Then) → G2 origem + MUST→golden test + aprovação por hash
  → ARCHITECT → PLANNER (DAG) → G3 ciclo/ids/owned_paths/colisão + aprovação por hash
  → IMPLEMENTER por tarefa em worktree agent/{run}/{T} → G4 allowlist, segredo, sintaxe, comando destrutivo
  → RUNNER externo (pytest + JUnit) → G5 todos os testes da spec PASS
  → REVIEWER independente + traceability.csv → G6 → PR_READY (PR simulado, sem merge) → G7 humano
```

Detalhes, artefatos por estágio e limites em [software_factory/README.md](software_factory/README.md).

### GraphRAG

```text
Documento → ingest() → indexado em Chroma (vetorial) + Knowledge Graph (entidades/relações)
Pergunta → retrieve() → busca vetorial (similaridade semântica) + travessia de grafo (relações)
         → contexto combinado → LLM
```

## 🧠 Verificação / Modelagem

| Camada | O que prova | Resultado |
|---|---|---|
| GraphRAG | Busca vetorial sozinha falha em perguntas relacionais ("onde X trabalhou") quando as entidades não compartilham vocabulário; o grafo resolve via aresta estruturada | 5/5 testes com fakes, incluindo o caso exato "vetorial não acha, grafo acha" — ver [`rag/GRAPH_RAG.md`](rag/GRAPH_RAG.md) |
| Pipeline de avaliação real | RAGAS/DeepEval estão de fato conectados ao golden-set e à chamada de API, não mockados | 24 jobs reais submetidos (8 perguntas × 3 métricas RAGAS) — todos retornaram `401` da OpenAI por chave expirada, não por falha de integração |
| Fallback de observabilidade | Tracing funciona mesmo sem Langfuse configurado | 8 execuções reais gravadas em `observability/traces/traces.jsonl`, `active_backend()` reporta `local_file` honestamente |
| Agregação do relatório | Consistência interna dos números do relatório de avaliação | testes de `evaluation/tests/` para a lógica de agregação/renderização de `run_all.py` |

## 🧪 Desenvolvimento Experimental

Fluxo: localizar código real nunca executado → construir golden-set e harness → rodar de verdade →
corrigir o que aparecer → documentar o que não pôde ser obtido.

**Achados reais (não plantados):**

1. **`HallucinationMetric` sem dado obrigatório:** a métrica lê `test_case.context` (confirmado lendo
   `deepeval/metrics/hallucination/hallucination.py::_required_params`), mas `run_deepeval` só
   preenchia `retrieval_context` — a métrica nunca tinha dado real para avaliar. Corrigido para
   preencher os dois campos.
2. **Leitura de atributos que o DeepEval nunca cria:** o código lia `tc.relevancy_score` /
   `tc.hallucination_score` do `LLMTestCase`; o score fica no objeto da métrica após `.measure()`, não
   no test case. Corrigido para ler `metric.measure(tc)` e o atributo `.reason` de cada métrica.
3. **`KeyError: 0` opaco no RAGAS:** quando todas as linhas falham (ex.: credencial inválida),
   `evaluate()` do RAGAS não propaga a exceção e `dict(eval_result)` lançava um `KeyError: 0` sem
   contexto ao tentar agregar um resultado vazio. Adicionada detecção explícita desse caso, com
   mensagem de erro legível.
4. **Achado fora do escopo original, mas relevante:** tanto `OPENAI_API_KEY` quanto
   `ANTHROPIC_API_KEY` no `.env` deste projeto estão inválidas/expiradas — testado com uma chamada
   mínima real a cada provedor, fora do harness, só para diagnosticar. É uma ação para o usuário
   (rotacionar as chaves), não um bug desta tarefa — documentado em vez de escondido.
5. **Decisão sobre Langfuse self-host:** o self-host completo do Langfuse v3 exige um stack
   multi-container (web, worker, Postgres, ClickHouse, Redis, MinIO). Provisionar e validar esse stack
   nesta sessão teria custo desproporcional e risco de falha parcial não diagnosticável a tempo.
   Decisão: implementar o fallback real em arquivo e documentar o self-host como próximo passo real.

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+
- **Orquestração de agentes:** LangChain · LangGraph
- **LLMs:** OpenAI (`gpt-4o-mini`) · Anthropic Claude — chaves presentes no `.env`, mas expiradas
  nesta sessão (ver Limitações)
- **Memória V1 (local):** Chroma (SQLite) · JSON em disco · dict em memória
- **Memória V2 (bancos reais, mesma interface):** MongoDB · Postgres + pgvector (HNSW, cosine) · Neo4j
  (Cypher `shortestPath`)
- **Evaluation:** RAGAS 0.4.3 · DeepEval 3.8.9 — ambos executados de verdade sobre golden-set nesta
  sessão
- **Observabilidade:** Langfuse 3.12.1 (cloud/self-host, não configurado nesta sessão) + fallback real
  em arquivo (`observability/langfuse_tracing.py`)
- **API:** FastAPI
- **Interface:** Streamlit
- **Voz:** Whisper · ElevenLabs
- **Dados:** Pandas · NumPy
- **Infraestrutura:** Docker (Dockerfile presente; stack completo não validado nesta sessão)

## 📊 Resultados

### Observabilidade (medido, `python -m evaluation.run_all`)

| Métrica | Valor |
|---|---:|
| Execuções reais do golden-set | 8 |
| Traces gravados (fallback `local_file`) | 8 |
| Latência total | 15646,94 ms |
| Latência média por execução | 1955,87 ms |

### RAGAS / DeepEval (medido — infraestrutura real, scores bloqueados)

| Item | Resultado |
|---|---|
| Jobs reais submetidos ao RAGAS (8 perguntas × 3 métricas) | 24 |
| Chamadas reais à API OpenAI que retornaram sucesso | 0 |
| Chamadas reais à API OpenAI que retornaram `401 invalid_api_key` | 24 |
| Causa | `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` expiradas no `.env` deste projeto |
| Modo offline (sem LLM, validado como caminho alternativo) | Determinístico — mesmos 8 contextos/respostas extrativas em execuções consecutivas, testado em `evaluation/tests/test_real_pipeline.py` |

Relatório completo desta execução: [`evaluation/reports/eval_20261007_112831.md`](evaluation/reports/eval_20261007_112831.md)
e `.json`.

### Adaptação de modelo — roteador de ferramentas (medido, 2026-10-21)

`Qwen2.5-0.5B-Instruct`, tarefa sintética de tool-calling (460 treino / 57 val / 114 teste, zero vazamento
verificado; 34 pedidos do teste usam uma formulação nunca vista no treino), RTX 3060 Ti 8 GB, 3 seeds
(média ± desvio). Fonte: [`model_adaptation/results/REPORT.md`](model_adaptation/results/REPORT.md).

| Variante | exact match | formulação nova (holdout) | VRAM de treino (GB) | adapter em disco | parâmetros treináveis | VRAM de inferência (GB) |
|---|---:|---:|---:|---:|---:|---:|
| Base (bf16), sem treino | 0,702 | 0,529 | — | — | — | 1,015 |
| Base (4-bit NF4), sem treino | 0,439 (JSON estrito 0,667) | 0,294 | — | — | — | 0,482 |
| Ajuste fino completo (bf16) | 0,927 ± 0,004 | 0,755 ± 0,014 | 7,87 (de 8,19) | 988 MB (modelo inteiro) | 100 % | 1,020 |
| LoRA (r=16, bf16) | 0,947 ± 0,029 | 0,843 ± 0,097 | 6,50 | 35,2 MB | 1,75 % | 1,083 |
| QLoRA (r=16, base 4-bit NF4) | 0,936 ± 0,030 | 0,833 ± 0,084 | 7,54 | 35,2 MB | 2,72 % | 0,545 |

Leitura honesta (o que os números sustentam e o que não):
- Os três métodos de treino ficam **muito acima da base** (0,70 → ≈0,93–0,95) e QLoRA recupera a base
  quantizada, que sozinha cai para 0,44.
- **Não há diferença estatisticamente distinguível entre LoRA, QLoRA e ajuste completo**: as diferenças
  (≤ 0,02) estão dentro do desvio entre seeds (≈ 0,03), com 3 seeds e 114 exemplos de teste.
- Na formulação nunca vista a variância é grande (0,74–0,97 entre seeds); nos erros inspecionados,
  `web_search` domina: o modelo copia "o que há de novo em" para dentro da query (outros: cidade com
  grafia distorcida, operando truncado). É um limite de generalização, não resolvido aqui.
- **QLoRA economizou memória só nos pesos/inferência** (0,48 vs 1,00 GB após carregar; 0,545 vs 1,083 GB na
  inferência), **não no pico de treino** (7,54 vs 6,50 GB). Não medi a causa; o pico neste regime
  (batch 8, vocabulário de ~152 mil tokens) provavelmente é dominado por logits/ativações e pelo cast para
  fp32 de `prepare_model_for_kbit_training`.
- O ajuste completo coube por pouco (7,87 de 8,19 GB) e só em bf16 puro; o adapter LoRA pesa ~3,6 % do modelo.
- **Tempos de treino e latências não são comparáveis entre variantes:** a mesma configuração LoRA levou de
  122 a 414 s entre seeds (a GPU é compartilhada e rodei outras cargas em paralelo), e adapters não mesclados
  têm custo de inferência próprio. Estão nos JSONs, mas não tiro conclusão de velocidade.
- Resultado de um modelo, uma tarefa sintética e uma GPU; não generaliza para LLMs maiores ou linguagem aberta.

### Harness de avaliação sobre o golden de agentes (`python -m evaluation.harness`)

12 casos escritos à mão (5 positivos, 7 negativos), juiz determinístico (proxies lexicais):
todos os 5 positivos completam a tarefa e **todos os 7 negativos são reprovados, cada um pelo motivo
esperado** (ferramenta errada, argumentos inválidos, argumentos errados, resultado ignorado, resposta não
ancorada, chamada ausente, alucinação). Relatório: [`evaluation/reports/harness_golden.md`](evaluation/reports/harness_golden.md).
RAGAS/DeepEval: `NOT_RUN` (sem `OPENAI_API_KEY`).

### Testes (confirmado nesta revisão)

| Suite | Resultado |
|---|---|
| `pytest software_factory/tests evaluation/tests model_adaptation/tests rag/tests` (v1.2, 2026-10-22) | **179/179 passando** — 1046 s (53 + 103 + 23 = 179; suíte completa dos quatro diretórios, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) |
| `pytest model_adaptation/tests` (v1.2, 2026-10-21) | **23/23 passando** — 49 s |
| `pytest evaluation/tests rag/tests` (v1.2) | **103/103 passando** — 118 s (63 novos + 35 de avaliação e 5 de GraphRAG pré-existentes, sem regressão) |
| `pytest evaluation/ rag/tests/` | **40/40 passando** — 70,02s (35 novos de `evaluation/tests/` + 5 pré-existentes de GraphRAG) |
| `pytest software_factory/tests` (v1.1, 2026-10-20) | **53/53 passando** — 232 s (inclui e2e com git e pytest reais); regressão `evaluation/tests` 35/35 e `rag/tests` 5/5 na mesma revisão |
| Demo `python -m software_factory demo --auto-approve` | `PR_READY`, 14/14 testes no worktree, requirement_coverage 1.0, trace_coverage 1.0 |

Nenhum teste mocka a lógica de cálculo de métrica ou de agregação — apenas a chamada cara de LLM
externa é mockada nos testes unitários do pipeline; os testes de integração real (`run_all.py`) usam a
API de verdade e, nesta sessão, documentam a falha de autenticação como resultado real.

## 🖼️ Evidências

Este projeto não tem dashboard visual nem screenshots versionados nesta revisão. A evidência de
execução real é textual/estruturada:

- Relatório de avaliação: [`evaluation/reports/eval_20261007_112831.md`](evaluation/reports/eval_20261007_112831.md)
- Traces reais: `observability/traces/traces.jsonl` (8 linhas, uma por execução do golden-set)

## 🚀 Aplicações

- Estudo e portfólio em engenharia de sistemas agentivos (planejamento, RAG, memória, avaliação).
- Base para experimentar GraphRAG real sem depender de infraestrutura gerenciada.
- Harness de avaliação reprodutível para comparar respostas de agente contra golden-set próprio.

## 🔭 Visão de Longo Prazo

```text
Núcleo de orquestração de agentes (planejamento, RAG, memória, ferramentas)
            ↓
Memória e conhecimento sobre bancos reais (MongoDB · pgvector · Neo4j) + GraphRAG
            ↓
Avaliação e observabilidade mensuráveis e reproduzíveis (RAGAS · DeepEval · Langfuse)
            ↓
Execução distribuída, colaboração multiusuário e monitoramento avançado
```

## 🗺️ Roadmap

**F0 — Núcleo (versões anteriores)** ✅ Concluída — orquestração multiagente, planejamento, RAG,
ferramentas dinâmicas, memória V1, reasoning/reflection, segurança, observabilidade básica.

**F1 — Memory V2 e GraphRAG** ✅ Concluída (código e testes) / 🟡 Parcial (validação contra bancos
reais em produção) — backends MongoDB/pgvector/Neo4j implementados atrás da mesma interface; GraphRAG
real com 5 testes; não validado nesta sessão contra instâncias reais dos três bancos.

**F2 — Avaliação e observabilidade reais** 🟡 Parcial — infraestrutura real e testada (40/40 testes,
8 execuções, 24 jobs RAGAS/DeepEval reais); scores numéricos bloqueados por chave de API expirada
(ação do usuário, não bug de código); Langfuse Cloud/self-host documentado como próximo passo, não
implementado.

**F2.5 — Software Factory SDD** ✅ Concluída (MVP com MockLLM) / 🟡 Parcial (Claude real) — gates
G0–G7, worktrees, runner externo e rastreabilidade com 53 testes; execução com `ClaudeProvider` real e
sandbox de SO (container sem rede) ficam para a próxima fase.

**F2.6 — Adaptação de modelo e harness de avaliação** ✅ Concluída (LoRA/QLoRA/completo executados, 3 seeds;
harness e tracing testados) / 🔴 Langfuse real `BLOCKED_BY_CONFIGURATION` / 🟡 RAGAS e DeepEval sem scores
(sem chave).

**F3 — Interface Visual, Fine-Tuning, Execução Distribuída, Multimodal, Colaboração, Monitoramento
Avançado** ⏳ Planejada — ver detalhamento em [🔮 Próximos Passos](#-próximos-passos).

## 🕓 Histórico e Mudanças

| Versão | O que mudou |
|---|---|
| v1.2.0 (2026-10-21) | `model_adaptation/` (LoRA/QLoRA/completo executados), harness de avaliação único, tool-call accuracy, juiz plugável, fila de avaliação humana, tracing do fluxo do agente, stack Langfuse self-host (não executada), ADR 0003, 86 testes |
| v1.1.0 (2026-10-20) | Módulo `software_factory/` (SDD com gates G0–G7, aprovação por hash, worktrees, runner externo, PR simulado), 53 testes, ADRs 0001/0002 |
| Unreleased | Golden-set reprodutível, pipeline real de RAGAS/DeepEval, fallback de tracing local, `evaluation/run_all.py`, 35 testes novos; 2 bugs reais corrigidos em `run_deepeval`; limitação de chaves de API expiradas documentada |
| v2 (memory) | Memory System V2: MongoDB + pgvector + Neo4j, mesma interface pública dos backends V1 |
| v2 (GraphRAG) | Composição real de `rag/` + `knowledge_graph/` em `rag/graph_rag.py`, 5 testes com fakes |
| v1.0 | Núcleo: orquestração multiagente, planejamento autônomo, RAG, ferramentas dinâmicas, memória local, reasoning, reflection, segurança, observabilidade |

Ver [CHANGELOG.md](CHANGELOG.md) e [WORKLOG.md](WORKLOG.md) para o detalhamento completo, incluindo o
que rodou de verdade e o que ficou documentado como limitação em cada sessão.

## 🔮 Próximos Passos

**Concluído na v1.2:**
- ✅ Ajuste fino executado e medido (base × LoRA × QLoRA × completo, 3 seeds) em `model_adaptation/`.
- ✅ Harness de avaliação único, tool-call accuracy, juiz plugável e fila de avaliação humana.
- ✅ Tracing do fluxo do agente (`observability/agent_tracing.py`) com sink JSONL local real.

**Concluído na v1.1:**
- ✅ Software Factory SDD (`software_factory/`) com 53 testes e demo ponta a ponta.

**Próximos da adaptação de modelo / avaliação:**
- Repetir o experimento com um modelo maior e uma tarefa não sintética; medir a causa de o pico de VRAM do
  QLoRA não ficar abaixo do LoRA; medir tempo/latência com a GPU dedicada (hoje compartilhada).
- Trocar o juiz determinístico (sobreposição lexical) por um juiz semântico quando houver chave de API.

**Próximos da Software Factory:**
- Rodar o mesmo fluxo com `ClaudeProvider` real (3 execuções independentes, custo e variação medidos).
- Runner em container sem rede e usuário não root; integração com PR real via GitHub (sem merge automático).

**Concluído em sessão anterior:**
- ✅ Golden-set reprodutível, pipeline real RAGAS/DeepEval, fallback de tracing local, 35 testes novos,
  2 bugs reais corrigidos em `run_deepeval`.

**Depende de terceiros / configuração:**
- Rotacionar `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` no `.env` para obter os *scores* reais de
  faithfulness/answer_relevancy/context_recall/hallucination (infraestrutura já pronta para isso).
- Credenciais/instâncias reais de MongoDB, Postgres e Neo4j para validar a Memory V2 em produção.
- Langfuse Cloud ou provisionamento do stack self-host (web, worker, Postgres, ClickHouse, Redis,
  MinIO) para tracing gerenciado em vez do fallback local.

**Próximos técnicos (o que seria feito numa v2 da plataforma):**
- Dashboard visual completo (Overview, Agent Graph, Arena Leaderboard, Memory Explorer, Chat).
- Execução distribuída (Kubernetes), colaboração multiusuário (WebSocket).
- Monitoramento avançado (Grafana) e remediação automática.

## ▶️ Como rodar localmente

### 1. Clonar e preparar ambiente

```bash
git clone https://github.com/Yuri-Fernando/OmniMind_AI_OS.git
cd OmniMind_AI_OS
python -m venv venv
```

Linux/macOS: `source venv/bin/activate` · Windows: `venv\Scripts\activate`

```bash
pip install -r requirements.txt
cp .env.example .env
```

Variáveis relevantes no `.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `LANGFUSE_PUBLIC_KEY`,
`MONGODB_URI`, `POSTGRES_DSN`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.

### 2. Rodar os testes

```bash
pytest evaluation/ rag/tests/ -q
```

Executado nesta revisão: **40/40 passando** em 70,02s.

### 3. Rodar a avaliação real (RAGAS/DeepEval + tracing)

```bash
python -m evaluation.run_all
```

Gera `evaluation/reports/eval_<timestamp>.{json,md}`. Com uma `OPENAI_API_KEY` válida, produz scores
reais de RAGAS/DeepEval; sem uma chave válida, documenta o erro de autenticação como resultado real
(não simula um score).

### 3b. Software Factory SDD (sem rede e sem chave)

```bash
python -m pytest -q -p no:cacheprovider software_factory/tests
python -m software_factory demo --workspace "<pasta fora de Drive/OneDrive>" --auto-approve
```

Executado nesta revisão: 53/53 e demo em `PR_READY` (Windows, Python 3.10). Fluxo com gates manuais em
[software_factory/README.md](software_factory/README.md).

### 4. Memory V2 (opcional, requer bancos reais)

```bash
pip install -r requirements_v2.txt
```

Ver `notebooks/memory_databases_v2.ipynb` para os três backends (MongoDB, pgvector, Neo4j) em uso lado
a lado.

### 5. Exemplo mínimo de uso do runtime

```python
from core.agent_runtime import AgentRuntime
from planning.autonomous_planner import AutonomousPlanner
import asyncio

async def main():
    runtime = AgentRuntime()
    planner = AutonomousPlanner(runtime)
    result = await planner.plan("Analise dados de vendas e gere insights")
    print("Resposta Final:", result.final_answer)

asyncio.run(main())
```

## 📁 Estrutura do repositório

```text
OmniMind_AI_OS/
├── agents/              # main, executor, rag, tool, planner, reflection
├── core/                # agent_runtime, orchestration_graph, router, config
├── planning/            # goal_manager, autonomous_planner, task_decomposer
├── reasoning/           # reasoning_engine, chain_of_thought, tree_of_thoughts
├── reflection/          # self_reflection_agent, answer_critic
├── memory/              # short/vector/long-term V1 + *_v2.py (Mongo/pgvector/Neo4j)
├── rag/                 # rag_pipeline, chunking, embeddings, graph_rag.py, tests/
├── knowledge_graph/     # entity_extractor, graph_builder, graph_retriever
├── tools/                # tool_registry, web_search, code_executor, etc.
├── skills/               # skill_registry, skill_loader, skill_learning
├── evaluation/           # golden_dataset, ragas_eval, deepeval_tests, run_all.py, harness.py, tool_call_accuracy.py,
│                         # llm_judge.py, human_eval.py, agent_golden.py, tests/, reports/
├── learning/             # feedback_loop, experience_buffer
├── arena/                # arena_runner, agent_arena, leaderboard
├── safety/               # prompt_injection_guard, content_filter, policy_engine
├── observability/        # langfuse_tracing, agent_tracing (v1.2), telemetry, traces/traces.jsonl
├── model_adaptation/     # LoRA/QLoRA/completo: datasets/, training/, inference/, evaluation/, results/ (v1.2)
├── software_factory/     # SDD: orchestrator, gates, roles, llm/, samples/, tests/ (v1.1)
├── voice/                # speech_to_text, text_to_speech
├── api/                  # server, routes
├── infra/                # config, env_config, dockerfile
├── docs/adr/             # ADR 0001-0003 (software factory, gates, adaptação de modelo)
├── docker-compose.langfuse.yml, .env.langfuse.example   # stack Langfuse self-host (nunca executada)
├── notebooks/, docs/
├── architecture_readme.md, estrutura.md
├── requirements.txt, requirements_v2.txt
├── .env.example
└── README.md
```

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [architecture_readme.md](architecture_readme.md) | Arquitetura e diagramas |
| [estrutura.md](estrutura.md) | Fluxos detalhados |
| [rag/GRAPH_RAG.md](rag/GRAPH_RAG.md) | Arquitetura do GraphRAG e caso de teste relacional |
| [CHANGELOG.md](CHANGELOG.md) | Mudanças por versão, formato Keep a Changelog |
| [WORKLOG.md](WORKLOG.md) | Relato cronológico de cada sessão, com números medidos |
| [software_factory/README.md](software_factory/README.md) | Software Factory SDD: fluxo, gates, artefatos, como rodar, o que a demo prova |
| [docs/adr/0001](docs/adr/0001-software-factory-dentro-do-omnimind.md) | Por que a fábrica é módulo do OmniMind e o que reusa |
| [docs/adr/0002](docs/adr/0002-software-factory-gates-e-isolamento.md) | Gates, isolamento por worktree, runner externo e limites |
| [docs/adr/0003](docs/adr/0003-model-adaptation.md) | Escolhas e limites da adaptação de modelo (LoRA/QLoRA/completo) |
| [model_adaptation/README.md](model_adaptation/README.md) | Como rodar o experimento; [REPORT.md](model_adaptation/results/REPORT.md) com a tabela medida |
| [evaluation/reports/harness_golden.md](evaluation/reports/harness_golden.md) | Relatório do harness sobre o golden de agentes |
| `docs/` | Documentação técnica adicional |
| `notebooks/` | Exemplos e experimentos, incluindo `memory_databases_v2.ipynb` |

## ⚠️ Limitações

- **Chaves de API expiradas:** `OPENAI_API_KEY` e `ANTHROPIC_API_KEY` no `.env` deste projeto estão
  inválidas/expiradas nesta sessão (confirmado com chamada mínima real a cada provedor). Por isso os
  scores de RAGAS/DeepEval desta execução vieram como erro de autenticação (`401`), não como número.
  A infraestrutura está pronta e produz números reais assim que uma chave válida for configurada.
- **Langfuse não configurado:** sem Cloud ou self-host configurado, o tracing cai no fallback real em
  arquivo local (`observability/traces/traces.jsonl`) — funcional, mas não é o backend gerenciado.
- **Memory V2 não validada em produção:** os backends MongoDB/pgvector/Neo4j foram implementados atrás
  da mesma interface da V1, mas não foram validados nesta sessão contra instâncias reais dos três
  bancos (sem credenciais/infra disponíveis).
- Dashboard visual completo, execução distribuída (Kubernetes), colaboração multiusuário em tempo real e
  monitoramento avançado (Grafana) permanecem no roadmap — não são apresentados como capacidades concluídas.
- **Adaptação de modelo (v1.2):** vale para um modelo de 0,5 B, uma tarefa sintética de roteamento de
  ferramentas e uma GPU de 8 GB compartilhada; LoRA, QLoRA e ajuste completo não se distinguem (diferença
  ≤ 0,02, dentro do desvio entre seeds ≈ 0,03). Tempos e latências não são comparáveis entre variantes.
  O QLoRA economizou memória nos pesos e na inferência, mas não no pico de treino (não medi a causa).
- **Harness (v1.2):** o juiz padrão é determinístico (sobreposição lexical), não semântico; o juiz Claude é
  opt-in (`OMNIMIND_ALLOW_CLOUD_JUDGE=1`) e foi testado só com cliente falso. RAGAS/DeepEval ficam
  `NOT_RUN` sem `OPENAI_API_KEY`.
- **Tracing (v1.2):** o `trace_run` legado chama `Langfuse.trace()`, que não existe no SDK instalado
  (v3); foi mantido intacto e o novo `agent_tracing.py` usa a API correta. Langfuse real:
  `BLOCKED_BY_CONFIGURATION`.
- **Software Factory:** as respostas do `MockLLM` na demo são fixtures escritas à mão — a demo prova
  gates, isolamento e verificação, não geração autônoma de código. `ClaudeProvider` foi testado só com
  cliente falso. Rede no runner é bloqueada em melhor esforço (proxy morto + ambiente sem segredos),
  não por sandbox de SO; execução de tarefas paralelas é validada mas feita em sequência.
- `Agent Arena` e a listagem de agentes (`gpt4_agent`, `claude_agent`, `llama_agent`) no exemplo de uso
  são ilustrativos da API; não representam um benchmark já executado contra esses três provedores
  nesta sessão.

## Status

🟢 **Concluído no escopo do núcleo — Versão 1.2.** Software Factory SDD com 53 testes e demo em
`PR_READY` (Claude real ainda não executado); ajuste fino LoRA/QLoRA executado e medido, harness de
avaliação único e tracing do agente implementados e testados. Memory V2 e GraphRAG implementados e testados.
RAGAS/DeepEval (scores) e Langfuse real seguem bloqueados por configuração externa (`OPENAI_API_KEY`
válida e stack self-host), não por problema de código.

## Contexto / Observações

Este é um projeto de P&D/portfólio pessoal de Yuri Fernando Dubbern — não afiliado a nenhuma empresa,
cliente ou produto comercial em produção. Os números de latência e contagem de testes citados foram
medidos localmente nesta máquina; onde um número não pôde ser obtido por falta de credencial válida,
isso está documentado explicitamente como limitação (ver [⚠️ Limitações](#️-limitações)), nunca
preenchido com uma estimativa.

## 🔗 Projetos Relacionados

Este repositório faz parte do portfólio público de Yuri Fernando Dubbern
([github.com/Yuri-Fernando](https://github.com/Yuri-Fernando)). Não há dependência de código obrigatória
entre os repositórios — cada um documenta seu próprio escopo, resultados e limitações.

| Projeto | Relação |
|---|---|
| [AegisLLM](https://github.com/Yuri-Fernando/AegisLLM) | Gateway de segurança e governança de IA: o tipo de controle que este runtime de agentes pode consumir |
| [RealTime-ML-Inference-Lab](https://github.com/Yuri-Fernando/RealTime-ML-Inference-Lab) | Serving de inferência em GPU (batching, quantização): onde um modelo ajustado aqui poderia ser servido |
| [OCR](https://github.com/Yuri-Fernando/OCR) | Motor documental e de áudio que pode alimentar o RAG deste runtime |
| [Engineering-CAD-AI](https://github.com/Yuri-Fernando/Engineering-CAD-AI) | Mesmo princípio de plano tipado + aprovação humana aplicado a desenhos CAD |

## 🤖 Autor

**Yuri Fernando Dubbern**

AI/ML Engineer · Generative AI · Agentic AI · Data Engineering · Intelligent Automation

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

## Licença

Este repositório não contém um arquivo `LICENSE` nesta revisão. Todo o conteúdo é apresentado para
fins de pesquisa, estudo e portfólio (ver [Contexto / Observações](#contexto--observações)).
