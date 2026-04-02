# agents_local/local_rag_agent.py
from rag.retriever import create_retriever

# variavel global para o retriever
retriever = None

def set_retriever_local(r):
    global retriever
    retriever = r

def local_rag_agent(state):
    global retriever
    question = state["question"]
    docs = retriever.get_relevant_documents(question)  # igual RAG normal
    context = "\n".join([d.page_content for d in docs])
    state["context"] = context
    return state