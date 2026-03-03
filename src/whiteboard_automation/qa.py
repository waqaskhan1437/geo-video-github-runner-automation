from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .models import PipelineConfig, Puzzle
from .utils import ensure_dir, read_json, write_json


HISTORY_FILE = "history.json"


def load_recent_signatures(config: PipelineConfig) -> List[str]:
    state_dir = ensure_dir(config.state_root)
    history_path = state_dir / HISTORY_FILE
    payload = read_json(history_path, default={"entries": []})
    entries = payload.get("entries", [])
    signatures = [entry.get("signature", "") for entry in entries if entry.get("signature")]
    return signatures[-config.min_unique_history :]


def append_history(config: PipelineConfig, puzzle: Puzzle, run_id: str) -> Path:
    state_dir = ensure_dir(config.state_root)
    history_path = state_dir / HISTORY_FILE
    payload = read_json(history_path, default={"entries": []})

    entries = payload.get("entries", [])
    entries.append(
        {
            "run_id": run_id,
            "puzzle_id": puzzle.puzzle_id,
            "signature": puzzle.signature,
            "answer": puzzle.answer,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )

    payload["entries"] = entries[-2000:]
    write_json(history_path, payload)
    return history_path


def validate_puzzle(puzzle: Puzzle) -> None:
    if puzzle.answer < 0:
        raise ValueError("Puzzle answer must be non-negative.")

    if not puzzle.equations:
        raise ValueError("Puzzle requires at least one equation.")

    if not puzzle.question.strip():
        raise ValueError("Puzzle question must not be empty.")

    if not puzzle.explanation:
        raise ValueError("Puzzle explanation must not be empty.")


def export_metadata(path: Path, payload: Dict[str, Any]) -> None:
    write_json(path, payload)
