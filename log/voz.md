# Módulo de Voz — Opções e Status

## STT (Fala → Texto)

| Solução | Offline? | PT-BR | Status |
|---------|----------|-------|--------|
| Whisper (OpenAI open source) | ✅ | ✅ | ✅ Integrado |
| VOSK | ✅ | ✅ | Opcional |
| Coqui STT | ✅ | ✅ | Opcional |

## TTS (Texto → Fala)

| Solução | Offline? | Qualidade | Status |
|---------|----------|-----------|--------|
| pyttsx3 | ✅ | Básica (vozes do SO) | ✅ Integrado |
| EdgeTTS (Microsoft) | ❌ (internet) | Alta | ✅ Integrado |
| ElevenLabs | ❌ (API paga) | Muito alta | ✅ Integrado (chave no .env) |
| Coqui TTS | ✅ | Alta | Opcional |

## Vídeo

| Solução | Modelo | Status |
|---------|--------|--------|
| LLaVA (Ollama) | llava:7b | ✅ Integrado |
| Whisper (extração de áudio de vídeo) | small | ✅ Integrado |
| ffmpeg (extração de frames) | — | ✅ Disponível |

## Pipeline de Voz Completo

```
Microfone → sounddevice → input.wav
    ↓
Whisper STT → texto
    ↓
Agente AIOS (LangGraph)
    ↓
Resposta em texto
    ↓
pyttsx3 / EdgeTTS / ElevenLabs → áudio
    ↓
Alto-falante
```

## Pipeline de Vídeo Completo

```
Arquivo .mp4
    ↓
ffmpeg → frames JPEG + audio.wav
    ↓
LLaVA (Ollama) → descrição dos frames
Whisper → transcrição do áudio
    ↓
Agente AIOS → análise e resposta
```
