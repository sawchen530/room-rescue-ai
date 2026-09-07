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

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

def extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ValueError("The model did not return valid JSON.")
        return json.loads(match.group(0))

@app.post("/api/analyze", response_model=Analysis)
async def analyze_room(
    image: UploadFile = File(...),
    room_hint: str = Form("Unknown"),
    time_budget: int = Form(30),
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server.")

    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Please upload a JPG, PNG, WebP, HEIC, or HEIF image.")

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large. Maximum size is 12 MB.")

    time_budget = max(5, min(int(time_budget), 240))
    b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{image.content_type};base64,{b64}"

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
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-luna"),
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
        payload = extract_json(response.output_text)
        analysis = Analysis.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}")

    rank = {"High": 0, "Medium": 1, "Low": 2}
    analysis.tasks.sort(key=lambda t: rank[t.priority])
    analysis.estimated_total_minutes = sum(t.minutes for t in analysis.tasks)
    return analysis
