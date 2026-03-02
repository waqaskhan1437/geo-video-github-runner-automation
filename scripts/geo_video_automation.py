#!/usr/bin/env python3
"""
Standalone geo-mapping video automation script.

This script:
1. Reads route points (lat/lon) from env JSON or a JSON file.
2. Downloads a lightweight world GeoJSON map (with local cache).
3. Renders animation frames with route progress.
4. Uses ffmpeg to encode MP4 output.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont


DEFAULT_GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
DEFAULT_TITLE = "Geo Mapping Route Animation"
DEFAULT_ATTRIBUTION = "Map: world.geo.json (open-source)"


@dataclass(frozen=True)
class RoutePoint:
    name: str
    lat: float
    lon: float


def env_int(name: str, default: int, min_value: int, max_value: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, min(value, max_value))


def env_float(name: str, default: float, min_value: float, max_value: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        value = default
    return max(min_value, min(value, max_value))


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def sanitize_output_name(name: str) -> str:
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_", ".", " "}).strip()
    if not cleaned:
        cleaned = "geo_mapping_video.mp4"
    if not cleaned.lower().endswith(".mp4"):
        cleaned += ".mp4"
    return cleaned


def _extract_lat_lon(item: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    lat_raw = item.get("lat", item.get("latitude"))
    lon_raw = item.get("lon", item.get("lng", item.get("longitude")))
    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except (TypeError, ValueError):
        return None, None
    return lat, lon


def parse_points_payload(payload: Any) -> List[RoutePoint]:
    if isinstance(payload, dict) and "points" in payload:
        payload = payload["points"]
    if not isinstance(payload, list):
        raise ValueError("Route data must be a list, or an object with `points` list.")
    if len(payload) < 2:
        raise ValueError("At least 2 route points are required.")

    points: List[RoutePoint] = []
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Point at index {idx} is not an object.")
        lat, lon = _extract_lat_lon(item)
        if lat is None or lon is None:
            raise ValueError(f"Point at index {idx} is missing valid lat/lon.")
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError(f"Point at index {idx} has out-of-range lat/lon.")
        name = str(item.get("name") or f"Point {idx + 1}")
        points.append(RoutePoint(name=name, lat=lat, lon=lon))
    return points


def load_route_points() -> List[RoutePoint]:
    points_json = os.getenv("GEO_POINTS_JSON", "").strip()
    points_file = os.getenv("GEO_POINTS_FILE", "data/route_points.sample.json").strip()

    if points_json:
        payload = json.loads(points_json)
        return parse_points_payload(payload)

    file_path = Path(points_file)
    if file_path.exists():
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        return parse_points_payload(payload)

    # Fallback default sample
    fallback = [
        {"name": "Karachi", "lat": 24.8607, "lon": 67.0011},
        {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
        {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784},
        {"name": "London", "lat": 51.5072, "lon": -0.1276},
    ]
    return parse_points_payload(fallback)


def lonlat_to_xy(lon: float, lat: float, width: int, height: int) -> Tuple[float, float]:
    x = ((lon + 180.0) / 360.0) * width
    y = ((90.0 - lat) / 180.0) * height
    return x, y


def build_gradient_background(width: int, height: int) -> Image.Image:
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)
    top = (10, 23, 39, 255)
    bottom = (19, 46, 72, 255)
    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return image


def draw_lat_lon_grid(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    for lon in range(-180, 181, 30):
        x, _ = lonlat_to_xy(float(lon), 0.0, width, height)
        color = (47, 87, 118, 190) if lon != 0 else (85, 130, 168, 230)
        draw.line([(x, 0), (x, height)], fill=color, width=1)
    for lat in range(-90, 91, 30):
        _, y = lonlat_to_xy(0.0, float(lat), width, height)
        color = (47, 87, 118, 190) if lat != 0 else (85, 130, 168, 230)
        draw.line([(0, y), (width, y)], fill=color, width=1)


def maybe_fetch_geojson(cache_path: Path, url: str) -> Optional[Dict[str, Any]]:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache_path.unlink(missing_ok=True)

    if not url:
        return None

    try:
        print(f"[info] downloading world map geojson: {url}")
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        payload = response.json()
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] map download failed: {exc}")
        return None


def iter_rings(geojson: Dict[str, Any]) -> Iterable[Sequence[Sequence[float]]]:
    features = geojson.get("features", [])
    for feature in features:
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


def draw_world_shapes(draw: ImageDraw.ImageDraw, width: int, height: int, geojson: Dict[str, Any]) -> None:
    fill = (23, 70, 102, 220)
    outline = (83, 145, 185, 180)
    for ring in iter_rings(geojson):
        if len(ring) < 3:
            continue
        points = [lonlat_to_xy(float(lon), float(lat), width, height) for lon, lat in ring]
        draw.polygon(points, fill=fill, outline=outline)


def calculate_segment_lengths(points_xy: Sequence[Tuple[float, float]]) -> Tuple[List[float], float]:
    lengths: List[float] = []
    total = 0.0
    for idx in range(len(points_xy) - 1):
        ax, ay = points_xy[idx]
        bx, by = points_xy[idx + 1]
        length = math.hypot(bx - ax, by - ay)
        lengths.append(length)
        total += length
    return lengths, max(total, 1.0)


def partial_route(
    points_xy: Sequence[Tuple[float, float]],
    segment_lengths: Sequence[float],
    total_length: float,
    progress: float,
) -> Tuple[List[Tuple[float, float]], Tuple[float, float]]:
    target = total_length * progress
    traveled = 0.0
    out = [points_xy[0]]
    current = points_xy[0]

    for idx, seg_len in enumerate(segment_lengths):
        start = points_xy[idx]
        end = points_xy[idx + 1]
        if traveled + seg_len <= target:
            out.append(end)
            current = end
            traveled += seg_len
            continue

        remain = target - traveled
        ratio = 0.0 if seg_len == 0 else remain / seg_len
        x = start[0] + (end[0] - start[0]) * ratio
        y = start[1] + (end[1] - start[1]) * ratio
        current = (x, y)
        out.append(current)
        return out, current

    return out, current


def point_label_position(x: float, y: float, width: int, height: int) -> Tuple[float, float]:
    tx = min(max(10.0, x + 10.0), width - 170.0)
    ty = min(max(10.0, y - 14.0), height - 24.0)
    return tx, ty


def write_github_output(output_path: Path) -> None:
    github_output = os.getenv("GITHUB_OUTPUT", "").strip()
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as fh:
        fh.write(f"output_video={output_path.as_posix()}\n")


def ensure_ffmpeg_exists() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg command not found. Install ffmpeg and retry.")


def render_video(
    points: List[RoutePoint],
    output_path: Path,
    width: int,
    height: int,
    fps: int,
    duration_seconds: float,
    title: str,
    attribution: str,
    keep_frames: bool,
    geojson_url: str,
) -> None:
    frame_count = max(2, int(fps * duration_seconds))
    work_root = output_path.parent / "_render_tmp"
    frames_dir = work_root / "frames"
    cache_geojson = work_root / "cache" / "world.geojson"
    frames_dir.mkdir(parents=True, exist_ok=True)

    geojson = maybe_fetch_geojson(cache_geojson, geojson_url)

    base = build_gradient_background(width, height)
    base_draw = ImageDraw.Draw(base)
    draw_lat_lon_grid(base_draw, width, height)
    if geojson:
        draw_world_shapes(base_draw, width, height, geojson)
    else:
        print("[warn] world map layer unavailable, continuing with grid background only.")

    font = ImageFont.load_default()
    base_draw.rectangle([(12, 10), (width - 12, 42)], fill=(0, 0, 0, 120))
    base_draw.text((24, 18), title, fill=(240, 248, 255, 255), font=font)
    base_draw.text((24, height - 24), attribution, fill=(210, 223, 235, 255), font=font)

    points_xy = [lonlat_to_xy(point.lon, point.lat, width, height) for point in points]
    segment_lengths, total_len = calculate_segment_lengths(points_xy)

    for index in range(frame_count):
        progress = index / (frame_count - 1)
        traveled_path, current_pos = partial_route(points_xy, segment_lengths, total_len, progress)

        frame = base.copy()
        draw = ImageDraw.Draw(frame)

        if len(points_xy) >= 2:
            draw.line(points_xy, fill=(255, 255, 255, 90), width=3)
        if len(traveled_path) >= 2:
            draw.line(traveled_path, fill=(255, 196, 73, 255), width=6)

        for idx, point in enumerate(points):
            px, py = points_xy[idx]
            radius = 5
            draw.ellipse(
                [(px - radius, py - radius), (px + radius, py + radius)],
                fill=(10, 38, 64, 255),
                outline=(245, 245, 245, 255),
                width=2,
            )
            lx, ly = point_label_position(px, py, width, height)
            draw.text((lx, ly), point.name, fill=(237, 245, 252, 255), font=font)

        marker_radius = 10
        mx, my = current_pos
        draw.ellipse(
            [(mx - marker_radius, my - marker_radius), (mx + marker_radius, my + marker_radius)],
            fill=(247, 106, 72, 255),
            outline=(255, 255, 255, 255),
            width=2,
        )

        status_text = f"Progress: {progress * 100:5.1f}%"
        draw.rectangle([(width - 190, 10), (width - 10, 42)], fill=(0, 0, 0, 120))
        draw.text((width - 178, 18), status_text, fill=(255, 238, 206, 255), font=font)

        frame_path = frames_dir / f"frame_{index:06d}.png"
        frame.convert("RGB").save(frame_path, format="PNG")

    ensure_ffmpeg_exists()
    ffmpeg_input = str(frames_dir / "frame_%06d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        ffmpeg_input,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    print("[info] encoding video with ffmpeg...")
    subprocess.run(cmd, check=True)
    print(f"[info] video ready: {output_path}")

    if not keep_frames:
        shutil.rmtree(work_root, ignore_errors=True)
    else:
        print(f"[info] kept frames at: {frames_dir}")


def main() -> int:
    try:
        width = env_int("GEO_WIDTH", 1280, 640, 3840)
        height = env_int("GEO_HEIGHT", 720, 360, 2160)
        fps = env_int("GEO_FPS", 30, 10, 60)
        duration_seconds = env_float("GEO_DURATION_SECONDS", 12.0, 2.0, 120.0)
        title = os.getenv("GEO_TITLE", DEFAULT_TITLE).strip() or DEFAULT_TITLE
        attribution = os.getenv("GEO_ATTRIBUTION", DEFAULT_ATTRIBUTION).strip() or DEFAULT_ATTRIBUTION
        geojson_url = os.getenv("GEO_GEOJSON_URL", DEFAULT_GEOJSON_URL).strip()
        keep_frames = env_bool("GEO_KEEP_FRAMES", default=False)

        output_dir = Path(os.getenv("GEO_OUTPUT_DIR", "outputs/geo-video")).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = sanitize_output_name(os.getenv("GEO_OUTPUT_NAME", "geo_mapping_video.mp4"))
        output_path = output_dir / output_name

        route_points = load_route_points()
        print(f"[info] points loaded: {len(route_points)}")
        print(f"[info] output path: {output_path}")
        render_video(
            points=route_points,
            output_path=output_path,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            title=title,
            attribution=attribution,
            keep_frames=keep_frames,
            geojson_url=geojson_url,
        )
        write_github_output(output_path)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
