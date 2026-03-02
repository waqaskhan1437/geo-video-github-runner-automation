#!/usr/bin/env python3
"""Shared helpers for video analysis and quality testing."""

from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageStat


def run_capture(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def parse_ratio(value: str) -> float:
    if "/" in value:
        a, b = value.split("/", 1)
        try:
            num = float(a)
            den = float(b)
            if den == 0:
                return 0.0
            return num / den
        except ValueError:
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def probe_video(video_path: Path) -> Dict[str, float]:
    result = run_capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(video_path),
        ]
    )
    payload = json.loads(result.stdout)
    fmt = payload.get("format", {})
    streams = payload.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    return {
        "duration": float(fmt.get("duration", 0.0)),
        "size_bytes": float(fmt.get("size", 0.0)),
        "width": float(video_stream.get("width", 0)),
        "height": float(video_stream.get("height", 0)),
        "fps": parse_ratio(video_stream.get("r_frame_rate", "0/1")),
        "video_codec": str(video_stream.get("codec_name", "")),
        "audio_codec": str(audio_stream.get("codec_name", "")),
        "has_audio": 1.0 if audio_stream else 0.0,
    }


def parse_loudnorm_json(stderr_text: str) -> Dict[str, float]:
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr_text, flags=re.DOTALL)
    if not blocks:
        return {}
    try:
        payload = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return {}

    def _val(key: str) -> float:
        value = payload.get(key)
        if value is None:
            return 0.0
        try:
            return float(str(value).replace("inf", "0"))
        except ValueError:
            return 0.0

    return {
        "input_i": _val("input_i"),
        "input_lra": _val("input_lra"),
        "input_tp": _val("input_tp"),
        "target_offset": _val("target_offset"),
    }


def measure_loudness(video_path: Path) -> Dict[str, float]:
    process = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(video_path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    # ffmpeg returns non-zero for null output in many setups, so do not check return code.
    return parse_loudnorm_json(process.stderr)


def sample_frame_luma(video_path: Path, every_seconds: int = 10, max_frames: int = 18) -> Dict[str, float]:
    root = Path("outputs/final")
    root.mkdir(parents=True, exist_ok=True)
    tmp_dir = root / f"_analysis_frames_{os.getpid()}_{random.randint(1000, 9999)}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    fps_expr = f"1/{max(1, every_seconds)}"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps_expr}",
            "-frames:v",
            str(max_frames),
            (tmp_dir / "frame_%03d.jpg").as_posix(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    means: List[float] = []
    stddevs: List[float] = []
    for frame in sorted(tmp_dir.glob("frame_*.jpg")):
        with Image.open(frame) as image:
            gray = image.convert("L")
            stat = ImageStat.Stat(gray)
            means.append(float(stat.mean[0]))
            stddevs.append(float(stat.stddev[0]))

    shutil.rmtree(tmp_dir, ignore_errors=True)
    if not means:
        return {"mean_luma": 0.0, "std_luma": 0.0, "samples": 0.0}
    return {
        "mean_luma": float(sum(means) / len(means)),
        "std_luma": float(sum(stddevs) / len(stddevs)),
        "samples": float(len(means)),
    }


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def round3(value: float) -> float:
    return float(f"{value:.3f}")


def score_quality(metrics: Dict[str, float]) -> float:
    score = 100.0
    mean_luma = metrics.get("mean_luma", 0.0)
    std_luma = metrics.get("std_luma", 0.0)
    loudness = metrics.get("input_i", -30.0)
    size_mb = metrics.get("size_bytes", 0.0) / (1024 * 1024)

    # Dark documentary visuals naturally have low luma.
    score -= abs(mean_luma - 16.0) * 1.15
    if std_luma < 8.0:
        score -= (8.0 - std_luma) * 2.2
    score -= abs(loudness - (-14.5)) * 3.0
    if size_mb < 4.0:
        score -= (4.0 - size_mb) * 6.0

    return round3(clamp(score, 0.0, 100.0))


def summarize_metrics(probe: Dict[str, float], loudness: Dict[str, float], luma: Dict[str, float]) -> Dict[str, float]:
    merged = dict(probe)
    merged.update(loudness)
    merged.update(luma)
    merged["quality_score"] = score_quality(merged)
    merged["size_mb"] = round3(merged.get("size_bytes", 0.0) / (1024 * 1024))
    merged["duration"] = round3(merged.get("duration", 0.0))
    merged["fps"] = round3(merged.get("fps", 0.0))
    merged["mean_luma"] = round3(merged.get("mean_luma", 0.0))
    merged["std_luma"] = round3(merged.get("std_luma", 0.0))
    merged["input_i"] = round3(merged.get("input_i", 0.0))
    merged["input_lra"] = round3(merged.get("input_lra", 0.0))
    merged["input_tp"] = round3(merged.get("input_tp", 0.0))
    return merged
