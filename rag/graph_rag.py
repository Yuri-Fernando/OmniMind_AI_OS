"""GraphRAG — retrieval híbrido: busca vetorial (similaridade semântica) +
travessia do grafo de conhecimento (relações estruturadas), mesclados num
único contexto para o LLM.

Este projeto já tinha os dois pedaços separados — `rag/` (Chroma +
embeddings) e `knowledge_graph/` (extração de entidades/relações via LLM +
travessia em grafo). GraphRAG é a composição real dos dois, não apenas os
dois nomes lado a lado: cada documento é indexado nos dois lados ao mesmo
tempo (`ingest`), e cada consulta usa ambos (`retrieve`).

A diferença prática de RAG puro (só similaridade): duas entidades
relacionadas podem não ser textualmente parecidas ("Maria Curie" e
"Sorbonne" não têm palavras em comum), então uma pergunta relacional
("onde Maria Curie trabalhou?") pode não recuperar o chunk certo por
similaridade — mas o grafo tem a aresta `trabalhou_em` direta. GraphRAG
soma os dois sinais em vez de depender só de um.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from knowledge_graph.entity_extractor import EntityExtractor
from knowledge_graph.graph_builder import KnowledgeGraphBuilder
from knowledge_graph.graph_retriever import GraphRetriever


class VectorStore(Protocol):
    """Interface mínima — `memory/vector_memory.py::VectorMemory` já a
    implementa; testes usam um fake com a mesma forma."""

    def store(self, text: str, metadata: dict | None = None) -> None: ...
    def search(self, query: str, k: int = 3) -> list[str]: ...


@dataclass
class GraphRAGContext:
    query: str
    vector_chunks: list[str] = field(default_factory=list)
    graph_entities: list[dict] = field(default_factory=list)
    graph_context: str = ""

    def render(self) -> str:
        """Contexto final, pronto para ir no prompt do LLM."""
        parts = []
        if self.vector_chunks:
            parts.append("[Trechos relevantes]\n" + "\n---\n".join(self.vector_chunks))
        if self.graph_context:
            parts.append("[Relações do grafo de conhecimento]\n" + self.graph_context)
        return "\n\n".join(parts)


class GraphRAGPipeline:
    def __init__(
        self,
        vector_store: VectorStore,
        kg_builder: KnowledgeGraphBuilder | None = None,
        entity_extractor: EntityExtractor | None = None,
        provider: str = "ollama",
        model: str = "mistral",
    ):
        self.vector_store = vector_store
        self.kg = kg_builder or KnowledgeGraphBuilder(provider, model)
        self.retriever = GraphRetriever(self.kg)
        # o KnowledgeGraphBuilder já tem seu próprio EntityExtractor
        # (`self.kg.extractor`); reaproveitamos por padrão para não
        # instanciar dois LLMs à toa, mas aceitamos injeção para testes.
        self.extractor = entity_extractor or self.kg.extractor

    def ingest(self, text: str, source: str = "") -> None:
        """Indexa o mesmo texto nos dois lados: vetorial (chunk completo) e
        grafo (entidades + relações extraídas pelo LLM)."""
        self.vector_store.store(text, metadata={"source": source})
        self.kg.add_text(text, source=source)

    def retrieve(self, query: str, k: int = 3) -> GraphRAGContext:
        ctx = GraphRAGContext(query=query)

        # 1. busca vetorial — similaridade semântica
        ctx.vector_chunks = self.vector_store.search(query, k=k)

        # 2. entidades mencionadas na query -> vizinhança direta no grafo
        query_entities = self.extractor.extract(query)
        graph_lines = []
        for ent in query_entities:
            name = ent["text"]
            neighbors = self.retriever.get_neighbors(name)
            if neighbors:
                ctx.graph_entities.append({"entity": name, "neighbors": neighbors})
                rels = "; ".join(f"{n['relation']} -> {n['entity']}" for n in neighbors[:5])
                graph_lines.append(f"{name}: {rels}")
        ctx.graph_context = "\n".join(graph_lines)
        return ctx

    def answer_context(self, query: str, k: int = 3) -> str:
        return self.retrieve(query, k=k).render()

    def stats(self) -> dict:
        return {**self.kg.stats(), "vector_store": type(self.vector_store).__name__}
