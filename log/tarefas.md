# Tarefas e Backlog AIOS

## Pendentes

- [ ] Interface web (Streamlit ou Gradio) para o agente
- [ ] Integrar wake word (pvporcupine) para assistente de voz hands-free
- [ ] Streaming de respostas na API e notebook
- [ ] Conectar guardrails no pipeline (pré/pós agente)
- [ ] Integrar n8n para automação de workflows
- [ ] Juntar módulos Jarvis (controle do PC) ao AIOS
- [ ] Integrar Alexa como interface de entrada/saída
- [ ] Fine-tuning com dados locais

## Concluídas

- [x] Pipeline RAG completo (PDF → Chroma → retriever)
- [x] LangGraph com múltiplos provedores (OpenAI/Anthropic/Ollama)
- [x] Ferramentas: clima, calculadora, scraper, file reader, code executor
- [x] STT com Whisper (open source, PT-BR)
- [x] TTS local (pyttsx3 + EdgeTTS gratuito)
- [x] Análise de vídeo com LLaVA (open source via Ollama)
- [x] Memória short-term, long-term e vetorial
- [x] Guardrails (prompt injection + content filter)
- [x] Observabilidade (tracing, telemetria, Langfuse)
- [x] Benchmark e Arena de LLMs no notebook
- [x] Pipeline completo: Vídeo → Áudio → Whisper → Agente → TTS

## Portfólio

**Título:** AI Agent Operating System (AIOS)
**Descrição:** Multi-agent AI platform with autonomous planning, RAG pipelines,
tool ecosystems, self-reflection, evaluation pipelines and LLM arena.
**Stack:** Python, LangGraph, LangChain, Chroma, Whisper, LLaVA, Ollama, FastAPI
