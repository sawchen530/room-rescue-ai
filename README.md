# Room Rescue AI

Mobile-friendly room photo analysis app. Upload or take a photo of a room and receive AI-generated cleaning, repair, organization, safety, and inspection tasks.

## Environment variables

- `OPENAI_API_KEY` — required
- `OPENAI_VISION_MODEL` — optional, defaults to `gpt-5.6-luna`

## Railway start command

`uvicorn app:app --host 0.0.0.0 --port $PORT`
