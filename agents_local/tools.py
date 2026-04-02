# agents_local/tools.py

def get_weather(city):
    # offline simples: retorna dado fixo ou simula consulta
    fake_data = {
        "Campinas": "25°C, sunny",
        "São Paulo": "22°C, cloudy"
    }
    return fake_data.get(city, "No data available")

def calculator(expression: str):
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"