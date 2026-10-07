"""
Testes com DeepEval — correctness, hallucination, answer relevancy.
Requer: pip install deepeval

Histórico (ver WORKLOG.md): `run_deepeval` já existia mas nunca era chamada
em lugar nenhum do repo — sem golden-set, sem script, sem CI. Esta função
continua existindo tal como estava (usada pelos testes unitários de
agregação); `run_deepeval_on_golden`, abaixo, é a execução real e nova sobre
o golden-set definido em `evaluation/golden_dataset.py`.
"""
from typing import List, Dict


def run_deepeval(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    expected: List[str] = None,
) -> List[Dict]:
    """
    Executa métricas DeepEval para cada par (pergunta, resposta).

    Returns:
        Lista de dicts com scores por item.
    """
    try:
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric

        test_cases = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            ctx = contexts[i] if i < len(contexts) else []
            exp = expected[i] if expected and i < len(expected) else None
            tc = LLMTestCase(
                input=q,
                actual_output=a,
                # `retrieval_context` é lido por métricas de RAG (ex.:
                # ContextualRelevancy); `context` é o campo que
                # `HallucinationMetric` de fato lê (ver
                # deepeval/metrics/hallucination/hallucination.py —
                # `_required_params` inclui LLMTestCaseParams.CONTEXT, não
                # RETRIEVAL_CONTEXT). Preenchemos os dois com os mesmos
                # chunks recuperados: sem um "contexto de referência"
                # separado disponível, tratamos o contexto recuperado como
                # a base factual contra a qual medir alucinação.
                retrieval_context=ctx,
                context=ctx,
                expected_output=exp,
            )
            test_cases.append(tc)

        # measure() retorna o score e também seta `metric.score`/`.reason`
        # no objeto da métrica — não no LLMTestCase (bug corrigido aqui: a
        # versão anterior lia `tc.relevancy_score`/`tc.hallucination_score`,
        # atributos que o deepeval nunca cria).
        results = []
        for tc in test_cases:
            relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
            hallucination_metric = HallucinationMetric(threshold=0.5)
            relevancy_score = relevancy_metric.measure(tc)
            hallucination_score = hallucination_metric.measure(tc)
            results.append({
                "question": tc.input,
                "answer": tc.actual_output[:150],
                "relevancy": relevancy_score,
                "relevancy_reason": getattr(relevancy_metric, "reason", None),
                "hallucination": hallucination_score,
                "hallucination_reason": getattr(hallucination_metric, "reason", None),
            })
        return results

    except ImportError:
        return [{"error": "deepeval não instalado. Execute: pip install deepeval"}]
    except Exception as e:
        return [{"error": str(e)}]


def run_deepeval_on_golden(model: str = "gpt-4o-mini") -> List[Dict]:
    """Roda DeepEval de verdade sobre o golden-set (contexto TF-IDF real +
    resposta real via OpenAI, ou fallback offline documentado — ver
    `evaluation/real_pipeline.py`)."""
    from evaluation.real_pipeline import generate_eval_records

    records = generate_eval_records(model=model)
    results = run_deepeval(
        questions=[r.question for r in records],
        answers=[r.answer for r in records],
        contexts=[r.contexts for r in records],
        expected=[r.ground_truth for r in records],
    )
    for item, record in zip(results, records):
        if isinstance(item, dict):
            item["mode"] = record.mode
    return results
