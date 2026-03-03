from __future__ import annotations

import html
from pathlib import Path

from .models import PipelineConfig, Puzzle
from .utils import ensure_dir, run_cmd, which


class ScriptimateError(RuntimeError):
    pass


def _write_text_svg(path: Path, text: str, width: int = 640, height: int = 90, font_size: int = 44) -> None:
    safe_text = html.escape(text)
    payload = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">\n  <rect width=\"{width}\" height=\"{height}\" fill=\"white\"/>\n  <text x=\"8\" y=\"{font_size + 8}\" font-family=\"Arial, sans-serif\" font-size=\"{font_size}\" fill=\"black\">{safe_text}</text>\n</svg>\n"""
    path.write_text(payload, encoding="utf-8")


def _build_smte(puzzle: Puzzle) -> str:
    lines = [
        "set_frame_size 720 1280",
        "place title 40 80 1 1",
        "animate_1500 pause",
        "place hook 40 180 1 1",
        "animate_1500 pause",
        "place eq1 60 360 1 1",
        "animate_1200 pause",
        "place eq2 60 470 1 1",
        "animate_1200 pause",
        "place eq3 60 580 1 1",
        "animate_1200 pause",
        "place q1 60 720 1 1",
        "animate_3000 pause",
        "place ans 60 900 1 1",
        "animate_2500 pause",
        "place exp 60 1010 1 1",
        "animate_2500 pause",
    ]
    return "\n".join(lines) + "\n"


def render_with_scriptimate(puzzle: Puzzle, run_dir: Path, config: PipelineConfig) -> Path:
    npx_exe = which("npx") or which("npx.cmd")
    if npx_exe is None:
        raise ScriptimateError("npx is required for Scriptimate rendering.")

    scene_dir = ensure_dir(run_dir / "scriptimate")

    # Build text assets used by Scriptimate timeline.
    _write_text_svg(scene_dir / "title.svg", puzzle.title)
    _write_text_svg(scene_dir / "hook.svg", puzzle.hook, font_size=36)
    _write_text_svg(scene_dir / "eq1.svg", puzzle.equations[0].text)
    _write_text_svg(scene_dir / "eq2.svg", puzzle.equations[1].text)
    _write_text_svg(scene_dir / "eq3.svg", puzzle.equations[2].text)
    _write_text_svg(scene_dir / "q1.svg", puzzle.question)
    _write_text_svg(scene_dir / "ans.svg", f"Answer: {puzzle.answer}", font_size=48)
    _write_text_svg(scene_dir / "exp.svg", puzzle.explanation[1], font_size=34)

    smte_path = scene_dir / "scene.smte"
    smte_path.write_text(_build_smte(puzzle), encoding="utf-8")

    cmd = [npx_exe, "scriptimate@latest", "-i", "scene.smte", "-f", "mp4"]
    try:
        result = run_cmd(cmd, cwd=scene_dir)
    except FileNotFoundError as exc:
        raise ScriptimateError(f"Failed to execute npx for Scriptimate: {exc}") from exc
    if result.returncode != 0:
        raise ScriptimateError(f"Scriptimate failed.\n{result.stderr}")

    outputs = sorted(scene_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not outputs:
        raise ScriptimateError("Scriptimate finished but no MP4 output was found.")

    out_file = run_dir / "video_scriptimate.mp4"
    outputs[0].replace(out_file)
    return out_file
