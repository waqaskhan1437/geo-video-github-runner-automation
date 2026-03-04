from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .creator_pack import generate_creator_pack
from .models import PipelineConfig
from .pipeline import run_pipeline
from .voiceover import available_voice_profiles


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CPU-first whiteboard puzzle video automation")

    parser.add_argument("--output-root", default="output", help="Output directory root")
    parser.add_argument("--state-root", default="state", help="State directory root")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Generate one video")
    run_cmd.add_argument("--date", default=date.today().isoformat(), help="Run date in YYYY-MM-DD")
    run_cmd.add_argument("--index", type=int, default=1, help="Daily index for multiple videos")
    run_cmd.add_argument("--mode", choices=["generated", "internet", "intelligence"], default="generated", help="Puzzle source mode")
    run_cmd.add_argument("--engine", choices=["pillow", "scriptimate"], default="pillow", help="Rendering engine")
    run_cmd.add_argument("--fps", type=int, default=24, help="Output frame rate")
    run_cmd.add_argument("--width", type=int, default=720, help="Output width")
    run_cmd.add_argument("--height", type=int, default=1280, help="Output height")
    run_cmd.add_argument("--with-voice", action="store_true", help="Generate voice-over with Piper")
    run_cmd.add_argument("--piper-model", default="", help="Path to Piper ONNX model")
    run_cmd.add_argument("--piper-exe", default="piper", help="Piper executable path or command")
    run_cmd.add_argument("--voice-profile", choices=available_voice_profiles(), default="calm", help="Voice tuning profile")

    batch_cmd = subparsers.add_parser("batch", help="Generate N daily videos")
    batch_cmd.add_argument("--date", default=date.today().isoformat(), help="Run date in YYYY-MM-DD")
    batch_cmd.add_argument("--count", type=int, default=3, help="How many videos to generate")
    batch_cmd.add_argument("--mode", choices=["generated", "internet", "intelligence"], default="generated")
    batch_cmd.add_argument("--engine", choices=["pillow", "scriptimate"], default="pillow")
    batch_cmd.add_argument("--fps", type=int, default=24)
    batch_cmd.add_argument("--width", type=int, default=720)
    batch_cmd.add_argument("--height", type=int, default=1280)
    batch_cmd.add_argument("--with-voice", action="store_true")
    batch_cmd.add_argument("--piper-model", default="")
    batch_cmd.add_argument("--piper-exe", default="piper")
    batch_cmd.add_argument("--voice-profile", choices=available_voice_profiles(), default="calm")

    pack_cmd = subparsers.add_parser("pack", help="Generate workflow creator pack from runs")
    pack_cmd.add_argument("--date", default=date.today().isoformat(), help="Run date in YYYY-MM-DD")

    return parser


def _build_config(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(
        width=args.width,
        height=args.height,
        fps=args.fps,
        output_root=Path(args.output_root),
        state_root=Path(args.state_root),
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        config = _build_config(args)
        run_date = _parse_date(args.date)
        piper_model = Path(args.piper_model) if args.piper_model else None

        artifacts = run_pipeline(
            run_date=run_date,
            index=args.index,
            config=config,
            mode=args.mode,
            engine=args.engine,
            with_voice=args.with_voice,
            piper_model=piper_model,
            piper_exe=args.piper_exe,
            voice_profile=args.voice_profile,
        )

        print(f"Run completed: {artifacts.run_id}")
        print(f"Output folder: {artifacts.run_dir}")
        return 0

    if args.command == "batch":
        config = _build_config(args)
        run_date = _parse_date(args.date)
        piper_model = Path(args.piper_model) if args.piper_model else None

        for idx in range(1, args.count + 1):
            artifacts = run_pipeline(
                run_date=run_date,
                index=idx,
                config=config,
                mode=args.mode,
                engine=args.engine,
                with_voice=args.with_voice,
                piper_model=piper_model,
                piper_exe=args.piper_exe,
                voice_profile=args.voice_profile,
            )
            print(f"[{idx}/{args.count}] {artifacts.run_id} -> {artifacts.run_dir}")

        return 0

    if args.command == "pack":
        run_date = _parse_date(args.date)
        output_root = Path(args.output_root)
        pack_dir = generate_creator_pack(output_root=output_root, run_date=run_date)
        print(f"Creator pack generated: {pack_dir}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
