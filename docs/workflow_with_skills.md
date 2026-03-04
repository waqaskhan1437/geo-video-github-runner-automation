# Skill-Driven Workflow Upgrade

This workflow maps your installed skills to concrete automation outputs.

## Skill mapping

1. `speech`
- Local Piper voice-over in generation (`--with-voice --piper-model ...`).
- `speech_direction.md` generated for delivery pacing and emphasis.

2. `sora`
- `sora_prompts.md` generated per run with scene timing and style constraints.
- Can be copied into Sora prompt workflow for faster iterations.

3. `figma`
- `figma_storyboard.csv` generated with scene IDs and timings.
- Import into Figma planning board/table for design handoff.

4. `jupyter-notebook`
- `workflow_tracker.ipynb` generated for daily analytics review.
- Reads run metadata and shows warnings/source fields quickly.

## End-to-end daily flow

1. Generate videos
```bash
python run.py batch --date 2026-03-04 --count 3 --mode internet --engine pillow --with-voice --piper-model models/en_US-amy-medium.onnx
```

2. Build creator pack
```bash
python run.py pack --date 2026-03-04
```

3. Review outputs under:
- `output/whiteboard_YYYYMMDD_*/`
- `output/creator_pack_YYYYMMDD/`

## GitHub runner

Both workflows now generate creator pack files automatically after video generation.
