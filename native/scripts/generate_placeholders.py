#!/usr/bin/env python3
"""Create store-candidate icons/splash from the Room Rescue house mark.

Still a simple forest/gold house — cleaner than the first scaffold, not
final commissioned art. Replace native/assets/icon.png (1024) and
splash.png (2732) with final art before App Store / Play submission, then
run `npm run assets` from native/. See native/assets/README.md.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WEB_ICON = ROOT.parent / "static" / "icon-512.png"
STORE_ASSETS = ROOT.parent / "docs" / "store-assets"

BG = (36, 48, 40, 255)  # #243028
BG_DEEP = (22, 30, 26, 255)
BG_LIFT = (49, 70, 58, 255)
CREAM = (243, 239, 228, 255)  # #f3efe4
GOLD = (201, 162, 39, 255)  # #c9a227
GOLD_LIGHT = (220, 188, 82, 255)
CLEAR = (0, 0, 0, 0)
PAPER = (232, 235, 228, 255)
INK = (28, 31, 26, 255)

FONT_DISPLAY = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")
FONT_BODY = Path("/usr/share/fonts/truetype/macos/Inter-Regular.ttf")
FONT_BODY_FALLBACK = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")

SCALE = 2  # draw oversized, then Lanczos-down for clean strokes


def _font(path: Path, size: int, fallback: Path | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (path, fallback):
        if candidate and candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _forest_fill(size: int, *, deep: bool = False) -> Image.Image:
    """Soft radial forest: slightly lighter in the upper-center."""
    inner = BG_LIFT if not deep else BG
    outer = BG_DEEP if deep else (27, 36, 31, 255)
    grad = Image.new("RGBA", (64, 64), outer)
    draw = ImageDraw.Draw(grad)
    for i in range(32, 0, -1):
        t = i / 32
        color = tuple(int(outer[c] + (inner[c] - outer[c]) * t) for c in range(3)) + (255,)
        draw.ellipse(
            (32 - i * 1.15, 22 - i * 0.95, 32 + i * 1.15, 28 + i * 1.05),
            fill=color,
        )
    return grad.resize((size, size), Image.Resampling.LANCZOS)


def _draw_house(
    draw: ImageDraw.ImageDraw,
    size: int,
    stroke: int,
    inset: float = 0.16,
    *,
    y_shift: float = 0.0,
) -> None:
    """House outline matching the web favicon (peaked roof, open door)."""
    pad = size * inset
    left = pad
    right = size - pad
    mid = size / 2
    roof_top = size * (0.17 + y_shift)
    eaves_y = size * (0.40 + y_shift)
    floor = size * (0.76 + y_shift)
    door_w = size * 0.20
    door_h = size * 0.24
    door_left = mid - door_w / 2
    door_top = floor - door_h

    outline = [
        (left, floor),
        (left, eaves_y),
        (mid, roof_top),
        (right, eaves_y),
        (right, floor),
        (left, floor),
    ]
    door = [
        (door_left, floor),
        (door_left, door_top),
        (door_left + door_w, door_top),
        (door_left + door_w, floor),
    ]
    # Double-stroke: a slightly darker cream underneath for weight, then cream.
    under = (214, 208, 190, 255)
    under_w = max(stroke + max(2, stroke // 6), stroke)
    draw.line(outline, fill=under, width=under_w, joint="curve")
    draw.line(door, fill=under, width=under_w, joint="curve")
    draw.line(outline, fill=CREAM, width=stroke, joint="curve")
    draw.line(door, fill=CREAM, width=stroke, joint="curve")
    # Round the visible corners so 1024px doesn't look stair-stepped.
    r = max(1, stroke // 2)
    for x, y in outline + door:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=CREAM)


def _gold_bar(draw: ImageDraw.ImageDraw, size: int, frac: float = 0.078) -> None:
    bar = max(8, int(size * frac))
    draw.rectangle((0, size - bar, size, size), fill=GOLD)
    highlight = max(2, bar // 6)
    draw.rectangle((0, size - bar, size, size - bar + highlight), fill=GOLD_LIGHT)


def _render_at_scale(size: int, painter) -> Image.Image:
    big = painter(size * SCALE)
    return big.resize((size, size), Image.Resampling.LANCZOS)


def _paint_icon(s: int) -> Image.Image:
    image = _forest_fill(s)
    draw = ImageDraw.Draw(image)
    _draw_house(draw, s, stroke=max(28, s // 26), inset=0.18, y_shift=-0.01)
    _gold_bar(draw, s)
    return image


def make_icon(size: int) -> Image.Image:
    return _render_at_scale(size, _paint_icon)


def make_foreground(size: int) -> Image.Image:
    def paint(s: int) -> Image.Image:
        image = Image.new("RGBA", (s, s), CLEAR)
        draw = ImageDraw.Draw(image)
        # Adaptive-icon safe zone is the inner ~66% circle.
        _draw_house(draw, s, stroke=max(32, s // 22), inset=0.27, y_shift=0.02)
        return image

    return _render_at_scale(size, paint)


def make_background(size: int) -> Image.Image:
    def paint(s: int) -> Image.Image:
        image = _forest_fill(s)
        draw = ImageDraw.Draw(image)
        _gold_bar(draw, s, frac=0.09)
        return image

    return _render_at_scale(size, paint)


def make_splash(size: int, *, dark: bool = False) -> Image.Image:
    def paint(s: int) -> Image.Image:
        image = _forest_fill(s, deep=dark)
        badge = int(s * 0.34)
        icon = _paint_icon(badge)
        mat = int(s * 0.42)
        mx = (s - mat) // 2
        my = (s - mat) // 2 - int(s * 0.02)
        shadow = Image.new("RGBA", (s, s), CLEAR)
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (mx + s * 0.008, my + s * 0.012, mx + mat + s * 0.008, my + mat + s * 0.012),
            radius=int(mat * 0.18),
            fill=(0, 0, 0, 90),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(min(28, max(8, s // 200))))
        image = Image.alpha_composite(image, shadow)
        overlay = Image.new("RGBA", (s, s), CLEAR)
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            (mx, my, mx + mat, my + mat),
            radius=int(mat * 0.18),
            fill=(49, 70, 58, 235),
        )
        od.rounded_rectangle(
            (mx, my, mx + mat, my + mat),
            radius=int(mat * 0.18),
            outline=GOLD,
            width=max(4, s // 220),
        )
        image = Image.alpha_composite(image, overlay)
        ix = (s - badge) // 2
        iy = my + (mat - badge) // 2
        image.alpha_composite(icon, (ix, iy))
        draw = ImageDraw.Draw(image)
        _gold_bar(draw, s, frac=0.032)
        return image

    return _render_at_scale(size, paint)


def make_play_feature(width: int = 1024, height: int = 500) -> Image.Image:
    """Play Console feature graphic — house mark + honest tagline."""
    image = Image.new("RGBA", (width, height), BG)
    # Stretch a forest fill across the banner.
    fill = _forest_fill(height)
    fill = fill.resize((width, height), Image.Resampling.LANCZOS)
    image.alpha_composite(fill, (0, 0))
    draw = ImageDraw.Draw(image)
    bar = 18
    draw.rectangle((0, height - bar, width, height), fill=GOLD)
    draw.rectangle((0, height - bar, width, height - bar + 4), fill=GOLD_LIGHT)

    icon = make_icon(280)
    image.alpha_composite(icon, (64, (height - bar - 280) // 2))

    title_font = _font(FONT_DISPLAY, 72)
    body_font = _font(FONT_BODY, 28, FONT_BODY_FALLBACK)
    note_font = _font(FONT_BODY, 22, FONT_BODY_FALLBACK)
    text_x = 380
    draw.text((text_x, 132), "Room Rescue", font=title_font, fill=CREAM)
    draw.text((text_x, 230), "Photograph a room. Get a fix-up list.", font=body_font, fill=CREAM)
    draw.text((text_x, 278), "DIY helper, not a professional inspection.", font=note_font, fill=(201, 196, 182, 255))
    return image


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    print(f"wrote {path} ({image.size[0]}x{image.size[1]})")


def main() -> None:
    save(make_icon(1024), ASSETS / "icon.png")
    save(make_icon(1024), ASSETS / "icon-only.png")
    save(make_foreground(1024), ASSETS / "icon-foreground.png")
    save(make_background(1024), ASSETS / "icon-background.png")
    save(make_splash(2732, dark=False), ASSETS / "splash.png")
    save(make_splash(2732, dark=True), ASSETS / "splash-dark.png")

    STORE_ASSETS.mkdir(parents=True, exist_ok=True)
    save(make_icon(512), STORE_ASSETS / "play-icon-512.png")
    save(make_play_feature(), STORE_ASSETS / "play-feature-1024x500.png")

    if WEB_ICON.exists():
        print(f"web icon available at {WEB_ICON} (kept as the PWA source)")


if __name__ == "__main__":
    main()
