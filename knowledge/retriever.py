"""Retriever RAG: busca chunks relevantes para uma query."""
from typing import List
from knowledge.vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore = None, k: int = 3):
        self.store = store or VectorStore()
        self.k = k

    def retrieve(self, query: str, k: int = None) -> List[str]:
        results = self.store.search(query, k=k or self.k)
        return [text for text, _, _ in results]

    def retrieve_with_scores(self, query: str, k: int = None) -> List[dict]:
        results = self.store.search(query, k=k or self.k)
        return [{"text": t, "score": s, "meta": m} for t, s, m in results]

    def build_context(self, query: str, separator: str = "\n\n---\n\n") -> str:
        chunks = self.retrieve(query)
        if not chunks:
            return ""
        return separator.join(chunks)
