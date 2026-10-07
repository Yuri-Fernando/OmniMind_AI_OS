"""
Retriever TF-IDF — recuperação lexical real (sem LLM, sem rede, determinística)
usada pelo eval reprodutível em `evaluation/real_pipeline.py`.

Por que TF-IDF em vez do backend real do projeto (Chroma +
sentence-transformers, `memory/vector_memory.py::VectorMemory`): esse backend
baixa um modelo do HuggingFace Hub na primeira chamada (rede + ~80MB) e usa
embeddings densos não-determinísticos entre versões de torch/CUDA. Para um
golden-set pequeno e um relatório que precisa ser reproduzível em qualquer
máquina sem depender de download externo, TF-IDF + similaridade de cosseno é
uma recuperação real (não mockada) e 100% determinística. O pipeline de RAG
real do projeto (`rag/rag_pipeline.py`, `rag/graph_rag.py`) continua sendo o
usado em produção; este módulo é especificamente o retriever do harness de
avaliação.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Chunking determinístico por caracteres (mesmos parâmetros de
    CHUNK_SIZE/CHUNK_OVERLAP usados em core/config.py e rag/rag_pipeline.py)."""
    if overlap >= chunk_size:
        raise ValueError("overlap deve ser menor que chunk_size")
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
    return chunks


@dataclass
class TfidfRetriever:
    """Implementa a mesma interface mínima de `rag.graph_rag.VectorStore`
    (`store`/`search`), mas com TF-IDF real por baixo."""

    documents: List[str]

    def __post_init__(self) -> None:
        if not self.documents:
            raise ValueError("TfidfRetriever precisa de ao menos 1 documento")
        self._vectorizer = TfidfVectorizer()
        self._matrix = self._vectorizer.fit_transform(self.documents)

    def store(self, text: str, metadata: dict | None = None) -> None:
        raise NotImplementedError(
            "TfidfRetriever é construído com o corpus fixo no __init__; "
            "não suporta ingestão incremental (fora do escopo do eval)."
        )

    def search(self, query: str, k: int = 3) -> List[str]:
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
        return [self.documents[i] for i in ranked[:k] if scores[i] > 0]

    def search_with_scores(self, query: str, k: int = 3):
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
        return [(self.documents[i], float(scores[i])) for i in ranked[:k] if scores[i] > 0]
