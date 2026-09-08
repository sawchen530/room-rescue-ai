import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTING = (ROOT / "docs" / "store-listing.md").read_text()
CHECKLIST = (ROOT / "docs" / "app-store-checklist.md").read_text()
ASSETS = ROOT / "docs" / "store-assets"
STORE = (ROOT / "STORE.md").read_text()


def _block(heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n.*?```\n(.*?)```"
    match = re.search(pattern, LISTING, re.S)
    assert match, f"missing fenced copy for {heading!r}"
    return match.group(1).strip("\n")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path.name
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_listing_copy_fits_store_limits():
    assert len(_block("Name (30)")) <= 30
    assert len(_block("Subtitle (30)")) <= 30
    assert len(_block("Promotional text (170)")) <= 170
    assert len(_block("Description (4000)")) <= 4000
    assert len(_block("Keywords (100)")) <= 100
    assert " " not in _block("Keywords (100)")
    assert len(_block("What’s New (1.0.0)")) <= 4000
    assert len(_block("Title (30)")) <= 30
    assert len(_block("Short description (80)")) <= 80
    assert len(_block("Full description (4000)")) <= 4000


def test_listing_copy_is_honest_diy_helper():
    haystack = LISTING.lower()
    for needle in (
        "not a professional inspection",
        "not a licensed inspection",
        "diy",
        "openai",
        "can miss things",
        "trust the room",
        "do not keep your photos",
        "no account",
    ):
        assert needle in haystack, needle

    for banned in (r"\bxp\b", r"achievement", r"gamif", r"streak", r"leaderboard"):
        assert re.search(banned, haystack) is None, banned

    keywords = _block("Keywords (100)").lower()
    assert "room rescue" not in keywords
    assert "diy" in keywords


def test_support_and_marketing_urls():
    live = "https://room-rescue-ai-production.up.railway.app"
    privacy = f"{live}/privacy"
    assert live in LISTING
    assert privacy in LISTING
    assert "Support URL" in LISTING
    assert "Marketing URL" in LISTING
    assert "not submitted" in LISTING.lower()


def test_checklist_points_at_listing_and_marks_jeff_work():
    assert "store-listing.md" in CHECKLIST
    assert "store-assets" in CHECKLIST
    assert "Only Jeff" in CHECKLIST or "only Jeff" in CHECKLIST
    assert "Mac" in CHECKLIST
    assert "not submitted" in CHECKLIST.lower()
    assert "real device" in CHECKLIST.lower()
    assert "store-listing.md" in STORE


def test_store_screenshots_exist_at_required_sizes():
    expected = {
        "iphone-6.7-01-home.png": (1290, 2796),
        "iphone-6.7-02-checklist.png": (1290, 2796),
        "iphone-6.7-03-progress.png": (1290, 2796),
        "iphone-6.7-04-privacy.png": (1290, 2796),
        "play-phone-01-home.png": (1080, 1920),
        "play-phone-02-checklist.png": (1080, 1920),
        "play-icon-512.png": (512, 512),
        "play-feature-1024x500.png": (1024, 500),
    }
    missing = [name for name in expected if not (ASSETS / name).is_file()]
    assert not missing, f"missing store assets: {missing}"
    for name, size in expected.items():
        assert _png_size(ASSETS / name) == size, name

    readme = (ASSETS / "README.md").read_text().lower()
    assert "still needs jeff" in readme
    assert "scaled from" in readme
