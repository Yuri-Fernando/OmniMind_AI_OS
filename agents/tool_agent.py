from agents.tools import get_weather

def tool_agent(state):

    question = state["question"]

    if "weather" in question.lower():

        result = get_weather("Campinas")

        state["context"] = result

    return state