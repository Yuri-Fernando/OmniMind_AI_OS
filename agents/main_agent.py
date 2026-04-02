from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

def create_agent(retriever):

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return chain