"""
Golden dataset reprodutível para avaliação RAGAS/DeepEval.

Corpus: os próprios documentos reais do repositório (README.md,
rag/GRAPH_RAG.md, architecture_readme.md) — sem dados sintéticos.
Perguntas e respostas de referência (ground_truth) foram escritas manualmente
a partir do conteúdo real desses arquivos, então qualquer resposta correta do
agente deve ser rastreável a um trecho real do corpus (Artigo IV — No
Invention, aplicado aqui ao próprio dataset de avaliação).

Nada de aleatoriedade: a lista é fixa e versionada, então rodar o eval duas
vezes sobre o mesmo corpus produz o mesmo conjunto de perguntas/contexto de
entrada (a única fonte de não-determinismo é a chamada ao LLM externo, fora
do controle deste módulo — ver `evaluation/real_pipeline.py`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent

# Documentos reais usados como corpus de RAG para este eval.
CORPUS_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "rag" / "GRAPH_RAG.md",
    REPO_ROOT / "architecture_readme.md",
]


@dataclass(frozen=True)
class GoldenItem:
    question: str
    ground_truth: str


# Perguntas fixas, com resposta de referência extraída do conteúdo real dos
# arquivos em CORPUS_FILES. Mantidas deliberadamente objetivas (fatos sobre o
# próprio projeto) para que RAGAS/DeepEval tenham um ground_truth verificável.
GOLDEN_SET: List[GoldenItem] = [
    GoldenItem(
        question="Quais ferramentas de avaliação o OmniMind AI OS usa?",
        ground_truth=(
            "RAGAS, DeepEval, métricas customizadas, benchmark de LLMs, "
            "Agent Arena e Leaderboard."
        ),
    ),
    GoldenItem(
        question="Quais ferramentas de observabilidade o projeto usa?",
        ground_truth=(
            "Langfuse, OpenTelemetry, logs estruturados, telemetria e "
            "execution tracing."
        ),
    ),
    GoldenItem(
        question="Qual é o ciclo de execução orientado por objetivos do OmniMind?",
        ground_truth="Goal → Plan → Execute → Learn → Improve → Final Answer.",
    ),
    GoldenItem(
        question="Por que busca vetorial pura falha em perguntas relacionais no GraphRAG?",
        ground_truth=(
            "Porque duas entidades relacionadas podem não compartilhar "
            "palavras (ex.: 'Marie Curie' e 'Sorbonne'), então a busca por "
            "similaridade textual pode não recuperar o chunk certo; o grafo "
            "de conhecimento tem a aresta direta (ex.: trabalhou_em -> "
            "Sorbonne) que resolve a pergunta relacional."
        ),
    ),
    GoldenItem(
        question="Quais interfaces o GraphRAGPipeline expõe?",
        ground_truth="ingest(), retrieve() e answer_context(), além de stats().",
    ),
    GoldenItem(
        question="Que backend de vector store o GraphRAG usa por padrão?",
        ground_truth=(
            "Qualquer objeto com .store(text, metadata) e .search(query, k); "
            "memory/vector_memory.py::VectorMemory (Chroma) já implementa "
            "essa interface e é o backend padrão em uso real."
        ),
    ),
    GoldenItem(
        question="Quantos testes existem para o GraphRAG e o que eles evitam depender?",
        ground_truth=(
            "5 testes em rag/tests/test_graph_rag.py, que usam fakes de "
            "vector store e grafo para evitar depender de Chroma ou de um "
            "provedor de LLM rodando."
        ),
    ),
    GoldenItem(
        question="Quais camadas compõem a Enterprise Architecture do OmniMind?",
        ground_truth=(
            "Interaction Layer, Goal Management Layer e Multi-Agent "
            "Coordination (Agent Router + Registry + Communication), "
            "seguidas da Agent Execution Layer."
        ),
    ),
]


def load_corpus_text() -> str:
    """Concatena o texto real dos arquivos do corpus (lança erro claro se
    algum arquivo não existir, em vez de inventar conteúdo)."""
    parts = []
    for path in CORPUS_FILES:
        if not path.exists():
            raise FileNotFoundError(
                f"Arquivo do corpus golden não encontrado: {path}"
            )
        parts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)
