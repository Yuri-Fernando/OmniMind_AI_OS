# 🤖 AI Agent OS — Sistema de Orquestração Inteligente de Agentes

Um **sistema operacional de IA** completo que orquestra múltiplos agentes para resolução de tarefas complexas com planning automático, RAG, tools dinâmicas, raciocínio avançado, auto-melhoria contínua e observabilidade enterprise.

---

## 🎯 O Que É

**AI Agent OS** é uma plataforma que implementa um ciclo completo:

```
Goal → Plan → Execute → Learn → Improve → Final Answer
```

Sistema modular e escalável que integra:
- ✅ **Multi-Agent Coordination** — múltiplos agentes especializados
- ✅ **Autonomous Planning** — decomposição automática de tarefas
- ✅ **RAG Pipeline** — recuperação de conhecimento em documentos
- ✅ **Dynamic Tools** — execução de APIs externas e ferramentas
- ✅ **Reasoning Engine** — CoT (Chain of Thought) / ToT (Tree of Thoughts)
- ✅ **Self-Improvement** — otimização automática de prompts
- ✅ **Memory System** — short-term, vector, long-term
- ✅ **Evaluation Pipeline** — RAGAS, DeepEval, métricas customizadas
- ✅ **Observability** — Langfuse, telemetry, logs estruturados

---

## 🏗️ Arquitetura

```
                              USER
                              │
                              ▼
                      Interaction Layer
            ┌──────────────────────────────┐
            │ API │ Notebook │ Voice │ CLI │
            └──────────────────────────────┘
                              │
                              ▼
                    Goal Management Layer
            ┌────────────────────────────┐
            │ • Goal Manager             │
            │ • Autonomous Planner       │
            │ • Task Decomposer          │
            └────────────────────────────┘
                              │
                              ▼
                  Multi-Agent Coordination
          ┌────────────────────────────────┐
          │ • Agent Router                 │
          │ • Agent Registry               │
          │ • Communication Protocol       │
          └────────────────────────────────┘
                              │
                              ▼
                      Agent Execution Layer
      ┌──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼
  RAG Agent      Tool Agent    Executor Agent
      │              │              │
      ▼              ▼              ▼
Knowledge         APIs          Skill
Retrieval      Tool Discovery   Execution
      │              │              │
      └───────┬──────┴──────┬───────┘
              ▼             ▼
       Reasoning Engine   Skill Selector
       (CoT / ToT)
              │
              ▼
         Reflection Agent
              │
              ▼
      Self-Improvement Engine
   (Prompt Optimizer / Failure Analysis)
              │
              ▼
          Memory System
 ┌──────────┬───────────┬──────────┐
 ▼          ▼           ▼
Short-Term  Vector    Long-Term
Memory      Memory     Memory
              │
              ▼
          World Model
      (Cognição do Agente)
              │
              ▼
          Learning Loop
    (Feedback / RL / Experience)
              │
              ▼
        Evaluation Layer
    (RAGAS / DeepEval / Metrics)
              │
              ▼
      Observability Layer
    (Langfuse / Logs / Telemetry)
```

---

## 📦 Componentes Principais

### 🎯 **Goal Management**
- **Goal Manager** — Define objetivos do usuário
- **Autonomous Planner** — Planeja estratégia automaticamente
- **Task Decomposer** — Decompõe em tarefas menores

### 🔀 **Multi-Agent System**
- **RAG Agent** — Busca conhecimento em vetores/documentos
- **Tool Agent** — Executa APIs externas e ferramentas dinâmicas
- **Executor Agent** — Executa skills e computação

### 🧠 **Raciocínio Avançado**
- **Reasoning Engine** — Chain of Thought (CoT) / Tree of Thoughts (ToT)
- **Reflection Agent** — Avalia respostas e aplica auto-reflexão
- **Self-Improvement** — Otimiza prompts e analisa falhas

### 💾 **Memory System**
- **Short-Term Memory** — Histórico recente de conversas
- **Vector Memory** — Embeddings semânticos para recuperação
- **Long-Term Memory** — Perfil persistente e conhecimento

### 🌍 **World Model**
- Crenças do agente sobre o ambiente
- Estado atual do sistema
- Histórico de experiências

### 📊 **Evaluation & Observability**
- **RAGAS** — Avaliação de RAG
- **DeepEval** — Avaliação de LLM
- **Langfuse** — Tracing e observabilidade
- **Custom Metrics** — Métricas customizadas

### 🏆 **Agent Arena**
Competição entre agentes para avaliar performance:
```
Tasks → Agents Generate Answers → Evaluation → Scoring → Leaderboard
```

---

## 📁 Estrutura de Diretórios

```
Agente AIOS/
├── agents/                  # Definições de agentes
├── core/                    # Engine central
├── planning/                # Planejamento autônomo
├── task_decomposer/         # Decomposição de tarefas
├── rag/                     # RAG Pipeline
├── knowledge/               # Base de conhecimento
├── knowledge_graph/         # Gráfico de conhecimento
├── memory/                  # Sistemas de memória
├── reasoning/               # Reasoning engines (CoT/ToT)
├── reflection/              # Reflection agent
├── self_improvement/        # Otimização de prompts
├── learning/                # Learning loop
├── skills/                  # Skills executáveis
├── tools/                   # Tool registry
├── evaluation/              # RAGAS, DeepEval, metrics
├── arena/                   # Agent Arena
├── agent_graph/             # Grafo de agentes
├── cognition/               # Cognição e world model
├── collaboration/           # Comunicação entre agentes
├── observability/           # Langfuse, telemetry
├── guardrails/              # Safety e prompt injection
├── api/                     # FastAPI endpoints
├── ingestion/               # Document/video ingestion
├── infra/                   # Infraestrutura
└── notebooks/               # Exemplos e testes
```

---

## 🚀 Como Usar

### 1️⃣ Instalação

```bash
# Clone
git clone https://github.com/Yuri-Fernando/OmniMind_AI_OS.git
cd OmniMind_AI_OS

# Instale dependências
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Adicione: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
```

### 2️⃣ Rodar Sistema

```python
from core.agent_runtime import AgentRuntime
from planning.autonomous_planner import AutonomousPlanner

# Inicialize runtime
runtime = AgentRuntime()

# Use planner para resolver tarefa
planner = AutonomousPlanner(runtime)
result = await planner.plan("Sua tarefa aqui")

print(result.final_answer)
```

### 3️⃣ Usar RAG Agent

```python
from agents.rag_agent import RAGAgent

rag = RAGAgent()
rag.ingest_documents("docs/")
answer = await rag.query("Pergunta sobre documentos")
```

### 4️⃣ Executar Tools

```python
from agents.tool_agent import ToolAgent

tool_agent = ToolAgent()
tool_agent.register_tool("web_search", web_search_func)
result = await tool_agent.execute("Pesquise sobre X")
```

### 5️⃣ Arena de Agentes

```python
from arena.arena_runner import ArenaRunner

arena = ArenaRunner()
results = await arena.run_competition(
    agents=[agent1, agent2, agent3],
    tasks=benchmark_tasks
)
print(arena.leaderboard())
```

---

## 🧠 Ciclo de Processamento

```
User Request
    │
    ▼
Goal Manager (extrai objetivo)
    │
    ▼
Autonomous Planner (cria plano)
    │
    ▼
Task Decomposer (divide em tarefas)
    │
    ▼
Multi-Agent Router (distribui aos agentes)
    │
    ├─ RAG Agent (busca documentos)
    ├─ Tool Agent (chama APIs)
    └─ Executor Agent (executa skills)
    │
    ▼
Reasoning Engine (pensa: CoT/ToT)
    │
    ▼
Reflection Agent (auto-avalia)
    │
    ▼
Self-Improvement (otimiza prompts)
    │
    ▼
Memory Update (aprende)
    │
    ▼
Evaluation Pipeline (nota resultados)
    │
    ▼
Observability (loga tudo)
    │
    ▼
Final Answer (retorna para usuário)
```

---

## 🔑 Recursos

### 🎬 Planning Autônomo
- Decompõe objetivos em tarefas
- Cria planos hierárquicos
- Otimiza ordem de execução

### 📚 RAG Inteligente
- Ingestão de PDFs, textos, vídeos
- Chunking automático
- Embeddings com múltiplos modelos
- Vector store (Chroma/Pinecone)

### 🔧 Tool Ecosystem
- Registro dinâmico de ferramentas
- Auto-discovery de APIs
- Execução paralela
- Fallback automático

### 🧠 Raciocínio Avançado
- **CoT** (Chain of Thought) — raciocínio passo-a-passo
- **ToT** (Tree of Thoughts) — exploração de múltiplos caminhos
- Pruning inteligente

### 🔄 Auto-Improvement
- **Prompt Optimizer** — melhora prompts automaticamente
- **Failure Analysis** — aprende com erros
- **Reflection** — auto-avalia respostas

### 📊 Evaluation
- RAGAS para RAG
- DeepEval para LLM
- Métricas customizadas
- Leaderboard automático

### 👁️ Observability
- Langfuse tracing
- OpenTelemetry
- Structured logs
- Performance metrics

---

## 💡 Exemplos

### Exemplo 1: Resolver Tarefa Complexa

```python
# Sistema planeja automaticamente
result = await planner.plan(
    "Pesquise sobre tendências de AI, analise dados e gere relatório"
)

# Sistema:
# 1. Decompõe em tarefas
# 2. RAG Agent busca documentos
# 3. Tool Agent pesquisa internet
# 4. Executor Agent analisa
# 5. Reflection Agent valida
# 6. Self-Improvement otimiza
# 7. Retorna resultado
```

### Exemplo 2: Competição de Agentes (Arena)

```python
# Compare múltiplos agentes
results = await arena.run_competition(
    agents=[gpt4_agent, claude_agent, llama_agent],
    tasks=benchmark_tasks
)

# Resultado: Leaderboard com scores
```

### Exemplo 3: Aprendizado Contínuo

```python
# Agent aprende com experiências
for task in task_list:
    result = await agent.execute(task)
    feedback = get_user_feedback()
    
    # Self-improvement automático
    await agent.learn_from_experience(result, feedback)
    
    # Próximas tarefas serão mais precisas
```

---

## 🛠️ Tecnologias

- **LLM**: Claude, GPT-4, Llama
- **Orquestração**: LangChain, LangGraph
- **Vector DB**: Chroma, Pinecone
- **API**: FastAPI
- **Observability**: Langfuse, OpenTelemetry
- **Evaluation**: RAGAS, DeepEval
- **Data**: Pandas, Numpy
- **Async**: AsyncIO, Concurrent.futures

---

## 📚 Documentação

- `architecture_readme.md` — Diagramas de arquitetura
- `estrutura.md` — Fluxos detalhados
- `/docs` — Documentação completa
- `/notebooks` — Exemplos e tutoriais

---

## 🧪 Testes

```bash
# Rodar testes unitários
pytest tests/ -v

# Rodar arena (compare agentes)
python -m arena.arena_runner

# Rodar evaluations
python -m evaluation.ragas_eval
```

---

## 🚀 Features

✅ Multi-agent coordination  
✅ Autonomous planning  
✅ RAG with knowledge retrieval  
✅ Dynamic tool execution  
✅ Advanced reasoning (CoT/ToT)  
✅ Self-improving prompts  
✅ Intelligent memory system  
✅ Evaluation pipeline  
✅ Agent Arena  
✅ Enterprise observability  
✅ Safety & guardrails  
✅ Learning from feedback  

---

## 📈 Roadmap

- [ ] Web UI para visualizar agents
- [ ] Fine-tuning automático
- [ ] Distributed execution
- [ ] Multi-modal models
- [ ] Persistent knowledge base
- [ ] Real-time collaboration

---

## 📝 Licença

MIT License

---

## 🔗 Links

- **GitHub**: https://github.com/Yuri-Fernando/OmniMind_AI_OS
- **Docs**: `/docs`
- **Examples**: `/notebooks`

---

**Built with Claude API & LangGraph**

---

**Status**: In Active Development  
**Version**: 1.0.0  
**Last Updated**: 2026-04-02
