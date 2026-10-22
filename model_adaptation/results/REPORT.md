# Resultados — roteador de ferramentas (base × LoRA × QLoRA)

Modelo base: `Qwen/Qwen2.5-0.5B-Instruct` · test = 114 pedidos (inclui template nunca visto no treino). Valores = média ± desvio entre seeds quando há mais de uma.

| Variante | status | seeds | exact match | JSON estrito | holdout EM | VRAM treino (GB) | tempo treino (s) | adapter (MB) | treináveis (%) | lat. p50 (ms) | lat. p95 (ms) | tokens/s | VRAM infer. (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base (bf16) | COMPLETED | 1 | 0.702 | 1.000 | 0.529 | — | — | — | — | 2457 | 4057 | 8.3 | 1.015 |
| Base (4-bit NF4) | COMPLETED | 1 | 0.439 | 0.667 | 0.294 | — | — | — | — | 3326 | 5468 | 6.0 | 0.482 |
| Ajuste fino completo | COMPLETED | 3 | 0.927 ± 0.004 | 1.000 ± 0.000 | 0.755 ± 0.014 | 7.869 ± 0.007 | 167.5 ± 74.9 | 988.1 ± 0.0 | 100.00 ± 0.00 | 1495 ± 163 | 2367 ± 311 | 10.8 ± 1.2 | 1.020 ± 0.003 |
| LoRA (bf16) | COMPLETED | 3 | 0.947 ± 0.029 | 1.000 ± 0.000 | 0.843 ± 0.097 | 6.495 ± 0.012 | 232.8 ± 129.0 | 35.2 ± 0.0 | 1.75 ± 0.00 | 3137 ± 564 | 4717 ± 916 | 5.4 ± 1.1 | 1.083 ± 0.000 |
| QLoRA (4-bit NF4) | COMPLETED | 3 | 0.936 ± 0.030 | 1.000 ± 0.000 | 0.833 ± 0.084 | 7.537 ± 0.020 | 631.9 ± 448.7 | 35.2 ± 0.0 | 2.72 ± 0.00 | 4001 ± 652 | 7169 ± 1284 | 3.8 ± 0.5 | 0.545 ± 0.000 |

Notas: VRAM = `torch.cuda.max_memory_allocated` (inclui pesos); latência em batch=1, geração gulosa, `max_new_tokens=64`; “exact match” = ferramenta correta + argumentos corretos (normalizados); “JSON estrito” = a saída inteira é só o JSON.
