"""
memory/long_term_memory_mongo_v2.py

V2 da Long-Term Memory: a V1 (long_term_memory.py) persiste em um arquivo
JSON local -- funciona, mas não escala para múltiplas instâncias do agente
nem oferece query por campo além de `key`/`category`. Esta V2 mantém
exatamente a mesma interface pública (`store`, `retrieve`,
`search_by_category`, `all_entries`, `delete`) só que backada por MongoDB,
com schema por documento (evento/fato do agente), CRUD e índices para as
buscas mais comuns.

O README do projeto já citava `MONGODB_URI` como variável de ambiente
opcional ("se usar sincronização em nuvem") -- esta V2 é a implementação
que faltava para essa variável ter efeito de verdade.

Uso:
    from memory.long_term_memory_mongo_v2 import MongoLongTermMemory

    ltm = MongoLongTermMemory(uri="mongodb://localhost:27017")
    ltm.store("user_name", "Yuri", category="profile")
    ltm.retrieve("user_name")
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from pymongo import MongoClient, ASCENDING


class MongoLongTermMemory:
    def __init__(
        self,
        uri: str = None,
        db_name: str = "agent_os",
        collection_name: str = "long_term_memory",
    ):
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self._client = MongoClient(self.uri)
        self._collection = self._client[db_name][collection_name]

        # Índices: busca por chave (upsert) e por categoria (search_by_category)
        self._collection.create_index([("key", ASCENDING)], unique=True)
        self._collection.create_index([("category", ASCENDING)])

    def store(self, key: str, value: Any, category: str = "general"):
        entry = {
            "key": key,
            "value": value,
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._collection.update_one({"key": key}, {"$set": entry}, upsert=True)

    def retrieve(self, key: str) -> Any:
        doc = self._collection.find_one({"key": key})
        return doc["value"] if doc else None

    def search_by_category(self, category: str) -> List[Dict]:
        docs = self._collection.find({"category": category})
        return [self._strip_mongo_id(d) for d in docs]

    def all_entries(self) -> List[Dict]:
        docs = self._collection.find()
        return [self._strip_mongo_id(d) for d in docs]

    def delete(self, key: str):
        self._collection.delete_one({"key": key})

    @staticmethod
    def _strip_mongo_id(doc: Dict) -> Dict:
        doc = dict(doc)
        doc.pop("_id", None)
        return doc

    def close(self):
        self._client.close()
