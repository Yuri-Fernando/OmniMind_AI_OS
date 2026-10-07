"""Testes do golden dataset — garantem que o corpus é real (arquivos do
próprio repo) e que o conjunto de perguntas é consistente."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.golden_dataset import CORPUS_FILES, GOLDEN_SET, load_corpus_text


def test_corpus_files_exist_and_are_real_repo_docs():
    for path in CORPUS_FILES:
        assert path.exists(), f"arquivo do corpus não encontrado: {path}"
        assert path.suffix == ".md"


def test_load_corpus_text_concatenates_all_files_non_empty():
    text = load_corpus_text()
    assert len(text) > 1000
    for path in CORPUS_FILES:
        # cada arquivo deve de fato contribuir conteúdo (não apenas o 1º)
        snippet = path.read_text(encoding="utf-8")[:50]
        assert snippet in text


def test_golden_set_has_unique_non_empty_questions_and_ground_truths():
    assert len(GOLDEN_SET) >= 5
    questions = [item.question for item in GOLDEN_SET]
    assert len(questions) == len(set(questions)), "perguntas duplicadas no golden-set"
    for item in GOLDEN_SET:
        assert item.question.strip()
        assert item.ground_truth.strip()
        assert item.question.endswith("?")
