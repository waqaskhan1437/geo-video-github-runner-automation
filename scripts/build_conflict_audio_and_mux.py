#!/usr/bin/env python3
"""
Generate narration voice + score + impact SFX, then mux with rendered visuals.

Main env vars:
- DOC_VISUAL_INPUT
- DOC_FINAL_OUTPUT
- DOC_NARRATION_FILE
- DOC_TARGET_SECONDS
- DOC_VOICE_NAME / DOC_VOICE_RATE / DOC_VOICE_PITCH / DOC_VOICE_GAIN
- DOC_VOICE_ENGINE (auto|edge|gtts)
- DOC_VOICE_STYLE (energetic|neutral)
- DOC_VOICE_ENERGY / DOC_VOICE_VARIATION
- DOC_MUSIC_GAIN / DOC_SFX_GAIN / DOC_IMPACT_TIMES
- DOC_AUDIO_BITRATE
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import wave
from pathlib import Path
from typing import List, Sequence, Tuple

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


def run(cmd: List[str]) -> None:
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


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def parse_percent(value: str) -> float:
    cleaned = value.strip().replace("%", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_percent(value: float) -> str:
    rounded = int(round(value))
    if rounded >= 0:
        return f"+{rounded}%"
    return f"{rounded}%"


def parse_pitch_hz(value: str) -> float:
    cleaned = value.strip().lower().replace("hz", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_pitch_hz(value: float) -> str:
    if abs(value) < 0.05:
        value = 0.0
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}Hz"


def speed_factor_from_percent(percent_value: float) -> float:
    return clamp(1.0 + (percent_value / 100.0), 0.60, 1.60)


TARGET_SECONDS = env_float("DOC_TARGET_SECONDS", 120.0, 30.0, 300.0)
VISUAL_VIDEO = Path(env_str("DOC_VISUAL_INPUT", "outputs/final/conflict_documentary_visual.mp4")).resolve()
FINAL_VIDEO = Path(env_str("DOC_FINAL_OUTPUT", "outputs/final/conflict_documentary_final_1080p.mp4")).resolve()
NARRATION_TEXT = Path(env_str("DOC_NARRATION_FILE", "data/narration_script.txt")).resolve()

VOICE_NAME = env_str("DOC_VOICE_NAME", "en-US-GuyNeural")
VOICE_RATE = env_str("DOC_VOICE_RATE", "-20%")
VOICE_PITCH = env_str("DOC_VOICE_PITCH", "+0Hz")
VOICE_ENGINE = env_str("DOC_VOICE_ENGINE", "auto").lower()
VOICE_STYLE = env_str("DOC_VOICE_STYLE", "energetic").lower()
VOICE_ENERGY = env_float("DOC_VOICE_ENERGY", 1.30, 0.70, 1.60)
VOICE_VARIATION = env_float("DOC_VOICE_VARIATION", 1.00, 0.30, 2.00)
VOICE_GAIN = env_float("DOC_VOICE_GAIN", 1.0, 0.70, 1.60)
MUSIC_GAIN = env_float("DOC_MUSIC_GAIN", 0.30, 0.08, 0.80)
SFX_GAIN = env_float("DOC_SFX_GAIN", 0.24, 0.00, 1.00)
AUDIO_BITRATE = env_int("DOC_AUDIO_BITRATE", 192, 96, 320)
GTTS_LANG = env_str("DOC_GTTS_LANG", "en")
GTTS_TLD = env_str("DOC_GTTS_TLD", "com")

IMPACT_TIMES_RAW = env_str("DOC_IMPACT_TIMES", "18.5,38.3,58.1,78.2,98.4,113.0")
SFX_ENABLED = env_int("DOC_SFX_ENABLED", 1, 0, 1) == 1

work_root = FINAL_VIDEO.parent / f"audio_{FINAL_VIDEO.stem}"
work_root.mkdir(parents=True, exist_ok=True)
segments_dir = work_root / "segments"
segments_dir.mkdir(parents=True, exist_ok=True)

VOICE_CONCAT = work_root / "voice_concat.wav"
TIMED_VOICE = work_root / "voice_timed.wav"
MUSIC_BED = work_root / "music_bed.wav"
SFX_TRACK = work_root / "sfx_track.wav"
MIXED_AUDIO = work_root / "mixed_audio.wav"


def read_segments() -> List[str]:
    if not NARRATION_TEXT.exists():
        raise FileNotFoundError(f"Narration text file not found: {NARRATION_TEXT}")

    text = NARRATION_TEXT.read_text(encoding="utf-8")
    blocks = [re.sub(r"\s+", " ", part.strip()) for part in re.split(r"\n\s*\n", text) if part.strip()]
    if blocks:
        return blocks
    fallback = re.sub(r"\s+", " ", text.strip())
    if fallback:
        return [fallback]
    raise ValueError(f"Narration text file is empty: {NARRATION_TEXT}")


def parse_impact_times() -> List[float]:
    values: List[float] = []
    for raw in IMPACT_TIMES_RAW.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            point = float(raw)
        except ValueError:
            continue
        if 0.0 <= point <= TARGET_SECONDS:
            values.append(point)
    return values


def segment_profile(index: int) -> Tuple[float, float]:
    base_rate = parse_percent(VOICE_RATE)
    base_pitch = parse_pitch_hz(VOICE_PITCH)

    if VOICE_STYLE == "neutral":
        rate_pattern = [2.0, 0.0, 3.0, 1.0, 0.5, 0.5]
        pitch_pattern = [0.2, 0.0, 0.3, 0.2, 0.1, 0.0]
    else:
        rate_pattern = [11.0, 7.0, 13.0, 9.0, 6.0, 5.0]
        pitch_pattern = [2.0, 1.0, 2.4, 1.5, 0.8, 0.6]

    rate_offset = rate_pattern[index % len(rate_pattern)] * VOICE_ENERGY * VOICE_VARIATION
    pitch_offset = pitch_pattern[index % len(pitch_pattern)] * VOICE_ENERGY * VOICE_VARIATION
    curve = math.sin((index + 1) * 0.95)
    rate_offset += curve * 1.7 * VOICE_VARIATION
    pitch_offset += curve * 0.3 * VOICE_VARIATION

    final_rate = clamp(base_rate + rate_offset, -40.0, 35.0)
    final_pitch = clamp(base_pitch + pitch_offset, -8.0, 8.0)
    return final_rate, final_pitch


def synth_segment_edge(text: str, index: int, rate_value: float, pitch_value: float, out_wav: Path) -> None:
    txt_path = segments_dir / f"seg_{index:02d}.txt"
    raw_mp3 = segments_dir / f"seg_{index:02d}_edge.mp3"
    txt_path.write_text(text.strip() + "\n", encoding="utf-8")

    run(
        [
            "python",
            "-m",
            "edge_tts",
            "--file",
            str(txt_path),
            "--voice",
            VOICE_NAME,
            f"--rate={format_percent(rate_value)}",
            f"--pitch={format_pitch_hz(pitch_value)}",
            "--write-media",
            str(raw_mp3),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_mp3),
            "-af",
            "highpass=f=65,lowpass=f=9800",
            "-ar",
            "44100",
            "-ac",
            "1",
            str(out_wav),
        ]
    )


def synth_segment_gtts(text: str, index: int, rate_value: float, pitch_value: float, out_wav: Path) -> None:
    raw_mp3 = segments_dir / f"seg_{index:02d}_gtts.mp3"
    tts = gTTS(text=text, lang=GTTS_LANG, tld=GTTS_TLD)
    tts.save(str(raw_mp3))

    pitch_factor = clamp(1.0 + (pitch_value / 120.0), 0.88, 1.18)
    tempo_factor = clamp(speed_factor_from_percent(rate_value) / pitch_factor, 0.45, 2.40)
    af = f"asetrate=44100*{pitch_factor:.6f},aresample=44100,{atempo_chain(tempo_factor)},highpass=f=65,lowpass=f=9800"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_mp3),
            "-af",
            af,
            "-ar",
            "44100",
            "-ac",
            "1",
            str(out_wav),
        ]
    )


def synthesize_with_engine(segments: Sequence[str], engine: str) -> List[Path]:
    files: List[Path] = []
    for idx, text in enumerate(segments):
        rate_value, pitch_value = segment_profile(idx)
        out_wav = segments_dir / f"seg_{idx:02d}.wav"
        if engine == "edge":
            synth_segment_edge(text, idx, rate_value, pitch_value, out_wav)
        else:
            synth_segment_gtts(text, idx, rate_value, pitch_value, out_wav)
        files.append(out_wav)
    return files


def generate_voice() -> None:
    segments = read_segments()
    selected_engine = VOICE_ENGINE
    if selected_engine not in {"auto", "edge", "gtts"}:
        selected_engine = "auto"

    if selected_engine == "edge":
        print("[voice] engine=edge")
        segment_files = synthesize_with_engine(segments, "edge")
    elif selected_engine == "gtts":
        print("[voice] engine=gtts")
        segment_files = synthesize_with_engine(segments, "gtts")
    else:
        try:
            print("[voice] engine=auto (trying edge-tts)")
            segment_files = synthesize_with_engine(segments, "edge")
        except Exception as exc:  # noqa: BLE001
            print(f"[voice] edge-tts failed, falling back to gTTS: {exc}")
            segment_files = synthesize_with_engine(segments, "gtts")

    concat_list = work_root / "segments_concat.txt"
    concat_list.write_text(
        "".join([f"file '{path.as_posix()}'\n" for path in segment_files]),
        encoding="utf-8",
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-ar",
            "44100",
            "-ac",
            "1",
            str(VOICE_CONCAT),
        ]
    )

    raw_dur = media_duration(VOICE_CONCAT)
    speed_factor = raw_dur / TARGET_SECONDS if TARGET_SECONDS > 0 else 1.0
    if speed_factor <= 0:
        speed_factor = 1.0
    chain = atempo_chain(speed_factor)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(VOICE_CONCAT),
            "-af",
            f"{chain},apad=pad_dur={TARGET_SECONDS},atrim=duration={TARGET_SECONDS}",
            str(TIMED_VOICE),
        ]
    )


def generate_music_bed() -> None:
    outro_start = max(0.0, TARGET_SECONDS - 4.0)
    expr = (
        f"sine=frequency=110:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.045[a0];"
        f"sine=frequency=165:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.040[a1];"
        f"sine=frequency=220:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.035[a2];"
        f"sine=frequency=165:duration={TARGET_SECONDS}:sample_rate=44100,volume=0.038[a3];"
        f"anoisesrc=color=pink:duration={TARGET_SECONDS}:sample_rate=44100,"
        "lowpass=f=1600,highpass=f=150,volume=0.015[a4];"
        f"sine=frequency=30:duration={TARGET_SECONDS}:sample_rate=44100,"
        "lowpass=f=200,volume=0.032[a5];"
        f"[a0][a1][a2][a3][a4][a5]amix=inputs=6:normalize=0,"
        f"afade=t=in:st=0:d=2,afade=t=out:st={outro_start}:d=4"
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


def generate_sfx_track() -> None:
    sr = 44100
    total_samples = int(TARGET_SECONDS * sr)
    impact_times = parse_impact_times()

    if total_samples <= 0:
        raise ValueError("Target duration is invalid.")

    pcm = [0.0] * total_samples
    if SFX_ENABLED:
        rng = random.Random(3217)
        for impact_time in impact_times:
            start = int(impact_time * sr)
            duration = int(1.8 * sr)
            for i in range(duration):
                idx = start + i
                if idx >= total_samples:
                    break
                t = i / sr
                env = math.exp(-3.5 * t)
                shock = math.exp(-12.0 * t) * math.sin(2.0 * math.pi * 4200.0 * t) if t < 0.08 else 0
                rumble_48 = math.sin(2.0 * math.pi * 48.0 * t)
                rumble_24 = math.sin(2.0 * math.pi * 24.0 * t) * 0.6
                ring = math.sin(2.0 * math.pi * 2400.0 * t) * math.exp(-2.5 * t) if t < 0.35 else 0
                crack = rng.uniform(-1.0, 1.0)
                debris = rng.uniform(-0.8, 0.8) * math.exp(-4.0 * t) if t < 0.5 else 0
                hiss = math.sin(2.0 * math.pi * (220.0 - 140.0 * min(1.0, t / 0.45)) * t)
                sample = (
                    0.20 * shock +
                    0.40 * rumble_48 +
                    0.25 * rumble_24 +
                    0.12 * ring +
                    0.15 * crack +
                    0.10 * debris +
                    0.12 * hiss
                ) * env
                pcm[idx] += sample * 0.32

    with wave.open(str(SFX_TRACK), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        frames = bytearray()
        for value in pcm:
            clamped = int(clamp(value, -1.0, 1.0) * 32767)
            frames.extend(int(clamped).to_bytes(2, byteorder="little", signed=True))
        wav.writeframes(frames)


def mix_audio() -> None:
    filter_complex = (
        "[0:a]highpass=f=65,lowpass=f=10200,asetrate=44100,"
        "lowpass=f=250:poles=2:a=0.707[warmth];"
        "[warmth]dynaudnorm=f=120:g=15,"
        "acompressor=threshold=-22dB:ratio=3.0:attack=8:release=120,"
        f"aecho=0.7:0.8:200:0.9,"
        f"volume={VOICE_GAIN:.4f}[voice];"
        f"[1:a]volume={MUSIC_GAIN:.4f}[music];"
        f"[2:a]volume={SFX_GAIN:.4f}[sfx];"
        "[voice][music][sfx]amix=inputs=3:normalize=0,acompressor=threshold=-18dB:ratio=1.8,"
        "alimiter=limit=0.97,loudnorm=I=-14:TP=-1.2:LRA=11:linear=true:print_format=none,"
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
            "-i",
            str(SFX_TRACK),
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
    generate_sfx_track()
    mix_audio()
    mux_final()
    append_github_output()
    print(f"[ok] final video ready: {FINAL_VIDEO}")


if __name__ == "__main__":
    main()

