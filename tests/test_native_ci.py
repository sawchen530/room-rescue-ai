from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "native-store.yml").read_text()
STORE = (ROOT / "STORE.md").read_text()
README = (ROOT / "README.md").read_text()
CHECKLIST = (ROOT / "docs" / "app-store-checklist.md").read_text()

SECRETS = (
    "APPLE_DISTRIBUTION_CERTIFICATE_P12_BASE64",
    "APPLE_DISTRIBUTION_CERTIFICATE_PASSWORD",
    "APPLE_PROVISIONING_PROFILE_BASE64",
    "APPLE_TEAM_ID",
    "APP_STORE_CONNECT_API_KEY_ID",
    "APP_STORE_CONNECT_API_ISSUER_ID",
    "APP_STORE_CONNECT_API_KEY_P8",
    "ANDROID_KEYSTORE_BASE64",
    "ANDROID_KEYSTORE_PASSWORD",
    "ANDROID_KEY_ALIAS",
    "ANDROID_KEY_PASSWORD",
)


def test_workflow_runs_cap_sync_on_cloud_mac_and_ubuntu():
    assert "runs-on: macos-latest" in WORKFLOW
    assert "runs-on: ubuntu-latest" in WORKFLOW
    assert "npm ci" in WORKFLOW
    assert "npx cap sync" in WORKFLOW
    assert 'node-version: "22"' in WORKFLOW
    assert "working-directory: native" in WORKFLOW
    assert "com.roomrescue.app" in WORKFLOW
    assert "xcodebuild" in WORKFLOW
    assert "bundleRelease" in WORKFLOW


def test_workflow_and_store_document_signing_secrets():
    for name in SECRETS:
        assert name in WORKFLOW, name
        assert name in STORE, name
    assert "com.roomrescue.app" in STORE


def test_ios_missing_secrets_fails_instead_of_pretending_success():
    assert "exit 1" in WORKFLOW
    assert "not a successful store build" in WORKFLOW.lower()
    assert "not submitted" in WORKFLOW.lower()
    assert "BEGIN PRIVATE KEY" not in WORKFLOW
    assert "BEGIN CERTIFICATE" not in WORKFLOW
    assert "MII" not in WORKFLOW


def test_android_skips_cleanly_without_keystore():
    assert "Skipping Android AAB" in WORKFLOW
    assert "present=false" in WORKFLOW
    assert "ANDROID_KEYSTORE_BASE64" in WORKFLOW
    assert "ROOMRESCUE_RELEASE_STORE_FILE" in WORKFLOW


def test_store_md_says_jeff_does_not_need_a_personal_mac():
    assert "Jeff does not need a personal Mac" in STORE
    assert "Mac with Xcode" in STORE
    assert "macos-latest" in STORE
    assert "not submitted" in STORE.lower()
    assert "real device" in STORE.lower()
    assert "GitHub signing secrets" in STORE or "GitHub Actions secrets" in STORE
    assert "does not submit" in STORE.lower() or "does not submit the app" in STORE.lower()


def test_docs_do_not_require_a_personal_mac():
    for text in (STORE, README, CHECKLIST):
        assert "personal Mac" in text
        assert "does not need a personal Mac" in text or "not required" in text.lower()
