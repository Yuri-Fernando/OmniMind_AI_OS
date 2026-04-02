"""
TTS local — duas opções sem custo:
  1. pyttsx3  — offline, usa vozes do sistema operacional
  2. edge-tts  — online gratuito (Microsoft Edge TTS, alta qualidade PT-BR)
"""
import asyncio
from typing import Optional


class PyttxsTTS:
    """TTS completamente offline usando vozes do Windows/Linux."""

    def __init__(self, rate: int = 150, volume: float = 1.0):
        import pyttsx3
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        self._set_portuguese_voice()

    def _set_portuguese_voice(self):
        voices = self.engine.getProperty("voices")
        for v in voices:
            if "pt" in v.id.lower() or "brazil" in v.name.lower() or "portuguese" in v.name.lower():
                self.engine.setProperty("voice", v.id)
                return

    def speak(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()

    def save(self, text: str, output_path: str = "output.wav"):
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
        return output_path


class EdgeTTS:
    """
    TTS de alta qualidade via Microsoft Edge (requer internet).
    Gratuito, sem chave de API.
    """

    def __init__(self, voice: str = "pt-BR-FranciscaNeural"):
        self.voice = voice

    async def _synthesize(self, text: str, output_path: str):
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def speak_to_file(self, text: str, output_path: str = "output_edge.mp3") -> str:
        asyncio.run(self._synthesize(text, output_path))
        return output_path

    def speak(self, text: str):
        """Sintetiza e reproduz via playsound."""
        path = self.speak_to_file(text)
        try:
            import playsound
            playsound.playsound(path)
        except ImportError:
            import subprocess
            subprocess.run(["start", path], shell=True)


def get_local_tts(engine: str = "pyttsx3") -> object:
    """Factory: retorna PyttxsTTS ou EdgeTTS."""
    if engine == "edge":
        return EdgeTTS()
    return PyttxsTTS()
