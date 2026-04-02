"""
Memória de longo prazo — persiste fatos importantes em JSON local.
Sobrevive entre sessões.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any


class LongTermMemory:
    def __init__(self, storage_path: str = "memory/ltm_store.json"):
        self.storage_path = storage_path
        self._store: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self._store = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._store, f, ensure_ascii=False, indent=2)

    def store(self, key: str, value: Any, category: str = "general"):
        entry = {
            "key": key,
            "value": value,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        }
        # Atualiza se a chave já existe
        for i, item in enumerate(self._store):
            if item["key"] == key:
                self._store[i] = entry
                self._save()
                return
        self._store.append(entry)
        self._save()

    def retrieve(self, key: str) -> Any:
        for item in self._store:
            if item["key"] == key:
                return item["value"]
        return None

    def search_by_category(self, category: str) -> List[Dict]:
        return [i for i in self._store if i["category"] == category]

    def all_entries(self) -> List[Dict]:
        return list(self._store)

    def delete(self, key: str):
        self._store = [i for i in self._store if i["key"] != key]
        self._save()
