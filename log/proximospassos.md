# Status do Projeto AIOS

## Progresso

| Fase | Descrição | Status |
|------|-----------|--------|
| Phase 1 — MVP Agent | Estrutura, planner, RAG, tools, runtime | ✅ Completo |
| Phase 2 — Intelligence | Reflection, guardrails, vector memory | ✅ Completo |
| Phase 3 — Platform | Orquestração multi-provedor, observabilidade | ✅ Completo |
| Phase 4 — Research Lab | Arena, benchmark, avaliação automática | ✅ Completo |

## O que está funcionando

- Pipeline RAG: PDF → chunking → embeddings → Chroma → retriever
- LangGraph com roteamento dinâmico (rag / tool)
- Suporte a múltiplos LLMs: OpenAI, Anthropic, Ollama
- Ferramentas: clima, calculadora, web scraper, file reader, code executor
- Multimodal: Whisper (STT), TTS local (pyttsx3/EdgeTTS), ElevenLabs
- Análise de vídeo com LLaVA via Ollama
- Memória: short-term, long-term (JSON), vector (semântica)
- Guardrails: prompt injection + content filter
- Observabilidade: tracing por nó, telemetria, Langfuse (opcional)
- Avaliação: métricas locais, RAGAS, DeepEval, benchmark automático
- Arena de comparação de LLMs no notebook teste2.ipynb

## Próximos passos sugeridos

1. Conectar guardrails no pipeline (pré e pós execução)
2. Implementar streaming de respostas na API
3. Interface web (Streamlit ou Gradio)
4. Integração com n8n para workflows automatizados
5. Fine-tuning de modelo local com dados do projeto
