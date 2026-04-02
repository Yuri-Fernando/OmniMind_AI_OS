retriever = None  # precisa estar no topo do arquivo

def set_retriever(r):
    global retriever
    retriever = r

def rag_agent(state):
    global retriever
    if retriever is None:
        raise ValueError("Retriever não está configurado! Chame set_retriever() antes.")
    
    question = state["question"]
    docs = retriever.invoke(question)  # LangChain novo usa invoke()
    
    context = "\n".join([d.page_content for d in docs])
    state["context"] = context
    return state