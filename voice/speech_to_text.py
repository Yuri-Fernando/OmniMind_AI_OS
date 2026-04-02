import sounddevice as sd
from scipy.io.wavfile import write
from .stt_whisper import WhisperSTT

class SpeechToText:

    def __init__(self):

        self.stt = WhisperSTT()

    def record_audio(self, filename="input.wav", duration=5, fs=44100):

        print("🎤 Gravando...")

        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)

        sd.wait()

        write(filename, fs, recording)

        print("✅ áudio capturado")

        return filename

    def listen(self):

        audio_file = self.record_audio()

        text = self.stt.transcribe(audio_file)

        return text