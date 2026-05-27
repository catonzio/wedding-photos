"""
Generate fake placeholder images for all media entries in tables.yaml.

Produces real JPEG files using Pillow so browsers can display them correctly.

Usage:
    python scripts/generate_fake_images.py
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Resolve project root
ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import yaml  # noqa: E402 — project dependency

TABLES_YAML = ROOT / "tables.yaml"

W, H = 800, 600

# Palette: (background_rgb, accent_rgb)
PALETTES: list[tuple[tuple[int, int, int], tuple[int, int, int]]] = [
    ((228, 234, 224), (122, 144, 105)),  # sage
    ((240, 234, 214), (184, 151, 46)),  # gold
    ((232, 237, 227), (90, 112, 80)),  # dark sage
    ((237, 232, 224), (140, 122, 90)),  # warm brown
    ((224, 228, 232), (90, 112, 128)),  # slate
    ((237, 224, 232), (128, 80, 106)),  # mauve
]


def _draw_botanical(
    draw: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple[int, int, int]
) -> None:
    """Draw a simple botanical stem with leaves."""
    lw = 2

    def pt(dx: float, dy: float) -> tuple[int, int]:
        return (cx + int(dx), cy + int(dy))

    # Main stem
    draw.line([pt(0, 90), pt(0, -50)], fill=color, width=lw)

    # Leaves as polygons approximated with ellipses
    for angle, rx, ry, ox, oy in [
        (-30, 28, 12, -20, 20),
        (30, 28, 12, 20, 10),
        (-20, 22, 10, -14, -20),
    ]:
        rad = math.radians(angle)
        # Draw a rotated oval by sampling points
        pts = []
        for i in range(20):
            t = 2 * math.pi * i / 20
            x = rx * math.cos(t)
            y = ry * math.sin(t)
            xr = x * math.cos(rad) - y * math.sin(rad)
            yr = x * math.sin(rad) + y * math.cos(rad)
            pts.append(pt(ox + xr, oy + yr))
        draw.polygon(pts, outline=color)

    # Flower bud at top
    draw.ellipse([pt(-12, -86), pt(12, -62)], outline=color, width=lw)

    # Side sprigs
    draw.line([pt(0, 55), pt(-40, 30)], fill=color, width=lw)
    draw.ellipse([pt(-52, 22), pt(-36, 38)], outline=color, width=lw)
    draw.line([pt(0, 50), pt(40, 25)], fill=color, width=lw)
    draw.ellipse([pt(36, 17), pt(52, 33)], outline=color, width=lw)


def _make_jpeg(table_id: int, filename: str, table_name: str) -> bytes:
    bg, accent = PALETTES[(table_id - 1) % len(PALETTES)]
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Botanical illustration centred slightly above middle
    _draw_botanical(draw, W // 2, H // 2 - 30, accent)

    # Corner marks
    for x1, y1, x2, y2 in [
        (20, 20, 60, 20),
        (20, 20, 20, 60),
        (W - 20, 20, W - 60, 20),
        (W - 20, 20, W - 20, 60),
        (20, H - 20, 60, H - 20),
        (20, H - 20, 20, H - 60),
        (W - 20, H - 20, W - 60, H - 20),
        (W - 20, H - 20, W - 20, H - 60),
    ]:
        draw.line([(x1, y1), (x2, y2)], fill=accent, width=1)

    # Labels — use default PIL font (no external font file needed)
    try:
        font_large = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Georgia.ttf", 28
        )
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = font_large

    label = filename.replace("_", " ").rsplit(".", 1)[0].title()
    draw.text(
        (W // 2, H // 2 + 120), table_name, fill=accent, font=font_large, anchor="mm"
    )
    draw.text((W // 2, H // 2 + 158), label, fill=accent, font=font_small, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def main() -> None:
    if not TABLES_YAML.exists():
        print(f"tables.yaml not found at {TABLES_YAML}", file=sys.stderr)
        sys.exit(1)

    with TABLES_YAML.open() as f:
        data = yaml.safe_load(f)

    # Resolve media output directory relative to the installed package
    media_dir = SRC / "wedding_photos" / "static" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for t in data.get("tables", []):
        table_id: int = t["id"]
        table_name: str = t.get("name", f"Tavolo {table_id}")
        items: list[str] = []
        if t.get("cover"):
            items.append(t["cover"])
        items.extend(t.get("media", []))

        for rel_path in items:
            dest = media_dir / rel_path
            if dest.exists():
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            filename = Path(rel_path).name
            dest.write_bytes(_make_jpeg(table_id, filename, table_name))
            print(f"  created  {rel_path}")
            created += 1

    print(f"\nDone — {created} file(s) created, {skipped} already existed.")


if __name__ == "__main__":
    main()
