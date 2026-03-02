# Geo Video GitHub Runner Automation

Yeh repo GitHub runners par documentary-style geo mapping videos automate karta hai.

## Core Workflows

```text
.github/workflows/geo-video-automation.yml
.github/workflows/conflict-doc-ai-pipeline.yml
.github/workflows/gpu-ai-stack-self-hosted.yml
```

## Basic Geo Mapping Automation

Files:

```text
scripts/geo_video_automation.py
data/route_points.sample.json
```

Run:
1. `Actions` tab me `Geo Mapping Video Automation` choose karo.
2. `Run workflow` karo.
3. `points_file` ya `points_json` input do.
4. Artifact download karo.

## AI Refine Pipeline (Render -> Analyze -> Refine -> Test)

Workflow: `.github/workflows/conflict-doc-ai-pipeline.yml`

Pipeline:
1. Pass 1 cinematic map render.
2. Pass 1 energetic voiceover + score + impact SFX.
3. Quality analysis (luma, contrast, loudness, motion, warm-impact ratio).
4. AI heuristic refine suggestions (`refine.env`).
5. Refined render + refined audio mix.
6. Strict final test.
7. Artifact upload.

Main scripts:

```text
scripts/render_conflict_documentary.py
scripts/build_conflict_audio_and_mux.py
scripts/ai_video_analyzer_refiner.py
scripts/test_video_output.py
scripts/video_quality_utils.py
data/narration_script.txt
```

Voice engines:
- Primary: `edge-tts`
- Fallback: `gTTS`

### Visual tuning env vars
- `DOC_MISSILE_DENSITY_SCALE`
- `DOC_IMPACT_RING_SCALE`
- `DOC_TARGET_CIRCLE_SCALE`
- `DOC_SHAKE_SCALE`
- `DOC_BOMBER_COUNT_SCALE`
- `DOC_SMOKE_ALPHA_SCALE`
- `DOC_EXPLOSION_ALPHA_SCALE`
- `DOC_GRAIN_ALPHA`

### Audio tuning env vars
- `DOC_VOICE_STYLE` (`energetic` / `neutral`)
- `DOC_VOICE_ENERGY`
- `DOC_VOICE_VARIATION`
- `DOC_MUSIC_GAIN`
- `DOC_SFX_GAIN`
- `DOC_IMPACT_TIMES`

## Optional GPU AI Stack (Self-Hosted Runner)

Workflow: `.github/workflows/gpu-ai-stack-self-hosted.yml`

Purpose:
- Self-hosted GPU runner par ComfyUI stack install karna.
- ComfyUI Manager + VideoHelperSuite install karna.
- Optional open-source editor stack install karna (`moviepy`, `opencv-python-headless`).

Setup script:

```text
scripts/setup_gpu_ai_stack.sh
```

Required labels:
- `self-hosted`
- `linux`
- `x64`
- `gpu`

## Research

Forums + GitHub stack research:

```text
docs/ai_stack_research.md
```

