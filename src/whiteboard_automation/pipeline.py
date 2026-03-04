from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Optional

from .ffmpeg_ops import frames_to_video, mux_with_voice
from .models import PipelineConfig, RunArtifacts
from .puzzles import generate_unique_puzzle
from .qa import append_history, export_metadata, load_recent_signatures, validate_puzzle
from .render_frames import render_frames
from .scriptimate_engine import ScriptimateError, render_with_scriptimate
from .utils import ensure_dir, write_json
from .voiceover import VoiceError, synthesize_with_piper


def _build_run_artifacts(config: PipelineConfig, run_date: date, index: int) -> RunArtifacts:
    run_id = f"{config.run_prefix}_{run_date.strftime('%Y%m%d')}_{index:02d}"
    run_dir = ensure_dir(config.output_root / run_id)
    frames_dir = ensure_dir(run_dir / config.frames_dir_name)

    return RunArtifacts(
        run_id=run_id,
        run_dir=run_dir,
        frames_dir=frames_dir,
        puzzle_json=run_dir / "puzzle.json",
        narration_txt=run_dir / "narration.txt",
        silent_video=run_dir / "video_silent.mp4",
        final_video=run_dir / "video_final.mp4",
        voice_wav=run_dir / "voice.wav",
        metadata=run_dir / "metadata.json",
    )


def _save_puzzle_artifacts(puzzle, artifacts: RunArtifacts) -> None:
    write_json(artifacts.puzzle_json, asdict(puzzle))
    artifacts.narration_txt.write_text(puzzle.narration, encoding="utf-8")


def run_pipeline(
    run_date: date,
    index: int,
    config: PipelineConfig,
    mode: str = "generated",
    engine: str = "pillow",
    with_voice: bool = False,
    piper_model: Optional[Path] = None,
    piper_exe: Optional[str] = None,
    voice_profile: str = "calm",
) -> RunArtifacts:
    ensure_dir(config.output_root)
    ensure_dir(config.state_root)

    recent_signatures = load_recent_signatures(config)
    puzzle = generate_unique_puzzle(run_date=run_date, index=index, recent_signatures=recent_signatures, mode=mode)
    validate_puzzle(puzzle)

    artifacts = _build_run_artifacts(config=config, run_date=run_date, index=index)
    _save_puzzle_artifacts(puzzle=puzzle, artifacts=artifacts)

    engine_used = engine
    warnings: list[str] = []

    if engine == "scriptimate":
        try:
            render_with_scriptimate(puzzle=puzzle, run_dir=artifacts.run_dir, config=config)
            scriptimate_video = artifacts.run_dir / "video_scriptimate.mp4"
            if scriptimate_video.exists():
                artifacts.silent_video = scriptimate_video
            else:
                raise ScriptimateError("Scriptimate output file not found after rendering.")
        except ScriptimateError as exc:
            warnings.append(f"Scriptimate failed, fallback to pillow renderer: {exc}")
            engine_used = "pillow"

    if engine_used == "pillow":
        render_frames(puzzle=puzzle, config=config, frames_dir=artifacts.frames_dir)
        frames_to_video(frames_dir=artifacts.frames_dir, fps=config.fps, out_file=artifacts.silent_video)

    final_video = artifacts.silent_video

    if with_voice:
        try:
            if not piper_model:
                raise VoiceError("with_voice enabled but --piper-model not provided.")
            synthesize_with_piper(
                text=puzzle.narration,
                out_wav=artifacts.voice_wav,
                model_path=piper_model,
                piper_exe=piper_exe,
                voice_profile=voice_profile,
            )
            mux_with_voice(video_file=artifacts.silent_video, voice_file=artifacts.voice_wav, out_file=artifacts.final_video)
            final_video = artifacts.final_video
        except VoiceError as exc:
            warnings.append(f"Voice-over skipped: {exc}")

    metadata = {
        "run_id": artifacts.run_id,
        "run_date": run_date.isoformat(),
        "engine": engine_used,
        "mode": mode,
        "requested_engine": engine,
        "with_voice": with_voice,
        "voice_profile": voice_profile if with_voice else "",
        "final_video": str(final_video),
        "answer": puzzle.answer,
        "puzzle_id": puzzle.puzzle_id,
        "category": puzzle.category,
        "source_url": puzzle.source_url,
        "source_note": puzzle.source_note,
        "signature": puzzle.signature,
        "warnings": warnings,
    }

    export_metadata(artifacts.metadata, metadata)
    append_history(config=config, puzzle=puzzle, run_id=artifacts.run_id)

    return artifacts
