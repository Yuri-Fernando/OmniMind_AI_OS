from langchain_community.vectorstores import Chroma
from rag.embeddings import get_embeddings

def create_retriever(docs):

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        docs,
        embedding=embeddings,
        persist_directory="vector_db"
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={"k":3}
    )

    return retriever