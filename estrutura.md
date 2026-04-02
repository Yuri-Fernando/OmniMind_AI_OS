User Input
    │
    ▼
API / Notebook
    │
    ▼
State Manager
    │
    ▼
Planner Agent
    │
    ▼
Task Decomposer
    │
    ▼
Multi-Agent Router
 ┌─────────────┬──────────────┐
 ▼             ▼              ▼
RAG Agent   Tool Agent   Executor Agent
 │             │              │
 ▼             ▼              ▼
Knowledge     APIs         Computation
 │
 ▼
Reflection Agent
 │
 ▼
Prompt Optimizer
 │
 ▼
Final Answer

🏗 Arquitetura do projeto
Usuário
   │
   ▼
API (FastAPI)
   │
   ▼
Agente LLM (LangChain / LangGraph)
   │
   ├── RAG (documentos)
   │
   ├── Tools (APIs)
   │
   ├── Guardrails
   │
   └── Memory
   │
   ▼
LLM (GPT / Claude / Llama)

                    User
                      │
                      ▼
           Interface Layer
     (Notebook / API / Voice UI)
                      │
                      ▼
               Orchestrator
                LangGraph
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
   Planner        Tool Agent      RAG Agent
      │               │                │
      ▼               ▼                ▼
 Task decomposition   APIs        Vector DB
      │
      ▼
  Memory Manager
      │
      ▼
   LLM Router
      │
      ▼
 GPT / Claude / Llama


Interface
│
├── FastAPI
├── Voice interface
│
Orchestration
│
├── LangGraph
├── Planner Agent
├── Tool Agent
├── RAG Agent
│
Knowledge
│
├── Vector DB (Chroma)
├── Document ingestion
│
Memory
│
├── Conversation memory
├── Vector memory
│
Safety
│
├── Prompt injection detection
├── Content filter
│
Observability
│
├── Langfuse
│
Evaluation
│
├── Ragas
├── DeepEval

 USER
                          │
                          ▼
                   Input Interface
             (API / Notebook / Voice)
                          │
                          ▼
                  Goal Manager
                          │
                          ▼
                    Planner Agent
                          │
                          ▼
                 Task Decomposer
                          │
                          ▼
                 Multi-Agent Router
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
     RAG Agent      Tool Agent      Executor Agent
        │               │               │
        ▼               ▼               ▼
   Knowledge Base     Tools API      Execution
    Vector Store     Tool Registry     Engine
        │               │               │
        ▼               ▼               ▼
      Retriever     Tool Discovery     Skills
        │               │               │
        └───────┬───────┴───────┬───────┘
                ▼               ▼
          Reasoning Engine   Skill Selector
           (CoT / ToT)            │
                │                 ▼
                ▼            Skill Execution
           Reflection Agent
                │
                ▼
         Self Improvement
      (Prompt Optimizer /
       Failure Analysis)
                │
                ▼
             Memory
    ┌──────────┼──────────┐
    ▼          ▼          ▼
Short Term   Vector    Long Term
 Memory      Memory     Memory
                │
                ▼
          World Model
        (Agent Cognition)
                │
                ▼
            Evaluation
     (RAGAS / DeepEval / Metrics)
                │
                ▼
          Observability
      (Langfuse / Telemetry)
                │
                ▼
             Logs



                                      USER
                          │
                          ▼
                  Interaction Layer
        ┌────────────────────────────────┐
        │ API │ Notebook │ Voice │ CLI   │
        └────────────────────────────────┘
                          │
                          ▼
                  Goal Management Layer
              ┌───────────────────────┐
              │ Goal Manager          │
              │ Autonomous Planner    │
              │ Task Decomposer       │
              └───────────────────────┘
                          │
                          ▼
                Multi-Agent Coordination
         ┌──────────────────────────────────┐
         │ Agent Router                     │
         │ Agent Registry                   │
         │ Communication Protocol           │
         └──────────────────────────────────┘
                          │
                          ▼
                  Agent Execution Layer
       ┌──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼
   RAG Agent      Tool Agent     Executor Agent
       │              │              │
       ▼              ▼              ▼
Knowledge Retrieval  Tools API    Skill Execution
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
 Short-Term   Vector     Long-Term
  Memory      Memory      Memory
               │
               ▼
            World Model
      (Beliefs / Environment State)
               │
               ▼
           Learning Loop
      (Feedback / RL / Experience)
               │
               ▼
           Evaluation Layer
       RAGAS │ DeepEval │ Metrics
               │
               ▼
        Observability Layer
       Logs │ Tracing │ Telemetry


       Goal
 │
 ▼
Planner
 │
 ▼
Task Decomposer
 │
 ▼
Skill Selector
 │
 ▼
Tool / RAG / Execution
 │
 ▼
World Model Update
 │
 ▼
Reflection Agent
 │
 ▼
Prompt Optimizer
 │
 ▼
Memory Update

objetivo → plano → executar → aprender → melhorar

   User request
     │
     ▼
Goal Manager
     │
     ▼
Planner Agent
     │
     ▼
Task Decomposer
     │
     ▼
Skill Selector
     │
     ▼
Execution (RAG / Tools)
     │
     ▼
World Model Update
     │
     ▼
Reflection Agent
     │
     ▼
Prompt Optimizer
     │
     ▼
Memory + Experience
     │
     ▼
Final Answer


tasks
 │
 ▼
Agent Arena
 │
 ▼
Agents generate answers
 │
 ▼
Evaluation Pipeline
 │
 ▼
Scores
 │
 ▼
Leaderboard