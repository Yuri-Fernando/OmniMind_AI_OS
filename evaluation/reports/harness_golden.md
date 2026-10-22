# Relatório do harness de avaliação (12 casos, juiz: `deterministic`)

| Métrica | Valor |
|---|---|
| faithfulness | 0.562 |
| answer_relevancy | 0.407 |
| context_recall | 1.000 |
| hallucination | 0.438 |
| correctness | 0.322 |
| tool_correctness | 0.600 |
| task_completion | 0.417 |
| latência média (ms) | 614 |
| latência p95 (ms) | 1200 |
| tokens entrada (média) | 212 |
| tokens saída (média) | 26.8 |
| custo total (USD) | 0.000000 |

## Tool-call accuracy

| tool_match | args_valid | args_match | result_used | grounded | overall |
|---|---|---|---|---|---|
| 0.800 | 0.800 | 0.600 | 0.625 | 0.778 | 0.400 |

- **ragas**: NOT_RUN — desligado na configuração
- **deepeval**: NOT_RUN — desligado na configuração

> `—` = métrica não aplicável aos casos (não entra na média). Juiz determinístico = proxies lexicais.
