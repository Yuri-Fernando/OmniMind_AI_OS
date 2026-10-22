# model_adaptation — LoRA × QLoRA × ajuste completo (experimento real)

Adapta `Qwen/Qwen2.5-0.5B-Instruct` (Apache-2.0) ao **roteamento de ferramentas** do agente: dado um pedido
em português, responder só com `{"tool": ..., "args": {...}}` (calculator, weather_api, web_search,
file_reader ou none). Decisões e limites: [ADR 0003](../docs/adr/0003-model-adaptation.md).
Resultados medidos: [`results/REPORT.md`](results/REPORT.md) (tabela também no README raiz).

## Como reproduzir

Python 3.10 canônico, GPU CUDA com ≥ 8 GB, `torch`, `transformers`, `peft`, `bitsandbytes` (sem `trl`).

```bash
python -m model_adaptation.datasets.prepare_dataset --seed 0      # gera + valida (falha se houver vazamento)
python -m model_adaptation.run_experiment --seeds 0 1 2           # base, base 4-bit, LoRA, QLoRA, completo
python -m model_adaptation.training.qlora --seed 0                # treinar uma variante isolada
```

Pesos e checkpoints vão para `D:\Claude Temp\staging\omnimind-adapt` (`OMNIMIND_ADAPT_STAGING`), nunca para o
Drive nem para o git; o repositório guarda só código, configs, dataset (≈100 KB, regenerável) e `results/`.

## Estrutura

| Caminho | Papel |
|---|---|
| `common.py` | modelo base, prompt de sistema, esquema das ferramentas (fonte única em `evaluation/tool_call_accuracy.py`) |
| `datasets/prepare_dataset.py`, `validation.py` | geração determinística; partição de entidades antes de gerar; template holdout só no teste; detector de vazamento |
| `training/trainer.py` + `lora.py`, `qlora.py`, `full_baseline.py` | loop PyTorch único; mede VRAM (`max_memory_allocated`), tempo, parâmetros, adapter em disco |
| `inference/base_model.py`, `adapter_loader.py` | base bf16 / 4-bit / 8-bit, adapter PEFT sem merge, geração batch=1 |
| `evaluation/benchmark.py` | exact match, JSON estrito, por ferramenta e por template, latência p50/p95, tokens/s, relatório |
| `evaluation/llm_judge.py`, `human_eval.py` | reexportam a implementação única de `evaluation/` |
| `configs/{lora,qlora,full}.yaml` | hiperparâmetros (LoRA e QLoRA idênticos de propósito) |
| `results/` | um JSON por variante×seed (tudo que o relatório mostra vem daqui) + `REPORT.md` |

## Limites

Um modelo de 0,5 B, uma tarefa sintética, uma GPU compartilhada, 3 seeds, 114 exemplos de teste. As
diferenças entre LoRA, QLoRA e ajuste completo estão dentro do desvio entre seeds. Tempos de treino e
latências são ruidosos (carga concorrente na GPU) e não devem ser comparados entre variantes.
