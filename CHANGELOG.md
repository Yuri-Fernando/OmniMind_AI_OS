# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Golden-set reprodutível (`evaluation/golden_dataset.py`) com 8 perguntas e
  respostas de referência extraídas do conteúdo real do próprio repositório
  (README.md, rag/GRAPH_RAG.md, architecture_readme.md).
- Retriever TF-IDF determinístico (`evaluation/tfidf_retriever.py`) usado
  como camada de recuperação real do harness de avaliação, sem depender de
  download de modelo nem de rede.
- Pipeline real de geração de respostas (`evaluation/real_pipeline.py`):
  contexto real (TF-IDF) + resposta real via OpenAI (gpt-4o-mini), com
  fallback offline determinístico documentado quando não há chave de API.
- Execução real de RAGAS (`evaluation/ragas_eval.run_ragas_on_golden`) sobre
  o golden-set, com relatório numérico salvo em `evaluation/reports/`.
- Execução real de DeepEval (`evaluation/deepeval_tests.run_deepeval_on_golden`)
  sobre o golden-set.
- Fallback local de tracing (`observability/langfuse_tracing.read_local_traces`,
  `active_backend`) que grava traces reais em
  `observability/traces/traces.jsonl` quando não há Langfuse Cloud/self-host
  configurado — documentado como limitação honesta, não como Langfuse real.
- Ponto de entrada único e reprodutível `python -m evaluation.run_all`, que
  gera `evaluation/reports/eval_<timestamp>.json` e `.md` com números medidos
  de verdade (não estimados).
- Suíte de testes para o novo código (`evaluation/tests/`): golden dataset,
  retriever TF-IDF, métricas puras, agregação do relatório.

### Fixed
- `evaluation/deepeval_tests.run_deepeval`: `HallucinationMetric` lê
  `test_case.context`, mas a função só preenchia `retrieval_context` — a
  métrica de hallucination nunca tinha dado reais para avaliar (campo
  obrigatório ausente). Corrigido para preencher os dois campos.
- `evaluation/deepeval_tests.run_deepeval`: lia `tc.relevancy_score`/
  `tc.hallucination_score` do `LLMTestCase`, atributos que o DeepEval nunca
  cria (o score é retornado por `metric.measure(tc)` e fica no objeto da
  métrica). Corrigido.
- `evaluation/ragas_eval.run_ragas_on_golden`: quando todas as chamadas ao
  LLM-juiz do RAGAS falham, `evaluate()` não propaga a exceção e
  `dict(eval_result)` lançava um `KeyError: 0` opaco ao tentar agregar um
  resultado vazio. Adicionada detecção explícita desse caso com mensagem
  de erro legível.

### Changed
- `evaluation/ragas_eval.py` e `evaluation/deepeval_tests.py` passam a ter,
  além das funções originais (mantidas por compatibilidade), uma função
  "on_golden" que de fato invoca essas avaliações com dados reais — até esta
  versão, nada no repositório chamava essas funções (não havia golden-set,
  script ou CI que as executasse).

### Known limitations
- `OPENAI_API_KEY` e `ANTHROPIC_API_KEY` no `.env` deste projeto estavam
  inválidas/expiradas nesta sessão (testado com chamada mínima real a cada
  provedor) — por isso os scores reais de RAGAS/DeepEval desta execução
  vieram como erro de autenticação, não como número. A infraestrutura está
  pronta e vai produzir números reais assim que uma chave válida estiver
  configurada; ver `WORKLOG.md` para o relato completo.
- Langfuse Cloud/self-host não configurado nesta sessão; tracing real cai
  no fallback local em arquivo (`observability/traces/traces.jsonl`).

## Contexto da auditoria

Item da auditoria de portfólio (seção "Agentic AI / RAG / LLMOps"):
"OmniMind: tornar RAGAS/DeepEval/Langfuse mensurados e reproduzíveis."

Estado anterior: README.md listava RAGAS, DeepEval e Langfuse como
funcionalidades do projeto; o código (`evaluation/ragas_eval.py`,
`evaluation/deepeval_tests.py`, `observability/langfuse_tracing.py`) existia
mas nunca era invocado por nada — sem golden-set, sem relatório gerado, sem
integração real de RAGAS/DeepEval, sem chaves de Langfuse configuradas.
As três bibliotecas (ragas, deepeval, langfuse) já estavam instaladas no
ambiente Python, mas isso não equivale a "mensurado e reproduzível".

Ver `WORKLOG.md` para o relato completo de execução desta tarefa, incluindo
o que rodou de verdade e o que ficou documentado como limitação.
