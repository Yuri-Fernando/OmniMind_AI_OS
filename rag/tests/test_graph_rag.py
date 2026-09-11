"""Testes do GraphRAG — usam fakes de vector store / grafo / extractor
(sem LLM, sem Chroma) para exercitar a lógica real de composição
vetorial+grafo de `graph_rag.py`, sem depender de um provedor de LLM rodando."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rag.graph_rag import GraphRAGPipeline  # noqa: E402


class FakeVectorStore:
    """Busca por overlap de palavras — suficiente para testar a composição,
    sem precisar de embeddings de verdade."""

    def __init__(self):
        self.docs: list[str] = []

    def store(self, text: str, metadata: dict | None = None) -> None:
        self.docs.append(text)

    def search(self, query: str, k: int = 3) -> list[str]:
        q_words = set(query.lower().split())
        scored = [(len(q_words & set(d.lower().split())), d) for d in self.docs]
        scored.sort(key=lambda t: -t[0])
        return [d for score, d in scored[:k] if score > 0]


class FakeKnowledgeGraph:
    """Substitui `KnowledgeGraphBuilder` — mesma forma (`nodes`, `edges`,
    `add_text`, `stats`) sem chamar LLM nenhum."""

    def __init__(self):
        self.nodes: dict = {}
        self.edges: list = []
        self.ingested: list[tuple[str, str]] = []

    def add_node(self, name: str, type_: str = "unknown") -> None:
        self.nodes[name] = {"name": name, "type": type_}

    def add_edge(self, source: str, relation: str, target: str) -> None:
        self.edges.append({"source": source, "relation": relation, "target": target})

    def add_text(self, text: str, source: str = "") -> None:
        self.ingested.append((text, source))

    def stats(self) -> dict:
        return {"nodes": len(self.nodes), "edges": len(self.edges)}


class FakeExtractor:
    def __init__(self, mapping: dict[str, list[dict]]):
        self.mapping = mapping

    def extract(self, text: str) -> list[dict]:
        return self.mapping.get(text, [])


def _build_pipeline():
    vs = FakeVectorStore()
    kg = FakeKnowledgeGraph()
    kg.add_node("Marie Curie", "person")
    kg.add_node("Sorbonne", "organization")
    kg.add_node("Pierre Curie", "person")
    kg.add_edge("Marie Curie", "trabalhou_em", "Sorbonne")
    kg.add_edge("Marie Curie", "colaborou_com", "Pierre Curie")

    extractor = FakeExtractor({
        "Onde Marie Curie trabalhou?": [{"text": "Marie Curie", "label": "person"}],
        "Quem é Pierre Curie?": [{"text": "Pierre Curie", "label": "person"}],
    })

    pipeline = GraphRAGPipeline(vector_store=vs, kg_builder=kg, entity_extractor=extractor)
    return pipeline, vs, kg


def test_ingest_indexes_both_vector_and_graph_sides():
    pipeline, vs, kg = _build_pipeline()
    pipeline.ingest("Marie Curie trabalhou com Pierre Curie na Sorbonne.", source="bio.txt")

    assert vs.docs == ["Marie Curie trabalhou com Pierre Curie na Sorbonne."]
    assert kg.ingested == [("Marie Curie trabalhou com Pierre Curie na Sorbonne.", "bio.txt")]


def test_graph_context_surfaces_relation_vector_search_would_miss():
    """A pergunta é relacional ('onde trabalhou') — um chunk sobre
    'RandomForest' não tem overlap de palavras com a query, então a busca
    vetorial sozinha não traria nada relevante. O grafo tem a aresta direta
    `trabalhou_em -> Sorbonne`, que é o dado que realmente responde."""
    pipeline, vs, kg = _build_pipeline()
    vs.store("O modelo de churn usa RandomForest e é avaliado por AUC.")

    ctx = pipeline.retrieve("Onde Marie Curie trabalhou?")

    assert ctx.vector_chunks == []  # nada relevante por similaridade de palavras
    assert any(e["entity"] == "Marie Curie" for e in ctx.graph_entities)
    assert "trabalhou_em -> Sorbonne" in ctx.graph_context
    rendered = ctx.render()
    assert "Sorbonne" in rendered
    assert "[Relações do grafo de conhecimento]" in rendered


def test_vector_and_graph_context_combine_when_both_have_signal():
    pipeline, vs, kg = _build_pipeline()
    vs.store("Marie Curie foi pioneira em radioatividade.")

    ctx = pipeline.retrieve("Onde Marie Curie trabalhou?")

    assert ctx.vector_chunks  # overlap em "Marie Curie"
    assert ctx.graph_context  # aresta trabalhou_em -> Sorbonne
    rendered = ctx.render()
    assert "[Trechos relevantes]" in rendered
    assert "[Relações do grafo de conhecimento]" in rendered


def test_query_without_known_entity_falls_back_to_vector_only():
    pipeline, vs, kg = _build_pipeline()
    vs.store("Documento qualquer sem entidades conhecidas do grafo.")

    ctx = pipeline.retrieve("Documento qualquer")

    assert ctx.vector_chunks
    assert ctx.graph_entities == []
    assert ctx.graph_context == ""


def test_stats_reports_graph_size_and_vector_store_type():
    pipeline, vs, kg = _build_pipeline()
    stats = pipeline.stats()
    assert stats["nodes"] == 3
    assert stats["edges"] == 2
    assert stats["vector_store"] == "FakeVectorStore"
