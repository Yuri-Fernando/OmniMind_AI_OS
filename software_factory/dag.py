"""Validação determinística do DAG de tarefas (gate G3)."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Iterable, List, Set

from .schemas import TaskDAG


class DAGError(ValueError):
    """Erro de plano com código estável (prefixo antes de ':')."""


def normalize_owned_path(raw: str) -> str:
    p = raw.replace("\\", "/").strip()
    if not p or p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        raise DAGError(f"OWNED_PATH_NOT_RELATIVE:{raw}")
    parts = PurePosixPath(p).parts
    if any(part in ("..", ".") for part in parts):
        raise DAGError(f"OWNED_PATH_TRAVERSAL:{raw}")
    return str(PurePosixPath(*parts))


def _overlaps(a: str, b: str) -> bool:
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def parallel_layers(dag: TaskDAG) -> List[List[str]]:
    """Ordem topológica em camadas: tarefas de uma camada podem rodar em paralelo."""
    by_id = {t.id: t for t in dag.tasks}
    done: Set[str] = set()
    layers: List[List[str]] = []
    remaining = set(by_id)
    while remaining:
        ready = sorted(t for t in remaining if set(by_id[t].requires) <= done)
        if not ready:
            raise DAGError("DAG_CYCLE:" + ",".join(sorted(remaining)))
        layers.append(ready)
        done.update(ready)
        remaining.difference_update(ready)
    return layers


def topological_order(dag: TaskDAG) -> List[str]:
    return [t for layer in parallel_layers(dag) for t in layer]


def validate_dag(dag: TaskDAG, known_req_ids: Iterable[str],
                 protected_prefixes: Iterable[str] = ()) -> List[List[str]]:
    """Valida o plano e devolve as camadas paralelas. Levanta DAGError."""
    known = set(known_req_ids)
    ids = [t.id for t in dag.tasks]
    if len(ids) != len(set(ids)):
        raise DAGError("DUPLICATE_TASK_ID")
    id_set = set(ids)
    protected = [normalize_owned_path(p) for p in protected_prefixes]
    covered: Set[str] = set()
    for t in dag.tasks:
        for dep in t.requires:
            if dep not in id_set:
                raise DAGError(f"UNKNOWN_DEPENDENCY:{t.id}->{dep}")
            if dep == t.id:
                raise DAGError(f"DAG_CYCLE:{t.id}")
        unknown = set(t.req_ids) - known
        if unknown:
            raise DAGError(f"UNKNOWN_REQ_ID:{t.id}:{','.join(sorted(unknown))}")
        covered.update(t.req_ids)
        for raw in t.owned_paths:
            norm = normalize_owned_path(raw)
            if any(_overlaps(norm, p) for p in protected):
                raise DAGError(f"OWNED_PATH_PROTECTED:{t.id}:{norm}")
    missing = known - covered
    if missing:
        raise DAGError("REQ_NOT_PLANNED:" + ",".join(sorted(missing)))
    layers = parallel_layers(dag)
    by_id = {t.id: t for t in dag.tasks}
    for layer in layers:
        for i, a in enumerate(layer):
            for b in layer[i + 1:]:
                for pa in by_id[a].owned_paths:
                    for pb in by_id[b].owned_paths:
                        if _overlaps(normalize_owned_path(pa), normalize_owned_path(pb)):
                            raise DAGError(f"OWNED_PATH_COLLISION:{a},{b}:{normalize_owned_path(pa)}")
    return layers
