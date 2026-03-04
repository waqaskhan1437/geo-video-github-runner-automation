# Whiteboard Puzzle GitHub Runner Automation

This repository is rebuilt from scratch for a CPU-first, self-hosted, command-line whiteboard puzzle pipeline. It generates daily short-form puzzle videos with flowers, animals, math traps, and final solution reveal.

## What this automation does

1. Generates a new puzzle script every day (date-seeded + uniqueness guard).
2. Validates answer logic to avoid wrong or dummy puzzle outputs.
3. Renders whiteboard-style vertical video frames on CPU.
4. Uses adaptive text wrapping/shrinking to prevent overflow.
5. Builds final MP4 with FFmpeg.
6. Optionally adds local realistic voice-over with Piper TTS.
7. Runs locally or through GitHub Actions schedule.
8. Supports `generated` mode and `internet` mode puzzle templates.
9. Includes `intelligence` mode for advanced non-calculation IQ puzzle questions.
10. Uses an advanced edge visual theme (modern cards, neon accents, progress timer).

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

## Creator pack generation

```bash
python run.py pack --date 2026-03-04
```

The creator pack is designed to improve workflow using installed skills:

1. `sora` -> auto cinematic prompt file.
2. `speech` -> voice direction script with pacing cues.
3. `figma` -> scene storyboard CSV for quick design handoff.
4. `jupyter-notebook` -> notebook template for daily review/analytics.

## Internet puzzle mode (2 videos)

```bash
python run.py batch --date 2026-03-04 --count 2 --mode internet --engine pillow
```

## Intelligence mode (2 videos)

```bash
python run.py batch --date 2026-03-04 --count 2 --mode intelligence --engine pillow --with-voice --piper-model models/en_US-amy-medium.onnx
```

`intelligence` mode rotates across 9 puzzle types:

1. Arrangement (seating order)
2. No-crossing line maze (visual hard mode)
3. Truth-check constraints
4. Odd-one-out
5. Analogy
6. Syllogism
7. Direction sense
8. Conditional elimination
9. Rotation pattern

## Voice-over run (Piper local TTS)

```bash
python run.py run \
  --date 2026-03-04 \
  --mode internet \
  --engine pillow \
  --with-voice \
  --voice-profile calm \
  --piper-model models/en_US-amy-medium.onnx
```

Available voice profiles:

1. `calm` (recommended, softer and less irritating)
2. `studio` (balanced)
3. `clear` (slightly more energetic)

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
8. `output/creator_pack_YYYYMMDD/sora_prompts.md` Sora prompt pack.
9. `output/creator_pack_YYYYMMDD/speech_direction.md` speech direction pack.
10. `output/creator_pack_YYYYMMDD/figma_storyboard.csv` storyboard sheet.
11. `output/creator_pack_YYYYMMDD/workflow_tracker.ipynb` notebook tracker.
12. `output/creator_pack_YYYYMMDD/pack_manifest.json` pack summary.

## GitHub Actions

Workflow files:

1. `.github/workflows/daily-whiteboard.yml`
2. `.github/workflows/runner-full-check.yml`

1. Scheduled daily run at `03:20 UTC`.
2. Manual run via `workflow_dispatch` with date/count/mode/engine inputs.
3. Uploads generated videos as workflow artifacts.
4. Automatically builds creator pack after video generation.

`runner-full-check.yml` performs a complete CI smoke test on GitHub runner:

1. Installs Python + Node + FFmpeg.
2. Installs project dependencies (including Piper voice stack).
3. Downloads a free Piper model.
4. Runs `pillow`, `scriptimate`, and `with-voice` generation tests.
5. Runs internet mode batch generation for 2 videos.
6. Builds creator pack assets (`sora/speech/figma/jupyter`).
7. Verifies `video_final.mp4` includes audio stream.

## Local helper script

PowerShell helper:

```powershell
.\scripts\run_daily.ps1 -RunDate 2026-03-04 -Count 3 -Engine pillow
```

## Notes

1. This repo is intentionally CPU-first and fully free for base operation.
2. For best human-like voice quality, use Piper models tuned for your target accent.
3. Keep puzzle uniqueness high by preserving `state/history.json` between runs.
4. Internet-sourced puzzle inspirations used in this repo are listed in `docs/internet_question_sources.md`.
5. IQ puzzle type reference is available at `docs/iq_question_types.md`.
6. Skill-driven workflow usage guide is available at `docs/workflow_with_skills.md`.
