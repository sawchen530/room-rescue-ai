import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native"
APP = json.loads((NATIVE / "app.json").read_text())


def test_native_identity_and_version_alignment():
    assert APP["appId"] == "com.roomrescue.app"
    assert APP["appName"] == "Room Rescue"
    assert APP["version"] == "1.0.0"
    assert APP["versionCode"] == 1
    assert APP["productionUrl"] == "https://room-rescue-ai-production.up.railway.app"

    package = json.loads((NATIVE / "package.json").read_text())
    assert package["version"] == APP["version"]
    assert package["name"] == "room-rescue-native"


def test_capacitor_config_points_at_live_site():
    config = (NATIVE / "capacitor.config.js").read_text()
    assert "CAPACITOR_SERVER_URL" in config
    assert "productionUrl" in config
    assert "webDir" in config
    assert 'webDir: "www"' in config


def test_fallback_www_and_placeholder_assets_exist():
    assert (NATIVE / "www" / "index.html").is_file()
    html = (NATIVE / "www" / "index.html").read_text()
    assert "Room Rescue" in html
    assert "room-rescue-ai-production.up.railway.app" in html

    for name in ("icon.png", "splash.png", "icon-foreground.png", "icon-background.png"):
        path = NATIVE / "assets" / name
        assert path.is_file(), name
        assert path.stat().st_size > 100


def test_store_docs_are_honest_scaffolding():
    store = (ROOT / "STORE.md").read_text()
    checklist = (ROOT / "docs" / "app-store-checklist.md").read_text()
    readme = (ROOT / "README.md").read_text()

    for text in (store, checklist, readme):
        assert "not" in text.lower() and "app store" in text.lower()
        assert "com.roomrescue.app" in text
        assert "openai" in text.lower() or "OpenAI" in text

    assert "scaffolding only" in checklist.lower() or "not submitted" in checklist.lower()
    assert "$99" in store and "$25" in store
    assert "nutrition" in checklist.lower()
    assert "screenshot" in checklist.lower()
    assert "4+" in checklist
    assert "Everyone" in checklist
    assert "only Jeff" in store or "Only Jeff" in checklist


def test_railway_stays_on_fastapi():
    procfile = (ROOT / "Procfile").read_text()
    assert "uvicorn app:app" in procfile
    nix = (ROOT / "nixpacks.toml").read_text()
    assert "uvicorn app:app" in nix
    assert not (ROOT / "package.json").exists()


def test_native_projects_use_bundle_id():
    gradle = NATIVE / "android" / "app" / "build.gradle"
    pbx = NATIVE / "ios" / "App" / "App.xcodeproj" / "project.pbxproj"
    plist = NATIVE / "ios" / "App" / "App" / "Info.plist"

    assert gradle.is_file()
    assert pbx.is_file()
    assert plist.is_file()

    gradle_text = gradle.read_text()
    assert 'applicationId "com.roomrescue.app"' in gradle_text
    assert 'versionName "1.0.0"' in gradle_text
    assert re.search(r"versionCode\s+1\b", gradle_text)

    pbx_text = pbx.read_text()
    assert "com.roomrescue.app" in pbx_text
    assert "MARKETING_VERSION = 1.0.0;" in pbx_text

    plist_text = plist.read_text()
    assert "NSCameraUsageDescription" in plist_text
    assert "NSPhotoLibraryUsageDescription" in plist_text
    assert "ITSAppUsesNonExemptEncryption" in plist_text

    privacy = (NATIVE / "ios" / "App" / "App" / "PrivacyInfo.xcprivacy").read_text()
    assert "NSPrivacyCollectedDataTypePhotosorVideos" in privacy
    assert "NSPrivacyTracking" in privacy

    manifest = (NATIVE / "android" / "app" / "src" / "main" / "AndroidManifest.xml").read_text()
    assert "android.permission.CAMERA" in manifest
    assert "android.permission.INTERNET" in manifest
    assert 'android:required="false"' in manifest

    colors = (NATIVE / "android" / "app" / "src" / "main" / "res" / "values" / "colors.xml").read_text()
    assert "#243028" in colors
