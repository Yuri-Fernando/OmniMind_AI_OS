# agents_local/local_tool_agent.py
from agents_local.tools import get_weather, calculator

def local_tool_agent(state):
    question = state["question"].lower()

    if "weather" in question:
        state["context"] = get_weather("Campinas")
    elif "calculate" in question or "compute" in question:
        state["context"] = calculator(question.replace("calculate", "").strip())
    
    return state