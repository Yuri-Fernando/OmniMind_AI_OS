"""
Avaliação com RAGAS — faithfulness, answer relevancy, context recall.
Requer: pip install ragas
"""
from typing import List, Dict


def run_ragas_eval(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[str] = None,
) -> Dict:
    """
    Executa avaliação RAGAS no conjunto fornecido.

    Args:
        questions: perguntas
        answers: respostas geradas
        contexts: lista de contextos recuperados por pergunta
        ground_truths: respostas de referência (opcional)

    Returns:
        Dict com scores médios.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_recall

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }
        if ground_truths:
            data["ground_truth"] = ground_truths
            metrics = [faithfulness, answer_relevancy, context_recall]
        else:
            metrics = [faithfulness, answer_relevancy]

        dataset = Dataset.from_dict(data)
        result = evaluate(dataset, metrics=metrics)
        return dict(result)
    except ImportError:
        return {"error": "ragas ou datasets não instalado. Execute: pip install ragas datasets"}
    except Exception as e:
        return {"error": str(e)}
