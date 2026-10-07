"""
Avaliação com RAGAS — faithfulness, answer relevancy, context recall.
Requer: pip install ragas

Histórico (ver WORKLOG.md): `run_ragas_eval` já existia neste repo, mas nunca
era chamada por nada — nenhum script, teste ou CLI a invocava, e não havia
golden-set nem relatório gerado. `run_ragas_on_golden` é a função nova que
de fato executa isso: gera contexto+resposta reais para o golden-set
(`evaluation/real_pipeline.py`) e chama `run_ragas_eval` de verdade.
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


def _build_ragas_llm_and_embeddings(model: str = "gpt-4o-mini"):
    """Monta o LLM-juiz e os embeddings reais usados pelas métricas RAGAS.

    RAGAS 0.4 trocou a API de wiring de LLM mais de uma vez (ver warnings de
    deprecation ao importar `ragas.metrics`); tentamos a fábrica nova
    primeiro e caímos para o wrapper via LangChain se não estiver disponível
    nesta versão instalada — em ambos os casos o resultado é um LLM real
    (OpenAI), nunca um stub.
    """
    try:
        from ragas.llms import llm_factory
        from ragas.embeddings import embedding_factory

        llm = llm_factory(model, provider="openai")
        embeddings = embedding_factory()
        return llm, embeddings
    except Exception:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        llm = LangchainLLMWrapper(ChatOpenAI(model=model, temperature=0))
        embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        return llm, embeddings


def run_ragas_on_golden(model: str = "gpt-4o-mini") -> Dict:
    """Roda RAGAS de verdade sobre `evaluation/golden_dataset.GOLDEN_SET`.

    Usa `evaluation.real_pipeline.generate_eval_records` para obter contexto
    (TF-IDF real) + resposta (OpenAI real, ou fallback offline se não houver
    chave) e então chama `run_ragas_eval` com um LLM-juiz real. Se o modo de
    geração foi "offline" (sem chave de API), o resultado é marcado
    `"degraded": True` — as métricas de faithfulness/relevancy feitas por um
    LLM-juiz não têm sentido sobre respostas extrativas, então o relatório
    final nunca deve apresentar esse número como avaliação real de LLM.
    """
    from evaluation.real_pipeline import generate_eval_records

    records = generate_eval_records(model=model)
    degraded = any(r.mode != "llm" for r in records)

    questions = [r.question for r in records]
    answers = [r.answer for r in records]
    contexts = [r.contexts for r in records]
    ground_truths = [r.ground_truth for r in records]

    result: Dict = {"degraded": degraded, "n_items": len(records)}
    if degraded:
        result["note"] = (
            "Ao menos um item não usou o LLM real (sem OPENAI_API_KEY ou "
            "erro de rede) — ver 'modes' para detalhe por item. Scores abaixo "
            "não devem ser tratados como avaliação de LLM real."
        )
        result["modes"] = [r.mode for r in records]

    try:
        llm, embeddings = _build_ragas_llm_and_embeddings(model=model)
    except Exception as e:
        result["error"] = f"não foi possível montar LLM/embeddings do RAGAS: {e}"
        return result

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_recall

        dataset = Dataset.from_dict(
            {
                "question": questions,
                "answer": answers,
                "contexts": contexts,
                "ground_truth": ground_truths,
            }
        )
        eval_result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall],
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False,
        )

        # O Executor interno do ragas captura exceções por job (visível no
        # stdout como "Exception raised in Job[N]: ...") em vez de propagar;
        # quando TODO job falhou (ex.: credencial inválida), `dict()`/
        # `repr()` sobre o resultado pode até lançar KeyError internamente
        # (bug observado nesta versão do ragas ao agregar um resultado
        # vazio). Então checamos a taxa de falha primeiro, pela contagem de
        # linhas computadas, antes de tentar extrair scores.
        import math

        try:
            n_rows = len(eval_result.scores)  # type: ignore[attr-defined]
            failed_rows = sum(
                1
                for row in eval_result.scores  # type: ignore[attr-defined]
                if not row or any(
                    v is None or (isinstance(v, float) and math.isnan(v))
                    for v in row.values()
                )
            )
        except Exception:
            n_rows, failed_rows = 0, 0

        if n_rows and failed_rows == n_rows:
            result["error"] = (
                f"RAGAS executou as {n_rows} linhas, mas todas as chamadas "
                "ao LLM-juiz falharam (ver logs do processo para a exceção "
                "real por job — nesta sessão: AuthenticationError 401, "
                "OPENAI_API_KEY inválida/expirada). Nenhum score real "
                "disponível."
            )
            return result

        scores = dict(eval_result)
        result["scores"] = scores
        result["per_question"] = [
            {"question": q, "answer": a[:200], "mode": r.mode}
            for q, a, r in zip(questions, answers, records)
        ]
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    return result
