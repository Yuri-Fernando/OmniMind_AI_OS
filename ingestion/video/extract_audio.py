import subprocess

def extract_audio(video_path, output_path="audio.wav", sample_rate=16000):
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ar", str(sample_rate),
        "-ac", "1",
        "-y",
        output_path
    ]

    subprocess.run(command)

    return output_path