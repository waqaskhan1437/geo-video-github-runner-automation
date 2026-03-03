from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .utils import run_cmd, which


class VoiceError(RuntimeError):
    pass


def prepare_narration_for_tts(text: str) -> str:
    normalized = text.strip()
    normalized = normalized.replace("=", " equals ")
    normalized = normalized.replace("+", " plus ")
    normalized = normalized.replace("-", " minus ")
    normalized = normalized.replace("*", " times ")
    normalized = normalized.replace("x", " times ")
    normalized = normalized.replace("->", " therefore ")
    normalized = normalized.replace(":", ", ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"([.!?])\s*", r"\1 ", normalized)
    return normalized


def has_piper(piper_exe: Optional[str] = None) -> bool:
    candidate = piper_exe or "piper"
    return which(candidate) is not None


def synthesize_with_piper(
    text: str,
    out_wav: Path,
    model_path: Path,
    piper_exe: Optional[str] = None,
    noise_scale: float = 0.5,
    length_scale: float = 1.08,
    noise_w: float = 0.9,
) -> Path:
    exe = piper_exe or "piper"
    if which(exe) is None:
        raise VoiceError("Piper binary not found in PATH.")

    if not model_path.exists():
        raise VoiceError(f"Piper model not found: {model_path}")

    out_wav.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        exe,
        "--model",
        str(model_path),
        "--output_file",
        str(out_wav),
        "--noise_scale",
        str(noise_scale),
        "--length_scale",
        str(length_scale),
        "--noise_w",
        str(noise_w),
    ]

    result = run_cmd(cmd, input_text=prepare_narration_for_tts(text))
    if result.returncode != 0:
        raise VoiceError(f"Piper voice synthesis failed.\n{result.stderr}")

    if not out_wav.exists() or out_wav.stat().st_size == 0:
        raise VoiceError("Piper command succeeded but no audio was generated.")

    return out_wav
