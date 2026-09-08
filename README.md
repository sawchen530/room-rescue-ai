# Room Rescue

Photograph a room. Get a practical checklist for what to clean, fix, organize, or inspect — then verify the work with an after photo.

Live: [https://room-rescue-ai-production.up.railway.app](https://room-rescue-ai-production.up.railway.app)

Built for DIY homeowners. No account, no payments, no photo library.

## How it works

1. Take a before photo from an angle you can repeat.
2. Room Rescue drafts a starting list from what’s visible, with time and ordinary supplies. The list can be wrong — see `/terms`.
3. Take an after photo from the same spot to check what’s done.

Photos are sent to our server in memory, then to OpenAI’s vision API for analysis. Large JPG/PNG/WebP shots are resized in the browser first so mobile uploads stay small; HEIC is left as-is when the phone format can’t be decoded. We do not store photos as a product feature. Checkmarks and a light progress summary stay in this browser’s local storage.

You can try the product without your own picture via **Use a sample room** (a bundled living-room photo). Privacy notes live at `/privacy`. Short terms — DIY helper, not professional advice — live at `/terms`.

Native iOS/Android packaging is a Capacitor shell around this same site. **It is not on the App Store or Play Store yet.** See [STORE.md](STORE.md), paste-ready listing copy in [docs/store-listing.md](docs/store-listing.md), framed screenshots in [docs/store-assets/](docs/store-assets/), and [docs/app-store-checklist.md](docs/app-store-checklist.md).

## Run locally (web)

This is the product Railway deploys. Native packaging does not replace it.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-key
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Environment variables

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key used for vision analysis |
| `OPENAI_VISION_MODEL` | No | `gpt-4o` | Must be a vision-capable model |
| `OPENAI_TIMEOUT_SECONDS` | No | `90` | How long to wait on the vision API |
| `ENABLE_DOCS` | No | off | Set `1` / `true` to expose `/docs`, `/redoc`, and `/openapi.json` |
| `PUBLIC_BASE_URL` | No | the Railway URL above | Canonical site URL for sitemap / robots |

## Railway

Start command:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Set `OPENAI_API_KEY` in Railway variables. Leave `ENABLE_DOCS` unset on the public deploy.

A `Procfile` and `nixpacks.toml` pin the same start command so the Capacitor project under `native/` is not treated as the web app.

## Native iOS / Android (Capacitor)

The app is FastAPI + static files. Checklists need `/api/analyze` and `/api/compare` (photos → our server → OpenAI), so the Capacitor WebView loads the **production URL** instead of shipping a second copy of `static/`.

| | |
| --- | --- |
| App name | Room Rescue |
| Bundle ID | `com.roomrescue.app` |
| Version | `1.0.0` (store-candidate; not submitted) |
| Shell | `native/` (`ios/`, `android/`, `capacitor.config.js`) |

**Jeff, prepare the native projects** (after the usual web `uvicorn` setup above if you want a local WebView target):

```bash
cd native
npm install
npx cap sync
```

- **iOS:** needs a Mac. `npx cap open ios` then archive in Xcode. Linux cannot sign or upload an App Store build. The `native/ios/` folder is still in git so you do not regenerate it from scratch.
- **Android:** `npx cap open android` in Android Studio. An AAB can be built on Linux or a Mac once a Play upload key exists.
- **Talk to local FastAPI** (phone and computer on one network — use the computer’s LAN IP):

```bash
cd native
CAPACITOR_SERVER_URL=http://192.168.1.20:8000 npx cap sync
```

iOS Simulator: `http://127.0.0.1:8000`. Android Emulator: `http://10.0.2.2:8000`.

Accounts, signing, screenshots, and clicking Submit are **only Jeff** — listed in [STORE.md](STORE.md).

## Privacy and terms

Plain-English privacy notes live at `/privacy`. Short terms — DIY helper, not professional advice — live at `/terms`.
