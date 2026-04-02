"""
Métricas específicas do agente AIOS: latência, tokens, sucesso por nó.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class NodeMetric:
    name: str
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class AgentRunReport:
    question: str
    provider: str
    model: str
    answer: str
    total_latency_ms: float
    node_metrics: List[NodeMetric] = field(default_factory=list)
    relevance_score: float = 0.0
    context_recall: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "provider": self.provider,
            "model": self.model,
            "answer": self.answer,
            "total_latency_ms": self.total_latency_ms,
            "relevance_score": self.relevance_score,
            "context_recall": self.context_recall,
            "nodes": [
                {"name": n.name, "latency_ms": n.latency_ms, "success": n.success}
                for n in self.node_metrics
            ],
        }


def evaluate_run(state: dict, start_time: float) -> AgentRunReport:
    from evaluation.metrics import answer_relevance, context_recall as ctx_recall

    elapsed = round((time.time() - start_time) * 1000, 2)
    answer = state.get("answer", "")
    question = state.get("question", "")
    context = state.get("context", "")

    return AgentRunReport(
        question=question,
        provider=state.get("provider", "unknown"),
        model=state.get("model", "unknown"),
        answer=answer,
        total_latency_ms=elapsed,
        relevance_score=answer_relevance(answer, question),
        context_recall=ctx_recall(answer, context),
    )
