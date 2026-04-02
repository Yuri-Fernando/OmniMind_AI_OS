# agents_local/local_reflection_agent.py
from langchain.llms import LlamaCpp

llm = LlamaCpp(model_path="models/ggml-model.bin", n_ctx=512)

def local_reflection_agent(state):
    question = state["question"]
    answer = state["answer"]
    prompt = f"Question: {question}\nAnswer: {answer}\nImprove the answer if needed:"
    improved = llm(prompt)
    state["answer"] = improved
    return state