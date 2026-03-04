from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Iterable, List

from .utils import ensure_dir


def _date_key(run_date: date) -> str:
    return run_date.strftime("%Y%m%d")


def _find_run_dirs(output_root: Path, run_date: date) -> List[Path]:
    key = _date_key(run_date)
    run_dirs = sorted(p for p in output_root.glob(f"whiteboard_{key}_*") if p.is_dir())
    return run_dirs


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _build_sora_prompt(run_id: str, puzzle: dict, metadata: dict) -> str:
    question = puzzle.get("question", "Solve the puzzle")
    equations = [item.get("text", "") for item in puzzle.get("equations", []) if item.get("text")]
    answer = puzzle.get("answer", metadata.get("answer", ""))

    equation_block = "\n".join(f"- {line}" for line in equations[:4])
    if not equation_block:
        equation_block = "- Show puzzle clues in clean whiteboard style"

    return "\n".join(
        [
            f"## {run_id}",
            "Vertical short video, 9:16, whiteboard background, realistic marker strokes.",
            "Timing plan:",
            "- 0s-3s: Hook with energetic camera push-in",
            "- 3s-16s: Show puzzle clues and timer",
            "- 16s-23s: Reveal and explain answer",
            "- 23s-28s: CTA for next puzzle",
            "Puzzle lines:",
            equation_block,
            f"Final question: {question}",
            f"Correct answer: {answer}",
            "Style notes: high contrast text, no overflow, smooth zoom, subtle paper texture.",
            "Audio notes: warm human voice, slight suspense bed, clear pause before reveal.",
            "",
        ]
    )


def _build_voice_direction(run_id: str, puzzle: dict) -> str:
    narration = puzzle.get("narration", "")
    narration_clean = " ".join(str(narration).split())
    return "\n".join(
        [
            f"[{run_id}]",
            "Voice style: warm, confident, medium pace, short pauses before answer.",
            "Emphasis words: solve, pause, trick, answer.",
            f"Narration draft: {narration_clean}",
            "",
        ]
    )


def _write_figma_storyboard(path: Path, rows: Iterable[dict]) -> Path:
    fieldnames = [
        "run_id",
        "scene_id",
        "start_sec",
        "end_sec",
        "frame_goal",
        "onscreen_text",
        "visual_direction",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _build_notebook_json(run_date: date) -> dict:
    key = _date_key(run_date)
    markdown = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Daily Content Tracker\\n",
            f"Run date: {run_date.isoformat()} (`{key}`)\\n",
            "Use this notebook to review metadata and quality flags per video.\\n",
        ],
    }

    code = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "from pathlib import Path\\n",
            "import json\\n",
            "\\n",
            f"date_key = '{key}'\\n",
            "root = Path('output')\\n",
            "rows = []\\n",
            "for path in sorted(root.glob(f'whiteboard_{date_key}_*/metadata.json')):\\n",
            "    data = json.loads(path.read_text(encoding='utf-8'))\\n",
            "    rows.append({\\n",
            "        'run_id': data.get('run_id'),\\n",
            "        'mode': data.get('mode'),\\n",
            "        'category': data.get('category'),\\n",
            "        'answer': data.get('answer'),\\n",
            "        'warnings': '; '.join(data.get('warnings', [])),\\n",
            "        'source_url': data.get('source_url', ''),\\n",
            "    })\\n",
            "\\n",
            "for row in rows:\\n",
            "    print(row)\\n",
        ],
    }

    return {
        "cells": [markdown, code],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def generate_creator_pack(output_root: Path, run_date: date) -> Path:
    run_dirs = _find_run_dirs(output_root=output_root, run_date=run_date)
    if not run_dirs:
        raise FileNotFoundError(f"No run folders found for date {run_date.isoformat()}")

    pack_dir = ensure_dir(output_root / f"creator_pack_{_date_key(run_date)}")

    sora_sections: list[str] = ["# Sora Prompt Pack", ""]
    voice_sections: list[str] = ["# Speech Direction Pack", ""]
    storyboard_rows: list[dict] = []

    for run_dir in run_dirs:
        run_id = run_dir.name
        puzzle_path = run_dir / "puzzle.json"
        metadata_path = run_dir / "metadata.json"

        if not puzzle_path.exists() or not metadata_path.exists():
            continue

        puzzle = _read_json(puzzle_path)
        metadata = _read_json(metadata_path)

        sora_sections.append(_build_sora_prompt(run_id=run_id, puzzle=puzzle, metadata=metadata))
        voice_sections.append(_build_voice_direction(run_id=run_id, puzzle=puzzle))

        question = puzzle.get("question", "")
        explanation_lines = puzzle.get("explanation", [])
        explanation_text = " | ".join(explanation_lines[:2])

        storyboard_rows.extend(
            [
                {
                    "run_id": run_id,
                    "scene_id": "scene_01_hook",
                    "start_sec": 0,
                    "end_sec": 3,
                    "frame_goal": "Stop scroll with hook",
                    "onscreen_text": puzzle.get("hook", ""),
                    "visual_direction": "Big title, marker stroke reveal, slight push-in",
                },
                {
                    "run_id": run_id,
                    "scene_id": "scene_02_puzzle",
                    "start_sec": 3,
                    "end_sec": 16,
                    "frame_goal": "Present clues clearly",
                    "onscreen_text": question,
                    "visual_direction": "Timer visible, equations centered, no text clipping",
                },
                {
                    "run_id": run_id,
                    "scene_id": "scene_03_solution",
                    "start_sec": 16,
                    "end_sec": 23,
                    "frame_goal": "Reveal and explain",
                    "onscreen_text": f"Answer: {metadata.get('answer')}",
                    "visual_direction": explanation_text or "Show concise explanation",
                },
                {
                    "run_id": run_id,
                    "scene_id": "scene_04_cta",
                    "start_sec": 23,
                    "end_sec": 28,
                    "frame_goal": "Drive follow/comment",
                    "onscreen_text": "Follow for tomorrow's harder puzzle",
                    "visual_direction": "Strong CTA, clean spacing, hold for readability",
                },
            ]
        )

    _write_text(pack_dir / "sora_prompts.md", "\n".join(sora_sections).strip() + "\n")
    _write_text(pack_dir / "speech_direction.md", "\n".join(voice_sections).strip() + "\n")
    _write_figma_storyboard(pack_dir / "figma_storyboard.csv", storyboard_rows)

    notebook_payload = _build_notebook_json(run_date=run_date)
    (pack_dir / "workflow_tracker.ipynb").write_text(json.dumps(notebook_payload, indent=2), encoding="utf-8")

    summary = {
        "run_date": run_date.isoformat(),
        "runs_included": [p.name for p in run_dirs],
        "files": [
            "sora_prompts.md",
            "speech_direction.md",
            "figma_storyboard.csv",
            "workflow_tracker.ipynb",
        ],
    }
    (pack_dir / "pack_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return pack_dir
