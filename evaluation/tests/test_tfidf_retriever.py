"""Testes reais (sem mock) do retriever TF-IDF e do chunker determinístico
usados pelo harness de avaliação."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from evaluation.tfidf_retriever import TfidfRetriever, chunk_text


def test_chunk_text_respects_chunk_size_and_overlap():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=150)
    assert len(chunks) > 1
    assert all(len(c) <= 800 for c in chunks)
    # cobre o texto inteiro (último chunk termina no fim do texto)
    assert chunks[-1] == "a" * ((2000 - 1) % 800 + 1) or len("".join(chunks)) >= len(text) - 150


def test_chunk_text_rejects_overlap_not_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("texto qualquer", chunk_size=100, overlap=100)


def test_chunk_text_single_short_text_returns_one_chunk():
    assert chunk_text("texto curto", chunk_size=800, overlap=150) == ["texto curto"]


def test_retriever_ranks_most_lexically_similar_document_first():
    docs = [
        "O OmniMind usa RAGAS e DeepEval para avaliação de RAG.",
        "Receita de bolo de chocolate com cobertura.",
        "Langfuse é usado para observabilidade e tracing de agentes.",
    ]
    retriever = TfidfRetriever(documents=docs)

    results = retriever.search("Quais ferramentas de avaliação o projeto usa?", k=1)

    assert results == [docs[0]]


def test_retriever_returns_empty_when_no_overlap():
    docs = ["Receita de bolo de chocolate."]
    retriever = TfidfRetriever(documents=docs)

    assert retriever.search("Qual a capital da França?", k=3) == []


def test_retriever_search_with_scores_is_sorted_descending():
    docs = [
        "avaliação com RAGAS e DeepEval",
        "avaliação, avaliação, avaliação com RAGAS",
        "um texto completamente não relacionado sobre jardinagem",
    ]
    retriever = TfidfRetriever(documents=docs)

    scored = retriever.search_with_scores("avaliação com RAGAS", k=3)

    scores = [s for _, s in scored]
    assert scores == sorted(scores, reverse=True)
    assert scored[0][0] == docs[1]  # mais repetições do termo da query


def test_retriever_requires_non_empty_corpus():
    with pytest.raises(ValueError):
        TfidfRetriever(documents=[])


def test_retriever_store_is_not_supported():
    retriever = TfidfRetriever(documents=["doc único"])
    with pytest.raises(NotImplementedError):
        retriever.store("novo texto")
