"""Rastreamento de execução do grafo de agente: captura estado por nó."""
import time
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class NodeTrace:
    node: str
    input_state: Dict
    output_state: Dict
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    error: str = ""


class ExecutionTrace:
    def __init__(self, run_id: str = ""):
        self.run_id = run_id or f"run_{int(time.time())}"
        self.traces: List[NodeTrace] = []
        self._start_time: float = time.time()

    def record(self, node: str, input_state: dict, output_state: dict,
               duration_ms: float, error: str = ""):
        self.traces.append(NodeTrace(
            node=node,
            input_state={k: str(v)[:200] for k, v in input_state.items()},
            output_state={k: str(v)[:200] for k, v in output_state.items()},
            duration_ms=duration_ms,
            error=error,
        ))

    def total_duration_ms(self) -> float:
        return sum(t.duration_ms for t in self.traces)

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "nodes_executed": len(self.traces),
            "total_ms": round(self.total_duration_ms(), 2),
            "errors": sum(1 for t in self.traces if t.error),
            "nodes": [{"node": t.node, "ms": t.duration_ms, "error": t.error} for t in self.traces],
        }

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "traces": [asdict(t) for t in self.traces],
            "total_ms": self.total_duration_ms(),
        }

    def print_trace(self):
        print(f"\n=== Execution Trace [{self.run_id}] ===")
        for i, t in enumerate(self.traces, 1):
            status = "✅" if not t.error else f"❌ {t.error}"
            print(f"  {i}. [{t.node}] {t.duration_ms:.1f}ms {status}")
        print(f"  Total: {self.total_duration_ms():.1f}ms")
