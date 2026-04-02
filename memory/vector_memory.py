"""
Memória vetorial — armazena e recupera memórias por similaridade semântica.
Usa Chroma como backend (mesmo do RAG).
"""
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from typing import List


class VectorMemory:
    def __init__(self, persist_dir: str = "vector_db/memory"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
            collection_name="agent_memory",
        )

    def store(self, text: str, metadata: dict = None):
        doc = Document(page_content=text, metadata=metadata or {})
        self.vectorstore.add_documents([doc])

    def search(self, query: str, k: int = 3) -> List[str]:
        results = self.vectorstore.similarity_search(query, k=k)
        return [r.page_content for r in results]

    def clear(self):
        self.vectorstore.delete_collection()
