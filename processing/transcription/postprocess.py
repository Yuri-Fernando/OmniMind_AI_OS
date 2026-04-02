import re

def clean_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def structure_segments(result):
    segments = []

    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": clean_text(seg["text"])
        })

    return segments