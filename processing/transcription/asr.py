import whisper
import os

class WhisperASR:
    def __init__(self, model_size="small"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path):
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Áudio não encontrado: {audio_path}")

        result = self.model.transcribe(
            audio_path,
            language="pt",
            task="transcribe",
            fp16=False
        )

        return result