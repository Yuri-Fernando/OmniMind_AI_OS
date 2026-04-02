"""Ingestão de documentos para o vector store (PDF, TXT, MD, DOCX)."""
import os
from typing import List
from knowledge.vector_store import VectorStore
from core.config import CHUNK_SIZE, CHUNK_OVERLAP


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c for c in chunks if c.strip()]


def ingest_text(text: str, store: VectorStore, source: str = "") -> int:
    chunks = _chunk_text(text)
    for i, chunk in enumerate(chunks):
        store.add(chunk, {"source": source, "chunk": i})
    return len(chunks)


def ingest_file(path: str, store: VectorStore) -> int:
    ext = os.path.splitext(path)[1].lower()
    text = ""
    if ext in (".txt", ".md"):
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            raise ImportError("Instale pypdf: pip install pypdf")
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("Instale python-docx: pip install python-docx")
    else:
        raise ValueError(f"Formato não suportado: {ext}")
    return ingest_text(text, store, source=os.path.basename(path))


def ingest_directory(directory: str, store: VectorStore, extensions=(".txt", ".md", ".pdf")) -> dict:
    results = {}
    for fname in os.listdir(directory):
        if any(fname.endswith(ext) for ext in extensions):
            path = os.path.join(directory, fname)
            try:
                n = ingest_file(path, store)
                results[fname] = n
            except Exception as e:
                results[fname] = f"ERRO: {e}"
    return results
