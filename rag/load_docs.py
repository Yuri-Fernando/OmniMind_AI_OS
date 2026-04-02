from langchain_community.document_loaders import PyPDFLoader
from rag.chunking import split_documents
from rag.retriever import create_retriever

def load_docs(path):

    loader = PyPDFLoader(path)

    docs = loader.load()

    chunks = split_documents(docs)

    retriever = create_retriever(chunks)

    return retriever