# ADR 0003 — Adaptação de modelo (LoRA/QLoRA), harness de avaliação único e tracing do agente

- **Status:** aceito (2026-10-21)
- **Contexto:** o OmniMind já avaliava RAG (RAGAS/DeepEval) mas não tinha (a) nenhuma evidência executada de
  ajuste fino de modelo, (b) um ponto único que reunisse juiz, métricas determinísticas e avaliação humana,
  (c) avaliação do *comportamento* do agente (escolha de ferramenta), nem (d) tracing do fluxo completo.

## Decisões

1. **Tarefa de adaptação = roteamento de ferramentas (tool-calling estruturado).** É o que o agente realmente
   faz, é verificável sem LLM-juiz (JSON + argumentos exatos) e cabe num modelo ≤1B numa GPU de 8 GB.
   Modelo: `Qwen/Qwen2.5-0.5B-Instruct` (Apache-2.0), cache em `Q:\Hugginface`.
2. **Dataset sintético, determinístico, anti-leakage por construção.** Entidades (cidades, assuntos,
   caminhos, operandos) são particionadas *antes* de gerar pedidos; o último template de cada ferramenta só
   existe no `test` (mede generalização para formulação nunca vista). `datasets/validation.py` falha se
   houver qualquer vazamento e os testes provam que o detector realmente detecta.
3. **Comparação justa:** mesmos hiperparâmetros de treino e de adapter para LoRA e QLoRA (a única diferença é
   a base em bf16 × 4-bit NF4 + double quant). Inclui-se a base sem treino (bf16 e 4-bit) como referência e
   um baseline de ajuste fino completo — que registra `OOM` com o pico medido se não couber, em vez de omitir.
4. **Loop de treino próprio (PyTorch + PEFT).** `trl` não está instalado e não foi instalado só para isto;
   o loop é curto, auditável e mede VRAM (`max_memory_allocated`), tempo e tamanho do adapter.
5. **Pesos fora do Drive e do git.** Adapters/checkpoints em `D:\Claude Temp\staging\omnimind-adapt`; o repo
   guarda só configs, dataset (≈100 KB, regenerável), código e `results/*.json`/`REPORT.md`.
6. **Harness único em `evaluation/harness.py`.** Métrica inaplicável é `None` e não entra na média; RAGAS e
   DeepEval rodam de verdade (com `OPENAI_API_KEY`) ou aparecem como `NOT_RUN` com o motivo — nunca simulados.
7. **Juiz plugável, local por padrão.** `DeterministicJudge` (proxies lexicais) é o padrão; `ClaudeJudge`
   exige opt-in explícito (`OMNIMIND_ALLOW_CLOUD_JUDGE=1`) e chave por env, trata o texto avaliado como dado
   não confiável e valida o JSON devolvido.
8. **Tool-call accuracy determinística** (`evaluation/tool_call_accuracy.py`): ferramenta, validade dos
   argumentos pelo esquema, igualdade normalizada, resultado usado e resposta ancorada. Fonte única do esquema
   das ferramentas; golden com casos positivos **e negativos**.
9. **Tracing com API correta do SDK v3.** O `langfuse_tracing.trace_run` antigo chama `Langfuse.trace()`, que
   não existe no SDK instalado (3.12.1). `observability/agent_tracing.py` usa `start_observation`/`create_score`,
   mascara segredos, trunca payloads e sempre grava também o JSONL local.

## Consequências / limites assumidos

- Resultados valem para **este** modelo, esta tarefa sintética e esta GPU; não generalizam para LLMs maiores
  nem para linguagem aberta. 3 seeds, variância reportada.
- O juiz determinístico é baseline lexical, não substitui juiz semântico.
- **Langfuse real: BLOCKED_BY_CONFIGURATION.** `docker-compose.langfuse.yml` está escrito mas nunca foi
  executado; o sink do SDK foi testado só contra um cliente falso.
- O `trace_run` antigo ficou intocado (compatibilidade); corrigi o caminho novo, não o legado.
