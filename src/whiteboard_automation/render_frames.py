from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .models import PipelineConfig, Puzzle
from .utils import ensure_dir


def _load_font(size: int) -> ImageFont.ImageFont:
    for font_name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0])


def _draw_flower(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, missing_petal: bool = False) -> None:
    cx = x + size // 2
    cy = y + size // 2
    petal_radius = max(4, size // 7)
    ring = size // 3

    petal_positions = []
    for step in range(8):
        angle = (math.pi * 2 / 8) * step
        px = int(cx + math.cos(angle) * ring)
        py = int(cy + math.sin(angle) * ring)
        petal_positions.append((px, py))

    if missing_petal:
        petal_positions = petal_positions[:-1]

    for px, py in petal_positions:
        draw.ellipse((px - petal_radius, py - petal_radius, px + petal_radius, py + petal_radius), outline="black", width=3, fill="white")

    center_radius = max(5, size // 6)
    draw.ellipse((cx - center_radius, cy - center_radius, cx + center_radius, cy + center_radius), outline="black", width=3, fill="#F5D76E")


def _draw_cat(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    cx = x + size // 2
    cy = y + size // 2
    radius = size // 3

    draw.polygon([(cx - radius, cy - radius // 2), (cx - radius // 2, y + size // 8), (cx - radius // 8, cy - radius)], outline="black", width=3, fill="white")
    draw.polygon([(cx + radius, cy - radius // 2), (cx + radius // 2, y + size // 8), (cx + radius // 8, cy - radius)], outline="black", width=3, fill="white")
    draw.ellipse((cx - radius, cy - radius // 2, cx + radius, cy + radius + radius // 2), outline="black", width=3, fill="white")

    eye_r = max(2, size // 18)
    for eye_x in (cx - size // 8, cx + size // 8):
        draw.ellipse((eye_x - eye_r, cy - eye_r, eye_x + eye_r, cy + eye_r), fill="black")

    draw.line((cx - size // 10, cy + size // 8, cx + size // 10, cy + size // 8), fill="black", width=3)


def _draw_rabbit(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    cx = x + size // 2
    cy = y + size // 2 + size // 10
    head_r = size // 3

    draw.ellipse((cx - head_r // 2, y, cx - head_r // 8, y + head_r), outline="black", width=3, fill="white")
    draw.ellipse((cx + head_r // 8, y, cx + head_r // 2, y + head_r), outline="black", width=3, fill="white")
    draw.ellipse((cx - head_r, cy - head_r, cx + head_r, cy + head_r), outline="black", width=3, fill="white")

    eye_r = max(2, size // 20)
    for eye_x in (cx - size // 8, cx + size // 8):
        draw.ellipse((eye_x - eye_r, cy - eye_r, eye_x + eye_r, cy + eye_r), fill="black")

    draw.ellipse((cx - 4, cy + size // 12, cx + 4, cy + size // 12 + 8), fill="black")


def _draw_symbol(draw: ImageDraw.ImageDraw, token: str, x: int, y: int, size: int) -> int:
    if token == "F":
        _draw_flower(draw, x, y, size, missing_petal=False)
    elif token == "F*":
        _draw_flower(draw, x, y, size, missing_petal=True)
    elif token == "C":
        _draw_cat(draw, x, y, size)
    elif token == "R":
        _draw_rabbit(draw, x, y, size)
    else:
        return x

    return x + size + 12


def _draw_equation_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    icon_size: int,
    font: ImageFont.ImageFont,
) -> None:
    cursor_x = x
    for token in text.split():
        if token in {"F", "F*", "C", "R"}:
            cursor_x = _draw_symbol(draw, token, cursor_x, y, icon_size)
            continue

        draw.text((cursor_x, y + icon_size // 5), token, font=font, fill="black")
        cursor_x += _text_width(draw, token, font) + 16


def _draw_whiteboard_base(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    margin = 36
    draw.rectangle((margin, margin, width - margin, height - margin), outline="black", width=4, fill="#FCFCFC")
    for line in range(8):
        y = margin + 80 + line * 130
        draw.line((margin + 24, y, width - margin - 24, y), fill="#E9E9E9", width=2)


def _draw_scene_hook(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, _height: int, t: float) -> None:
    title_font = _load_font(56)
    body_font = _load_font(40)

    pulse = 1.0 + (math.sin(t * 4) * 0.02)
    title = puzzle.title
    title_w = _text_width(draw, title, title_font)
    draw.text((int((width - title_w) / 2), 120), title, fill="black", font=title_font)

    hook_text = puzzle.hook
    hook_w = _text_width(draw, hook_text, body_font)
    draw.text((int((width - hook_w) / 2), 260), hook_text, fill="black", font=body_font)

    size = int(100 * pulse)
    x = (width // 2) - (size // 2)
    _draw_flower(draw, x, 420, size, missing_petal=False)


def _draw_scene_puzzle(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, t: float) -> None:
    header_font = _load_font(42)
    eq_font = _load_font(44)
    timer_font = _load_font(48)

    draw.text((72, 100), "Solve before timer ends", fill="black", font=header_font)

    elapsed = max(0.0, t - 3.0)
    timer_left = max(0, 10 - int(elapsed))
    timer_text = f"Timer: {timer_left}s"
    draw.text((width - 250, 105), timer_text, fill="black", font=timer_font)

    line_start_y = 270
    step = 170
    _draw_equation_line(draw, puzzle.equations[0].text, 90, line_start_y, 80, eq_font)
    _draw_equation_line(draw, puzzle.equations[1].text, 90, line_start_y + step, 80, eq_font)
    _draw_equation_line(draw, puzzle.equations[2].text, 90, line_start_y + step * 2, 80, eq_font)
    _draw_equation_line(draw, puzzle.question, 90, line_start_y + step * 3 + 30, 80, eq_font)

    draw.text((80, 1130), "Pause and comment your answer", fill="black", font=_load_font(36))


def _draw_scene_solution(draw: ImageDraw.ImageDraw, puzzle: Puzzle, _width: int) -> None:
    header_font = _load_font(56)
    line_font = _load_font(40)

    draw.text((72, 120), f"Answer: {puzzle.answer}", fill="black", font=header_font)

    y = 320
    for line in puzzle.explanation:
        draw.text((72, y), line, fill="black", font=line_font)
        y += 140

    draw.text((72, 1050), "Common trap: F* is missing one petal", fill="black", font=_load_font(36))


def _draw_scene_cta(draw: ImageDraw.ImageDraw, _puzzle: Puzzle, _width: int) -> None:
    draw.text((72, 240), "Want harder puzzle?", fill="black", font=_load_font(58))
    draw.text((72, 420), "Follow for daily UK/USA style brain teasers.", fill="black", font=_load_font(36))
    draw.text((72, 560), "Next video drops tomorrow.", fill="black", font=_load_font(36))


def render_frames(puzzle: Puzzle, config: PipelineConfig, frames_dir: Path) -> int:
    ensure_dir(frames_dir)

    total_duration = 28.0
    total_frames = int(total_duration * config.fps)

    for frame_idx in range(total_frames):
        t = frame_idx / config.fps
        img = Image.new("RGB", (config.width, config.height), "white")
        draw = ImageDraw.Draw(img)

        _draw_whiteboard_base(draw, config.width, config.height)

        if t < 3.0:
            _draw_scene_hook(draw, puzzle, config.width, config.height, t)
        elif t < 16.0:
            _draw_scene_puzzle(draw, puzzle, config.width, t)
        elif t < 23.0:
            _draw_scene_solution(draw, puzzle, config.width)
        else:
            _draw_scene_cta(draw, puzzle, config.width)

        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, format="PNG")

    return total_frames
