#!/usr/bin/env python3
"""
Generate realistic narration voice + background bed, then mux with visual video.

Main env vars:
- DOC_VISUAL_INPUT
- DOC_FINAL_OUTPUT
- DOC_NARRATION_FILE
- DOC_TARGET_SECONDS
- DOC_VOICE_NAME / DOC_VOICE_RATE / DOC_VOICE_PITCH / DOC_VOICE_GAIN
- DOC_MUSIC_GAIN
- DOC_AUDIO_BITRATE
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from gtts import gTTS

def env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def media_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    return float(payload["format"]["duration"])


def atempo_chain(factor: float) -> str:
    parts = []
    remaining = factor
    while remaining < 0.5:
        parts.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)


TARGET_SECONDS = env_float("DOC_TARGET_SECONDS", 120.0, 30.0, 300.0)
VISUAL_VIDEO = Path(env_str("DOC_VISUAL_INPUT", "outputs/final/conflict_documentary_visual.mp4")).resolve()
FINAL_VIDEO = Path(env_str("DOC_FINAL_OUTPUT", "outputs/final/conflict_documentary_final_1080p.mp4")).resolve()
NARRATION_TEXT = Path(env_str("DOC_NARRATION_FILE", "data/narration_script.txt")).resolve()

VOICE_NAME = env_str("DOC_VOICE_NAME", "en-US-GuyNeural")
VOICE_RATE = env_str("DOC_VOICE_RATE", "-20%")
VOICE_PITCH = env_str("DOC_VOICE_PITCH", "+0Hz")
VOICE_ENGINE = env_str("DOC_VOICE_ENGINE", "auto").lower()
VOICE_GAIN = env_float("DOC_VOICE_GAIN", 1.0, 0.70, 1.50)
MUSIC_GAIN = env_float("DOC_MUSIC_GAIN", 0.30, 0.10, 0.60)
AUDIO_BITRATE = env_int("DOC_AUDIO_BITRATE", 192, 96, 320)
GTTS_LANG = env_str("DOC_GTTS_LANG", "en")
GTTS_TLD = env_str("DOC_GTTS_TLD", "com")

work_root = FINAL_VIDEO.parent / f"audio_{FINAL_VIDEO.stem}"
work_root.mkdir(parents=True, exist_ok=True)
RAW_VOICE = work_root / "voice_raw.mp3"
TIMED_VOICE = work_root / "voice_timed.wav"
MUSIC_BED = work_root / "music_bed.wav"
MIXED_AUDIO = work_root / "mixed_audio.wav"


def run_edge_tts() -> None:
    run(
        [
            "python",
            "-m",
            "edge_tts",
            "--file",
            str(NARRATION_TEXT),
            "--voice",
            VOICE_NAME,
            f"--rate={VOICE_RATE}",
            f"--pitch={VOICE_PITCH}",
            "--write-media",
            str(RAW_VOICE),
        ]
    )


def run_gtts() -> None:
    text = NARRATION_TEXT.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Narration text file is empty: {NARRATION_TEXT}")
    tts = gTTS(text=text, lang=GTTS_LANG, tld=GTTS_TLD)
    tts.save(str(RAW_VOICE))


def generate_voice() -> None:
    if not NARRATION_TEXT.exists():
        raise FileNotFoundError(f"Narration text file not found: {NARRATION_TEXT}")

    selected_engine = VOICE_ENGINE
    if selected_engine not in {"auto", "edge", "gtts"}:
        selected_engine = "auto"

    if selected_engine == "edge":
        print("[voice] engine=edge")
        run_edge_tts()
    elif selected_engine == "gtts":
        print("[voice] engine=gtts")
        run_gtts()
    else:
        # Auto: prefer edge-tts first, fallback to gTTS if blocked.
        try:
            print("[voice] engine=auto (trying edge-tts)")
            run_edge_tts()
        except Exception as exc:  # noqa: BLE001
            print(f"[voice] edge-tts failed, falling back to gTTS: {exc}")
            run_gtts()

    raw_dur = media_duration(RAW_VOICE)
    speed_factor = raw_dur / TARGET_SECONDS if TARGET_SECONDS > 0 else 1.0
    if speed_factor <= 0:
        speed_factor = 1.0
    chain = atempo_chain(speed_factor)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(RAW_VOICE),
            "-af",
            f"{chain},apad=pad_dur={TARGET_SECONDS},atrim=duration={TARGET_SECONDS}",
            str(TIMED_VOICE),
        ]
    )


def generate_music_bed() -> None:
    # Subtle documentary texture.
    expr = (
        f"sine=frequency=74:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.055[a0];"
        f"sine=frequency=111:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.040[a1];"
        f"anoisesrc=color=pink:duration={TARGET_SECONDS}:sample_rate=44100,"
        "lowpass=f=1200,highpass=f=120,volume=0.010[a2];"
        "[a0][a1][a2]amix=inputs=3:normalize=0,afade=t=in:st=0:d=2,afade=t=out:st=116:d=4"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            expr,
            str(MUSIC_BED),
        ]
    )


def mix_audio() -> None:
    filter_complex = (
        f"[0:a]volume={VOICE_GAIN:.4f}[voice];"
        f"[1:a]volume={MUSIC_GAIN:.4f}[music];"
        "[voice][music]amix=inputs=2:normalize=0,"
        "alimiter=limit=0.95,loudnorm=I=-14:TP=-1.2:LRA=10:linear=true:print_format=none,"
        f"atrim=duration={TARGET_SECONDS}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(TIMED_VOICE),
            "-i",
            str(MUSIC_BED),
            "-filter_complex",
            filter_complex,
            str(MIXED_AUDIO),
        ]
    )


def mux_final() -> None:
    if not VISUAL_VIDEO.exists():
        raise FileNotFoundError(f"Visual video missing: {VISUAL_VIDEO}")

    FINAL_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(VISUAL_VIDEO),
            "-i",
            str(MIXED_AUDIO),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            f"{AUDIO_BITRATE}k",
            "-shortest",
            str(FINAL_VIDEO),
        ]
    )


def append_github_output() -> None:
    github_output = os.getenv("GITHUB_OUTPUT", "").strip()
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        handle.write(f"final_output={FINAL_VIDEO.as_posix()}\n")


def main() -> None:
    generate_voice()
    generate_music_bed()
    mix_audio()
    mux_final()
    append_github_output()
    print(f"[ok] final video ready: {FINAL_VIDEO}")


if __name__ == "__main__":
    main()
