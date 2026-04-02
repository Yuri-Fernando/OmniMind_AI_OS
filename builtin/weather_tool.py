"""Ferramenta de clima — Open-Meteo (gratuita, sem API key)."""
import urllib.request, json

def get_weather(city: str) -> dict:
    """Obtém temperatura atual para uma cidade via Open-Meteo + geocoding."""
    try:
        # Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=pt"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read())
        if not geo.get("results"):
            return {"error": f"Cidade '{city}' não encontrada", "ok": False}
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = loc.get("name", city)

        # Clima
        wx_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true&temperature_unit=celsius"
        )
        with urllib.request.urlopen(wx_url, timeout=5) as r:
            wx = json.loads(r.read())
        cw = wx.get("current_weather", {})
        return {
            "city": name, "lat": lat, "lon": lon,
            "temp_c": cw.get("temperature"),
            "wind_kmh": cw.get("windspeed"),
            "ok": True,
        }
    except Exception as e:
        return {"error": str(e), "ok": False}

class WeatherTool:
    name = "weather"
    description = "Retorna clima atual de uma cidade. Input: nome da cidade."

    def run(self, city: str) -> str:
        r = get_weather(city)
        if r["ok"]:
            return f"{r['city']}: {r['temp_c']}°C, vento {r['wind_kmh']} km/h"
        return f"Erro: {r['error']}"
