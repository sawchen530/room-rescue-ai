import io

from fastapi.testclient import TestClient

import app as room_app
from app import sniff_image_media_type, sniff_magic

JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
WEBP = b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"\x00" * 8
HEIC = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 12


def client() -> TestClient:
    return TestClient(room_app.app)


def test_sniff_magic_types():
    assert sniff_magic(JPEG) == "image/jpeg"
    assert sniff_magic(PNG) == "image/png"
    assert sniff_magic(WEBP) == "image/webp"
    assert sniff_magic(HEIC) == "image/heic"
    assert sniff_magic(b"not-an-image") is None


def test_sniff_falls_back_to_extension_for_octet_stream():
    media = sniff_image_media_type("yard.heic", "application/octet-stream", b"\x00\x01\x02")
    assert media == "image/heic"


def test_sniff_rejects_unknown_bytes():
    try:
        sniff_image_media_type("notes.txt", "text/plain", b"hello")
    except room_app.HTTPException as exc:
        assert exc.status_code == 415
        assert "JPG" in exc.detail
    else:
        raise AssertionError("expected 415")


def test_home_and_privacy():
    response = client().get("/")
    assert response.status_code == 200
    assert "Room Rescue" in response.text
    assert "og:image" in response.text
    assert "room-rescue-ai-production.up.railway.app" in response.text

    privacy = client().get("/privacy")
    assert privacy.status_code == 200
    assert "local storage" in privacy.text.lower() or "localStorage" in privacy.text


def test_robots_and_sitemap():
    robots = client().get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap:" in robots.text
    assert "/api/" in robots.text

    sitemap = client().get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "room-rescue-ai-production.up.railway.app" in sitemap.text
    assert "/privacy" in sitemap.text


def test_docs_are_disabled_by_default():
    http = client()
    assert http.get("/docs").status_code == 404
    assert http.get("/redoc").status_code == 404
    assert http.get("/openapi.json").status_code == 404


def test_health_and_manifest():
    assert client().get("/health").json() == {"status": "ok"}
    manifest = client().get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.json()["name"] == "Room Rescue"
    assert manifest.json()["theme_color"] == "#243028"


def test_static_assets_have_cache_headers():
    response = client().get("/static/app.css")
    assert response.status_code == 200
    assert "max-age" in response.headers.get("cache-control", "")


def test_analyze_rejects_non_image():
    response = client().post(
        "/api/analyze",
        files={"image": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"room_hint": "Kitchen", "time_budget": "30"},
    )
    assert response.status_code == 415
    assert "JPG" in response.json()["detail"]


def test_analyze_accepts_heic_octet_stream_then_clean_config_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client().post(
        "/api/analyze",
        files={"image": ("garage.heic", io.BytesIO(HEIC), "application/octet-stream")},
        data={"room_hint": "Garage", "time_budget": "30"},
    )
    assert response.status_code == 500
    assert "OPENAI" not in response.json()["detail"]
    assert "try again" in response.json()["detail"].lower()


def test_analyze_oversize_image():
    huge = b"\xff\xd8\xff" + b"x" * (12 * 1024 * 1024 + 10)
    response = client().post(
        "/api/analyze",
        files={"image": ("big.jpg", io.BytesIO(huge), "image/jpeg")},
        data={"room_hint": "Kitchen", "time_budget": "30"},
    )
    assert response.status_code == 413
    assert "12 MB" in response.json()["detail"]


def test_compare_bad_tasks_is_clean():
    response = client().post(
        "/api/compare",
        files={
            "before_image": ("a.jpg", io.BytesIO(JPEG), "image/jpeg"),
            "after_image": ("b.jpg", io.BytesIO(JPEG), "image/jpeg"),
        },
        data={"tasks_json": "not-json", "room_type": "Kitchen"},
    )
    assert response.status_code == 400
    assert "not-json" not in response.json()["detail"]


def test_analyze_success_shape(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_model(_prompt, _urls):
        return {
            "room_type": "Kitchen",
            "summary": "A usable first session for the counters and floor.",
            "tasks": [
                {
                    "title": "Clear the left counter",
                    "category": "Organization",
                    "priority": "High",
                    "minutes": 10,
                    "reason": "Items are piled on the work surface.",
                    "confidence": "High",
                    "diy_level": "Easy",
                    "supplies": ["box"],
                },
                {
                    "title": "Sweep the floor",
                    "category": "Cleaning",
                    "priority": "Medium",
                    "minutes": 8,
                    "reason": "Crumbs are visible near the fridge.",
                    "confidence": "Medium",
                    "diy_level": "Easy",
                    "supplies": ["broom"],
                },
            ],
            "cautions": [],
            "estimated_total_minutes": 99,
        }

    monkeypatch.setattr(room_app, "call_json_model", fake_model)
    response = client().post(
        "/api/analyze",
        files={"image": ("room.jpg", io.BytesIO(JPEG), "application/octet-stream")},
        data={"room_hint": "Kitchen", "time_budget": "30"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["room_type"] == "Kitchen"
    assert body["estimated_total_minutes"] == 18
    assert [task["title"] for task in body["tasks"]] == ["Clear the left counter", "Sweep the floor"]


def test_analyze_failure_does_not_leak_exception(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def boom(_prompt, _urls):
        raise RuntimeError("secret stack trace xyz")

    monkeypatch.setattr(room_app, "call_json_model", boom)
    response = client().post(
        "/api/analyze",
        files={"image": ("room.jpg", io.BytesIO(JPEG), "image/jpeg")},
        data={"room_hint": "Kitchen", "time_budget": "30"},
    )
    assert response.status_code == 502
    assert "xyz" not in response.json()["detail"]
    assert "secret" not in response.json()["detail"]


def test_compare_success_shape(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    task = {
        "title": "Clear the left counter",
        "category": "Organization",
        "priority": "High",
        "minutes": 10,
        "reason": "Items are piled on the work surface.",
        "confidence": "High",
        "diy_level": "Easy",
        "supplies": ["box"],
    }

    def fake_model(_prompt, _urls):
        return {
            "summary": "The counter is clearer.",
            "encouragement": "Nice start.",
            "successes": ["Counter is visible again"],
            "failures": [],
            "task_results": [
                {
                    "title": "Clear the left counter",
                    "status": "Completed",
                    "evidence": "The pile is gone.",
                    "next_step": "Move on.",
                    "confidence": "High",
                }
            ],
        }

    monkeypatch.setattr(room_app, "call_json_model", fake_model)
    response = client().post(
        "/api/compare",
        files={
            "before_image": ("a.jpg", io.BytesIO(JPEG), "image/jpeg"),
            "after_image": ("b.jpg", io.BytesIO(JPEG), "image/jpeg"),
        },
        data={"tasks_json": __import__("json").dumps([task]), "room_type": "Kitchen"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["completed_percentage"] == 100
    assert body["should_retake"] is False
    assert body["task_results"][0]["status"] == "Completed"
