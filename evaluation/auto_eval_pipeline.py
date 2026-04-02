"""
Pipeline de avaliação automática — executa benchmark e gera relatório JSON.
"""
import json
import os
from datetime import datetime
from evaluation.benchmark_llm import benchmark, DEFAULT_QUESTIONS
from evaluation.agent_metrics import evaluate_run


def run_auto_eval(
    providers,
    questions=None,
    output_dir: str = "evaluation/reports",
) -> str:
    """
    Executa benchmark automático e salva relatório.

    Args:
        providers: lista de (provider, model)
        questions: perguntas de teste
        output_dir: onde salvar o JSON

    Returns:
        Caminho do arquivo de relatório gerado.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = benchmark(providers, questions or DEFAULT_QUESTIONS)

    report = {
        "timestamp": datetime.now().isoformat(),
        "providers_tested": [f"{p}/{m}" for p, m in providers],
        "total_runs": len(results),
        "results": results,
    }

    filename = os.path.join(
        output_dir, f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Relatório salvo em: {filename}")
    return filename
