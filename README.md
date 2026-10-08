# 🤖 OmniMind AI OS — Plataforma Modular de Orquestração de Agentes de IA

### Python · LangChain · LangGraph · FastAPI · MongoDB · Postgres/pgvector · Neo4j · RAGAS · DeepEval · Langfuse

![versão](https://img.shields.io/badge/vers%C3%A3o-1.0-4a5563)
![python](https://img.shields.io/badge/python-3.10%2B-4a5563)
![testes](https://img.shields.io/badge/testes-40%2F40-0a8a0a)
![uso](https://img.shields.io/badge/uso-P%26D%20%2F%20portf%C3%B3lio-c8742a)

## Status

🟢 **Concluído no escopo do núcleo — Versão 1.0 / P&D em Agentic AI**

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

### Testes (confirmado nesta revisão)

| Suite | Resultado |
|---|---|
| `pytest evaluation/ rag/tests/` | **40/40 passando** — 70,02s (35 novos de `evaluation/tests/` + 5 pré-existentes de GraphRAG) |

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

**F3 — Interface Visual, Fine-Tuning, Execução Distribuída, Multimodal, Colaboração, Monitoramento
Avançado** ⏳ Planejada — ver detalhamento em [🔮 Próximos Passos](#-próximos-passos).

## 🕓 Histórico e Mudanças

| Versão | O que mudou |
|---|---|
| Unreleased | Golden-set reprodutível, pipeline real de RAGAS/DeepEval, fallback de tracing local, `evaluation/run_all.py`, 35 testes novos; 2 bugs reais corrigidos em `run_deepeval`; limitação de chaves de API expiradas documentada |
| v2 (memory) | Memory System V2: MongoDB + pgvector + Neo4j, mesma interface pública dos backends V1 |
| v2 (GraphRAG) | Composição real de `rag/` + `knowledge_graph/` em `rag/graph_rag.py`, 5 testes com fakes |
| v1.0 | Núcleo: orquestração multiagente, planejamento autônomo, RAG, ferramentas dinâmicas, memória local, reasoning, reflection, segurança, observabilidade |

Ver [CHANGELOG.md](CHANGELOG.md) e [WORKLOG.md](WORKLOG.md) para o detalhamento completo, incluindo o
que rodou de verdade e o que ficou documentado como limitação em cada sessão.

## 🔮 Próximos Passos

**Concluído nesta sessão:**
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
- Fine-tuning (LoRA), execução distribuída (Kubernetes), colaboração multiusuário (WebSocket).
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
├── evaluation/           # golden_dataset, ragas_eval, deepeval_tests, run_all.py, tests/, reports/
├── learning/             # feedback_loop, experience_buffer
├── arena/                # arena_runner, agent_arena, leaderboard
├── safety/               # prompt_injection_guard, content_filter, policy_engine
├── observability/        # langfuse_tracing, telemetry, traces/traces.jsonl
├── voice/                # speech_to_text, text_to_speech
├── api/                  # server, routes
├── infra/                # config, env_config, dockerfile
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
- Dashboard visual completo, fine-tuning automatizado, execução distribuída (Kubernetes), colaboração
  multiusuário em tempo real e monitoramento avançado (Grafana) permanecem no roadmap — não são
  apresentados como capacidades concluídas.
- `Agent Arena` e a listagem de agentes (`gpt4_agent`, `claude_agent`, `llama_agent`) no exemplo de uso
  são ilustrativos da API; não representam um benchmark já executado contra esses três provedores
  nesta sessão.

## Status

🟢 **Concluído no escopo do núcleo — Versão 1.0.** Memory V2 e GraphRAG implementados e testados.
Evaluation e Observability passaram de código nunca executado para infraestrutura real e testada
(40/40 testes, 8 execuções reais, 24 jobs RAGAS/DeepEval reais) — bloqueada apenas por chave de API
expirada, uma dependência de configuração externa, não um problema de código.

## Contexto / Observações

Este é um projeto de P&D/portfólio pessoal de Yuri Fernando Dubbern — não afiliado a nenhuma empresa,
cliente ou produto comercial em produção. Os números de latência e contagem de testes citados foram
medidos localmente nesta máquina; onde um número não pôde ser obtido por falta de credencial válida,
isso está documentado explicitamente como limitação (ver [⚠️ Limitações](#️-limitações)), nunca
preenchido com uma estimativa.

## 🔗 Projetos Relacionados

Este repositório faz parte do portfólio público de Yuri Fernando Dubbern
([github.com/Yuri-Fernando](https://github.com/Yuri-Fernando)). Não há dependência de código entre os
repositórios do portfólio — cada um documenta seu próprio escopo, resultados e limitações de forma
independente.

## 🤖 Autor

**Yuri Fernando Dubbern**

AI/ML Engineer · Generative AI · Agentic AI · Data Engineering · Intelligent Automation

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

## Licença

Este repositório não contém um arquivo `LICENSE` nesta revisão. Todo o conteúdo é apresentado para
fins de pesquisa, estudo e portfólio (ver [Contexto / Observações](#contexto--observações)).
