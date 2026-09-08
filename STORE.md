# Room Rescue — store packaging (not submitted)

This repository now has a **Capacitor shell** so Jeff can produce iOS and Android projects from the existing FastAPI + static web app. **Nothing has been submitted to the App Store or Play Store.** The next step is developer accounts, GitHub signing secrets, screenshots, and review — not a personal Mac.

Live web (unchanged): [https://room-rescue-ai-production.up.railway.app](https://room-rescue-ai-production.up.railway.app)

Listing copy (paste into Connect / Play Console): [docs/store-listing.md](docs/store-listing.md)  
Screenshot capture plan + framed web shots: [docs/store-assets/README.md](docs/store-assets/README.md)  
Detailed submission steps: [docs/app-store-checklist.md](docs/app-store-checklist.md)  
Share / Product Hunt / friend-intro copy (web only; stores are not submitted): [docs/marketing.md](docs/marketing.md)

## Why a WebView of the live site

Room Rescue is not a static SPA. The UI in `static/` is served by FastAPI, and `/api/analyze` / `/api/compare` send photos (in memory) to OpenAI. A bundled-only app would still need that backend.

The Capacitor 8 WebView therefore loads the production URL by default. One Railway deploy keeps web and native in sync. Local native debugging points the same WebView at `uvicorn` via `CAPACITOR_SERVER_URL`.

This is scaffolding. Apple and Google sometimes reject thin website wrappers (Apple 4.2 Minimum Functionality). That risk is documented in the checklist; this PR does not try to “pass review” from Linux CI.

## Identity

| Field | Value |
| --- | --- |
| App name | Room Rescue |
| Bundle ID / applicationId | `com.roomrescue.app` |
| Version | `1.0.0` (store-candidate number; **not shipped**) |
| Android `versionCode` / iOS build | `1` |
| Apple Team ID | `4Z83VV99SL` |
| Production URL | `https://room-rescue-ai-production.up.railway.app` |

Bump `native/app.json`, then from `native/` run `npm run version:sync` and commit the iOS/Android file changes.

## What Jeff does locally

Web (same as today — this is what Railway runs):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-key
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Native projects (after cloning):

```bash
cd native
npm install
npx cap sync
```

- **iOS archive / upload:** GitHub Actions on `macos-latest` (see [Cloud Mac CI](#cloud-mac-ci-jeff-does-not-need-a-personal-mac)). You do not need a personal Mac. `native/ios/` stays in the repo so the cloud Mac (or Xcode, if you want it) can open the project without regenerating.
- **Android:** `npx cap open android` (Android Studio) is optional. CI on Ubuntu builds a Play **AAB** when a keystore secret exists.
- **Point at local FastAPI** (phone and computer on the same Wi-Fi; use the computer’s LAN IP, not `127.0.0.1`):

```bash
cd native
CAPACITOR_SERVER_URL=http://192.168.1.20:8000 npx cap sync
npx cap open ios      # optional; archive is cloud Mac CI
npx cap open android
```

iOS Simulator can often use `http://127.0.0.1:8000`. Android Emulator uses `http://10.0.2.2:8000`.

## Cloud Mac CI (Jeff does not need a personal Mac)

GitHub Actions [`.github/workflows/native-store.yml`](.github/workflows/native-store.yml) replaces the old **“Mac with Xcode”** step. On `macos-latest` it runs, from `native/`, `npm ci` and `npx cap sync`, then archives the iOS app when Apple signing secrets are present. A Ubuntu job builds a Play **AAB** when a keystore secret exists.

**This workflow does not submit the app.** With an App Store Connect API key it can upload a *build*. Jeff still clicks Submit for Review in Connect / Play Console.

Apple signing secrets are saved. Team ID is `4Z83VV99SL`. First archive requested 2026-09-08. Not submitted.

- If Apple signing secrets are missing, the iOS job **fails with a clear message**. It does not upload a dummy IPA or report a successful store build.
- If `ANDROID_KEYSTORE_BASE64` is missing, the Android job **skips cleanly** (no AAB artifact, not a Play upload).

### Required GitHub Actions secrets

Repo → Settings → Secrets and variables → Actions. **Never commit these.** Bundle ID is `com.roomrescue.app`.

**iOS archive** — all four required:

| Secret | Contents |
| --- | --- |
| `APPLE_DISTRIBUTION_CERTIFICATE_P12_BASE64` | Apple **Distribution** `.p12`, base64-encoded |
| `APPLE_DISTRIBUTION_CERTIFICATE_PASSWORD` | Password for that `.p12` |
| `APPLE_PROVISIONING_PROFILE_BASE64` | App Store `.mobileprovision` for `com.roomrescue.app`, base64-encoded |
| `APPLE_TEAM_ID` | 10-character Apple Developer Team ID (`4Z83VV99SL`) |

**iOS upload** (optional App Store Connect API key — upload a build, still not Submit):

| Secret | Contents |
| --- | --- |
| `APP_STORE_CONNECT_API_KEY_ID` | Key ID |
| `APP_STORE_CONNECT_API_ISSUER_ID` | Issuer ID (UUID) |
| `APP_STORE_CONNECT_API_KEY_P8` | Full `.p8` private-key file text |

**Android AAB** — skip the job if the keystore is unset:

| Secret | Contents |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Play upload keystore (`.jks` / `.keystore`), base64-encoded |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias |
| `ANDROID_KEY_PASSWORD` | Key password (defaults to the keystore password if omitted) |

Encode files locally (do not paste certs into git):

```bash
base64 -i AppleDistribution.p12 | pbcopy
base64 -w0 AppStore_com.roomrescue.app.mobileprovision
base64 -w0 play-upload.keystore
```

Create the Distribution cert and App Store profile in the [Apple Developer portal](https://developer.apple.com/account). Create an App Store Connect API key if you want CI to upload. Create a Play upload keystore if you want an AAB artifact. Then use **Actions → Native store builds → Run workflow**.

## What only Jeff can do

Cloud Mac CI does **not** replace accounts, secrets, screenshots, or Submit:

- Enroll in the [Apple Developer Program](https://developer.apple.com/programs/) ($99/year) and create the App Store Connect listing
- Create the [Google Play Console](https://play.google.com/console/) account ($25 one-time) and the Play listing
- Confirm `com.roomrescue.app` is unused, or pick another bundle ID and update `native/app.json`
- Create iOS signing (certificates, profiles) and Android Play App Signing / upload keystore, then paste them as the GitHub secrets above
- Answer export compliance, age rating, and privacy nutrition questionnaires
- Recapture required screenshots on a **real device or simulator** (this repo has live-site frames in `docs/store-assets/`, not native captures)
- Click Submit for Review

## Privacy (for store forms)

Honest summary matching `/privacy` and `/terms`:

- No accounts, payments, ads, or photo library
- User photos leave the device: browser → our server (memory only) → OpenAI vision API
- We do not keep photos as a product feature
- Checkmarks stay in on-device storage (browser `localStorage` / the WebView equivalent)
- Adults; not directed at children under 13
- DIY helper, not a professional inspection; the list can be wrong

See the nutrition-label notes in [docs/app-store-checklist.md](docs/app-store-checklist.md).
