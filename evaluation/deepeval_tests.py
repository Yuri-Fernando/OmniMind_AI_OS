"""
Testes com DeepEval — correctness, hallucination, answer relevancy.
Requer: pip install deepeval
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
        from deepeval import evaluate as dv_evaluate
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric

        test_cases = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            ctx = contexts[i] if i < len(contexts) else []
            exp = expected[i] if expected and i < len(expected) else None
            tc = LLMTestCase(
                input=q,
                actual_output=a,
                retrieval_context=ctx,
                expected_output=exp,
            )
            test_cases.append(tc)

        metrics = [AnswerRelevancyMetric(threshold=0.5), HallucinationMetric(threshold=0.5)]
        results = []
        for tc in test_cases:
            for m in metrics:
                m.measure(tc)
            results.append({
                "question": tc.input,
                "answer": tc.actual_output[:150],
                "relevancy": getattr(tc, "relevancy_score", None),
                "hallucination": getattr(tc, "hallucination_score", None),
            })
        return results

    except ImportError:
        return [{"error": "deepeval não instalado. Execute: pip install deepeval"}]
    except Exception as e:
        return [{"error": str(e)}]
