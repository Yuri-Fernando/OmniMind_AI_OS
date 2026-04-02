"""
Runtime do agente: executa o grafo e retorna o resultado com metadados de tempo.
"""
import time
from core.orchestration_graph import build_graph
from core.state_manager import new_state


class AgentRuntime:
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.graph = build_graph(provider=provider, model=model)

    def run(self, question: str) -> dict:
        """Executa o agente e retorna o estado final com latência."""
        state = new_state(question, provider=self.provider, model=self.model)
        start = time.time()
        result = self.graph.invoke(state)
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        return result

    def stream(self, question: str):
        """Executa o agente em modo streaming (yield de cada nó)."""
        state = new_state(question, provider=self.provider, model=self.model)
        for chunk in self.graph.stream(state):
            yield chunk
