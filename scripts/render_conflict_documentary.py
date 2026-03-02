#!/usr/bin/env python3
"""
Render a 2-minute documentary-style map timeline video.

Main env vars:
- DOC_VISUAL_OUTPUT (default: outputs/final/conflict_documentary_visual.mp4)
- DOC_WIDTH / DOC_HEIGHT / DOC_FPS / DOC_SECONDS
- DOC_MAP_BRIGHTNESS (default: 1.0)
- DOC_TEXT_ALPHA_SCALE (default: 1.0)
- DOC_ROUTE_GLOW_SCALE (default: 1.0)
- DOC_ROUTE_CORE_SCALE (default: 1.0)
- DOC_ROUTE_DENSITY_SCALE (default: 1.0)
- DOC_MISSILE_DENSITY_SCALE / DOC_IMPACT_RING_SCALE / DOC_TARGET_CIRCLE_SCALE
- DOC_SHAKE_SCALE / DOC_BOMBER_COUNT_SCALE
- DOC_SMOKE_ALPHA_SCALE / DOC_EXPLOSION_ALPHA_SCALE / DOC_GRAIN_ALPHA
- DOC_RENDER_CRF (default: 20)
- DOC_RENDER_PRESET (default: medium)
"""

from __future__ import annotations

import json
import math
import os
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


WIDTH = env_int("DOC_WIDTH", 1920, 640, 3840)
HEIGHT = env_int("DOC_HEIGHT", 1080, 360, 2160)
FPS = env_int("DOC_FPS", 24, 12, 60)
TOTAL_SECONDS = env_int("DOC_SECONDS", 120, 30, 300)
TOTAL_FRAMES = FPS * TOTAL_SECONDS

MAP_BRIGHTNESS = env_float("DOC_MAP_BRIGHTNESS", 1.0, 0.75, 1.35)
TEXT_ALPHA_SCALE = env_float("DOC_TEXT_ALPHA_SCALE", 1.0, 0.70, 1.40)
ROUTE_GLOW_SCALE = env_float("DOC_ROUTE_GLOW_SCALE", 1.0, 0.60, 1.60)
ROUTE_CORE_SCALE = env_float("DOC_ROUTE_CORE_SCALE", 1.0, 0.60, 1.60)
ROUTE_DENSITY_SCALE = env_float("DOC_ROUTE_DENSITY_SCALE", 1.0, 0.70, 1.80)
MISSILE_DENSITY_SCALE = env_float("DOC_MISSILE_DENSITY_SCALE", 1.0, 0.70, 2.40)
IMPACT_RING_SCALE = env_float("DOC_IMPACT_RING_SCALE", 1.0, 0.60, 2.40)
TARGET_CIRCLE_SCALE = env_float("DOC_TARGET_CIRCLE_SCALE", 1.0, 0.70, 1.90)
SHAKE_SCALE = env_float("DOC_SHAKE_SCALE", 1.0, 0.00, 2.30)
BOMBER_COUNT_SCALE = env_float("DOC_BOMBER_COUNT_SCALE", 1.0, 0.00, 2.50)
SMOKE_ALPHA_SCALE = env_float("DOC_SMOKE_ALPHA_SCALE", 1.0, 0.50, 2.20)
EXPLOSION_ALPHA_SCALE = env_float("DOC_EXPLOSION_ALPHA_SCALE", 1.0, 0.60, 2.20)
GRAIN_ALPHA = env_int("DOC_GRAIN_ALPHA", 28, 0, 95)
VIGNETTE_ALPHA = env_int("DOC_VIGNETTE_ALPHA", 120, 40, 220)
RENDER_CRF = env_int("DOC_RENDER_CRF", 20, 16, 28)
RENDER_PRESET = env_str("DOC_RENDER_PRESET", "medium")
RANDOM_SEED = env_int("DOC_RANDOM_SEED", 1234, 1, 9999999)
WATERMARK = env_str("DOC_WATERMARK", "Documentary Simulation | Scripted Timeline Visualization")

BASE_MAP_W = 4096
BASE_MAP_H = 2048
OUTPUT_PATH = Path(env_str("DOC_VISUAL_OUTPUT", "outputs/final/conflict_documentary_visual.mp4")).resolve()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

WORLD_GEOJSON_CANDIDATES = [
    Path("data/world.geojson"),
    Path("outputs/test/_render_tmp/cache/world.geojson"),
]

LOCATIONS: Dict[str, Tuple[float, float]] = {
    "Tehran": (35.6892, 51.3890),
    "Nevatim Air Base": (31.2080, 35.0130),
    "Ramon Air Base": (30.7780, 34.6670),
    "Tel Nof Air Base": (31.8390, 34.8210),
    "Dimona": (31.0690, 35.0330),
    "Tel Aviv": (32.0853, 34.7818),
    "Negev": (30.9000, 34.9000),
    "Mediterranean Zone": (33.4000, 31.5000),
    "Jordan Corridor": (31.2000, 36.2000),
}


@dataclass(frozen=True)
class RouteSpec:
    source: str
    target: str
    count_hint: int
    color: Tuple[int, int, int]
    spread: float = 0.35


@dataclass(frozen=True)
class ImpactSpec:
    hotspot: str
    start_progress: float
    strength: float


@dataclass(frozen=True)
class BomberPass:
    start_progress: float
    duration: float
    y_norm: float
    direction: int
    size: float
    trail_alpha: float


@dataclass(frozen=True)
class Scene:
    name: str
    date_label: str
    operation_label: str
    start_s: int
    end_s: int
    focus_start: Tuple[float, float, float, float]
    focus_end: Tuple[float, float, float, float]
    narration: str
    routes: Tuple[RouteSpec, ...]
    hotspots: Tuple[str, ...]

    @property
    def duration_s(self) -> int:
        return self.end_s - self.start_s


SCENES: List[Scene] = [
    Scene(
        name="Scene 1",
        date_label="April 2024",
        operation_label="Operation True Promise One",
        start_s=0,
        end_s=20,
        focus_start=(8.0, 8.0, 72.0, 48.0),
        focus_end=(16.0, 12.0, 64.0, 44.0),
        narration="In April 2024, Operation True Promise One began with over 300 missiles and drones, marking an unprecedented escalation.",
        routes=(
            RouteSpec("Tehran", "Nevatim Air Base", 120, (255, 186, 92)),
            RouteSpec("Tehran", "Ramon Air Base", 90, (255, 133, 102)),
            RouteSpec("Tehran", "Tel Aviv", 60, (255, 220, 130)),
        ),
        hotspots=("Tehran", "Nevatim Air Base", "Ramon Air Base", "Tel Aviv"),
    ),
    Scene(
        name="Scene 2",
        date_label="April 2024",
        operation_label="Strike Routes: Tehran to Negev",
        start_s=20,
        end_s=40,
        focus_start=(25.0, 19.0, 58.0, 40.0),
        focus_end=(30.0, 23.0, 53.0, 37.5),
        narration="Projectiles moved from Tehran toward Nevatim and Ramon in the Negev, challenging long-held assumptions of deterrence.",
        routes=(
            RouteSpec("Tehran", "Nevatim Air Base", 120, (255, 201, 116)),
            RouteSpec("Tehran", "Ramon Air Base", 90, (255, 124, 97)),
        ),
        hotspots=("Tehran", "Negev", "Nevatim Air Base", "Ramon Air Base"),
    ),
    Scene(
        name="Scene 3",
        date_label="October 2024",
        operation_label="Operation True Promise Two",
        start_s=40,
        end_s=60,
        focus_start=(25.0, 20.0, 58.0, 39.5),
        focus_end=(31.0, 23.5, 52.0, 36.8),
        narration="Months later, a new wave of approximately 180 ballistic missiles targeted Nevatim and Tel Nof in another high-intensity barrage.",
        routes=(
            RouteSpec("Tehran", "Nevatim Air Base", 100, (255, 194, 104)),
            RouteSpec("Tehran", "Tel Nof Air Base", 80, (255, 101, 86)),
        ),
        hotspots=("Tehran", "Nevatim Air Base", "Tel Nof Air Base"),
    ),
    Scene(
        name="Scene 4",
        date_label="June 2025",
        operation_label="Operation True Promise Three",
        start_s=60,
        end_s=80,
        focus_start=(28.0, 24.0, 53.0, 37.5),
        focus_end=(31.5, 28.5, 40.0, 34.2),
        narration="June 2025 saw intense missile exchanges with strategic focus near Dimona and Tel Aviv during the twelve-day war.",
        routes=(
            RouteSpec("Tehran", "Dimona", 90, (255, 165, 83)),
            RouteSpec("Tehran", "Tel Aviv", 90, (255, 88, 82)),
        ),
        hotspots=("Tehran", "Dimona", "Tel Aviv"),
    ),
    Scene(
        name="Scene 5",
        date_label="Feb-Mar 2026",
        operation_label="Regional Counter-Effort",
        start_s=80,
        end_s=100,
        focus_start=(18.0, 8.0, 66.0, 44.0),
        focus_end=(20.0, 10.0, 62.0, 42.0),
        narration="In early 2026, retaliatory planning expanded regional risk zones, widening the uncertainty across the Middle East.",
        routes=(
            RouteSpec("Tehran", "Jordan Corridor", 70, (255, 171, 97)),
            RouteSpec("Tehran", "Mediterranean Zone", 70, (255, 112, 96)),
            RouteSpec("Tehran", "Tel Aviv", 50, (255, 204, 108)),
        ),
        hotspots=("Tehran", "Jordan Corridor", "Mediterranean Zone", "Tel Aviv"),
    ),
    Scene(
        name="Scene 6",
        date_label="Ongoing",
        operation_label="Escalation and Uncertainty",
        start_s=100,
        end_s=120,
        focus_start=(15.0, 8.0, 66.0, 44.0),
        focus_end=(12.0, 6.5, 70.0, 46.0),
        narration="As trajectories persist across the map, the region remains in flux and the long-term consequences are still unfolding.",
        routes=(
            RouteSpec("Tehran", "Nevatim Air Base", 60, (255, 180, 102)),
            RouteSpec("Tehran", "Ramon Air Base", 60, (255, 130, 102)),
            RouteSpec("Tehran", "Tel Nof Air Base", 60, (255, 98, 88)),
            RouteSpec("Tehran", "Dimona", 60, (255, 200, 118)),
            RouteSpec("Tehran", "Tel Aviv", 60, (255, 142, 94)),
        ),
        hotspots=("Tehran", "Nevatim Air Base", "Ramon Air Base", "Tel Nof Air Base", "Dimona", "Tel Aviv"),
    ),
]

SCENE_IMPACTS: Dict[str, Tuple[ImpactSpec, ...]] = {
    "Scene 1": (
        ImpactSpec("Nevatim Air Base", 0.44, 1.00),
        ImpactSpec("Ramon Air Base", 0.62, 1.05),
        ImpactSpec("Tel Aviv", 0.81, 0.82),
    ),
    "Scene 2": (
        ImpactSpec("Nevatim Air Base", 0.40, 0.92),
        ImpactSpec("Negev", 0.58, 0.75),
        ImpactSpec("Ramon Air Base", 0.74, 1.10),
    ),
    "Scene 3": (
        ImpactSpec("Nevatim Air Base", 0.36, 1.00),
        ImpactSpec("Tel Nof Air Base", 0.57, 1.20),
        ImpactSpec("Nevatim Air Base", 0.83, 0.84),
    ),
    "Scene 4": (
        ImpactSpec("Dimona", 0.33, 1.08),
        ImpactSpec("Tel Aviv", 0.52, 1.18),
        ImpactSpec("Tel Aviv", 0.73, 0.92),
    ),
    "Scene 5": (
        ImpactSpec("Jordan Corridor", 0.34, 0.84),
        ImpactSpec("Mediterranean Zone", 0.56, 0.95),
        ImpactSpec("Tel Aviv", 0.78, 1.02),
    ),
    "Scene 6": (
        ImpactSpec("Nevatim Air Base", 0.28, 0.85),
        ImpactSpec("Ramon Air Base", 0.42, 0.82),
        ImpactSpec("Tel Nof Air Base", 0.56, 0.94),
        ImpactSpec("Dimona", 0.70, 0.93),
        ImpactSpec("Tel Aviv", 0.84, 1.03),
    ),
}


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def clamp_int(value: int, low: int, high: int) -> int:
    if value < low:
        return low
    if value > high:
        return high
    return value


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_bbox(
    start_bbox: Tuple[float, float, float, float],
    end_bbox: Tuple[float, float, float, float],
    t: float,
) -> Tuple[float, float, float, float]:
    return (
        lerp(start_bbox[0], end_bbox[0], t),
        lerp(start_bbox[1], end_bbox[1], t),
        lerp(start_bbox[2], end_bbox[2], t),
        lerp(start_bbox[3], end_bbox[3], t),
    )


def scale_channel(value: int, factor: float) -> int:
    return int(clamp(value * factor, 0, 255))


def scale_rgb(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return (
        scale_channel(color[0], factor),
        scale_channel(color[1], factor),
        scale_channel(color[2], factor),
    )


def world_xy_from_lonlat(lon: float, lat: float, width: int, height: int) -> Tuple[float, float]:
    x = ((lon + 180.0) / 360.0) * width
    y = ((90.0 - lat) / 180.0) * height
    return x, y


def lonlat_to_frame_xy(lon: float, lat: float, bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    lon_min, lat_min, lon_max, lat_max = bbox
    span_lon = max(0.0001, lon_max - lon_min)
    span_lat = max(0.0001, lat_max - lat_min)
    x = ((lon - lon_min) / span_lon) * WIDTH
    y = ((lat_max - lat) / span_lat) * HEIGHT
    return x, y


def load_geojson() -> Optional[dict]:
    for candidate in WORLD_GEOJSON_CANDIDATES:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def iter_rings(geojson: dict) -> Iterable[Sequence[Sequence[float]]]:
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry", {})
        gtype = geometry.get("type")
        coords = geometry.get("coordinates", [])
        if gtype == "Polygon":
            for ring in coords:
                yield ring
        elif gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    yield ring


def build_base_map() -> Image.Image:
    image = Image.new("RGBA", (BASE_MAP_W, BASE_MAP_H), (5, 11, 20, 255))
    draw = ImageDraw.Draw(image)

    top = scale_rgb((6, 12, 20), MAP_BRIGHTNESS)
    bottom = scale_rgb((12, 25, 41), MAP_BRIGHTNESS)
    for y in range(BASE_MAP_H):
        ratio = y / max(1, BASE_MAP_H - 1)
        color = (
            int(top[0] + (bottom[0] - top[0]) * ratio),
            int(top[1] + (bottom[1] - top[1]) * ratio),
            int(top[2] + (bottom[2] - top[2]) * ratio),
            255,
        )
        draw.line([(0, y), (BASE_MAP_W, y)], fill=color)

    grid_a = scale_rgb((28, 58, 86), MAP_BRIGHTNESS)
    grid_b = scale_rgb((40, 76, 107), MAP_BRIGHTNESS)
    for lon in range(-180, 181, 15):
        x, _ = world_xy_from_lonlat(float(lon), 0.0, BASE_MAP_W, BASE_MAP_H)
        line_color = grid_a + (130,) if lon % 30 else grid_b + (170,)
        draw.line([(x, 0), (x, BASE_MAP_H)], fill=line_color, width=1)
    for lat in range(-90, 91, 15):
        _, y = world_xy_from_lonlat(0.0, float(lat), BASE_MAP_W, BASE_MAP_H)
        line_color = grid_a + (130,) if lat % 30 else grid_b + (170,)
        draw.line([(0, y), (BASE_MAP_W, y)], fill=line_color, width=1)

    geojson = load_geojson()
    if geojson:
        fill = scale_rgb((21, 70, 102), MAP_BRIGHTNESS) + (230,)
        outline = scale_rgb((86, 150, 191), MAP_BRIGHTNESS) + (190,)
        for ring in iter_rings(geojson):
            if len(ring) < 3:
                continue
            points = [world_xy_from_lonlat(float(lon), float(lat), BASE_MAP_W, BASE_MAP_H) for lon, lat in ring]
            draw.polygon(points, fill=fill, outline=outline)

    random.seed(RANDOM_SEED)
    for _ in range(1700):
        x = random.randint(0, BASE_MAP_W - 1)
        y = random.randint(0, BASE_MAP_H - 1)
        brightness = random.randint(120, 210)
        brightness = scale_channel(brightness, MAP_BRIGHTNESS)
        blue = scale_channel(min(255, brightness + 20), MAP_BRIGHTNESS)
        image.putpixel((x, y), (brightness, brightness, blue, 255))

    image = image.filter(ImageFilter.GaussianBlur(radius=0.45))
    return image


def crop_world_to_frame(
    world_map: Image.Image,
    bbox: Tuple[float, float, float, float],
    impact_energy: float,
    seconds: float,
) -> Image.Image:
    lon_min, lat_min, lon_max, lat_max = bbox
    wx, wy = world_map.size
    x1 = int(clamp((lon_min + 180.0) / 360.0 * wx, 0, wx - 1))
    x2 = int(clamp((lon_max + 180.0) / 360.0 * wx, x1 + 1, wx))
    y1 = int(clamp((90.0 - lat_max) / 180.0 * wy, 0, wy - 1))
    y2 = int(clamp((90.0 - lat_min) / 180.0 * wy, y1 + 1, wy))
    crop = world_map.crop((x1, y1, x2, y2))

    overscan = max(16, int(28 * SHAKE_SCALE))
    enlarged = crop.resize((WIDTH + (overscan * 2), HEIGHT + (overscan * 2)), Image.Resampling.LANCZOS)
    shake_px = int(clamp(impact_energy * 4.6 * SHAKE_SCALE, 0.0, float(max(1, overscan - 2))))
    if shake_px <= 0:
        return enlarged.crop((overscan, overscan, overscan + WIDTH, overscan + HEIGHT))

    dx = int((math.sin(seconds * 23.1) * 0.7 + math.sin(seconds * 57.9) * 0.3) * shake_px)
    dy = int((math.cos(seconds * 19.7) * 0.6 + math.sin(seconds * 43.3) * 0.4) * shake_px)
    left = clamp_int(overscan + dx, 0, overscan * 2)
    top = clamp_int(overscan + dy, 0, overscan * 2)
    return enlarged.crop((left, top, left + WIDTH, top + HEIGHT))


def best_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        length = font.getlength(trial) if hasattr(font, "getlength") else len(trial) * 10
        if length <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def add_vignette(frame: Image.Image) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    margin = 120
    for i in range(220):
        alpha = int(255 * (i / 220.0) ** 2)
        draw.rectangle(
            [margin - i, margin - i, WIDTH - margin + i, HEIGHT - margin + i],
            outline=alpha,
            width=1,
        )
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, VIGNETTE_ALPHA))
    frame = frame.copy()
    frame.paste(dark, (0, 0), ImageOps.invert(mask))
    return frame


def quad_bezier(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    t: float,
) -> Tuple[float, float]:
    omt = 1.0 - t
    x = omt * omt * p0[0] + 2.0 * omt * t * p1[0] + t * t * p2[0]
    y = omt * omt * p0[1] + 2.0 * omt * t * p1[1] + t * t * p2[1]
    return x, y


def build_arc_points(
    p0: Tuple[float, float],
    p2: Tuple[float, float],
    samples: int = 76,
    arc_factor: float = 0.18,
) -> List[Tuple[float, float]]:
    mx = (p0[0] + p2[0]) * 0.5
    my = (p0[1] + p2[1]) * 0.5
    dx = p2[0] - p0[0]
    dy = p2[1] - p0[1]
    dist = max(1.0, math.hypot(dx, dy))
    nx = -dy / dist
    ny = dx / dist
    p1 = (mx + nx * dist * arc_factor, my + ny * dist * arc_factor)
    return [quad_bezier(p0, p1, p2, idx / (samples - 1)) for idx in range(samples)]


@dataclass(frozen=True)
class RouteInstance:
    source_lat: float
    source_lon: float
    target_lat: float
    target_lon: float
    color: Tuple[int, int, int]
    delay: float
    speed_mul: float


def build_route_instances(scene: Scene, scene_idx: int) -> List[RouteInstance]:
    instances: List[RouteInstance] = []
    rng = random.Random(1000 + scene_idx * 97)
    for spec in scene.routes:
        s_lat, s_lon = LOCATIONS[spec.source]
        t_lat, t_lon = LOCATIONS[spec.target]
        line_count = int(clamp((spec.count_hint / 8.0) * ROUTE_DENSITY_SCALE * MISSILE_DENSITY_SCALE, 10, 92))
        for i in range(line_count):
            jitter_s_lat = s_lat + rng.uniform(-spec.spread, spec.spread) * 0.55
            jitter_s_lon = s_lon + rng.uniform(-spec.spread, spec.spread)
            jitter_t_lat = t_lat + rng.uniform(-spec.spread, spec.spread) * 0.5
            jitter_t_lon = t_lon + rng.uniform(-spec.spread, spec.spread)
            delay = (i / max(1, line_count - 1)) * 0.66
            speed_mul = rng.uniform(0.90, 1.12)
            instances.append(
                RouteInstance(
                    source_lat=jitter_s_lat,
                    source_lon=jitter_s_lon,
                    target_lat=jitter_t_lat,
                    target_lon=jitter_t_lon,
                    color=spec.color,
                    delay=delay,
                    speed_mul=speed_mul,
                )
            )
    return instances


def locate_scene(seconds: float) -> Tuple[Scene, int]:
    for idx, scene in enumerate(SCENES):
        if scene.start_s <= seconds < scene.end_s:
            return scene, idx
    return SCENES[-1], len(SCENES) - 1


def scene_impacts(scene: Scene) -> Tuple[ImpactSpec, ...]:
    return SCENE_IMPACTS.get(scene.name, tuple())


def impact_energy(scene: Scene, scene_progress: float) -> float:
    total = 0.0
    for impact in scene_impacts(scene):
        dt = scene_progress - impact.start_progress
        if dt < -0.08 or dt > 0.30:
            continue
        if dt < 0:
            e = 1.0 - abs(dt) / 0.08
        else:
            e = max(0.0, 1.0 - dt / 0.30)
        total += e * impact.strength
    return total


def build_bomber_passes(scene_idx: int) -> List[BomberPass]:
    rng = random.Random(7000 + scene_idx * 133)
    count = int(clamp(round((2.1 + (scene_idx % 2) * 0.8) * BOMBER_COUNT_SCALE), 0, 6))
    passes: List[BomberPass] = []
    for _ in range(count):
        passes.append(
            BomberPass(
                start_progress=rng.uniform(0.05, 0.72),
                duration=rng.uniform(0.26, 0.44),
                y_norm=rng.uniform(0.20, 0.50),
                direction=1 if rng.random() > 0.5 else -1,
                size=rng.uniform(0.84, 1.25),
                trail_alpha=rng.uniform(0.45, 0.80),
            )
        )
    return passes


def draw_bomber_passes(
    draw: ImageDraw.ImageDraw,
    bombers: Sequence[BomberPass],
    scene_progress: float,
    seconds: float,
) -> None:
    for bomber in bombers:
        local = (scene_progress - bomber.start_progress) / max(0.001, bomber.duration)
        if local < 0.0 or local > 1.0:
            continue

        if bomber.direction > 0:
            x = lerp(-160.0, WIDTH + 160.0, local)
            angle = -0.10
        else:
            x = lerp(WIDTH + 160.0, -160.0, local)
            angle = math.pi + 0.10
        y = HEIGHT * bomber.y_norm + math.sin((seconds + local * 2.5) * 2.1) * 14.0

        size = 22.0 * bomber.size
        points = [
            (-2.0 * size, 0.0),
            (-1.30 * size, -0.35 * size),
            (-0.45 * size, -0.25 * size),
            (0.50 * size, -0.08 * size),
            (1.90 * size, 0.00),
            (0.50 * size, 0.08 * size),
            (-0.45 * size, 0.25 * size),
            (-1.30 * size, 0.35 * size),
        ]

        cs = math.cos(angle)
        sn = math.sin(angle)
        rotated = [(x + px * cs - py * sn, y + px * sn + py * cs) for px, py in points]
        draw.polygon(rotated, fill=(20, 20, 24, 232))
        draw.line(
            [
                (x - math.cos(angle) * size * 2.6, y - math.sin(angle) * size * 2.6),
                (x - math.cos(angle) * size * 5.8, y - math.sin(angle) * size * 5.8),
            ],
            fill=(180, 186, 198, int(90 * bomber.trail_alpha)),
            width=max(1, int(size * 0.08)),
        )


def draw_impact_effects(
    draw: ImageDraw.ImageDraw,
    scene: Scene,
    bbox: Tuple[float, float, float, float],
    scene_progress: float,
    seconds: float,
) -> float:
    energy_sum = 0.0
    for impact in scene_impacts(scene):
        lat, lon = LOCATIONS[impact.hotspot]
        x, y = lonlat_to_frame_xy(lon, lat, bbox)
        if x < -180 or x > WIDTH + 180 or y < -180 or y > HEIGHT + 180:
            continue

        dt = scene_progress - impact.start_progress
        if dt < -0.06 or dt > 0.32:
            continue

        if dt < 0:
            local_energy = max(0.0, 1.0 - (abs(dt) / 0.06))
        else:
            local_energy = max(0.0, 1.0 - (dt / 0.32))
        local_energy *= impact.strength
        energy_sum += local_energy

        if dt < 0:
            continue

        ring_base = (10.0 + dt * 340.0 * impact.strength) * IMPACT_RING_SCALE
        for idx in range(3):
            rr = ring_base * (1.0 + idx * 0.32)
            alpha = int(clamp((1.0 - dt / 0.32) * (215 - idx * 56) * EXPLOSION_ALPHA_SCALE, 0, 255))
            width = max(1, int(4 - idx))
            draw.ellipse([(x - rr, y - rr), (x + rr, y + rr)], outline=(255, 52, 52, alpha), width=width)

        fire_r = (22.0 - dt * 52.0) * impact.strength * IMPACT_RING_SCALE
        if fire_r > 1:
            draw.ellipse(
                [(x - fire_r, y - fire_r), (x + fire_r, y + fire_r)],
                fill=(255, 162, 74, int(clamp(166 * (1.0 - dt / 0.32) * EXPLOSION_ALPHA_SCALE, 0, 255))),
            )
            inner = fire_r * 0.50
            draw.ellipse(
                [(x - inner, y - inner), (x + inner, y + inner)],
                fill=(255, 235, 196, int(clamp(186 * (1.0 - dt / 0.32), 0, 255))),
            )

        spark_progress = dt / 0.32
        for k in range(12):
            ang = ((k * 137 + int(seconds * 120)) % 360) * (math.pi / 180.0)
            dist = (16.0 + spark_progress * 160.0) * (0.7 + 0.04 * (k % 5))
            sx = x + math.cos(ang) * dist
            sy = y + math.sin(ang) * dist
            spark_a = int(clamp((1.0 - spark_progress) * 225, 0, 255))
            spark_r = max(1.0, 2.4 - spark_progress * 1.4)
            draw.ellipse([(sx - spark_r, sy - spark_r), (sx + spark_r, sy + spark_r)], fill=(255, 205, 126, spark_a))

    return energy_sum


def build_smoke_textures() -> List[Image.Image]:
    textures: List[Image.Image] = []
    rng = random.Random(9000 + RANDOM_SEED)
    base_colors = [(58, 68, 86), (74, 84, 101)]
    for idx, color in enumerate(base_colors):
        tex = Image.new("L", (WIDTH * 2, HEIGHT * 2), 0)
        draw = ImageDraw.Draw(tex)
        for _ in range(260):
            cx = rng.randint(-120, tex.width + 120)
            cy = rng.randint(-120, tex.height + 120)
            rx = rng.randint(80, 260)
            ry = int(rx * rng.uniform(0.45, 1.08))
            alpha = rng.randint(8, 32)
            draw.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)], fill=alpha)
        tex = tex.filter(ImageFilter.GaussianBlur(radius=26 + idx * 10))
        rgba = Image.new("RGBA", tex.size, color + (0,))
        rgba.putalpha(tex.point(lambda p: int(clamp(p * SMOKE_ALPHA_SCALE, 0, 255))))
        textures.append(rgba)
    return textures


def apply_smoke_overlay(frame: Image.Image, textures: Sequence[Image.Image], seconds: float) -> None:
    for idx, tex in enumerate(textures):
        max_x = max(1, tex.width - WIDTH)
        max_y = max(1, tex.height - HEIGHT)
        x = int((seconds * (12.0 + idx * 6.0)) % max_x)
        y = int((seconds * (7.0 + idx * 4.0)) % max_y)
        patch = tex.crop((x, y, x + WIDTH, y + HEIGHT))
        frame.alpha_composite(patch)


def build_grain_frames() -> List[Image.Image]:
    if GRAIN_ALPHA <= 0:
        return []
    frames: List[Image.Image] = []
    for idx in range(6):
        sigma = 30 + idx * 3
        noise = Image.effect_noise((WIDTH, HEIGHT), sigma).convert("L")
        alpha = noise.point(lambda p: int(clamp(((p - 96) / 159.0) * GRAIN_ALPHA, 0, 255)))
        grain = Image.new("RGBA", (WIDTH, HEIGHT), (232, 232, 238, 0))
        grain.putalpha(alpha)
        frames.append(grain)
    return frames


def draw_hotspot(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[float, float, float, float],
    name: str,
    pulse: float,
    font: ImageFont.ImageFont,
) -> None:
    lat, lon = LOCATIONS[name]
    x, y = lonlat_to_frame_xy(lon, lat, bbox)
    if x < -120 or x > WIDTH + 120 or y < -120 or y > HEIGHT + 120:
        return

    is_source = name == "Tehran"
    ring_color = (255, 198, 112, 210) if is_source else (255, 74, 74, 225)
    core_color = (247, 240, 228, 255) if is_source else (255, 220, 220, 245)
    pulse_r = int((8 if is_source else 10) + (8 + (4 if is_source else 7)) * (0.5 + 0.5 * math.sin(pulse * 2.0 * math.pi)))
    pulse_r = int(clamp(pulse_r * TARGET_CIRCLE_SCALE, 6, 38))
    width = int(clamp(2.0 * TARGET_CIRCLE_SCALE, 1, 4))
    draw.ellipse([(x - pulse_r, y - pulse_r), (x + pulse_r, y + pulse_r)], outline=ring_color, width=width)
    draw.ellipse([(x - 4, y - 4), (x + 4, y + 4)], fill=core_color)
    tx = clamp(x + 10, 20, WIDTH - 260)
    ty = clamp(y - 26, 20, HEIGHT - 40)
    draw.text((tx, ty), name, fill=(236, 245, 255, 240), font=font, stroke_width=1, stroke_fill=(0, 0, 0, 180))


def draw_scene_text(
    draw: ImageDraw.ImageDraw,
    scene: Scene,
    scene_progress: float,
    font_title: ImageFont.ImageFont,
    font_sub: ImageFont.ImageFont,
    font_body: ImageFont.ImageFont,
) -> None:
    fade_in = clamp(scene_progress / 0.12, 0.0, 1.0)
    fade_out = clamp((1.0 - scene_progress) / 0.16, 0.0, 1.0)
    alpha = int(255 * min(fade_in, fade_out) * TEXT_ALPHA_SCALE)
    alpha = int(clamp(alpha, 0, 255))

    top_box = (24, 24, WIDTH - 24, 156)
    draw.rounded_rectangle(
        top_box,
        radius=16,
        fill=(0, 0, 0, int(120 * (alpha / 255.0))),
        outline=(90, 145, 186, alpha),
        width=2,
    )
    draw.text((42, 40), scene.operation_label, fill=(255, 214, 153, alpha), font=font_title)
    draw.text((42, 95), scene.date_label, fill=(216, 232, 247, alpha), font=font_sub)
    draw.text((WIDTH - 248, 95), scene.name, fill=(228, 233, 240, alpha), font=font_sub)

    wrapped = wrap_text(scene.narration, font_body, WIDTH - 180)[:4]
    line_h = 44
    lower_h = 46 + line_h * len(wrapped)
    lower_box = (56, HEIGHT - lower_h - 40, WIDTH - 56, HEIGHT - 26)
    draw.rounded_rectangle(
        lower_box,
        radius=14,
        fill=(0, 0, 0, int(138 * (alpha / 255.0))),
        outline=(82, 132, 171, alpha),
        width=2,
    )
    y = lower_box[1] + 20
    for line in wrapped:
        draw.text((80, y), line, fill=(240, 246, 255, alpha), font=font_body)
        y += line_h


def draw_routes(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[float, float, float, float],
    scene_progress: float,
    route_instances: Sequence[RouteInstance],
) -> None:
    for route in route_instances:
        local_progress = (scene_progress * route.speed_mul - route.delay) / max(0.0001, (1.0 - route.delay))
        local_progress = clamp(local_progress, 0.0, 1.0)
        if local_progress <= 0.0:
            continue

        source_xy = lonlat_to_frame_xy(route.source_lon, route.source_lat, bbox)
        target_xy = lonlat_to_frame_xy(route.target_lon, route.target_lat, bbox)
        if (
            (source_xy[0] < -200 and target_xy[0] < -200)
            or (source_xy[0] > WIDTH + 200 and target_xy[0] > WIDTH + 200)
            or (source_xy[1] < -200 and target_xy[1] < -200)
            or (source_xy[1] > HEIGHT + 200 and target_xy[1] > HEIGHT + 200)
        ):
            continue

        arc = build_arc_points(source_xy, target_xy)
        head_idx = max(1, int(local_progress * (len(arc) - 1)))
        tail_idx = max(0, head_idx - int(12 * ROUTE_CORE_SCALE))
        segment = arc[tail_idx : head_idx + 1]

        glow_alpha = int(clamp(118 * ROUTE_GLOW_SCALE, 45, 250))
        core_alpha = int(clamp(228 * ROUTE_CORE_SCALE, 85, 255))
        glow_width = int(clamp(7 * ROUTE_GLOW_SCALE, 3, 16))
        core_width = int(clamp(3 * ROUTE_CORE_SCALE, 2, 9))
        glow = (route.color[0], route.color[1], route.color[2], glow_alpha)
        core = (route.color[0], route.color[1], route.color[2], core_alpha)
        draw.line(segment, fill=glow, width=glow_width)
        draw.line(segment, fill=core, width=core_width)

        head = segment[-1]
        prev = segment[-2] if len(segment) > 1 else segment[-1]
        dx = head[0] - prev[0]
        dy = head[1] - prev[1]
        mag = max(0.0001, math.hypot(dx, dy))
        ux = dx / mag
        uy = dy / mag
        px = -uy
        py = ux

        body_len = clamp(8.0 * ROUTE_CORE_SCALE, 5.0, 16.0)
        body_w = clamp(2.7 * ROUTE_CORE_SCALE, 1.8, 6.5)
        tip = (head[0] + ux * body_len, head[1] + uy * body_len)
        left = (head[0] - ux * body_len * 0.45 + px * body_w, head[1] - uy * body_len * 0.45 + py * body_w)
        right = (head[0] - ux * body_len * 0.45 - px * body_w, head[1] - uy * body_len * 0.45 - py * body_w)
        draw.polygon([tip, left, right], fill=(255, 240, 210, 246))

        flame_r = clamp(4.2 * ROUTE_GLOW_SCALE, 2.0, 9.0)
        flame = (head[0] - ux * body_len * 0.9, head[1] - uy * body_len * 0.9)
        draw.ellipse(
            [(flame[0] - flame_r, flame[1] - flame_r), (flame[0] + flame_r, flame[1] + flame_r)],
            fill=(255, 143, 84, 212),
        )


def append_github_output(path: Path) -> None:
    github_output = os.getenv("GITHUB_OUTPUT", "").strip()
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        handle.write(f"visual_output={path.as_posix()}\n")


def render_video() -> None:
    world_map = build_base_map()
    route_cache: Dict[int, List[RouteInstance]] = {
        idx: build_route_instances(scene, idx) for idx, scene in enumerate(SCENES)
    }
    bomber_cache: Dict[int, List[BomberPass]] = {idx: build_bomber_passes(idx) for idx in range(len(SCENES))}
    smoke_textures = build_smoke_textures()
    grain_frames = build_grain_frames()

    font_title = best_font(52)
    font_sub = best_font(34)
    font_body = best_font(36)
    font_loc = best_font(24)
    font_watermark = best_font(22)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        RENDER_PRESET,
        "-crf",
        str(RENDER_CRF),
        "-pix_fmt",
        "yuv420p",
        str(OUTPUT_PATH),
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert process.stdin is not None

    for frame_idx in range(TOTAL_FRAMES):
        seconds = frame_idx / FPS
        scene, scene_idx = locate_scene(seconds)
        scene_progress = clamp((seconds - scene.start_s) / max(1e-6, scene.duration_s), 0.0, 1.0)
        bbox = lerp_bbox(scene.focus_start, scene.focus_end, smoothstep(scene_progress))

        pre_energy = impact_energy(scene, scene_progress)
        frame = crop_world_to_frame(world_map, bbox, pre_energy, seconds).convert("RGBA")
        frame = add_vignette(frame)
        draw = ImageDraw.Draw(frame, "RGBA")

        draw_routes(draw, bbox, scene_progress, route_cache[scene_idx])
        draw_bomber_passes(draw, bomber_cache[scene_idx], scene_progress, seconds)
        pulse = (seconds * 0.9) % 1.0
        for hotspot in scene.hotspots:
            draw_hotspot(draw, bbox, hotspot, pulse, font_loc)

        impact_drawn_energy = draw_impact_effects(draw, scene, bbox, scene_progress, seconds)
        if impact_drawn_energy > 1.15:
            alpha = int(clamp(impact_drawn_energy * 22.0 * EXPLOSION_ALPHA_SCALE, 0, 84))
            frame.alpha_composite(Image.new("RGBA", (WIDTH, HEIGHT), (255, 92, 62, alpha)))

        apply_smoke_overlay(frame, smoke_textures, seconds)
        if grain_frames:
            frame.alpha_composite(grain_frames[frame_idx % len(grain_frames)])

        draw = ImageDraw.Draw(frame, "RGBA")
        draw_scene_text(draw, scene, scene_progress, font_title, font_sub, font_body)

        draw.rectangle([(0, HEIGHT - 38), (WIDTH, HEIGHT)], fill=(0, 0, 0, 140))
        draw.text((22, HEIGHT - 31), WATERMARK, fill=(210, 227, 242, 220), font=font_watermark)

        process.stdin.write(frame.convert("RGB").tobytes())
        if frame_idx % (FPS * 10) == 0:
            print(f"[render] frame {frame_idx}/{TOTAL_FRAMES}")

    process.stdin.close()
    result = process.wait()
    if result != 0:
        raise RuntimeError(f"ffmpeg encode failed with code {result}")
    append_github_output(OUTPUT_PATH)
    print(f"[ok] visual video created: {OUTPUT_PATH}")


if __name__ == "__main__":
    render_video()

