"""Máquina de estados do run. Saltos arbitrários levantam InvalidTransition."""
from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class RunState(str, Enum):
    CREATED = "CREATED"
    INPUT_VALIDATED = "INPUT_VALIDATED"
    ASSESSED = "ASSESSED"
    RESOLUTION_PENDING = "RESOLUTION_PENDING"
    SPEC_APPROVED = "SPEC_APPROVED"
    DESIGN_APPROVED = "DESIGN_APPROVED"
    TASKS_APPROVED = "TASKS_APPROVED"
    IMPLEMENTING = "IMPLEMENTING"
    VERIFYING = "VERIFYING"
    REVIEWING = "REVIEWING"
    PR_READY = "PR_READY"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


TERMINAL: Set[RunState] = {RunState.COMPLETE, RunState.FAILED, RunState.CANCELLED,
                           RunState.REJECTED, RunState.BUDGET_EXCEEDED}

_FORWARD: Dict[RunState, Set[RunState]] = {
    RunState.CREATED: {RunState.INPUT_VALIDATED},
    RunState.INPUT_VALIDATED: {RunState.ASSESSED},
    RunState.ASSESSED: {RunState.RESOLUTION_PENDING, RunState.SPEC_APPROVED},
    RunState.RESOLUTION_PENDING: {RunState.SPEC_APPROVED},
    RunState.SPEC_APPROVED: {RunState.DESIGN_APPROVED},
    RunState.DESIGN_APPROVED: {RunState.TASKS_APPROVED},
    RunState.TASKS_APPROVED: {RunState.IMPLEMENTING},
    RunState.IMPLEMENTING: {RunState.VERIFYING},
    # retrabalho limitado volta para IMPLEMENTING
    RunState.VERIFYING: {RunState.REVIEWING, RunState.IMPLEMENTING},
    RunState.REVIEWING: {RunState.PR_READY, RunState.IMPLEMENTING},
    RunState.PR_READY: {RunState.COMPLETE},
}


class InvalidTransition(RuntimeError):
    pass


def can_transition(src: RunState, dst: RunState) -> bool:
    if src in TERMINAL:
        return False
    if dst in TERMINAL - {RunState.COMPLETE}:
        return True  # qualquer estado não terminal pode falhar/cancelar/rejeitar/estourar budget
    return dst in _FORWARD.get(src, set())


def transition(src: RunState, dst: RunState) -> RunState:
    if not can_transition(src, dst):
        raise InvalidTransition(f"{src.value} -> {dst.value} não permitido")
    return dst
