# 🏗️ System Architecture

## 🔹 Main Flow
```text
User Input
    │
    ▼
API / Interface (Notebook / Voice)
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
    ├───────────────┬───────────────┐
    ▼               ▼               ▼
RAG Agent      Tool Agent      Executor Agent
    │               │               │
    ▼               ▼               ▼
Knowledge Base     APIs         Execution Engine
    │
    ▼
Reflection Agent
    │
    ▼
Prompt Optimizer
    │
    ▼
Memory Update
    │
    ▼
Final Answer
```

---

## 🔹 Enterprise Architecture
```text
USER
  │
  ▼
Interaction Layer
(API / Notebook / Voice / CLI)
  │
  ▼
Goal Management Layer
(Goal Manager + Planner + Task Decomposer)
  │
  ▼
Multi-Agent Coordination
(Agent Router + Registry + Communication)
  │
  ▼
Agent Execution Layer
 ├──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼
RAG Agent    Tool Agent    Executor Agent
 │              │              │
 ▼              ▼              ▼
Vector DB      APIs        Computation
 │
 ▼
Reasoning Engine (CoT / ToT)
  │
  ▼
Reflection Agent
  │
  ▼
Self-Improvement Engine
(Prompt Optimizer + Failure Analysis)
  │
  ▼
Memory System
 ├──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼
Short-Term    Vector       Long-Term
 Memory       Memory        Memory
  │
  ▼
World Model
  │
  ▼
Evaluation Layer (RAGAS / DeepEval)
  │
  ▼
Observability (Logs / Tracing / Telemetry)
```

---

## 🔹 Simplified Flow
```text
Goal → Plan → Execute → Learn → Improve

User Request
    │
    ▼
Planner
    │
    ▼
Task Decomposition
    │
    ▼
Execution (RAG / Tools)
    │
    ▼
Reflection
    │
    ▼
Memory Update
    │
    ▼
Final Answer
```

---

## 🔹 Evaluation Pipeline
```text
Tasks
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
Scoring System
  │
  ▼
Leaderboard
```
