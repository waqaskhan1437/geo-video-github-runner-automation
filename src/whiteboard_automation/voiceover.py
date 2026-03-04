from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .utils import run_cmd, which


class VoiceError(RuntimeError):
    pass


VOICE_PROFILES: dict[str, dict[str, float]] = {
    "calm": {
        "noise_scale": 0.36,
        "length_scale": 1.16,
        "noise_w": 0.74,
        "sentence_silence": 0.22,
    },
    "studio": {
        "noise_scale": 0.33,
        "length_scale": 1.11,
        "noise_w": 0.70,
        "sentence_silence": 0.18,
    },
    "clear": {
        "noise_scale": 0.40,
        "length_scale": 1.08,
        "noise_w": 0.78,
        "sentence_silence": 0.16,
    },
}


def available_voice_profiles() -> list[str]:
    return sorted(VOICE_PROFILES.keys())


def _normalize_option_ranges(text: str) -> str:
    # Example: (1-4) -> one to four
    text = re.sub(r"\(\s*1\s*-\s*4\s*\)", " one to four ", text)
    text = re.sub(r"\(\s*1\s*=\s*", " options: one equals ", text)
    text = re.sub(r",\s*2\s*=\s*", ", two equals ", text)
    text = re.sub(r",\s*3\s*=\s*", ", three equals ", text)
    text = re.sub(r",\s*4\s*=\s*", ", four equals ", text)
    text = re.sub(r"\s*\)", ". ", text)
    return text


def _split_long_sentences(text: str, max_words: int = 14) -> str:
    chunks: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()
        if len(words) <= max_words:
            chunks.append(sentence)
            continue

        for i in range(0, len(words), max_words):
            piece = " ".join(words[i : i + max_words]).strip()
            if piece:
                if piece[-1] not in ".!?":
                    piece += "."
                chunks.append(piece)

    return " ".join(chunks)


def prepare_narration_for_tts(text: str) -> str:
    normalized = text.strip()
    normalized = _normalize_option_ranges(normalized)
    normalized = normalized.replace("=", " equals ")
    normalized = normalized.replace("+", " plus ")
    normalized = normalized.replace("-", " minus ")
    normalized = normalized.replace("*", " times ")
    normalized = normalized.replace("x", " times ")
    normalized = normalized.replace("->", " therefore ")
    normalized = normalized.replace(":", ". ")
    normalized = normalized.replace("(", " ")
    normalized = normalized.replace(")", " ")
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"([.!?])\s*", r"\1 ", normalized)
    normalized = _split_long_sentences(normalized, max_words=14)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized and normalized[-1] not in ".!?":
        normalized += "."
    return normalized


def has_piper(piper_exe: Optional[str] = None) -> bool:
    candidate = piper_exe or "piper"
    return which(candidate) is not None


def synthesize_with_piper(
    text: str,
    out_wav: Path,
    model_path: Path,
    piper_exe: Optional[str] = None,
    voice_profile: str = "calm",
) -> Path:
    exe = piper_exe or "piper"
    if which(exe) is None:
        raise VoiceError("Piper binary not found in PATH.")

    if not model_path.exists():
        raise VoiceError(f"Piper model not found: {model_path}")

    profile = VOICE_PROFILES.get(voice_profile.lower())
    if profile is None:
        supported = ", ".join(available_voice_profiles())
        raise VoiceError(f"Unsupported voice profile '{voice_profile}'. Supported: {supported}")

    out_wav.parent.mkdir(parents=True, exist_ok=True)

    base_cmd = [
        exe,
        "--model",
        str(model_path),
        "--output_file",
        str(out_wav),
        "--noise_scale",
        str(profile["noise_scale"]),
        "--length_scale",
        str(profile["length_scale"]),
        "--noise_w",
        str(profile["noise_w"]),
    ]

    cmd_with_pause = [
        *base_cmd,
        "--sentence_silence",
        str(profile["sentence_silence"]),
    ]

    narration_text = prepare_narration_for_tts(text)
    result = run_cmd(cmd_with_pause, input_text=narration_text)
    if result.returncode != 0 and "sentence_silence" in (result.stderr or ""):
        # Older piper builds may not support this flag.
        result = run_cmd(base_cmd, input_text=narration_text)

    if result.returncode != 0:
        raise VoiceError(f"Piper voice synthesis failed.\n{result.stderr}")

    if not out_wav.exists() or out_wav.stat().st_size == 0:
        raise VoiceError("Piper command succeeded but no audio was generated.")

    return out_wav
