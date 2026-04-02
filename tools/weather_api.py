"""Ferramenta de clima usando wttr.in (gratuita, sem chave)."""
import requests


class WeatherAPITool:
    def run(self, city: str) -> str:
        try:
            url = f"https://wttr.in/{city}?format=3&lang=pt"
            response = requests.get(url, timeout=5)
            return response.text.strip()
        except requests.RequestException as e:
            return f"Erro ao consultar clima de {city}: {e}"

    def get_detailed(self, city: str) -> dict:
        try:
            url = f"https://wttr.in/{city}?format=j1"
            data = requests.get(url, timeout=5).json()
            current = data["current_condition"][0]
            return {
                "city": city,
                "temp_c": current["temp_C"],
                "feels_like_c": current["FeelsLikeC"],
                "humidity": current["humidity"],
                "description": current["weatherDesc"][0]["value"],
                "wind_kmph": current["windspeedKmph"],
            }
        except Exception as e:
            return {"error": str(e)}
