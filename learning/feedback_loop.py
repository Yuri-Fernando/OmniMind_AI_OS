"""Loop de feedback: coleta avaliações humanas e ajusta comportamento."""
import json, os, time
from typing import List, Callable, Optional


class FeedbackLoop:
    def __init__(self, storage_path: str = "data/feedback.json"):
        self.storage_path = storage_path
        self.records: List[dict] = []
        self._on_feedback: List[Callable] = []
        self._load()

    def collect(self, question: str, answer: str, rating: int, comment: str = "") -> dict:
        """Registra feedback humano (rating: 1-5)."""
        record = {
            "question": question, "answer": answer,
            "rating": rating, "comment": comment,
            "ts": time.time(),
        }
        self.records.append(record)
        self._save()
        for cb in self._on_feedback:
            cb(record)
        return record

    def on_feedback(self, callback: Callable):
        """Registra callback executado a cada novo feedback."""
        self._on_feedback.append(callback)

    def average_rating(self) -> float:
        if not self.records:
            return 0.0
        return sum(r["rating"] for r in self.records) / len(self.records)

    def low_rated(self, threshold: int = 2) -> List[dict]:
        return [r for r in self.records if r["rating"] <= threshold]

    def summary(self) -> dict:
        return {
            "total": len(self.records),
            "avg_rating": round(self.average_rating(), 2),
            "low_rated": len(self.low_rated()),
        }

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.records, f, indent=2)

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                self.records = json.load(f)
