"""
memory/memory_manager_v2.py

V2 do Memory Manager: mesma orquestração da V1 (memory_manager.py) --
short-term + long-term + vector -- mas com os backends de banco de dados
"de verdade" no lugar de JSON local e Chroma local:

  - Long-term memory -> MongoDB   (memory/long_term_memory_mongo_v2.py)
  - Vector memory     -> pgvector (memory/vector_memory_pgvector_v2.py)
  - Short-term memory -> igual à V1 (não precisa de banco; vive na sessão)

A V1 continua funcionando exatamente como antes (JSON + Chroma); esta V2 é
uma implementação alternativa com a mesma API pública
(`add_turn`, `get_relevant_memories`, `build_context_for_agent`,
`remember`, `recall`), para quem quiser rodar o agente contra
infraestrutura gerenciada (Mongo Atlas, Postgres com pgvector) em vez de
arquivos locais.
"""

from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory_mongo_v2 import MongoLongTermMemory
from memory.vector_memory_pgvector_v2 import PgVectorMemory


class MemoryManagerV2:
    def __init__(
        self,
        max_short_turns: int = 10,
        mongo_uri: str = None,
        postgres_dsn: str = None,
    ):
        self.short = ShortTermMemory(max_turns=max_short_turns)
        self.long = MongoLongTermMemory(uri=mongo_uri)
        self._vector = None
        self._postgres_dsn = postgres_dsn

    @property
    def vector(self) -> PgVectorMemory:
        if self._vector is None:
            self._vector = PgVectorMemory(dsn=self._postgres_dsn)
        return self._vector

    def add_turn(self, user_msg: str, assistant_msg: str):
        self.short.add("user", user_msg)
        self.short.add("assistant", assistant_msg)
        self.vector.store(f"User: {user_msg}\nAssistant: {assistant_msg}")

    def get_relevant_memories(self, query: str, k: int = 3) -> str:
        memories = self.vector.search(query, k=k)
        if not memories:
            return ""
        return "\n---\n".join(memories)

    def build_context_for_agent(self, query: str) -> str:
        short_ctx = self.short.get_context_string()
        mem_ctx = self.get_relevant_memories(query)
        parts = []
        if short_ctx:
            parts.append(f"[Histórico recente]\n{short_ctx}")
        if mem_ctx:
            parts.append(f"[Memórias relevantes]\n{mem_ctx}")
        return "\n\n".join(parts)

    def remember(self, key: str, value):
        self.long.store(key, value)

    def recall(self, key: str):
        return self.long.retrieve(key)

    def close(self):
        self.long.close()
        if self._vector is not None:
            self._vector.close()
