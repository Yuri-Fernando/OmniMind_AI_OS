"""
memory/vector_memory_pgvector_v2.py

V2 da Vector Memory: a V1 (vector_memory.py) usa Chroma (arquivo local via
SQLite) como vector store. Esta V2 mantém a mesma interface pública
(`store`, `search`, `clear`) e os mesmos embeddings
(sentence-transformers/all-MiniLM-L6-v2), mas persiste em **Postgres +
pgvector** -- útil quando a memória do agente precisa viver no mesmo banco
relacional do resto do sistema (joins com outras tabelas, backups/HA de
Postgres, múltiplas instâncias do agente lendo/escrevendo concorrentemente).

Requer a extensão `pgvector` habilitada no Postgres:
    CREATE EXTENSION IF NOT EXISTS vector;

Uso:
    from memory.vector_memory_pgvector_v2 import PgVectorMemory

    vm = PgVectorMemory(dsn="postgresql://user:pass@localhost:5432/agent_os")
    vm.store("O usuário prefere respostas curtas.", metadata={"source": "chat"})
    vm.search("como o usuário gosta de receber respostas?", k=3)
"""

import json
import os
from typing import List, Optional

import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # dimensão do all-MiniLM-L6-v2


class PgVectorMemory:
    def __init__(
        self,
        dsn: str = None,
        table_name: str = "agent_memory",
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self.dsn = dsn or os.getenv("POSTGRES_DSN", "postgresql://localhost:5432/agent_os")
        self.table_name = table_name
        self.model = SentenceTransformer(embedding_model)

        self._conn = psycopg2.connect(self.dsn)
        self._conn.autocommit = True
        register_vector(self._conn)
        self._ensure_schema()

    def _ensure_schema(self):
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}'::jsonb,
                    embedding VECTOR({EMBEDDING_DIM}) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
            # índice HNSW para busca aproximada por similaridade (cosine)
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name} USING hnsw (embedding vector_cosine_ops);
                """
            )

    def store(self, text: str, metadata: Optional[dict] = None):
        embedding = self.model.encode(text).tolist()
        with self._conn.cursor() as cur:
            execute_values(
                cur,
                f"INSERT INTO {self.table_name} (content, metadata, embedding) VALUES %s",
                [(text, json.dumps(metadata or {}), embedding)],
            )

    def search(self, query: str, k: int = 3) -> List[str]:
        query_embedding = self.model.encode(query).tolist()
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT content FROM {self.table_name}
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (query_embedding, k),
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def clear(self):
        with self._conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {self.table_name};")

    def close(self):
        self._conn.close()
