import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger("room_rescue")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://room-rescue-ai-production.up.railway.app",
).rstrip("/")
DEFAULT_VISION_MODEL = "gpt-4o"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_REQUEST_BYTES = 28 * 1024 * 1024
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "90"))
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "").strip().lower() in {"1", "true", "yes", "on"}

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
GENERIC_TYPES = {"", "application/octet-stream", "binary/octet-stream", "application/x-www-form-urlencoded"}
TYPE_ALIASES = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
}
EXT_TO_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}
HEIF_BRANDS = {
    b"heic",
    b"heix",
    b"hevc",
    b"hevx",
    b"heim",
    b"heis",
    b"hevm",
    b"hevs",
    b"mif1",
    b"msf1",
    b"heif",
}
STATUS_ORDER = {
    "Not Done": 0,
    "Need Better Photo": 1,
    "Partially Done": 2,
    "Completed": 3,
}

ANALYZE_FAILED_MESSAGE = "We couldn’t build a checklist from that photo. Please try again in a moment."
COMPARE_FAILED_MESSAGE = "We couldn’t compare those photos. Please try again in a moment."
TIMEOUT_MESSAGE = "The photo check took too long. Try again with a smaller or clearer photo."
CONFIG_MESSAGE = "Room Rescue isn’t ready to analyze photos right now. Please try again later."
UNSUPPORTED_IMAGE_MESSAGE = "Please upload a JPG, PNG, WebP, HEIC, or HEIF image."
TOO_LARGE_MESSAGE = "That photo is too large. Please use one under 12 MB."
REQUEST_TOO_LARGE_MESSAGE = "That upload is too large. Please use photos under 12 MB each."


def _docs_url(path: str) -> Optional[str]:
    return path if ENABLE_DOCS else None


app = FastAPI(
    title="Room Rescue",
    docs_url=_docs_url("/docs"),
    redoc_url=_docs_url("/redoc"),
    openapi_url=_docs_url("/openapi.json"),
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class Task(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    category: Literal["Cleaning", "Repair", "Organization", "Safety", "Inspection"]
    priority: Literal["High", "Medium", "Low"]
    minutes: int = Field(ge=1, le=180)
    reason: str = Field(min_length=3, max_length=300)
    confidence: Literal["High", "Medium", "Low"]
    diy_level: Literal["Easy", "Moderate", "Professional"]
    supplies: List[str] = Field(default_factory=list, max_length=8)


class Analysis(BaseModel):
    room_type: str
    summary: str
    tasks: List[Task]
    cautions: List[str] = []
    estimated_total_minutes: int


class ComparisonTask(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    status: Literal["Completed", "Partially Done", "Not Done", "Need Better Photo"]
    evidence: str = Field(min_length=3, max_length=300)
    next_step: str = Field(min_length=3, max_length=220)
    confidence: Literal["High", "Medium", "Low"]


class ComparisonDraft(BaseModel):
    summary: str
    encouragement: str
    successes: List[str] = []
    failures: List[str] = []
    task_results: List[ComparisonTask]


class ComparisonResultTask(BaseModel):
    title: str
    category: Literal["Cleaning", "Repair", "Organization", "Safety", "Inspection"]
    priority: Literal["High", "Medium", "Low"]
    status: Literal["Completed", "Partially Done", "Not Done", "Need Better Photo"]
    evidence: str
    next_step: str
    confidence: Literal["High", "Medium", "Low"]


class ComparisonResult(BaseModel):
    summary: str
    encouragement: str
    successes: List[str] = []
    failures: List[str] = []
    completed_percentage: int
    completed_tasks: int
    total_tasks: int
    remaining_tasks: List[str] = []
    task_results: List[ComparisonResultTask]
    next_action: str
    should_retake: bool


def _html(path: str, cache_control: str = "no-cache") -> FileResponse:
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": cache_control})


@app.middleware("http")
async def add_static_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if response.status_code == 200 and path.startswith("/static/"):
        if path.endswith((".html", ".webmanifest", ".json")):
            response.headers.setdefault("Cache-Control", "public, max-age=300")
        else:
            response.headers.setdefault("Cache-Control", "public, max-age=86400")
    return response


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse({"detail": REQUEST_TOO_LARGE_MESSAGE}, status_code=413)
    return await call_next(request)


@app.get("/")
def home():
    return _html("static/index.html")


@app.get("/privacy")
def privacy():
    return _html("static/privacy.html")


@app.get("/terms")
def terms():
    return _html("static/terms.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /docs\n"
        "Disallow: /redoc\n"
        "Disallow: /openapi.json\n"
        f"Sitemap: {PUBLIC_BASE_URL}/sitemap.xml\n"
    )
    return PlainTextResponse(body, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/sitemap.xml")
def sitemap():
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{PUBLIC_BASE_URL}/</loc></url>\n"
        f"  <url><loc>{PUBLIC_BASE_URL}/privacy</loc></url>\n"
        f"  <url><loc>{PUBLIC_BASE_URL}/terms</loc></url>\n"
        "</urlset>\n"
    )
    return Response(content=body, media_type="application/xml", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(
        "static/manifest.webmanifest",
        media_type="application/manifest+json",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/favicon.svg")
def favicon_svg():
    return FileResponse("static/favicon.svg", media_type="image/svg+xml")


@app.get("/favicon-32.png")
def favicon_png():
    return FileResponse("static/favicon-32.png", media_type="image/png")


@app.get("/apple-touch-icon.png")
def apple_touch_icon():
    return FileResponse("static/apple-touch-icon.png", media_type="image/png")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not configured")
        raise HTTPException(status_code=500, detail=CONFIG_MESSAGE)
    return OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT_SECONDS)


def _declared_media_type(content_type: Optional[str]) -> str:
    return (content_type or "").split(";")[0].strip().lower()


def sniff_magic(raw: bytes) -> Optional[str]:
    if len(raw) >= 3 and raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if len(raw) >= 12 and raw[4:8] == b"ftyp":
        brand = raw[8:12]
        compatible = {raw[i : i + 4] for i in range(8, len(raw) - 3, 4) if i < 96}
        if brand in HEIF_BRANDS or compatible & HEIF_BRANDS:
            return "image/heic" if brand in {b"heic", b"heix", b"hevc", b"hevx"} or b"heic" in compatible else "image/heif"
    return None


def sniff_image_media_type(filename: Optional[str], content_type: Optional[str], raw: bytes) -> str:
    magic = sniff_magic(raw)
    if magic:
        return magic

    declared = TYPE_ALIASES.get(_declared_media_type(content_type), _declared_media_type(content_type))
    if declared in ALLOWED_TYPES:
        return declared

    extension = Path(filename or "").suffix.lower()
    if extension in EXT_TO_TYPE:
        return EXT_TO_TYPE[extension]

    raise HTTPException(status_code=415, detail=UNSUPPORTED_IMAGE_MESSAGE)


def extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ValueError("The model did not return valid JSON.")
        return json.loads(match.group(0))


async def upload_to_data_url(image: UploadFile) -> str:
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=TOO_LARGE_MESSAGE)
    media_type = sniff_image_media_type(image.filename, image.content_type, raw)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{media_type};base64,{b64}"


def _is_timeout_error(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return "timeout" in name or "timed out" in str(exc).lower()


def call_json_model(prompt: str, image_urls: List[str]) -> dict:
    client = get_client()
    content = [{"type": "input_text", "text": prompt}]
    for image_url in image_urls:
        content.append({"type": "input_image", "image_url": image_url})

    response = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", DEFAULT_VISION_MODEL),
        input=[{"role": "user", "content": content}],
    )
    return extract_json(response.output_text)


@app.post("/api/analyze", response_model=Analysis)
async def analyze_room(
    image: UploadFile = File(...),
    room_hint: str = Form("Unknown"),
    time_budget: int = Form(30),
):
    time_budget = max(5, min(int(time_budget), 240))
    data_url = await upload_to_data_url(image)

    prompt = f"""
You are Room Rescue, a careful home-maintenance visual assistant.

Analyze ONE photograph of a room and create an actionable plan for cleaning,
organization, visible repairs, safety, and further inspection.

User room hint: {room_hint}
Preferred first-session time budget: {time_budget} minutes.

IMPORTANT RULES:
- Base findings only on things that are actually visible or reasonably supported by the image.
- Never claim hidden mold, structural damage, electrical faults, plumbing leaks, pests,
  asbestos, lead, or other concealed hazards are confirmed from a photo.
- If something looks suspicious but cannot be diagnosed visually, create an "Inspection"
  task and explain what to check.
- Put immediate trip, fire, sharp-object, unstable-stack, visible-water-near-electric,
  or blocked-exit concerns first.
- For electrical, structural, gas, substantial water intrusion, or hazardous-material
  concerns, recommend a qualified professional rather than detailed risky repair instructions.
- Be concrete: say what object/area to address and what action to take.
- Keep the list useful, not overwhelming: 5 to 12 tasks.
- Estimate hands-on minutes for each task.
- Use the time budget to favor tasks that could form a good first work session.
- "confidence" refers to how confident you are that the issue/action is supported by the photo.
- "diy_level" must be Easy, Moderate, or Professional.
- supplies should contain only ordinary supplies that are likely useful.

Return ONLY JSON matching this exact shape:
{{
  "room_type": "string",
  "summary": "1-3 sentence overview",
  "tasks": [
    {{
      "title": "actionable task",
      "category": "Cleaning|Repair|Organization|Safety|Inspection",
      "priority": "High|Medium|Low",
      "minutes": 10,
      "reason": "what in the image prompted this",
      "confidence": "High|Medium|Low",
      "diy_level": "Easy|Moderate|Professional",
      "supplies": ["item"]
    }}
  ],
  "cautions": ["short caution if needed"],
  "estimated_total_minutes": 60
}}
"""

    try:
        payload = call_json_model(prompt, [data_url])
        analysis = Analysis.model_validate(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("AI analysis failed")
        raise HTTPException(
            status_code=502,
            detail=TIMEOUT_MESSAGE if _is_timeout_error(exc) else ANALYZE_FAILED_MESSAGE,
        )

    rank = {"High": 0, "Medium": 1, "Low": 2}
    analysis.tasks.sort(key=lambda t: rank[t.priority])
    analysis.estimated_total_minutes = sum(t.minutes for t in analysis.tasks)
    return analysis


@app.post("/api/compare", response_model=ComparisonResult)
async def compare_room_progress(
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
    tasks_json: str = Form(...),
    room_type: str = Form("room"),
):
    try:
        parsed_tasks = json.loads(tasks_json)
        original_tasks = [Task.model_validate(item) for item in parsed_tasks]
    except Exception:
        logger.exception("Could not parse original tasks")
        raise HTTPException(
            status_code=400,
            detail="Could not read the original checklist. Make a new checklist and try again.",
        )

    if not original_tasks:
        raise HTTPException(status_code=400, detail="No original tasks were provided for comparison.")

    before_data_url = await upload_to_data_url(before_image)
    after_data_url = await upload_to_data_url(after_image)

    task_lines = []
    for idx, task in enumerate(original_tasks, start=1):
        task_lines.append(
            f"{idx}. {task.title} | category={task.category} | priority={task.priority} | reason={task.reason}"
        )

    prompt = f"""
You are Room Rescue, a strict but helpful before/after room progress evaluator.

Image 1 is the BEFORE photo.
Image 2 is the AFTER photo.
Compare the two photos for the same {room_type} and judge progress against the original task list below.

Original task list:
{chr(10).join(task_lines)}

IMPORTANT RULES:
- Base all judgments only on what is visibly supported by the two photos.
- Do not invent improvements or failures that are not visible.
- If the after photo does not clearly show the relevant area, use status "Need Better Photo".
- Allowed statuses are exactly: "Completed", "Partially Done", "Not Done", "Need Better Photo".
- Return one task result for every original task title, using the same title text.
- "successes" should highlight specific visible wins.
- "failures" should highlight specific unfinished or poorly addressed items.
- "next_step" should tell the user what to do next for that exact task.
- Be encouraging but honest.
- If anything is still unfinished, the overall guidance should clearly tell the user to finish those tasks and upload another after photo until the room is fully done.

Return ONLY JSON matching this exact shape:
{{
  "summary": "brief comparison overview",
  "encouragement": "short motivational comment",
  "successes": ["specific win"],
  "failures": ["specific unfinished item"],
  "task_results": [
    {{
      "title": "exact original task title",
      "status": "Completed|Partially Done|Not Done|Need Better Photo",
      "evidence": "what the photos show",
      "next_step": "what to do next",
      "confidence": "High|Medium|Low"
    }}
  ]
}}
"""

    try:
        payload = call_json_model(prompt, [before_data_url, after_data_url])
        draft = ComparisonDraft.model_validate(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("AI comparison failed")
        raise HTTPException(
            status_code=502,
            detail=TIMEOUT_MESSAGE if _is_timeout_error(exc) else COMPARE_FAILED_MESSAGE,
        )

    normalized = {}
    for item in draft.task_results:
        normalized[item.title.strip().lower()] = item

    merged_results: List[ComparisonResultTask] = []
    for task in original_tasks:
        found = normalized.get(task.title.strip().lower())
        if not found:
            found = ComparisonTask(
                title=task.title,
                status="Need Better Photo",
                evidence="This task could not be confidently verified from the after photo.",
                next_step="Retake the after photo so this area is visible, or complete the task if it is still unfinished.",
                confidence="Low",
            )
        merged_results.append(
            ComparisonResultTask(
                title=task.title,
                category=task.category,
                priority=task.priority,
                status=found.status,
                evidence=found.evidence,
                next_step=found.next_step,
                confidence=found.confidence,
            )
        )

    merged_results.sort(key=lambda t: (STATUS_ORDER[t.status], 0 if t.priority == "High" else 1 if t.priority == "Medium" else 2))

    total_tasks = len(merged_results)
    completed_tasks = sum(1 for item in merged_results if item.status == "Completed")
    remaining_tasks = [item.title for item in merged_results if item.status != "Completed"]
    completed_percentage = round((completed_tasks / total_tasks) * 100) if total_tasks else 0
    should_retake = bool(remaining_tasks)

    if should_retake:
        next_action = (
            "Complete the remaining tasks, make sure the unfinished areas are clearly visible, "
            "and upload another after photo until your completed percentage reaches 100%."
        )
    else:
        next_action = "Everything looks complete. Great work — this room appears fully done."

    return ComparisonResult(
        summary=draft.summary,
        encouragement=draft.encouragement,
        successes=draft.successes,
        failures=draft.failures,
        completed_percentage=completed_percentage,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        remaining_tasks=remaining_tasks,
        task_results=merged_results,
        next_action=next_action,
        should_retake=should_retake,
    )
