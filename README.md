# OmniMind AI OS — Sistema de Orquestração Inteligente de Agentes

### Agentic AI Infrastructure · Multi-Agent Systems · RAG · Planning · Memory · Evaluation

## Status

🟢 **Concluído — Versão 1.0 / P&D em Agentic AI**

O **OmniMind AI OS** é uma plataforma modular de orquestração de agentes de IA desenvolvida para resolução de tarefas complexas por meio de **planning automático, coordenação multiagente, RAG, ferramentas dinâmicas, memória, avaliação, reflexão e observabilidade**.

O núcleo atual integra múltiplos componentes de Agentic AI em uma arquitetura modular, incluindo planejamento, execução, conhecimento, ferramentas, memória, avaliação, segurança e observabilidade.

> O core da versão atual está concluído. O roadmap representa evoluções futuras da infraestrutura.

---

## Sobre o Projeto

O OmniMind AI OS implementa um ciclo de execução orientado por objetivos:

```text
Goal
 ↓
Plan
 ↓
Execute
 ↓
Learn
 ↓
Improve
 ↓
Final Answer
```

A arquitetura foi desenvolvida para permitir que diferentes agentes especializados cooperem na resolução de tarefas, utilizando conhecimento recuperado, ferramentas externas, memória e mecanismos de avaliação.

---

## Funcionalidades

### Multi-Agent Coordination

- Roteamento entre agentes especializados;
- Registry de agentes;
- Protocolo de comunicação;
- Execução coordenada entre diferentes responsabilidades.

### Autonomous Planning

- Goal Manager;
- Planejamento automático;
- Decomposição de tarefas;
- Planos hierárquicos;
- Otimização da ordem de execução.

### RAG

- Ingestão de documentos;
- Chunking;
- Embeddings;
- Busca semântica;
- Vector Store;
- Recuperação contextual.

### Dynamic Tools

- Registro de ferramentas;
- Auto-discovery;
- Execução de APIs;
- Web Search;
- Web Scraping;
- Code Execution;
- File Reader;
- Calculator;
- Weather API.

### Reasoning & Reflection

- Reasoning Engine;
- Estratégias CoT e ToT;
- Reflection Agent;
- Answer Critic;
- Failure Analysis;
- Prompt Optimization.

### Memory

- Short-Term Memory;
- Vector Memory (Chroma local; **V2: Postgres + pgvector**);
- Long-Term Memory (JSON local; **V2: MongoDB**);
- Knowledge Graph (dict em memória; **V2: Neo4j**);
- Memory Manager.

### Evaluation

- RAGAS;
- DeepEval;
- Métricas customizadas;
- Benchmark de LLMs;
- Agent Arena;
- Leaderboard.

### Segurança

- Prompt Injection Guard;
- Content Filter;
- Policy Engine;
- Guardrails.

### Observabilidade

- Langfuse;
- OpenTelemetry;
- Structured Logs;
- Telemetry;
- Execution Tracing.

### Multimodalidade

- Speech-to-Text;
- Text-to-Speech;
- Whisper;
- ElevenLabs;
- Processamento de vídeo;
- Extração de áudio;
- Transcrição.

---

# Arquitetura

```text
                              USER
                                │
                                ▼
                       Interaction Layer
             ┌─────────────────────────────────┐
             │ API │ Notebook │ Voice │ CLI   │
             └────────────────┬────────────────┘
                              │
                              ▼
                      Goal Management Layer
             ┌─────────────────────────────────┐
             │ Goal Manager                    │
             │ Autonomous Planner              │
             │ Task Decomposer                 │
             └────────────────┬────────────────┘
                              │
                              ▼
                    Multi-Agent Coordination
             ┌─────────────────────────────────┐
             │ Agent Router                    │
             │ Agent Registry                  │
             │ Communication Protocol          │
             └────────────────┬────────────────┘
                              │
                              ▼
                      Agent Execution
             ┌─────────────────────────────────┐
             │ RAG Agent                       │
             │ Tool Agent                      │
             │ Executor Agent                  │
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
                              │
                              ▼
                         World Model
                              │
                              ▼
                         Learning Loop
                              │
                              ▼
                      Evaluation Layer
                              │
                              ▼
                    Observability Layer
```

---

# Ciclo de Execução

```text
User Request
     ↓
Goal Manager
     ↓
Autonomous Planner
     ↓
Task Decomposer
     ↓
Multi-Agent Router
     ├── RAG Agent
     ├── Tool Agent
     └── Executor Agent
     ↓
Reasoning Engine
     ↓
Reflection Agent
     ↓
Self-Improvement
     ↓
Memory Update
     ↓
Evaluation Pipeline
     ↓
Observability
     ↓
Final Answer
```

---

# Componentes Principais

## Goal Management

```text
Goal Manager
Autonomous Planner
Task Decomposer
```

Responsáveis por transformar objetivos em estratégias e subtarefas executáveis.

## Agent Layer

```text
Main Agent
Planner Agent
RAG Agent
Tool Agent
Executor Agent
Reflection Agent
```

## Memory

```text
Short-Term Memory
Vector Memory
Long-Term Memory
Memory Manager
```

## Knowledge

```text
RAG Pipeline
Vector Store
Document Ingestion
Retriever
Knowledge Graph
```

## Tools & Skills

```text
Tool Registry
Tool Loader
Auto Tool Discovery
Skill Registry
Skill Loader
Skill Selector
Skill Learning
```

## Evaluation

```text
RAGAS
DeepEval
Agent Metrics
Auto Evaluation
LLM Benchmark
Custom Metrics
Agent Arena
```

## Safety & Reliability

```text
Prompt Injection Guard
Content Filter
Policy Engine
Guardrails
```

## Observability

```text
Langfuse
OpenTelemetry
Telemetry
Structured Logging
Execution Tracing
```

---

# Estrutura do Projeto

```text
OmniMind_AI_OS/
│
├── agents/
│   ├── main_agent.py
│   ├── executor_agent.py
│   ├── rag_agent.py
│   ├── tool_agent.py
│   ├── planner_agent.py
│   ├── reflection_agent.py
│   └── _llm_factory.py
│
├── agents_local/
│
├── core/
│   ├── agent_runtime.py
│   ├── orchestration_graph.py
│   ├── state_manager.py
│   ├── router.py
│   └── config.py
│
├── planning/
│   ├── autonomous_planner.py
│   ├── goal_manager.py
│   └── task_decomposer.py
│
├── reasoning/
│   ├── reasoning_engine.py
│   ├── chain_of_thought.py
│   └── tree_of_thoughts.py
│
├── reflection/
│   ├── self_reflection_agent.py
│   ├── answer_critic.py
│   └── improvement_engine.py
│
├── self_improvement/
│   ├── prompt_optimizer.py
│   ├── failure_analysis.py
│   └── self_reflection.py
│
├── memory/
│   ├── short_term_memory.py
│   ├── vector_memory.py
│   ├── long_term_memory.py
│   └── memory_manager.py
│
├── rag/
│   ├── rag_pipeline.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── retriever.py
│   └── load_docs.py
│
├── knowledge/
│   ├── vector_store.py
│   ├── database.py
│   ├── document_ingestion.py
│   ├── retriever.py
│   └── embeddings.py
│
├── knowledge_graph/
│   ├── entity_extractor.py
│   ├── graph_builder.py
│   └── graph_retriever.py
│
├── vector_db/
│
├── tools/
│   ├── tool_registry.py
│   ├── tool_loader.py
│   ├── auto_tool_discovery.py
│   ├── web_search.py
│   ├── web_scraper.py
│   ├── calculator.py
│   ├── code_executor.py
│   ├── weather_api.py
│   └── file_reader.py
│
├── skills/
│   ├── skill_registry.py
│   ├── skill_loader.py
│   ├── skill_selector.py
│   └── skill_learning.py
│
├── builtin/
│
├── evaluation/
│   ├── ragas_eval.py
│   ├── deepeval_tests.py
│   ├── agent_metrics.py
│   ├── auto_eval_pipeline.py
│   ├── benchmark_llm.py
│   └── metrics.py
│
├── learning/
│   ├── feedback_loop.py
│   ├── experience_buffer.py
│   └── reinforcement_learning.py
│
├── cognition/
│   ├── world_model.py
│   ├── belief_state.py
│   └── environment_context.py
│
├── arena/
│   ├── arena_runner.py
│   ├── agent_arena.py
│   ├── leaderboard.py
│   └── tasks_dataset.py
│
├── agent_graph/
│
├── safety/
│   ├── prompt_injection_guard.py
│   ├── content_filter.py
│   └── policy_engine.py
│
├── guardrails/
│
├── collaboration/
│
├── observability/
│   ├── langfuse_tracing.py
│   ├── telemetry.py
│   ├── tracing.py
│   └── logging.py
│
├── ingestion/
│   └── video/
│
├── processing/
│   └── transcription/
│
├── voice/
│   ├── speech_to_text.py
│   ├── text_to_speech.py
│   ├── stt_whisper.py
│   ├── tts_elevenlabs.py
│   └── tts_local.py
│
├── api/
│   ├── server.py
│   └── routes.py
│
├── infra/
│   ├── config.py
│   ├── env_config.py
│   └── dockerfile
│
├── simulation/
│
├── notebooks/
├── docs/
├── log/
├── data/
├── input/
├── ffmpeg/
│
├── architecture_readme.md
├── estrutura.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Como Executar

## 1. Clonar

```bash
git clone https://github.com/Yuri-Fernando/OmniMind_AI_OS.git
cd OmniMind_AI_OS
```

## 2. Criar ambiente virtual

```bash
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

## 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Exemplo:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
LANGFUSE_PUBLIC_KEY
MONGODB_URI
```

---

# Sistema Principal

```python
from core.agent_runtime import AgentRuntime
from planning.autonomous_planner import AutonomousPlanner
import asyncio

async def main():

    runtime = AgentRuntime()

    planner = AutonomousPlanner(runtime)

    result = await planner.plan(
        "Analise dados de vendas e gere insights"
    )

    print("Resposta Final:", result.final_answer)
    print("Agentes Usados:", result.agents_used)
    print("Tempo Total:", result.execution_time)

asyncio.run(main())
```

---

# RAG Agent

```python
from agents.rag_agent import RAGAgent
import asyncio

async def retrieve_knowledge():

    rag = RAGAgent()

    rag.ingest_documents("docs/")

    answer = await rag.query(
        "Como funciona o sistema?"
    )

    print(answer)

asyncio.run(retrieve_knowledge())
```

---

# Dynamic Tool Agent

```python
from agents.tool_agent import ToolAgent
import asyncio

async def execute_tools():

    tool_agent = ToolAgent()

    tool_agent.register_tool(
        "my_api",
        my_custom_function
    )

    result = await tool_agent.execute(
        "Pesquise sobre tendências de IA"
    )

    print(result)

asyncio.run(execute_tools())
```

---

# Agent Arena

```python
from arena.arena_runner import ArenaRunner
import asyncio

async def run_arena():

    arena = ArenaRunner()

    results = await arena.run_competition(
        agents=[
            "gpt4_agent",
            "claude_agent",
            "llama_agent"
        ],
        tasks=[
            "Qual é a capital da França?",
            "Explique quantum computing",
            "Crie um plano de marketing"
        ]
    )

    print(arena.leaderboard())

asyncio.run(run_arena())
```

---

# Evaluation

```python
from evaluation.ragas_eval import RAGASEvaluator
from evaluation.deepeval_tests import DeepEvalSuite
import asyncio

async def evaluate():

    ragas_eval = RAGASEvaluator()

    rag_score = await ragas_eval.evaluate(
        question="O que é RAG?",
        contexts=["doc1", "doc2"],
        answer="Resposta do agente"
    )

    deepeval = DeepEvalSuite()

    deep_score = await deepeval.run_all_tests()

    print(f"RAGAS Score: {rag_score}")
    print(f"DeepEval Score: {deep_score}")

asyncio.run(evaluate())
```

---

# Self-Improvement

```python
from self_improvement.prompt_optimizer import PromptOptimizer
from learning.feedback_loop import FeedbackLoop
import asyncio

async def improve():

    optimizer = PromptOptimizer()
    feedback = FeedbackLoop()

    improved_prompt = await optimizer.optimize(
        original_prompt="Explique IA em uma sentença",
        evaluation_metric="clarity"
    )

    await feedback.process_feedback(
        result="resposta anterior",
        user_feedback="muito técnico",
        action="simplificar"
    )

asyncio.run(improve())
```

---

# Interface Visual

Instalação:

```bash
pip install streamlit plotly pandas
```

Execução:

```bash
streamlit run ui/dashboard.py
```

A interface contempla estrutura para:

- Overview;
- Status dos agentes;
- Agent Graph;
- Arena Leaderboard;
- Memory Explorer;
- Chat Interface.

---

# Voice Interface

```python
from voice.speech_to_text import WhisperSTT
from voice.text_to_speech import ElevenLabsTTS
from agents.main_agent import MainAgent
import asyncio

async def voice_conversation():

    stt = WhisperSTT()
    tts = ElevenLabsTTS()
    agent = MainAgent()

    user_input = await stt.transcribe(
        "input/user_audio.wav"
    )

    response = await agent.process(user_input)

    await tts.synthesize(
        response,
        "output/response.mp3"
    )

asyncio.run(voice_conversation())
```

---

# Tecnologias

| Camada | Tecnologias |
|---|---|
| Linguagem | Python |
| LLMs | Claude · GPT-4 · Llama |
| Orquestração | LangChain · LangGraph |
| Vector DB | Chroma · Pinecone |
| API | FastAPI |
| Evaluation | RAGAS · DeepEval |
| Observabilidade | Langfuse · OpenTelemetry |
| Data | Pandas · NumPy |
| Async | AsyncIO · Concurrent.futures |
| Interface | Streamlit |
| Voice | Whisper · ElevenLabs |
| Infraestrutura | Docker |

---

# O que este projeto demonstra

- Engenharia de sistemas de IA agentiva;
- Multi-Agent Systems;
- Autonomous Planning;
- Task Decomposition;
- RAG;
- Dynamic Tool Execution;
- Tool Discovery;
- Multi-Tier Memory;
- Knowledge Graphs;
- Reasoning Orchestration;
- Reflection;
- Prompt Optimization;
- Evaluation de LLMs;
- Agent Benchmarking;
- Guardrails;
- Observabilidade;
- Processamento multimodal;
- APIs assíncronas;
- Arquitetura modular.

---

# Features Implementadas

- ✅ Multi-Agent Coordination
- ✅ Autonomous Planning
- ✅ RAG Pipeline
- ✅ Dynamic Tool Execution
- ✅ Advanced Reasoning
- ✅ Reflection
- ✅ Self-Improving Prompts
- ✅ Multi-Tier Memory
- ✅ Evaluation Pipeline
- ✅ Agent Arena
- ✅ Safety & Guardrails
- ✅ Learning from Feedback
- ✅ Voice Interface
- ✅ Video Processing
- ✅ Knowledge Graph
- ✅ World Model
- ✅ Observability

---

# Testes

### Testes unitários

```bash
pytest tests/ -v
```

### Agent Arena

```bash
python -m arena.arena_runner
```

### Evaluation

```bash
python -m evaluation.ragas_eval
```

---

# Limitações Atuais

O projeto possui uma arquitetura ampla e modular, mas algumas capacidades ainda representam extensões da infraestrutura:

- Dashboard visual completo;
- Fine-tuning automatizado;
- Execução distribuída;
- Kubernetes;
- Knowledge Graph persistente em infraestrutura dedicada;
- Colaboração multiusuário em tempo real;
- Monitoramento avançado com Grafana;
- Remediação automática.

Esses itens fazem parte do roadmap de evolução da plataforma.

---

# Roadmap

## Fase 1 — Interface Visual

- [ ] Dashboard completo
- [ ] Agent Monitor
- [ ] Agent Graph
- [ ] Arena Leaderboard
- [ ] Memory Explorer
- [ ] Chat Interface

## Fase 2 — Fine-Tuning

- [ ] LoRA
- [ ] Dataset pipeline
- [ ] Feedback-driven training
- [ ] Prompt Optimization v2
- [ ] A/B testing

## Fase 3 — Distributed Execution

- [ ] Multi-Machine Orchestration
- [ ] Load Balancing
- [ ] Distributed State
- [ ] Kubernetes
- [ ] Autoscaling

## Fase 4 — Multimodal

- [ ] Vision Models
- [ ] OCR
- [ ] Scene Detection
- [ ] Enhanced Video Processing

## Fase 5 — Knowledge

- [ ] Neo4j
- [ ] Temporal Reasoning
- [ ] Knowledge Enrichment
- [ ] Continuous Ingestion

## Fase 6 — Collaboration

- [ ] WebSocket
- [ ] Multi-user Support
- [ ] Shared Workspace
- [ ] Shared Memory

## Fase 7 — Advanced Monitoring

- [ ] Grafana
- [ ] Resource Monitoring
- [ ] Automatic Alerts
- [ ] Performance Degradation Detection
- [ ] Automatic Remediation

---

# Documentação

- `architecture_readme.md` — arquitetura e diagramas;
- `estrutura.md` — fluxos detalhados;
- `docs/` — documentação técnica;
- `notebooks/` — exemplos e experimentos.

---

## 🧬 Memory System V2 — MongoDB + pgvector + Neo4j

A V1 do Memory System roda inteira sobre armazenamento local: `LongTermMemory` grava um
JSON em disco, `VectorMemory` usa Chroma via SQLite, e o `KnowledgeGraphBuilder` guarda nós
e arestas em dicionários Python em memória (perdidos ao final do processo). Funciona bem
para rodar o agente localmente, mas não escala para múltiplas instâncias nem sobrevive fora
do processo.

A V2 substitui cada um desses três backends por um banco de dados real, **mantendo a mesma
interface pública** de cada componente — nenhum agente que já consome `MemoryManager`,
`LongTermMemory`, `VectorMemory` ou `KnowledgeGraphBuilder` precisa mudar:

| Componente | V1 (local) | V2 (banco de dados) | Arquivo V2 |
|---|---|---|---|
| Long-Term Memory | JSON em disco | **MongoDB** (upsert por `key`, índice em `category`) | `memory/long_term_memory_mongo_v2.py` |
| Vector Memory | Chroma (SQLite local) | **Postgres + pgvector** (índice HNSW, cosine) | `memory/vector_memory_pgvector_v2.py` |
| Knowledge Graph | dict em memória + BFS Python | **Neo4j** (nós/relações reais + `shortestPath` em Cypher) | `knowledge_graph/graph_builder_neo4j_v2.py` |
| Orquestração | `memory/memory_manager.py` | `memory/memory_manager_v2.py` (mesma API, backends V2) | `memory/memory_manager_v2.py` |

O README já citava `MONGODB_URI` como variável de ambiente opcional ("se usar sincronização
em nuvem") — a V2 é a implementação que dá efeito real a essa variável, e adiciona
`POSTGRES_DSN`, `NEO4J_URI`, `NEO4J_USER` e `NEO4J_PASSWORD` para os outros dois backends.

Ver `notebooks/memory_databases_v2.ipynb` para os três backends em uso lado a lado, e
`requirements_v2.txt` (estende `requirements.txt` com `pymongo`, `psycopg2-binary`,
`pgvector` e `neo4j`).

---

# Status Final

🟢 **Concluído — Versão 1.0**

O core atual do OmniMind AI OS está implementado e documentado, reunindo:

- ✅ Orquestração multiagente;
- ✅ Planejamento autônomo;
- ✅ RAG;
- ✅ Ferramentas dinâmicas;
- ✅ Reasoning;
- ✅ Reflection;
- ✅ Self-Improvement;
- ✅ Memória multi-tier;
- ✅ Evaluation;
- ✅ Agent Arena;
- ✅ Safety & Guardrails;
- ✅ Observabilidade;
- ✅ Voice;
- ✅ Video Processing;
- ✅ Knowledge Graph;
- ✅ World Model;
- ✅ API;
- ✅ Arquitetura modular.

O roadmap representa a evolução contínua da infraestrutura, especialmente em **execução distribuída, fine-tuning, colaboração, multimodalidade e observabilidade avançada**.

---

# Licença

MIT License.

---

# Links

- **GitHub:** https://github.com/Yuri-Fernando/OmniMind_AI_OS
- **Docs:** `/docs`
- **Examples:** `/notebooks`

---

# Autor

**Yuri Fernando Dubbern**

AI/ML Engineer · Generative AI · Agentic AI · Data Engineering · Intelligent Automation

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

---

> **OmniMind AI OS é uma infraestrutura experimental de P&D para Agentic AI, organizada para integrar agentes, planejamento, conhecimento, ferramentas, memória, avaliação e observabilidade em uma arquitetura modular e evolutiva.**
