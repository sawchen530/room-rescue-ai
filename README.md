# Room Rescue

Photograph a room. Get a practical checklist for what to clean, fix, organize, or inspect — then verify the work with an after photo.

Live: [https://room-rescue-ai-production.up.railway.app](https://room-rescue-ai-production.up.railway.app)

Built for DIY homeowners. No account, no payments, no photo library.

## How it works

1. Take a before photo from an angle you can repeat.
2. Room Rescue lists what’s actually visible, with time and ordinary supplies.
3. Take an after photo from the same spot to check what’s done.

Photos are sent to our server in memory, then to OpenAI’s vision API for analysis. Large JPG/PNG/WebP shots are resized in the browser first so mobile uploads stay small; HEIC is left as-is when the phone format can’t be decoded. We do not store photos as a product feature. Checkmarks and a light progress summary stay in this browser’s local storage.

You can try the product without your own picture via **Use a sample room** (a bundled living-room photo). Privacy notes live at `/privacy`. Short terms — DIY helper, not professional advice — live at `/terms`.

## Run locally

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

## Privacy

Plain-English notes live at `/privacy`.
