"""Geração de embeddings com sentence-transformers (local, sem API)."""
from typing import List
from core.config import EMBEDDING_MODEL


class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def embed(self, text: str) -> List[float]:
        self._load()
        return self._model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._load()
        return self._model.encode(texts).tolist()

    def similarity(self, text_a: str, text_b: str) -> float:
        from sentence_transformers import util
        self._load()
        emb_a = self._model.encode(text_a, convert_to_tensor=True)
        emb_b = self._model.encode(text_b, convert_to_tensor=True)
        return float(util.cos_sim(emb_a, emb_b))
