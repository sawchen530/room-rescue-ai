#!/usr/bin/env python3
"""Create placeholder store icons/splash from the Room Rescue brand marks.

These are scaffolding assets (same house + gold bar as the web favicon).
Replace native/assets/icon.png (1024) and splash.png (2732) with final art
before App Store / Play submission. See STORE.md.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WEB_ICON = ROOT.parent / "static" / "icon-512.png"

BG = (36, 48, 40, 255)  # #243028
CREAM = (243, 239, 228, 255)  # #f3efe4
GOLD = (201, 162, 39, 255)  # #c9a227
CLEAR = (0, 0, 0, 0)


def _draw_house(draw: ImageDraw.ImageDraw, size: int, stroke: int, inset: float = 0.16) -> None:
    pad = size * inset
    left = pad
    right = size - pad
    mid = size / 2
    roof_top = size * 0.18
    eaves_y = size * 0.42
    floor = size * 0.78
    door_w = size * 0.22
    door_h = size * 0.22
    door_left = mid - door_w / 2
    door_top = floor - door_h

    roof = [(left, eaves_y), (mid, roof_top), (right, eaves_y)]
    walls = [
        (left, eaves_y),
        (right, eaves_y),
        (right, floor),
        (left, floor),
        (left, eaves_y),
    ]
    door = [
        (door_left, floor),
        (door_left, door_top),
        (door_left + door_w, door_top),
        (door_left + door_w, floor),
    ]
    draw.line(roof + [roof[0]], fill=CREAM, width=stroke, joint="curve")
    draw.line(walls, fill=CREAM, width=stroke, joint="curve")
    draw.line(door, fill=CREAM, width=stroke, joint="curve")


def make_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(image)
    bar = max(8, int(size * 0.07))
    draw.rectangle((0, size - bar, size, size), fill=GOLD)
    _draw_house(draw, size, stroke=max(8, size // 28), inset=0.17)
    return image


def make_foreground(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), CLEAR)
    draw = ImageDraw.Draw(image)
    _draw_house(draw, size, stroke=max(10, size // 24), inset=0.26)
    return image


def make_background(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(image)
    bar = max(10, int(size * 0.08))
    draw.rectangle((0, size - bar, size, size), fill=GOLD)
    return image


def make_splash(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(image)
    icon_box = int(size * 0.28)
    icon = make_icon(icon_box)
    x = (size - icon_box) // 2
    y = (size - icon_box) // 2
    image.alpha_composite(icon, (x, y))
    bar = max(24, int(size * 0.035))
    draw.rectangle((0, size - bar, size, size), fill=GOLD)
    return image


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    print(f"wrote {path.relative_to(ROOT)} ({image.size[0]}x{image.size[1]})")


def main() -> None:
    save(make_icon(1024), ASSETS / "icon.png")
    save(make_icon(1024), ASSETS / "icon-only.png")
    save(make_foreground(1024), ASSETS / "icon-foreground.png")
    save(make_background(1024), ASSETS / "icon-background.png")
    save(make_splash(2732), ASSETS / "splash.png")
    save(make_splash(2732), ASSETS / "splash-dark.png")
    if WEB_ICON.exists():
        print(f"web icon available at {WEB_ICON} (kept as the PWA source)")


if __name__ == "__main__":
    main()
