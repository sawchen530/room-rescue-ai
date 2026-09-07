import base64
import json
import os
import re
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Room Rescue AI")
app.mount("/static", StaticFiles(directory="static"), name="static")

MAX_IMAGE_BYTES = 12 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
STATUS_ORDER = {
    "Not Done": 0,
    "Need Better Photo": 1,
    "Partially Done": 2,
    "Completed": 3,
}


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


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server.")
    return OpenAI(api_key=api_key)


def validate_image_upload(image: UploadFile) -> None:
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Please upload a JPG, PNG, WebP, HEIC, or HEIF image.",
        )


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
    validate_image_upload(image)
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large. Maximum size is 12 MB.")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{image.content_type};base64,{b64}"


def call_json_model(prompt: str, image_urls: List[str]) -> dict:
    client = get_client()
    content = [{"type": "input_text", "text": prompt}]
    for image_url in image_urls:
        content.append({"type": "input_image", "image_url": image_url})

    response = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-luna"),
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
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}")

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
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read original tasks: {exc}")

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
        raise HTTPException(status_code=502, detail=f"AI comparison failed: {exc}")

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
