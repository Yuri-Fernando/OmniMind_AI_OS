# agents_local/local_executor_agent.py
from langchain.llms import LlamaCpp

llm = LlamaCpp(model_path="models/ggml-model.bin", n_ctx=512)

def local_executor_agent(state):
    question = state["question"]
    context = state.get("context", "")
    prompt = f"Question: {question}\nContext: {context}\nAnswer:"
    answer = llm(prompt)
    state["answer"] = answer
    return state