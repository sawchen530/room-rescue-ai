# Room Rescue — store packaging (not submitted)

This repository now has a **Capacitor shell** so Jeff can produce iOS and Android projects from the existing FastAPI + static web app. **Nothing has been submitted to the App Store or Play Store.** The next step is developer accounts, a Mac for the iOS archive, signing, screenshots, and review.

Live web (unchanged): [https://room-rescue-ai-production.up.railway.app](https://room-rescue-ai-production.up.railway.app)

Detailed submission steps: [docs/app-store-checklist.md](docs/app-store-checklist.md)

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

- **iOS archive / upload:** Mac + Xcode. Linux CI cannot sign or upload an App Store build. `native/ios/` is still in the repo so you can open it on a Mac without regenerating.
- **Android:** `npx cap open android` (Android Studio). An AAB can be built on Linux or macOS once a Play keystore exists.
- **Point at local FastAPI** (phone and computer on the same Wi-Fi; use the computer’s LAN IP, not `127.0.0.1`):

```bash
cd native
CAPACITOR_SERVER_URL=http://192.168.1.20:8000 npx cap sync
npx cap open ios      # Mac
npx cap open android
```

iOS Simulator can often use `http://127.0.0.1:8000`. Android Emulator uses `http://10.0.2.2:8000`.

## What only Jeff can do

These cannot be finished from this repo or from Linux CI:

- Enroll in the [Apple Developer Program](https://developer.apple.com/programs/) ($99/year) and create the App Store Connect listing
- Create the [Google Play Console](https://play.google.com/console/) account ($25 one-time) and the Play listing
- Confirm `com.roomrescue.app` is unused, or pick another bundle ID and update `native/app.json`
- Create iOS signing (certificates, profiles) and Android Play App Signing / upload keystore
- Build the iOS archive on a Mac and upload with Xcode or Transporter
- Answer export compliance, age rating, and privacy nutrition questionnaires
- Capture required device screenshots
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
