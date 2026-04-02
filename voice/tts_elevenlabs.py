from elevenlabs import generate, play, set_api_key

class ElevenLabsTTS:

    def __init__(self, api_key):

        set_api_key(api_key)

    def speak(self, text):

        audio = generate(
            text=text,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )

        play(audio)