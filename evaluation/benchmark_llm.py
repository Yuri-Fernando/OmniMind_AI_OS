"""
Benchmark de LLMs — executa o mesmo conjunto de perguntas em múltiplos provedores
e retorna uma tabela comparativa de latência, qualidade e tokens.
"""
import time
from typing import List, Dict, Tuple
from core.agent_runtime import AgentRuntime
from evaluation.metrics import answer_relevance, token_overlap_f1, length_score, aggregate_scores


DEFAULT_QUESTIONS = [
    "Qual a capital do Brasil?",
    "Explique o que é inteligência artificial em 2 frases.",
    "Quanto é 347 × 29?",
    "Quais são os principais benefícios da energia solar?",
]


def benchmark(
    providers: List[Tuple[str, str]],
    questions: List[str] = None,
    reference_answers: List[str] = None,
) -> List[Dict]:
    """
    Args:
        providers: lista de (provider, model), ex: [('openai','gpt-4o-mini'), ('ollama','mistral')]
        questions: lista de perguntas; usa DEFAULT_QUESTIONS se None
        reference_answers: respostas de referência (opcional, para F1)

    Returns:
        Lista de dicts com métricas por provedor/pergunta
    """
    questions = questions or DEFAULT_QUESTIONS
    results = []

    for provider, model in providers:
        try:
            runtime = AgentRuntime(provider=provider, model=model)
        except Exception as e:
            results.append({"provider": provider, "model": model, "error": str(e)})
            continue

        for i, q in enumerate(questions):
            t0 = time.time()
            try:
                state = runtime.run(q)
                answer = state.get("answer", "")
                latency = round((time.time() - t0) * 1000, 2)
                scores = [answer_relevance(answer, q), length_score(answer)]
                if reference_answers and i < len(reference_answers):
                    scores.append(token_overlap_f1(answer, reference_answers[i]))
                results.append({
                    "provider": provider,
                    "model": model,
                    "question": q,
                    "answer": answer[:200],
                    "latency_ms": latency,
                    "quality_score": aggregate_scores(scores),
                })
            except Exception as e:
                results.append({
                    "provider": provider,
                    "model": model,
                    "question": q,
                    "error": str(e),
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                })

    return results


def print_benchmark_table(results: List[Dict]):
    print(f"\n{'Provider':<12} {'Model':<20} {'Latency(ms)':<14} {'Quality':<10} {'Question'}")
    print("-" * 90)
    for r in results:
        if "error" in r:
            print(f"{r['provider']:<12} {r['model']:<20} {'ERROR':<14} {'':<10} {r.get('question','')[:40]}")
        else:
            print(
                f"{r['provider']:<12} {r['model']:<20} "
                f"{r['latency_ms']:<14} {r['quality_score']:<10.3f} "
                f"{r['question'][:40]}"
            )
