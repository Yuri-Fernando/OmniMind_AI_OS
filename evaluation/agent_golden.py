"""Golden de comportamento de agente: casos positivos e NEGATIVOS escritos à mão.

Os negativos existem para provar que a métrica falha quando deve (um avaliador que só aprova não vale
nada). Cada caso traz o `label` do que se espera detectar.
"""
from __future__ import annotations

from typing import List

from evaluation.harness import AgentCase

_CALC = {"tool": "calculator", "args": {"expression": "37*12"}}
_WEATHER = {"tool": "weather_api", "args": {"city": "Curitiba"}}
_FILE = {"tool": "file_reader", "args": {"path": "docs/ata_01.md"}}
_SEARCH = {"tool": "web_search", "args": {"query": "energia solar"}}
_RAG_CTX = ["O OmniMind AI OS usa RAGAS e DeepEval para avaliar respostas e Langfuse para tracing."]


def golden_cases() -> List[AgentCase]:
    return [
        # ---------------------------------------------------------------- positivos
        AgentCase("pos-calc", "Quanto é 37 vezes 12?", "37 vezes 12 é 444.", ground_truth="444",
                  expected_call=_CALC, actual_call=_CALC, tool_result="444", latency_ms=420, input_tokens=180,
                  output_tokens=22, model="golden", label="positive"),
        AgentCase("pos-weather", "Como está o tempo em Curitiba?", "Em Curitiba está nublado, com 14 graus.",
                  expected_call=_WEATHER, actual_call=_WEATHER, tool_result="Curitiba: nublado +14°C",
                  latency_ms=950, input_tokens=190, output_tokens=30, model="golden", label="positive"),
        AgentCase("pos-file", "Leia docs/ata_01.md", "A reunião está marcada para 15/03 às 14h.",
                  expected_call=_FILE, actual_call=_FILE, tool_result="Reunião marcada para 15/03 às 14h",
                  latency_ms=300, input_tokens=170, output_tokens=24, model="golden", label="positive"),
        AgentCase("pos-none", "Olá, tudo bem?", "Olá! Tudo bem por aqui, em que posso ajudar?",
                  expected_call={"tool": "none", "args": {}}, actual_call={"tool": "none", "args": {}},
                  tool_result="", latency_ms=200, input_tokens=120, output_tokens=18, model="golden", label="positive"),
        AgentCase("pos-rag", "Quais ferramentas de avaliação o OmniMind usa?",
                  "O OmniMind usa RAGAS e DeepEval para avaliar respostas.", contexts=_RAG_CTX,
                  ground_truth="RAGAS e DeepEval", latency_ms=1200, input_tokens=400, output_tokens=40,
                  model="golden", label="positive"),
        # ---------------------------------------------------------------- negativos
        AgentCase("neg-wrong-tool", "Quanto é 37 vezes 12?", "Encontrei resultados sobre multiplicação.",
                  expected_call=_CALC, actual_call=_SEARCH, tool_result="links...", model="golden",
                  label="negative:wrong_tool"),
        AgentCase("neg-bad-args", "Quanto é 37 vezes 12?", "37 vezes 12 é 444.",
                  expected_call=_CALC, actual_call={"tool": "calculator", "args": {"expr": "37*12"}},
                  tool_result="444", model="golden", label="negative:invalid_args"),
        AgentCase("neg-wrong-args", "Quanto é 37 vezes 12?", "37 vezes 21 é 777.",
                  expected_call=_CALC, actual_call={"tool": "calculator", "args": {"expression": "37*21"}},
                  tool_result="777", model="golden", label="negative:wrong_args"),
        AgentCase("neg-ignored-result", "Quanto é 37 vezes 12?", "Não sei responder a isso.",
                  expected_call=_CALC, actual_call=_CALC, tool_result="444", model="golden",
                  label="negative:result_ignored"),
        AgentCase("neg-ungrounded", "Como está o tempo em Curitiba?", "Em Curitiba faz 31 graus e há 80% de umidade.",
                  expected_call=_WEATHER, actual_call=_WEATHER, tool_result="Curitiba: nublado +14°C",
                  model="golden", label="negative:ungrounded"),
        AgentCase("neg-no-call", "Quanto é 37 vezes 12?", "Deve dar uns 450.", expected_call=_CALC,
                  actual_call=None, model="golden", label="negative:missing_call"),
        AgentCase("neg-hallucination", "Quais ferramentas de avaliação o OmniMind usa?",
                  "O OmniMind usa TensorBoard, Weights & Biases e MLflow Tracking Server em Kubernetes.",
                  contexts=_RAG_CTX, ground_truth="RAGAS e DeepEval", model="golden", label="negative:hallucination"),
    ]
