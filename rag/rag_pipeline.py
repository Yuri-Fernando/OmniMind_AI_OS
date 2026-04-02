"""
rag/rag_pipeline.py
Pipeline RAG completo: escaneia pasta, carrega documentos, cria embeddings,
salva resumos no banco SQLite (knowledge/database.py)
"""
import os
import glob
from pathlib import Path
from typing import List, Optional

# LangChain
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Banco de conhecimento
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge.database import init_db, salvar_resumo_rag, buscar_resumos

# -- Configuracoes ------------------------------------------------------------
RAG_DIR = Path(__file__).parent.parent / "rag"
DOCS_DIR = Path(__file__).parent.parent / "docs"
VECTOR_DB_DIR = Path(__file__).parent.parent / "vector_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


class RAGPipeline:
    """
    Pipeline RAG que:
    1. Escaneia toda a pasta rag/ e docs/ por PDFs, TXTs e MDs
    2. Cria chunks e embeddings
    3. Persiste no Chroma vector DB
    4. Salva resumo de cada documento no SQLite
    """

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or str(VECTOR_DB_DIR)
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        self.vectorstore: Optional[Chroma] = None
        init_db()

    def _escanear_documentos(self) -> List[str]:
        """Retorna lista de caminhos de todos os docs na pasta rag/ e docs/."""
        padroes = [
            str(RAG_DIR / "**/*.pdf"),
            str(RAG_DIR / "**/*.txt"),
            str(RAG_DIR / "**/*.md"),
            str(DOCS_DIR / "**/*.pdf"),
            str(DOCS_DIR / "**/*.txt"),
            str(DOCS_DIR / "**/*.md"),
        ]
        arquivos = []
        for padrao in padroes:
            arquivos.extend(glob.glob(padrao, recursive=True))
        # Remover __pycache__ e arquivos Python
        arquivos = [a for a in arquivos if "__pycache__" not in a and not a.endswith(".py")]
        print(f"[RAG] {len(arquivos)} documentos encontrados")
        return arquivos

    def _carregar_documento(self, caminho: str):
        """Carrega documento baseado na extensao."""
        ext = Path(caminho).suffix.lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(caminho)
            else:
                loader = TextLoader(caminho, encoding="utf-8")
            return loader.load()
        except Exception as e:
            print(f"[RAG] Erro ao carregar {caminho}: {e}")
            return []

    def ingerir_tudo(self) -> dict:
        """
        Ingere todos os documentos da pasta rag/ e docs/.
        Salva embeddings no Chroma e resumos no SQLite.
        """
        arquivos = self._escanear_documentos()
        if not arquivos:
            print("[RAG] Nenhum documento encontrado. Coloque PDFs em rag/ ou docs/")
            return {"documentos": 0, "chunks": 0}

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        todos_chunks = []
        total_docs = 0

        for caminho in arquivos:
            docs = self._carregar_documento(caminho)
            if not docs:
                continue

            chunks = splitter.split_documents(docs)
            todos_chunks.extend(chunks)
            total_docs += 1

            # Resumo simples = primeiros 500 chars do primeiro chunk
            resumo = chunks[0].page_content[:500] if chunks else "sem conteudo"
            nome = Path(caminho).stem

            # Salvar no SQLite
            salvar_resumo_rag(
                fonte=caminho,
                titulo=nome,
                resumo=resumo,
                chunks=len(chunks),
                tags=["auto-ingestao"]
            )
            print(f"[RAG] {nome}: {len(chunks)} chunks -> SQLite OK")

        # Criar/atualizar vector store
        if todos_chunks:
            self.vectorstore = Chroma.from_documents(
                documents=todos_chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
            self.vectorstore.persist()
            print(f"[RAG] Vector DB atualizado: {len(todos_chunks)} chunks totais")

        return {"documentos": total_docs, "chunks": len(todos_chunks)}

    def carregar_existente(self):
        """Carrega vector DB ja existente do disco."""
        if Path(self.persist_dir).exists():
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
            print(f"[RAG] Vector DB carregado de {self.persist_dir}")
        else:
            print("[RAG] Nenhum vector DB encontrado. Rode ingerir_tudo() primeiro.")

    def buscar(self, query: str, k: int = 3) -> List[str]:
        """Busca semantica retornando lista de textos relevantes."""
        if not self.vectorstore:
            self.carregar_existente()
        if not self.vectorstore:
            return []
        resultados = self.vectorstore.similarity_search(query, k=k)
        return [r.page_content for r in resultados]

    def resumos_sql(self, query: str = None) -> list:
        """Retorna resumos do banco SQLite (nao do vector DB)."""
        return buscar_resumos(query=query)


# -- Uso direto ---------------------------------------------------------------
if __name__ == "__main__":
    pipeline = RAGPipeline()
    resultado = pipeline.ingerir_tudo()
    print("Resultado:", resultado)

    # Mostrar resumos no SQLite
    resumos = pipeline.resumos_sql()
    print(f"\n{len(resumos)} documentos no banco:")
    for r in resumos:
        print(f"  [{r['id']}] {r['titulo']} -- {r['chunks']} chunks -- {r['criado_em'][:10]}")
