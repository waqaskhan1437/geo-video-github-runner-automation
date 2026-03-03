from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class PuzzleSymbol:
    key: str
    label: str
    value: int


@dataclass(frozen=True)
class PuzzleEquation:
    text: str


@dataclass(frozen=True)
class Puzzle:
    puzzle_id: str
    title: str
    hook: str
    category: str
    source_url: str
    source_note: str
    symbols: Dict[str, PuzzleSymbol]
    equations: List[PuzzleEquation]
    question: str
    answer: int
    explanation: List[str]
    narration: str
    signature: str


@dataclass
class PipelineConfig:
    width: int = 720
    height: int = 1280
    fps: int = 24
    output_root: Path = Path("output")
    state_root: Path = Path("state")
    frames_dir_name: str = "frames"
    run_prefix: str = "whiteboard"
    min_unique_history: int = 365


@dataclass
class RunArtifacts:
    run_id: str
    run_dir: Path
    frames_dir: Path
    puzzle_json: Path
    narration_txt: Path
    silent_video: Path
    final_video: Path
    voice_wav: Path
    metadata: Path
    extra_files: List[Path] = field(default_factory=list)
