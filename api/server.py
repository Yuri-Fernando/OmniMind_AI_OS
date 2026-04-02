from fastapi import FastAPI
from core.orchestration_graph import build_graph

app = FastAPI()

agent = build_graph()

@app.post("/ask")

def ask(question: str):

    result = agent.invoke({
        "question":question
    })

    return {
        "answer":result["answer"]
    }