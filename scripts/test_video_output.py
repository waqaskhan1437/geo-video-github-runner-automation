#!/usr/bin/env python3
"""Quality test gate for final documentary output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from video_quality_utils import (
    measure_loudness,
    probe_video,
    sample_frame_luma,
    sample_motion_energy,
    sample_warm_ratio,
    summarize_metrics,
)


def validate(metrics: Dict[str, float], strict: bool) -> List[str]:
    issues: List[str] = []

    duration = metrics.get("duration", 0.0)
    width = int(metrics.get("width", 0))
    height = int(metrics.get("height", 0))
    fps = metrics.get("fps", 0.0)
    size_mb = metrics.get("size_mb", 0.0)
    loudness_i = metrics.get("input_i", -30.0)
    loudness_lra = metrics.get("input_lra", 99.0)
    mean_luma = metrics.get("mean_luma", 0.0)
    std_luma = metrics.get("std_luma", 0.0)
    motion_mean = metrics.get("motion_mean", 0.0)
    warm_ratio = metrics.get("warm_ratio", 0.0)
    has_audio = metrics.get("has_audio", 0.0) >= 1.0

    dur_lo = 119.4 if strict else 118.5
    dur_hi = 120.6 if strict else 121.5
    if not (dur_lo <= duration <= dur_hi):
        issues.append(f"Duration out of range: {duration:.3f}s")

    if width != 1920 or height != 1080:
        issues.append(f"Resolution mismatch: {width}x{height} (expected 1920x1080)")

    if not (23.8 <= fps <= 24.2):
        issues.append(f"FPS out of range: {fps:.3f}")

    if size_mb < (4.0 if strict else 3.0):
        issues.append(f"File size too small: {size_mb:.2f} MB")

    if not has_audio:
        issues.append("Audio stream missing")

    if strict:
        if not (-17.5 <= loudness_i <= -13.0):
            issues.append(f"Integrated loudness out of range: {loudness_i:.3f} LUFS")
        if loudness_lra > 12.0:
            issues.append(f"Loudness range too high: {loudness_lra:.3f}")
    else:
        if not (-19.0 <= loudness_i <= -11.5):
            issues.append(f"Integrated loudness out of relaxed range: {loudness_i:.3f} LUFS")

    if mean_luma < 4 or mean_luma > 70:
        issues.append(f"Average luma unusual: {mean_luma:.3f}")
    if std_luma < 4:
        issues.append(f"Visual contrast too low (std_luma): {std_luma:.3f}")
    if motion_mean < (3.2 if strict else 2.4):
        issues.append(f"Motion intensity too low: {motion_mean:.3f}")
    if warm_ratio < (0.004 if strict else 0.003):
        issues.append(f"Impact highlight ratio too low: {warm_ratio:.3f}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run output quality checks.")
    parser.add_argument("--video", required=True, help="Video file path")
    parser.add_argument("--report", required=True, help="JSON report output path")
    parser.add_argument("--strict", action="store_true", help="Enable strict gate")
    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    probe = probe_video(video_path)
    loudness = measure_loudness(video_path)
    luma = sample_frame_luma(video_path, every_seconds=10, max_frames=18)
    motion = sample_motion_energy(video_path, fps=1.2, max_frames=120)
    warmth = sample_warm_ratio(video_path, every_seconds=6, max_frames=24)
    metrics = summarize_metrics(probe, loudness, luma, motion=motion, warmth=warmth)
    issues = validate(metrics, strict=args.strict)

    report = {
        "video": str(video_path),
        "strict": bool(args.strict),
        "metrics": metrics,
        "passed": len(issues) == 0,
        "issues": issues,
    }

    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if issues:
        print("[test] FAILED")
        for issue in issues:
            print(" -", issue)
        return 1

    print("[test] PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
