"""
Gerenciador de memória unificado — orquestra short-term, long-term e vector.
"""
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory
from memory.vector_memory import VectorMemory


class MemoryManager:
    def __init__(self, max_short_turns: int = 10, ltm_path: str = "memory/ltm_store.json"):
        self.short = ShortTermMemory(max_turns=max_short_turns)
        self.long = LongTermMemory(storage_path=ltm_path)
        self._vector = None  # lazy init para não carregar embeddings sem necessidade

    @property
    def vector(self) -> VectorMemory:
        if self._vector is None:
            self._vector = VectorMemory()
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
