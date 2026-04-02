# Arquitetura AIOS

## Fluxo Principal

```
Usuário
   │
   ▼
Interface Layer (API FastAPI / Notebook / Voz / CLI)
   │
   ▼
Orchestrator — LangGraph
   │
   ├── Planner Agent       → gera estratégia
   │
   ├── Router              → decide RAG ou Tool
   │
   ├── RAG Agent           → recupera do Vector DB (Chroma)
   │   └── Tool Agent      → chama APIs externas
   │
   ├── Executor Agent      → gera resposta com LLM
   │
   └── Reflection Agent    → avalia e melhora resposta
           │
           ▼
      Memory System
      ├── Short-Term (deque, RAM)
      ├── Vector Memory (Chroma semântico)
      └── Long-Term (JSON persistido)
           │
           ▼
      Evaluation & Observability
      ├── Métricas (relevância, F1, latência)
      ├── Tracing (spans por nó)
      └── Telemetria (runs, tokens, erros)
```

## Camadas do Sistema

| Camada | Componentes |
|--------|-------------|
| Interface | FastAPI, Notebook, Voice (Whisper/TTS) |
| Orquestração | LangGraph, Router, State Manager |
| Agentes | Planner, RAG, Tool, Executor, Reflection |
| Conhecimento | Chroma (vector DB), PDF loader, chunking |
| Ferramentas | Clima, Calculadora, Web scraper, File reader, Code executor |
| Modelos | OpenAI, Anthropic, Ollama (Mistral, LLaVA) |
| Memória | Short-term, Vector, Long-term |
| Segurança | Prompt injection detector, Content filter |
| Observabilidade | Tracing, Telemetria, Langfuse |
| Avaliação | Métricas locais, RAGAS, DeepEval, Benchmark Arena |

## Seleção de LLM

```
Provider  │ Modelos                          │ Requer
──────────┼──────────────────────────────────┼──────────────────
openai    │ gpt-4o-mini, gpt-4o              │ OPENAI_API_KEY
anthropic │ claude-haiku-4-5, claude-sonnet  │ ANTHROPIC_API_KEY
ollama    │ mistral, llava:7b, llama3        │ Ollama local
```
