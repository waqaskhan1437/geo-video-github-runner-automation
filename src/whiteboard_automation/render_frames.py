from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

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


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0]), int(box[3] - box[1])


def _split_long_word(draw: ImageDraw.ImageDraw, word: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for ch in word:
        candidate = current + ch
        w, _ = _text_size(draw, candidate, font)
        if w <= max_width or not current:
            current = candidate
        else:
            chunks.append(current)
            current = ch
    if current:
        chunks.append(current)
    return chunks


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current: list[str] = []

    for word in words:
        test_line = " ".join(current + [word])
        width, _ = _text_size(draw, test_line, font)
        if width <= max_width:
            current.append(word)
            continue

        if current:
            lines.append(" ".join(current))
            current = []

        single_width, _ = _text_size(draw, word, font)
        if single_width > max_width:
            parts = _split_long_word(draw, word, font, max_width)
            lines.extend(parts[:-1])
            current = [parts[-1]]
        else:
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def _fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    max_font_size: int,
    min_font_size: int = 20,
    line_spacing: int = 8,
) -> tuple[ImageFont.ImageFont, list[str], int, int]:
    for size in range(max_font_size, min_font_size - 1, -2):
        font = _load_font(size)
        lines = _wrap_text(draw, text, font, max_width)
        _, line_h = _text_size(draw, "Ag", font)
        total_h = (line_h * len(lines)) + (line_spacing * max(0, len(lines) - 1))
        if total_h <= max_height:
            return font, lines, line_h, total_h

    font = _load_font(min_font_size)
    lines = _wrap_text(draw, text, font, max_width)
    _, line_h = _text_size(draw, "Ag", font)
    total_h = (line_h * len(lines)) + (line_spacing * max(0, len(lines) - 1))
    return font, lines, line_h, total_h


def _draw_wrapped_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    max_font_size: int,
    min_font_size: int = 20,
    line_spacing: int = 8,
    align: str = "left",
    valign: str = "top",
) -> int:
    x1, y1, x2, y2 = box
    max_width = max(40, x2 - x1)
    max_height = max(20, y2 - y1)

    font, lines, line_h, total_h = _fit_text_block(
        draw=draw,
        text=text,
        max_width=max_width,
        max_height=max_height,
        max_font_size=max_font_size,
        min_font_size=min_font_size,
        line_spacing=line_spacing,
    )

    if valign == "center":
        y = y1 + max(0, (max_height - total_h) // 2)
    else:
        y = y1

    for line in lines:
        line_w, _ = _text_size(draw, line, font)
        if align == "center":
            x = x1 + max(0, (max_width - line_w) // 2)
        elif align == "right":
            x = x2 - line_w
        else:
            x = x1

        draw.text((x, y), line, font=font, fill="black")
        y += line_h + line_spacing

    return y


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
    max_width: int,
) -> int:
    cursor_x = x
    cursor_y = y
    line_h = max(icon_size + 8, _text_size(draw, "Ag", font)[1] + 16)
    max_x = x + max_width

    for token in text.split():
        if token in {"F", "F*", "C", "R"}:
            token_w = icon_size + 12
            token_h = icon_size
        else:
            token_w = _text_size(draw, token, font)[0] + 16
            token_h = _text_size(draw, token, font)[1]

        if cursor_x + token_w > max_x and cursor_x > x:
            cursor_x = x
            cursor_y += line_h

        if token in {"F", "F*", "C", "R"}:
            _draw_symbol(draw, token, cursor_x, cursor_y, icon_size)
        else:
            token_y = cursor_y + max(0, (line_h - token_h) // 2)
            draw.text((cursor_x, token_y), token, font=font, fill="black")

        cursor_x += token_w

    return cursor_y + line_h + 10


def _draw_whiteboard_base(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    margin = 28
    draw.rectangle((margin, margin, width - margin, height - margin), outline="black", width=4, fill="#FCFCFC")

    grid_top = margin + 72
    grid_bottom = height - margin - 24
    spacing = 92
    y = grid_top
    while y <= grid_bottom:
        draw.line((margin + 18, y, width - margin - 18, y), fill="#E9E9E9", width=2)
        y += spacing


def _draw_scene_hook(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int, t: float) -> None:
    _draw_wrapped_block(
        draw,
        puzzle.title,
        box=(56, 92, width - 56, 238),
        max_font_size=62,
        min_font_size=30,
        line_spacing=6,
        align="center",
        valign="center",
    )

    _draw_wrapped_block(
        draw,
        puzzle.hook,
        box=(56, 250, width - 56, 410),
        max_font_size=42,
        min_font_size=24,
        line_spacing=8,
        align="center",
        valign="center",
    )

    pulse = 1.0 + (math.sin(t * 4) * 0.03)
    size = int(min(width, height) * 0.18 * pulse)
    size = max(72, min(140, size))

    x = (width // 2) - (size // 2)
    y = min(height - size - 180, 430)
    _draw_flower(draw, x, y, size, missing_petal=False)


def _draw_scene_puzzle(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int, t: float) -> None:
    _draw_wrapped_block(
        draw,
        "Solve before timer ends",
        box=(60, 86, width - 270, 170),
        max_font_size=44,
        min_font_size=24,
        align="left",
        valign="center",
    )

    elapsed = max(0.0, t - 3.0)
    timer_left = max(0, 10 - int(elapsed))
    _draw_wrapped_block(
        draw,
        f"Timer: {timer_left}s",
        box=(width - 230, 86, width - 62, 170),
        max_font_size=40,
        min_font_size=22,
        align="right",
        valign="center",
    )

    eq_font = _load_font(36)
    cursor_y = 220
    max_width = width - 130

    for line in puzzle.equations:
        cursor_y = _draw_equation_line(
            draw=draw,
            text=line.text,
            x=66,
            y=cursor_y,
            icon_size=62,
            font=eq_font,
            max_width=max_width,
        )
        cursor_y += 8

    cursor_y = _draw_equation_line(
        draw=draw,
        text=f"Final: {puzzle.question}",
        x=66,
        y=cursor_y + 8,
        icon_size=62,
        font=_load_font(38),
        max_width=max_width,
    )

    footer_top = min(height - 170, cursor_y + 20)
    _draw_wrapped_block(
        draw,
        "Pause, solve, then drop your answer in comments.",
        box=(60, footer_top, width - 60, height - 52),
        max_font_size=34,
        min_font_size=20,
        align="left",
        valign="center",
    )


def _draw_scene_solution(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int) -> None:
    _draw_wrapped_block(
        draw,
        f"Answer: {puzzle.answer}",
        box=(60, 92, width - 60, 220),
        max_font_size=62,
        min_font_size=30,
        align="left",
        valign="center",
    )

    y = 252
    for line in puzzle.explanation:
        y = _draw_wrapped_block(
            draw,
            line,
            box=(60, y, width - 60, y + 160),
            max_font_size=40,
            min_font_size=22,
            align="left",
            valign="top",
        ) + 14

    _draw_wrapped_block(
        draw,
        "If you solved this fast, next one will be harder.",
        box=(60, height - 190, width - 60, height - 58),
        max_font_size=32,
        min_font_size=20,
        align="left",
        valign="center",
    )


def _draw_scene_cta(draw: ImageDraw.ImageDraw, _puzzle: Puzzle, width: int, height: int) -> None:
    _draw_wrapped_block(
        draw,
        "Want harder puzzle?",
        box=(60, 180, width - 60, 320),
        max_font_size=64,
        min_font_size=30,
        align="left",
        valign="center",
    )

    _draw_wrapped_block(
        draw,
        "Follow for daily UK and USA style brain teasers with full solution reveal.",
        box=(60, 370, width - 60, 620),
        max_font_size=38,
        min_font_size=20,
        align="left",
        valign="top",
    )

    _draw_wrapped_block(
        draw,
        "Next video drops tomorrow.",
        box=(60, height - 220, width - 60, height - 70),
        max_font_size=40,
        min_font_size=24,
        align="left",
        valign="center",
    )


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
            _draw_scene_puzzle(draw, puzzle, config.width, config.height, t)
        elif t < 23.0:
            _draw_scene_solution(draw, puzzle, config.width, config.height)
        else:
            _draw_scene_cta(draw, puzzle, config.width, config.height)

        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, format="PNG")

    return total_frames
