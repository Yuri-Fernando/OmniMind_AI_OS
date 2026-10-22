"""Avaliação humana (human-in-the-loop): fila JSON com aprovação/reprovação + comentário.

    python -m evaluation.human_eval --file fila.json list
    python -m evaluation.human_eval --file fila.json review ITEM_ID approved --comment "ok" --reviewer yuri
    python -m evaluation.human_eval --file fila.json summary

Escrita atômica (tmp + replace). Um item revisado não volta a `pending` sem `reopen`. Revisões ficam
no próprio arquivo, com revisor e horário — trilha mínima de auditoria.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

VERDICTS = {"approved", "rejected"}


class HumanEvalQueue:
    def __init__(self, path):
        self.path = Path(path)
        self._items: Dict[str, Dict[str, Any]] = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._items = {i["id"]: i for i in data.get("items", [])}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"version": 1, "items": list(self._items.values())}, ensure_ascii=False, indent=2)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, self.path)

    def enqueue(self, item_id: str, question: str, answer: str, context: Optional[List[str]] = None,
                meta: Optional[Dict[str, Any]] = None) -> bool:
        """Idempotente: devolve False (e não altera nada) se o item já existe."""
        if item_id in self._items:
            return False
        self._items[item_id] = {"id": item_id, "question": question, "answer": answer, "context": context or [],
                                "meta": meta or {}, "status": "pending", "comment": "", "reviewer": None,
                                "reviewed_at": None}
        self._save()
        return True

    def pending(self) -> List[Dict[str, Any]]:
        return [i for i in self._items.values() if i["status"] == "pending"]

    def review(self, item_id: str, verdict: str, comment: str = "", reviewer: str = "anonymous") -> Dict[str, Any]:
        if verdict not in VERDICTS:
            raise ValueError(f"veredito inválido: {verdict!r} (use {sorted(VERDICTS)})")
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"item inexistente: {item_id}")
        if item["status"] != "pending":
            raise ValueError(f"item {item_id} já revisado ({item['status']}); use reopen()")
        if verdict == "rejected" and not comment.strip():
            raise ValueError("reprovação exige comentário")
        item.update(status=verdict, comment=comment, reviewer=reviewer, reviewed_at=time.time())
        self._save()
        return item

    def reopen(self, item_id: str) -> None:
        item = self._items[item_id]
        item.update(status="pending", reviewer=None, reviewed_at=None)
        self._save()

    def aggregate(self) -> Dict[str, Any]:
        items = list(self._items.values())
        appr = sum(i["status"] == "approved" for i in items)
        rej = sum(i["status"] == "rejected" for i in items)
        reviewed = appr + rej
        return {
            "total": len(items), "pending": len(items) - reviewed, "approved": appr, "rejected": rej,
            "approval_rate": round(appr / reviewed, 4) if reviewed else None,
            "reject_comments": [{"id": i["id"], "comment": i["comment"]} for i in items if i["status"] == "rejected"],
        }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("summary")
    rv = sub.add_parser("review")
    rv.add_argument("item_id")
    rv.add_argument("verdict", choices=sorted(VERDICTS))
    rv.add_argument("--comment", default="")
    rv.add_argument("--reviewer", default="anonymous")
    ns = ap.parse_args(argv)
    q = HumanEvalQueue(ns.file)
    if ns.cmd == "list":
        for i in q.pending():
            print(f"{i['id']}\n  P: {i['question']}\n  R: {i['answer']}")
    elif ns.cmd == "summary":
        print(json.dumps(q.aggregate(), ensure_ascii=False, indent=2))
    else:
        q.review(ns.item_id, ns.verdict, ns.comment, ns.reviewer)
        print(f"{ns.item_id}: {ns.verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
