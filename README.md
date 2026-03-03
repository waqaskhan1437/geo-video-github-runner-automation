# Whiteboard Puzzle GitHub Runner Automation

This repository is rebuilt from scratch for a CPU-first, self-hosted, command-line whiteboard puzzle pipeline. It generates daily short-form puzzle videos with flowers, animals, math traps, and final solution reveal.

## What this automation does

1. Generates a new puzzle script every day (date-seeded + uniqueness guard).
2. Validates answer logic to avoid wrong or dummy puzzle outputs.
3. Renders whiteboard-style vertical video frames on CPU.
4. Builds final MP4 with FFmpeg.
5. Optionally adds local realistic voice-over with Piper TTS.
6. Runs locally or through GitHub Actions schedule.

## Free tool plan used in this codebase

1. Python + Pillow for CPU whiteboard rendering.
2. FFmpeg for encoding and muxing.
3. Scriptimate support included as optional alternative renderer.
4. Piper support included as optional local voice-over engine.
5. GitHub Actions for daily automation runner.

## Requirements

1. Python 3.11+
2. FFmpeg in PATH
3. Optional: Node.js + npx (for Scriptimate engine)
4. Optional: Piper binary + ONNX voice model (for local human-like voice)

## Quick start (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py run --date 2026-03-04 --engine pillow
```

## Quick start (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py run --date 2026-03-04 --engine pillow
```

## Daily batch generation

```bash
python run.py batch --date 2026-03-04 --count 3 --engine pillow
```

## Voice-over run (Piper local TTS)

```bash
python run.py run \
  --date 2026-03-04 \
  --engine pillow \
  --with-voice \
  --piper-model models/en_US-amy-medium.onnx
```

## Scriptimate run (optional)

```bash
python run.py run --date 2026-03-04 --engine scriptimate
```

If Scriptimate fails or is unavailable, the pipeline falls back to the Pillow renderer.

## Output layout

1. `output/<run_id>/puzzle.json` generated puzzle data.
2. `output/<run_id>/narration.txt` voice-over script.
3. `output/<run_id>/frames/` rendered frame sequence.
4. `output/<run_id>/video_silent.mp4` silent render.
5. `output/<run_id>/voice.wav` optional Piper output.
6. `output/<run_id>/video_final.mp4` final muxed video.
7. `output/<run_id>/metadata.json` run metadata and warnings.

## GitHub Actions

Workflow file: `.github/workflows/daily-whiteboard.yml`

1. Scheduled daily run at `03:20 UTC`.
2. Manual run via `workflow_dispatch` with date/count/engine inputs.
3. Uploads generated videos as workflow artifacts.

## Local helper script

PowerShell helper:

```powershell
.\scripts\run_daily.ps1 -RunDate 2026-03-04 -Count 3 -Engine pillow
```

## Notes

1. This repo is intentionally CPU-first and fully free for base operation.
2. For best human-like voice quality, use Piper models tuned for your target accent.
3. Keep puzzle uniqueness high by preserving `state/history.json` between runs.
