"""
Análise de vídeo com LLaVA (open source, via Ollama).
Pipeline: vídeo → frames extraídos → LLaVA descreve cada frame → resumo agregado.
"""
import base64
import os
import subprocess
from typing import List, Optional

from core.config import FFMPEG_PATH, OLLAMA_BASE_URL, OLLAMA_VISION_MODEL


def extract_frames(video_path: str, output_dir: str = "temp_frames", fps: float = 0.5) -> List[str]:
    """
    Extrai frames de um vídeo a <fps> frames por segundo.

    Returns:
        Lista de caminhos dos frames extraídos (JPEG).
    """
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        "-y", pattern,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg erro: {result.stderr}")

    frames = sorted(
        [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".jpg")]
    )
    return frames


def _image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def describe_frame_llava(image_path: str, prompt: str = "Descreva o que está acontecendo nesta imagem em português.") -> str:
    """Envia um frame ao LLaVA via Ollama API e retorna a descrição."""
    try:
        import ollama
        img_b64 = _image_to_base64(image_path)
        response = ollama.chat(
            model=OLLAMA_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64],
            }],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"[Erro ao analisar frame: {e}]"


def analyze_video(
    video_path: str,
    fps: float = 0.5,
    max_frames: int = 5,
    prompt: str = "Descreva o que está acontecendo nesta cena em português.",
    cleanup: bool = True,
) -> dict:
    """
    Pipeline completo de análise de vídeo com LLaVA.

    Args:
        video_path: caminho do arquivo de vídeo
        fps: frames por segundo para extrair
        max_frames: máximo de frames a analisar (evita custo excessivo)
        prompt: instrução para o modelo de visão
        cleanup: remover frames temporários após análise

    Returns:
        Dict com descrições por frame e resumo geral.
    """
    temp_dir = "temp_video_frames"
    frames = extract_frames(video_path, output_dir=temp_dir, fps=fps)
    frames = frames[:max_frames]

    descriptions = []
    for i, frame_path in enumerate(frames):
        print(f"  Analisando frame {i+1}/{len(frames)}...")
        desc = describe_frame_llava(frame_path, prompt)
        descriptions.append({"frame": i + 1, "path": frame_path, "description": desc})

    # Resumo agregado
    all_descs = "\n".join([f"Frame {d['frame']}: {d['description']}" for d in descriptions])

    if cleanup:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    return {
        "video": video_path,
        "frames_analyzed": len(descriptions),
        "descriptions": descriptions,
        "summary": all_descs,
    }
