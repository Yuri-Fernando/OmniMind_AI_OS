"""Teto rígido de tokens e de chamadas por run e por estágio."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .schemas import StageUsage


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Budget:
    max_total_tokens: int = 200_000
    max_calls_per_stage: int = 12
    max_rework_attempts: int = 2
    # preço aproximado por 1M tokens (entrada, saída) — só para estimativa no relatório
    price_in_per_mtok: float = 0.0
    price_out_per_mtok: float = 0.0
    usage: Dict[str, StageUsage] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return sum(u.input_tokens + u.output_tokens for u in self.usage.values())

    def check_call(self, stage: str) -> None:
        u = self.usage.get(stage)
        if u and u.calls >= self.max_calls_per_stage:
            raise BudgetExceeded(f"CALLS_PER_STAGE:{stage}:{u.calls}")
        if self.total_tokens >= self.max_total_tokens:
            raise BudgetExceeded(f"TOKENS:{self.total_tokens}>={self.max_total_tokens}")

    def record(self, stage: str, input_tokens: int, output_tokens: int, duration_ms: float) -> None:
        u = self.usage.setdefault(stage, StageUsage(stage=stage))
        u.calls += 1
        u.input_tokens += input_tokens
        u.output_tokens += output_tokens
        u.duration_ms += duration_ms
        if self.total_tokens > self.max_total_tokens:
            raise BudgetExceeded(f"TOKENS:{self.total_tokens}>{self.max_total_tokens}")

    def estimated_cost(self) -> float:
        tin = sum(u.input_tokens for u in self.usage.values())
        tout = sum(u.output_tokens for u in self.usage.values())
        return round(tin / 1e6 * self.price_in_per_mtok + tout / 1e6 * self.price_out_per_mtok, 6)
