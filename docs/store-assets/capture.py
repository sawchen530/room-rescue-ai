#!/usr/bin/env python3
"""Capture live-site screenshots and composite them into device frames.

Outputs PNG files under docs/store-assets/. Requires:

    python3 -m pip install pillow playwright
    python3 -m playwright install chromium

These are web captures in a phone/tablet frame — not App Store Connect
captures from a physical iPhone. Recapture on real devices before submit.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "store-assets"
LIVE = "https://room-rescue-ai-production.up.railway.app"

GOLD = (201, 162, 39, 255)
PAPER = (232, 235, 228, 255)
BEZEL = (18, 22, 20, 255)

IPHONE_67 = (1290, 2796)
IPHONE_65 = (1284, 2778)
IPHONE_69 = (1320, 2868)
PLAY_PHONE = (1080, 1920)
IPAD_13 = (2048, 2732)

def _paper_bg(size: tuple[int, int]) -> Image.Image:
    w, h = size
    image = Image.new("RGBA", size, PAPER)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-w * 0.2, -h * 0.15, w * 0.9, h * 0.35), fill=(223, 229, 214, 180))
    return Image.alpha_composite(image, overlay)


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def _paste_rounded(base: Image.Image, src: Image.Image, xy: tuple[int, int], radius: int) -> None:
    mask = _rounded_mask(src.size, radius)
    base.paste(src, xy, mask)


def frame_iphone(shot: Image.Image, canvas_size: tuple[int, int] = IPHONE_67) -> Image.Image:
    """Phone bezel around a portrait screenshot. Fills most of the store canvas."""
    W, H = canvas_size
    canvas = _paper_bg((W, H))
    margin_x = int(W * 0.055)
    margin_y = int(H * 0.045)
    phone = (margin_x, margin_y, W - margin_x, H - margin_y)
    pw, ph = phone[2] - phone[0], phone[3] - phone[1]
    radius = int(pw * 0.12)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (phone[0] + 10, phone[1] + 22, phone[2] + 10, phone[3] + 22),
        radius=radius,
        fill=(0, 0, 0, 70),
    )
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(22)))

    bezel_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bezel_layer)
    bd.rounded_rectangle(phone, radius=radius, fill=BEZEL)
    bd.rounded_rectangle(phone, radius=radius, outline=GOLD, width=max(3, W // 400))
    canvas = Image.alpha_composite(canvas, bezel_layer)

    inset = max(14, int(pw * 0.028))
    screen = (phone[0] + inset, phone[1] + inset, phone[2] - inset, phone[3] - inset)
    sw, sh = screen[2] - screen[0], screen[3] - screen[1]
    fitted = shot.convert("RGBA").resize((sw, sh), Image.Resampling.LANCZOS)
    _paste_rounded(canvas, fitted, (screen[0], screen[1]), radius=max(8, radius - inset))

    # Dynamic Island
    island_w, island_h = int(pw * 0.28), int(pw * 0.055)
    ix = phone[0] + (pw - island_w) // 2
    iy = phone[1] + int(inset * 0.85)
    idraw = ImageDraw.Draw(canvas)
    idraw.rounded_rectangle((ix, iy, ix + island_w, iy + island_h), radius=island_h // 2, fill=BEZEL)
    # Home indicator
    bar_w, bar_h = int(pw * 0.28), max(6, int(pw * 0.012))
    bx = phone[0] + (pw - bar_w) // 2
    by = phone[3] - inset - bar_h - 8
    idraw.rounded_rectangle((bx, by, bx + bar_w, by + bar_h), radius=bar_h // 2, fill=(255, 255, 255, 90))
    return canvas.convert("RGBA")


def frame_ipad(shot: Image.Image, canvas_size: tuple[int, int] = IPAD_13) -> Image.Image:
    W, H = canvas_size
    canvas = _paper_bg((W, H))
    margin_x = int(W * 0.06)
    margin_y = int(H * 0.05)
    tablet = (margin_x, margin_y, W - margin_x, H - margin_y)
    tw, th = tablet[2] - tablet[0], tablet[3] - tablet[1]
    radius = int(tw * 0.045)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (tablet[0] + 12, tablet[1] + 24, tablet[2] + 12, tablet[3] + 24),
        radius=radius,
        fill=(0, 0, 0, 60),
    )
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(24)))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle(tablet, radius=radius, fill=BEZEL)
    ld.rounded_rectangle(tablet, radius=radius, outline=GOLD, width=4)
    canvas = Image.alpha_composite(canvas, layer)

    inset = max(18, int(tw * 0.025))
    screen = (tablet[0] + inset, tablet[1] + inset, tablet[2] - inset, tablet[3] - inset)
    sw, sh = screen[2] - screen[0], screen[3] - screen[1]
    fitted = shot.convert("RGBA").resize((sw, sh), Image.Resampling.LANCZOS)
    _paste_rounded(canvas, fitted, (screen[0], screen[1]), radius=max(8, radius - 8))

    # Camera dot
    cx = tablet[0] + tw // 2
    cy = tablet[1] + inset // 2
    r = max(6, inset // 6)
    ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), fill=(8, 10, 9, 255))
    return canvas.convert("RGBA")


def save(image: Image.Image, name: str) -> Path:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = image.convert("RGB")
    rgb.save(path, "PNG", optimize=True)
    print(f"wrote {path.name} ({rgb.size[0]}x{rgb.size[1]})")
    return path


def _wait_fonts(page) -> None:
    page.evaluate("() => document.fonts.ready")
    page.add_style_tag(
        content="html{scroll-behavior:auto!important}.skip{display:none!important}"
    )


def _screenshot(page) -> Image.Image:
    raw = page.screenshot(type="png", full_page=False, animations="disabled")
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def capture_live(base_url: str) -> dict[str, Image.Image]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    shots: dict[str, Image.Image] = {}
    url = base_url.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        phone = browser.new_context(
            viewport={"width": 430, "height": 932},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        page = phone.new_page()
        page.goto(url + "/", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        _wait_fonts(page)
        page.wait_for_selector("#useSample", timeout=15000)
        page.wait_for_timeout(400)
        shots["phone-home"] = _screenshot(page)

        page.click("#useSample")
        try:
            page.locator("#results:not([hidden]) article.task").first.wait_for(timeout=120000)
            page.locator("#results").scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            shots["phone-checklist"] = _screenshot(page)
            after = page.locator("#afterSection")
            if after.is_visible():
                after.scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                shots["phone-progress"] = _screenshot(page)
        except PlaywrightTimeout:
            print("warning: sample checklist did not appear within 120s", file=sys.stderr)
            err = page.locator("#analyzeErrorBox:not([hidden])")
            if err.count():
                print("analyze error is visible on the live site", file=sys.stderr)

        page.goto(url + "/privacy", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        _wait_fonts(page)
        page.wait_for_selector("article.prose h1", timeout=15000)
        page.wait_for_timeout(400)
        shots["phone-privacy"] = _screenshot(page)
        phone.close()

        tablet = browser.new_context(
            viewport={"width": 1024, "height": 1366},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        tpage = tablet.new_page()
        tpage.goto(url + "/", wait_until="domcontentloaded", timeout=60000)
        try:
            tpage.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        _wait_fonts(tpage)
        tpage.wait_for_selector("#useSample", timeout=15000)
        tpage.wait_for_timeout(400)
        shots["tablet-home"] = _screenshot(tpage)

        tpage.click("#useSample")
        try:
            tpage.locator("#results:not([hidden]) article.task").first.wait_for(timeout=120000)
            tpage.locator("#results").scroll_into_view_if_needed()
            tpage.wait_for_timeout(600)
            shots["tablet-checklist"] = _screenshot(tpage)
        except PlaywrightTimeout:
            print("warning: tablet sample checklist did not appear", file=sys.stderr)

        tpage.goto(url + "/privacy", wait_until="domcontentloaded", timeout=60000)
        try:
            tpage.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        _wait_fonts(tpage)
        tpage.wait_for_selector("article.prose h1", timeout=15000)
        tpage.wait_for_timeout(400)
        shots["tablet-privacy"] = _screenshot(tpage)
        tablet.close()
        browser.close()

    return shots


def compose(shots: dict[str, Image.Image]) -> None:
    phone_home = shots["phone-home"]
    framed_home = frame_iphone(phone_home, IPHONE_67)
    save(framed_home, "iphone-6.7-01-home.png")
    save(framed_home.resize(IPHONE_65, Image.Resampling.LANCZOS), "iphone-6.5-01-home.png")
    save(framed_home.resize(IPHONE_69, Image.Resampling.LANCZOS), "iphone-6.9-01-home.png")
    save(frame_iphone(phone_home, PLAY_PHONE), "play-phone-01-home.png")

    if "phone-checklist" in shots:
        framed = frame_iphone(shots["phone-checklist"], IPHONE_67)
        save(framed, "iphone-6.7-02-checklist.png")
        save(framed.resize(IPHONE_65, Image.Resampling.LANCZOS), "iphone-6.5-02-checklist.png")
        save(framed.resize(IPHONE_69, Image.Resampling.LANCZOS), "iphone-6.9-02-checklist.png")
        save(frame_iphone(shots["phone-checklist"], PLAY_PHONE), "play-phone-02-checklist.png")

    if "phone-progress" in shots:
        framed = frame_iphone(shots["phone-progress"], IPHONE_67)
        save(framed, "iphone-6.7-03-progress.png")
        save(framed.resize(IPHONE_65, Image.Resampling.LANCZOS), "iphone-6.5-03-progress.png")
        save(framed.resize(IPHONE_69, Image.Resampling.LANCZOS), "iphone-6.9-03-progress.png")
        save(frame_iphone(shots["phone-progress"], PLAY_PHONE), "play-phone-03-progress.png")

    if "phone-privacy" in shots:
        framed = frame_iphone(shots["phone-privacy"], IPHONE_67)
        save(framed, "iphone-6.7-04-privacy.png")
        save(framed.resize(IPHONE_65, Image.Resampling.LANCZOS), "iphone-6.5-04-privacy.png")
        save(framed.resize(IPHONE_69, Image.Resampling.LANCZOS), "iphone-6.9-04-privacy.png")
        save(frame_iphone(shots["phone-privacy"], PLAY_PHONE), "play-phone-04-privacy.png")

    if "tablet-home" in shots:
        save(frame_ipad(shots["tablet-home"], IPAD_13), "ipad-13-01-home.png")
    if "tablet-checklist" in shots:
        save(frame_ipad(shots["tablet-checklist"], IPAD_13), "ipad-13-02-checklist.png")
    if "tablet-privacy" in shots:
        save(frame_ipad(shots["tablet-privacy"], IPAD_13), "ipad-13-04-privacy.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=LIVE, help="Site to capture (default: production)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"capturing {args.url}")
    shots = capture_live(args.url)
    compose(shots)
    missing = [k for k in ("phone-home", "phone-checklist", "phone-progress", "phone-privacy") if k not in shots]
    if missing:
        print(f"incomplete capture, missing: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
