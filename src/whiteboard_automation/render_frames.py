from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import PipelineConfig, Puzzle
from .utils import ensure_dir


COLORS = {
    "bg_top": (7, 14, 28),
    "bg_bottom": (16, 38, 58),
    "grid": (27, 60, 88),
    "panel": (14, 24, 40),
    "panel_alt": (19, 33, 54),
    "panel_border": (63, 138, 176),
    "accent_cyan": (58, 215, 224),
    "accent_orange": (255, 174, 76),
    "text_primary": (234, 246, 255),
    "text_muted": (170, 205, 224),
    "chip_bg": (32, 55, 79),
    "chip_text": (194, 236, 255),
}


BOLD_FONT_FILES = (
    "segoeuib.ttf",
    "seguisb.ttf",
    "arialbd.ttf",
    "Bahnschrift.ttf",
    "DejaVuSans-Bold.ttf",
)

REGULAR_FONT_FILES = (
    "segoeui.ttf",
    "arial.ttf",
    "DejaVuSans.ttf",
)


def _load_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = BOLD_FONT_FILES if bold else REGULAR_FONT_FILES
    for font_name in candidates:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    for font_name in REGULAR_FONT_FILES:
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
    min_font_size: int = 18,
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
    min_font_size: int = 18,
    line_spacing: int = 8,
    align: str = "left",
    valign: str = "top",
    fill: tuple[int, int, int] = COLORS["text_primary"],
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

        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + line_spacing

    return y


def _draw_vertical_gradient(image: Image.Image, top_rgb: tuple[int, int, int], bottom_rgb: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    for y in range(height):
        ratio = y / max(1, (height - 1))
        color = (
            int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * ratio),
            int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * ratio),
            int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * ratio),
        )
        draw.line((0, y, width, y), fill=color)


def _build_base_canvas(width: int, height: int) -> Image.Image:
    base = Image.new("RGB", (width, height), COLORS["bg_top"])
    _draw_vertical_gradient(base, COLORS["bg_top"], COLORS["bg_bottom"])

    draw = ImageDraw.Draw(base)

    for y in range(0, height, 72):
        draw.line((0, y, width, y), fill=COLORS["grid"], width=1)
    for x in range(0, width, 90):
        draw.line((x, 0, x, height), fill=COLORS["grid"], width=1)

    draw.arc((width - 360, -110, width + 60, 300), start=195, end=25, fill=COLORS["accent_cyan"], width=3)
    draw.arc((-140, height - 350, 260, height + 80), start=25, end=220, fill=COLORS["accent_orange"], width=3)

    return base


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    radius: int = 26,
    border: int = 3,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 3, y1 + 5, x2 + 3, y2 + 5), radius=radius, fill=(5, 10, 18), outline=None)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=border)


def _draw_chip(draw: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    font = _load_font(24)
    tw, th = _text_size(draw, text, font)
    pad_x = 16
    pad_y = 8
    box = (x, y, x + tw + (pad_x * 2), y + th + (pad_y * 2))
    draw.rounded_rectangle(box, radius=16, fill=COLORS["chip_bg"], outline=COLORS["panel_border"], width=2)
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=COLORS["chip_text"])


def _draw_category_badge(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int) -> None:
    label = f"{puzzle.category.upper()} MODE"
    _draw_chip(draw, label, width - 260, 56)


def _draw_dynamic_accents(draw: ImageDraw.ImageDraw, width: int, height: int, t: float) -> None:
    pulse = int(18 * math.sin(t * 1.8))
    x_shift = int(22 * math.cos(t * 1.3))

    draw.arc((width - 330 + x_shift, 82 + pulse, width - 40 + x_shift, 334 + pulse), start=200, end=22, fill=COLORS["accent_cyan"], width=4)
    draw.arc((28 - x_shift, height - 334 - pulse, 330 - x_shift, height - 40 - pulse), start=25, end=225, fill=COLORS["accent_orange"], width=4)


def _draw_scene_hook(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int, t: float) -> None:
    _draw_category_badge(draw, puzzle, width)

    hero_box = (40, 140, width - 40, 500)
    _draw_panel(draw, hero_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=34)

    _draw_wrapped_block(
        draw,
        puzzle.title,
        box=(74, 188, width - 74, 310),
        max_font_size=64,
        min_font_size=30,
        align="center",
        valign="center",
        fill=COLORS["text_primary"],
    )

    _draw_wrapped_block(
        draw,
        puzzle.hook,
        box=(74, 322, width - 74, 470),
        max_font_size=40,
        min_font_size=22,
        align="center",
        valign="center",
        fill=COLORS["text_muted"],
    )

    pulse = 1.0 + (math.sin(t * 4.0) * 0.06)
    orb_r = int(68 * pulse)
    cx = width // 2
    cy = min(height - 220, 700)
    draw.ellipse((cx - orb_r, cy - orb_r, cx + orb_r, cy + orb_r), fill=COLORS["chip_bg"], outline=COLORS["accent_cyan"], width=5)
    draw.text((cx - 18, cy - 28), "IQ", font=_load_font(46), fill=COLORS["accent_orange"])


def _draw_timer(draw: ImageDraw.ImageDraw, width: int, t: float) -> None:
    elapsed = max(0.0, t - 3.0)
    timer_left = max(0, 10 - int(elapsed))
    progress = min(1.0, max(0.0, elapsed / 10.0))

    _draw_wrapped_block(
        draw,
        f"{timer_left}s",
        box=(width - 178, 118, width - 66, 158),
        max_font_size=36,
        min_font_size=22,
        align="right",
        valign="center",
    )

    bar_box = (60, 172, width - 60, 190)
    draw.rounded_rectangle(bar_box, radius=9, fill=(34, 51, 72), outline=COLORS["panel_border"], width=2)
    fill_w = int((bar_box[2] - bar_box[0]) * progress)
    if fill_w > 0:
        draw.rounded_rectangle((bar_box[0], bar_box[1], bar_box[0] + fill_w, bar_box[3]), radius=9, fill=COLORS["accent_cyan"], outline=None)


def _draw_equation_items(draw: ImageDraw.ImageDraw, texts: list[str], box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    item_count = max(1, len(texts))
    gap = 12
    inner_h = y2 - y1
    row_h = max(68, (inner_h - (gap * (item_count - 1))) // item_count)

    for idx, text in enumerate(texts):
        row_top = y1 + idx * (row_h + gap)
        row_bottom = min(y2, row_top + row_h)
        row_box = (x1, row_top, x2, row_bottom)
        _draw_panel(draw, row_box, fill=COLORS["panel_alt"], outline=(52, 99, 136), radius=20, border=2)

        badge = (x1 + 14, row_top + 14, x1 + 52, row_top + 52)
        draw.ellipse(badge, fill=COLORS["chip_bg"], outline=COLORS["accent_orange"], width=2)
        draw.text((x1 + 28, row_top + 22), str(idx + 1), fill=COLORS["accent_orange"], font=_load_font(20))

        _draw_wrapped_block(
            draw,
            text,
            box=(x1 + 66, row_top + 12, x2 - 14, row_bottom - 12),
            max_font_size=38,
            min_font_size=19,
            line_spacing=6,
            align="left",
            valign="center",
        )


def _draw_equation_items_tight(
    draw: ImageDraw.ImageDraw,
    texts: list[str],
    box: tuple[int, int, int, int],
    min_row_height: int = 48,
) -> None:
    x1, y1, x2, y2 = box
    item_count = max(1, len(texts))
    gap = 10
    inner_h = y2 - y1
    row_h = max(min_row_height, (inner_h - (gap * (item_count - 1))) // item_count)

    for idx, text in enumerate(texts):
        row_top = y1 + idx * (row_h + gap)
        row_bottom = min(y2, row_top + row_h)
        row_box = (x1, row_top, x2, row_bottom)
        _draw_panel(draw, row_box, fill=COLORS["panel_alt"], outline=(52, 99, 136), radius=18, border=2)

        badge = (x1 + 12, row_top + 10, x1 + 44, row_top + 42)
        draw.ellipse(badge, fill=COLORS["chip_bg"], outline=COLORS["accent_orange"], width=2)
        draw.text((x1 + 23, row_top + 16), str(idx + 1), fill=COLORS["accent_orange"], font=_load_font(16))

        _draw_wrapped_block(
            draw,
            text,
            box=(x1 + 56, row_top + 8, x2 - 12, row_bottom - 8),
            max_font_size=30,
            min_font_size=16,
            line_spacing=4,
            align="left",
            valign="center",
        )


def _is_link_maze(puzzle: Puzzle) -> bool:
    return puzzle.title.startswith("No Crossing Link Maze")


def _draw_link_maze_board(
    draw: ImageDraw.ImageDraw,
    puzzle: Puzzle,
    box: tuple[int, int, int, int],
    show_solution: bool = False,
) -> None:
    _draw_panel(draw, box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=28)
    x1, y1, x2, y2 = box

    board = (x1 + 22, y1 + 20, x2 - 22, y2 - 20)
    draw.rounded_rectangle(board, radius=18, fill=(10, 20, 34), outline=(66, 124, 156), width=2)

    bx1, by1, bx2, by2 = board
    left_x = bx1 + 86
    right_x = bx2 - 86
    top_y = by1 + 78
    mid_y = (by1 + by2) // 2
    bot_y = by2 - 78

    left_labels = ("A", "C", "B")
    right_labels = ("B", "C", "A")
    left_pts = [(left_x, top_y), (left_x, mid_y), (left_x, bot_y)]
    right_pts = [(right_x, top_y), (right_x, mid_y), (right_x, bot_y)]

    mid_x = (left_x + right_x) // 2
    gate_h = 62
    gate_top = mid_y - (gate_h // 2)
    gate_bottom = gate_top + gate_h

    draw.line((mid_x, by1 + 14, mid_x, gate_top), fill=COLORS["text_muted"], width=7)
    draw.line((mid_x, gate_bottom, mid_x, by2 - 14), fill=COLORS["text_muted"], width=7)
    draw.rounded_rectangle((mid_x - 16, gate_top, mid_x + 16, gate_bottom), radius=8, outline=COLORS["accent_orange"], width=2, fill=(24, 36, 54))
    draw.text((mid_x - 24, gate_top - 28), "GATE", fill=COLORS["accent_orange"], font=_load_font(14))

    for idx, (pt, label) in enumerate(zip(left_pts, left_labels)):
        px, py = pt
        draw.line((px + 18, py, px + 64, py), fill=COLORS["panel_border"], width=3)
        draw.ellipse((px - 20, py - 20, px + 20, py + 20), fill=(40, 20, 26), outline=(255, 110, 110), width=3)
        draw.text((px - 9, py - 14), label, fill=(255, 170, 170), font=_load_font(28))

    for pt, label in zip(right_pts, right_labels):
        px, py = pt
        draw.line((px - 64, py, px - 18, py), fill=COLORS["panel_border"], width=3)
        draw.ellipse((px - 20, py - 20, px + 20, py + 20), fill=(40, 20, 26), outline=(255, 110, 110), width=3)
        draw.text((px - 9, py - 14), label, fill=(255, 170, 170), font=_load_font(28))

    if show_solution:
        # C path through center gate.
        draw.line((left_x + 20, mid_y, mid_x - 18, mid_y), fill=COLORS["accent_cyan"], width=5)
        draw.line((mid_x + 18, mid_y, right_x - 20, mid_y), fill=COLORS["accent_cyan"], width=5)

        # B top outside route.
        draw.line((left_x + 20, bot_y, left_x + 20, by2 + 8), fill=COLORS["accent_orange"], width=4)
        draw.line((left_x + 20, by2 + 8, right_x - 20, by2 + 8), fill=COLORS["accent_orange"], width=4)
        draw.line((right_x - 20, by2 + 8, right_x - 20, top_y), fill=COLORS["accent_orange"], width=4)

        # A bottom outside route.
        draw.line((left_x + 20, top_y, left_x + 20, by1 - 8), fill=(190, 146, 255), width=4)
        draw.line((left_x + 20, by1 - 8, right_x - 20, by1 - 8), fill=(190, 146, 255), width=4)
        draw.line((right_x - 20, by1 - 8, right_x - 20, bot_y), fill=(190, 146, 255), width=4)


def _draw_scene_puzzle_link_maze(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int, t: float) -> None:
    _draw_category_badge(draw, puzzle, width)

    top_box = (40, 90, width - 40, 208)
    _draw_panel(draw, top_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=26)

    _draw_wrapped_block(
        draw,
        "No crossing path challenge",
        box=(62, 114, width - 230, 154),
        max_font_size=40,
        min_font_size=22,
        valign="center",
    )
    _draw_timer(draw, width, t)

    _draw_link_maze_board(draw, puzzle, box=(40, 228, width - 40, 700), show_solution=False)

    clues = [eq.text for eq in puzzle.equations]
    clues.append(f"Final: {puzzle.question}")
    clue_box = (40, 716, width - 40, height - 228)
    _draw_panel(draw, clue_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=24)
    _draw_equation_items_tight(draw, clues, box=(58, 742, width - 58, height - 254), min_row_height=48)

    foot_box = (40, height - 210, width - 40, height - 64)
    _draw_panel(draw, foot_box, fill=COLORS["panel"], outline=(72, 126, 162), radius=24)
    _draw_wrapped_block(
        draw,
        "Mentally draw paths first. One wrong start creates dead-end.",
        box=(62, height - 186, width - 62, height - 88),
        max_font_size=30,
        min_font_size=18,
        align="left",
        valign="center",
        fill=COLORS["text_muted"],
    )


def _draw_scene_puzzle(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int, t: float) -> None:
    if _is_link_maze(puzzle):
        _draw_scene_puzzle_link_maze(draw, puzzle, width, height, t)
        return

    _draw_category_badge(draw, puzzle, width)

    top_box = (40, 90, width - 40, 208)
    _draw_panel(draw, top_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=26)

    _draw_wrapped_block(
        draw,
        "Solve before timer ends",
        box=(62, 114, width - 230, 154),
        max_font_size=42,
        min_font_size=22,
        valign="center",
    )
    _draw_timer(draw, width, t)

    puzzle_box = (40, 228, width - 40, height - 282)
    _draw_panel(draw, puzzle_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=30)

    lines = [eq.text for eq in puzzle.equations]
    lines.append(f"Final: {puzzle.question}")
    _draw_equation_items(draw, lines, box=(58, 258, width - 58, height - 314))

    foot_box = (40, height - 246, width - 40, height - 64)
    _draw_panel(draw, foot_box, fill=COLORS["panel"], outline=(72, 126, 162), radius=24)
    _draw_wrapped_block(
        draw,
        "Pause now. Solve first, then comment your answer.",
        box=(62, height - 222, width - 62, height - 88),
        max_font_size=34,
        min_font_size=20,
        align="left",
        valign="center",
        fill=COLORS["text_muted"],
    )


def _draw_scene_solution(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int) -> None:
    if _is_link_maze(puzzle):
        _draw_category_badge(draw, puzzle, width)

        answer_box = (40, 90, width - 40, 220)
        _draw_panel(draw, answer_box, fill=COLORS["panel"], outline=COLORS["accent_orange"], radius=28)
        _draw_wrapped_block(
            draw,
            f"Answer: {puzzle.answer}",
            box=(62, 122, width - 62, 196),
            max_font_size=62,
            min_font_size=28,
            align="left",
            valign="center",
            fill=COLORS["accent_orange"],
        )

        _draw_link_maze_board(draw, puzzle, box=(40, 240, width - 40, 760), show_solution=True)

        explain_box = (40, 776, width - 40, height - 194)
        _draw_panel(draw, explain_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=24)
        _draw_equation_items_tight(draw, puzzle.explanation, box=(58, 804, width - 58, height - 222), min_row_height=58)

        tail_box = (40, height - 170, width - 40, height - 64)
        _draw_panel(draw, tail_box, fill=COLORS["panel"], outline=(72, 126, 162), radius=24)
        _draw_wrapped_block(
            draw,
            "Hard visual puzzle solved. Next maze will be tougher.",
            box=(62, height - 148, width - 62, height - 84),
            max_font_size=30,
            min_font_size=18,
            valign="center",
            fill=COLORS["text_muted"],
        )
        return

    _draw_category_badge(draw, puzzle, width)

    answer_box = (40, 110, width - 40, 250)
    _draw_panel(draw, answer_box, fill=COLORS["panel"], outline=COLORS["accent_orange"], radius=28)
    _draw_wrapped_block(
        draw,
        f"Answer: {puzzle.answer}",
        box=(62, 142, width - 62, 222),
        max_font_size=66,
        min_font_size=30,
        align="left",
        valign="center",
        fill=COLORS["accent_orange"],
    )

    explain_box = (40, 278, width - 40, height - 224)
    _draw_panel(draw, explain_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=28)
    _draw_equation_items(draw, puzzle.explanation, box=(58, 306, width - 58, height - 250))

    tail_box = (40, height - 194, width - 40, height - 64)
    _draw_panel(draw, tail_box, fill=COLORS["panel"], outline=(72, 126, 162), radius=24)
    _draw_wrapped_block(
        draw,
        "Fast solve? Next one gets harder.",
        box=(62, height - 172, width - 62, height - 84),
        max_font_size=34,
        min_font_size=20,
        valign="center",
        fill=COLORS["text_muted"],
    )


def _draw_scene_cta(draw: ImageDraw.ImageDraw, puzzle: Puzzle, width: int, height: int) -> None:
    _draw_category_badge(draw, puzzle, width)

    main_box = (40, 170, width - 40, 620)
    _draw_panel(draw, main_box, fill=COLORS["panel"], outline=COLORS["panel_border"], radius=32)

    _draw_wrapped_block(
        draw,
        "Advanced Brain Teaser Series",
        box=(62, 210, width - 62, 320),
        max_font_size=58,
        min_font_size=28,
        align="left",
        valign="center",
    )

    _draw_wrapped_block(
        draw,
        "Follow for daily intelligence puzzles with instant solution reveal and stronger logic rounds.",
        box=(62, 340, width - 62, 548),
        max_font_size=36,
        min_font_size=20,
        line_spacing=7,
        align="left",
        valign="top",
        fill=COLORS["text_muted"],
    )

    source_text = "Original challenge"
    if puzzle.source_url:
        source_text = "Inspired by trusted puzzle sources"
    _draw_wrapped_block(
        draw,
        source_text,
        box=(62, 560, width - 62, 604),
        max_font_size=26,
        min_font_size=16,
        align="left",
        valign="center",
        fill=COLORS["accent_cyan"],
    )

    cta_box = (40, height - 220, width - 40, height - 70)
    _draw_panel(draw, cta_box, fill=COLORS["panel"], outline=COLORS["accent_orange"], radius=26)
    _draw_wrapped_block(
        draw,
        "Comment your score and tag a friend for the next round.",
        box=(62, height - 194, width - 62, height - 90),
        max_font_size=34,
        min_font_size=20,
        align="left",
        valign="center",
        fill=COLORS["text_primary"],
    )


def render_frames(puzzle: Puzzle, config: PipelineConfig, frames_dir: Path) -> int:
    ensure_dir(frames_dir)

    total_duration = 28.0
    total_frames = int(total_duration * config.fps)
    base = _build_base_canvas(config.width, config.height)

    for frame_idx in range(total_frames):
        t = frame_idx / config.fps
        img = base.copy()
        draw = ImageDraw.Draw(img)

        _draw_dynamic_accents(draw, config.width, config.height, t)

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
