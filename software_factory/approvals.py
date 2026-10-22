"""Aprovações humanas vinculadas ao SHA-256 do artefato aprovado.

Se o artefato mudar depois da aprovação, o hash não bate e a aprovação
deixa de valer (expira). Persistido em runs/{run_id}/approvals.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import utc_now


class ApprovalStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._items: Dict[str, dict] = {}
        if self.path.exists():
            self._items = {a["artifact"]: a for a in json.loads(self.path.read_text(encoding="utf-8"))}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(list(self._items.values()), ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def approve(self, artifact: str, sha256: str, approver: str, reason: str = "") -> dict:
        if not approver.strip():
            raise ValueError("APPROVER_REQUIRED")
        record = {"artifact": artifact, "sha256": sha256, "approver": approver,
                  "reason": reason, "approved_at": utc_now()}
        self._items[artifact] = record
        self._save()
        return record

    def status(self, artifact: str, current_sha256: str) -> str:
        """MISSING | EXPIRED | VALID."""
        rec = self._items.get(artifact)
        if rec is None:
            return "MISSING"
        return "VALID" if rec["sha256"] == current_sha256 else "EXPIRED"

    def get(self, artifact: str) -> Optional[dict]:
        return self._items.get(artifact)

    def all(self) -> List[dict]:
        return list(self._items.values())
