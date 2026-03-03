from __future__ import annotations

from pathlib import Path

from .utils import run_cmd, which


class FfmpegError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    if which("ffmpeg") is None:
        raise FfmpegError("ffmpeg binary not found in PATH.")


def frames_to_video(frames_dir: Path, fps: int, out_file: Path) -> None:
    ensure_ffmpeg()

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(out_file),
    ]

    result = run_cmd(cmd)
    if result.returncode != 0:
        raise FfmpegError(f"ffmpeg failed while building silent video.\n{result.stderr}")


def mux_with_voice(video_file: Path, voice_file: Path, out_file: Path) -> None:
    ensure_ffmpeg()

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_file),
        "-i",
        str(voice_file),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(out_file),
    ]

    result = run_cmd(cmd)
    if result.returncode != 0:
        raise FfmpegError(f"ffmpeg failed while muxing voice-over.\n{result.stderr}")
