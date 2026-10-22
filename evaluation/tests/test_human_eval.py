"""Fila de avaliação humana: aprovação/reprovação, comentário, agregação, persistência e CLI."""
import json

import pytest

from evaluation.human_eval import HumanEvalQueue, main


@pytest.fixture
def q(tmp_path):
    queue = HumanEvalQueue(tmp_path / "fila.json")
    for i in range(4):
        queue.enqueue(f"c{i}", f"pergunta {i}", f"resposta {i}")
    return queue


def test_enqueue_is_idempotent(q):
    assert q.enqueue("c0", "outra", "outra") is False
    assert len(q.pending()) == 4 and q.pending()[0]["question"] == "pergunta 0"


def test_review_and_aggregate(q):
    q.review("c0", "approved", "ótima", "ana")
    q.review("c1", "approved", reviewer="ana")
    q.review("c2", "rejected", "alucinou o valor", "ana")
    agg = q.aggregate()
    assert (agg["total"], agg["approved"], agg["rejected"], agg["pending"]) == (4, 2, 1, 1)
    assert agg["approval_rate"] == round(2 / 3, 4)
    assert agg["reject_comments"] == [{"id": "c2", "comment": "alucinou o valor"}]


def test_rejection_requires_comment(q):
    with pytest.raises(ValueError, match="comentário"):
        q.review("c0", "rejected", "  ")
    assert q.aggregate()["rejected"] == 0


def test_invalid_verdict_unknown_item_and_double_review(q):
    with pytest.raises(ValueError):
        q.review("c0", "talvez")
    with pytest.raises(KeyError):
        q.review("nao-existe", "approved")
    q.review("c0", "approved")
    with pytest.raises(ValueError, match="já revisado"):
        q.review("c0", "rejected", "mudei de ideia")
    q.reopen("c0")
    q.review("c0", "rejected", "agora reprovo")
    assert q.aggregate()["rejected"] == 1


def test_persists_across_instances_with_audit_fields(q, tmp_path):
    q.review("c0", "approved", "ok", "ana")
    again = HumanEvalQueue(tmp_path / "fila.json")
    item = next(i for i in again._items.values() if i["id"] == "c0")
    assert item["status"] == "approved" and item["reviewer"] == "ana" and item["reviewed_at"]
    assert json.loads((tmp_path / "fila.json").read_text(encoding="utf-8"))["version"] == 1


def test_empty_queue_has_no_rate(tmp_path):
    assert HumanEvalQueue(tmp_path / "vazia.json").aggregate()["approval_rate"] is None


def test_cli_roundtrip(q, tmp_path, capsys):
    f = str(tmp_path / "fila.json")
    assert main(["--file", f, "review", "c3", "approved", "--comment", "ok", "--reviewer", "bia"]) == 0
    assert main(["--file", f, "summary"]) == 0
    out = capsys.readouterr().out
    assert '"approved": 1' in out and "c3: approved" in out
