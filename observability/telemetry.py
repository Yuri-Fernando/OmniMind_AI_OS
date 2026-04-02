"""
Telemetria do AIOS — coleta métricas de uso: latência, tokens, erros.
"""
from dataclasses import dataclass, field
from typing import Dict, List
import time


@dataclass
class RunMetrics:
    provider: str
    model: str
    question: str
    latency_ms: float
    tokens_in: int = 0
    tokens_out: int = 0
    success: bool = True
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class Telemetry:
    def __init__(self):
        self._runs: List[RunMetrics] = []

    def record(self, **kwargs) -> RunMetrics:
        m = RunMetrics(**kwargs)
        self._runs.append(m)
        return m

    def summary(self) -> Dict:
        if not self._runs:
            return {}
        latencies = [r.latency_ms for r in self._runs]
        return {
            "total_runs": len(self._runs),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "errors": sum(1 for r in self._runs if not r.success),
            "providers_used": list({r.provider for r in self._runs}),
        }

    def by_provider(self) -> Dict[str, List[RunMetrics]]:
        result: Dict[str, List[RunMetrics]] = {}
        for run in self._runs:
            result.setdefault(run.provider, []).append(run)
        return result

    def reset(self):
        self._runs.clear()


telemetry = Telemetry()
