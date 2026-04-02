"""
Tracing leve do AIOS.
Rastreia cada execução de nó com tempo e resultado — sem dependência externa.
"""
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    start: float = field(default_factory=time.time)
    end: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, **meta):
        self.end = time.time()
        self.metadata.update(meta)

    @property
    def duration_ms(self) -> float:
        return round((self.end - self.start) * 1000, 2)


class Tracer:
    def __init__(self):
        self.spans: List[Span] = []
        self._active: Dict[str, Span] = {}

    def start(self, name: str) -> Span:
        span = Span(name=name)
        self._active[name] = span
        return span

    def finish(self, name: str, **meta) -> Span:
        span = self._active.pop(name, None)
        if span:
            span.finish(**meta)
            self.spans.append(span)
        return span

    def summary(self) -> List[Dict]:
        return [
            {"node": s.name, "duration_ms": s.duration_ms, **s.metadata}
            for s in self.spans
        ]

    def reset(self):
        self.spans.clear()
        self._active.clear()


# Instância global
tracer = Tracer()
