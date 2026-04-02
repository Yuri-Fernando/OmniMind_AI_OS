"""Armazenamento vetorial com FAISS (persistência em disco)."""
import os, json
import numpy as np
from typing import List, Tuple
from knowledge.embeddings import EmbeddingModel


class VectorStore:
    def __init__(self, store_path: str = "vector_db", model: EmbeddingModel = None):
        self.store_path = store_path
        self.emb = model or EmbeddingModel()
        self._index = None
        self._texts: List[str] = []
        self._meta: List[dict] = []
        os.makedirs(store_path, exist_ok=True)
        self._load()

    def add(self, text: str, metadata: dict = None):
        import faiss
        vec = np.array([self.emb.embed(text)], dtype="float32")
        if self._index is None:
            self._index = faiss.IndexFlatL2(vec.shape[1])
        self._index.add(vec)
        self._texts.append(text)
        self._meta.append(metadata or {})
        self._save()

    def add_batch(self, texts: List[str], metas: List[dict] = None):
        for i, t in enumerate(texts):
            m = metas[i] if metas else {}
            self.add(t, m)

    def search(self, query: str, k: int = 3) -> List[Tuple[str, float, dict]]:
        if self._index is None or len(self._texts) == 0:
            return []
        import faiss
        vec = np.array([self.emb.embed(query)], dtype="float32")
        k = min(k, len(self._texts))
        distances, indices = self._index.search(vec, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                results.append((self._texts[idx], float(dist), self._meta[idx]))
        return results

    def _save(self):
        import faiss
        if self._index:
            faiss.write_index(self._index, os.path.join(self.store_path, "index.faiss"))
        with open(os.path.join(self.store_path, "texts.json"), "w") as f:
            json.dump({"texts": self._texts, "meta": self._meta}, f)

    def _load(self):
        idx_path = os.path.join(self.store_path, "index.faiss")
        txt_path = os.path.join(self.store_path, "texts.json")
        if os.path.exists(idx_path) and os.path.exists(txt_path):
            import faiss
            self._index = faiss.read_index(idx_path)
            with open(txt_path) as f:
                data = json.load(f)
            self._texts = data.get("texts", [])
            self._meta = data.get("meta", [])
