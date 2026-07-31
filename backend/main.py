import os
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from dotenv import load_dotenv

from face_analyzer import analyze_frame
from safety_filter import analyze_message
from therapy_engine import TherapyEngine
from tts import text_to_audio

load_dotenv()

app = FastAPI(title="AI Therapist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

therapy_engine = TherapyEngine()

CRISIS_TEXT = (
    "I hear you, and I'm really glad you reached out. "
    "What you're feeling matters deeply. Please connect with someone who can help right now. "
    "You can call or text 988 — the Suicide and Crisis Lifeline — anytime, day or night. "
    "You can also text HOME to 741741 to reach the Crisis Text Line. "
    "You are not alone in this."
)
class AnalyzeFaceRequest(BaseModel):
    image: str  # base64-encoded JPEG
class ChatRequest(BaseModel):
    session_id: str
    message: str
    emotional_context: dict = {}
@app.get("/api/health")
async def health():
    return {"status": "ok"}
@app.post("/api/session/new")
async def new_session():
    session = therapy_engine.create_session()
    return {"session_id": session["session_id"]}
@app.post("/api/analyze-face")
async def analyze_face(req: AnalyzeFaceRequest):
    result = analyze_frame(req.image)
    return result
@app.post("/api/chat")
async def chat(req: ChatRequest):
    if req.session_id not in therapy_engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Safety check first — never bypass this
    safety = analyze_message(req.message)

    if safety["level"] == "CRISIS":
        audio_bytes = text_to_audio(CRISIS_TEXT)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {
            "text": CRISIS_TEXT,
            "audio": audio_b64,
            "crisis": True,
        }

    safety_injection = safety["message"] if safety["level"] == "WARNING" else ""

    reply_text = therapy_engine.get_response(
        session_id=req.session_id,
        user_message=req.message,
        emotional_context=req.emotional_context,
        safety_injection=safety_injection,
    )

    audio_bytes = text_to_audio(reply_text)
    audio_b64 = base64.b64encode(audio_bytes).decode()

    return {
        "text": reply_text,
        "audio": audio_b64,
        "crisis": False,
    }
