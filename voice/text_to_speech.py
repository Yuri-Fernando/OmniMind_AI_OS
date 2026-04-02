from .tts_elevenlabs import ElevenLabsTTS

class TextToSpeech:

    def __init__(self, api_key):

        self.tts = ElevenLabsTTS(api_key)

    def speak(self, text):

        self.tts.speak(text)