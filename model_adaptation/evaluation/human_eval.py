"""Avaliação humana — implementação única em `evaluation/human_eval.py` (reexportada aqui)."""
from evaluation.human_eval import HumanEvalQueue, VERDICTS, main  # noqa: F401

__all__ = ["HumanEvalQueue", "VERDICTS", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
