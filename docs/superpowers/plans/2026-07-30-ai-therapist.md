# AI Therapist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack AI therapist web app with real-time facial emotion detection, a Gemini-powered therapy engine, voice I/O, and a 3D animated avatar.

**Architecture:** React frontend (Vercel) communicates with a FastAPI backend (Render) via REST. The backend runs DeepFace + MediaPipe for facial analysis, Google Gemini 2.0 Flash for therapy responses, and gTTS for text-to-speech. The frontend renders a Ready Player Me 3D avatar that lip-syncs to audio using the Web Audio API.

**Tech Stack:** Python 3.11, FastAPI, DeepFace, MediaPipe, google-generativeai, gTTS, React 18, Vite, Tailwind CSS, shadcn/ui, Framer Motion, React Three Fiber, @react-three/drei

## Global Constraints

- Python 3.11+
- Node 20+
- All backend routes prefixed with `/api`
- CORS allows `http://localhost:5173` in dev and the Vercel domain in prod
- `GEMINI_API_KEY` stored in `backend/.env`, never committed
- `VITE_API_URL` stored in `frontend/.env`, never committed
- Crisis responses NEVER go through Gemini — hardcoded only
- Avatar GLB file stored at `frontend/public/avatar.glb`

---

## File Map

### Backend (`backend/`)
| File | Responsibility |
|---|---|
| `main.py` | FastAPI app, routes, CORS |
| `face_analyzer.py` | DeepFace emotion detection + MediaPipe gaze estimation |
| `safety_filter.py` | Crisis/warning detection before Gemini |
| `therapy_engine.py` | Gemini integration, session memory, style switching |
| `tts.py` | Convert text to audio bytes with gTTS |
| `requirements.txt` | All Python dependencies |
| `tests/test_safety_filter.py` | Safety filter unit tests |
| `tests/test_therapy_engine.py` | Therapy engine unit tests |
| `tests/test_face_analyzer.py` | Face analyzer unit tests |
| `tests/test_api.py` | FastAPI integration tests |

### Frontend (`frontend/src/`)
| File | Responsibility |
|---|---|
| `App.jsx` | React Router setup, two routes: `/` and `/session` |
| `lib/api.js` | Axios API client, all backend calls |
| `pages/Welcome.jsx` | Disclaimer screen, Begin Session button |
| `pages/Session.jsx` | Main session screen, wires all components together |
| `components/WebcamFeed.jsx` | Webcam video + emotion badge display |
| `components/ChatWindow.jsx` | Scrollable message bubbles |
| `components/VoiceInput.jsx` | Mic button + text input + send |
| `components/Avatar.jsx` | 3D RPM avatar with lip sync |
| `components/CrisisCard.jsx` | Full-screen crisis overlay with hotlines |
| `hooks/useWebcam.js` | Webcam stream, frame capture, polling backend |
| `hooks/useSpeech.js` | Web Speech API voice input |

---

## Task 1: Backend Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/tests/__init__.py`

**Interfaces:**
- Produces: Python environment ready to run FastAPI

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
deepface==0.0.93
opencv-python-headless==4.10.0.84
mediapipe==0.10.14
google-generativeai==0.7.2
gTTS==2.5.1
python-dotenv==1.0.1
pytest==8.2.2
httpx==0.27.0
```

Save to `backend/requirements.txt`.

- [ ] **Step 2: Create .env.example**

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Save to `backend/.env.example`. Copy to `backend/.env` and fill in your key.

- [ ] **Step 3: Create .gitignore at project root**

```
# Python
backend/.env
backend/__pycache__/
backend/.pytest_cache/
backend/*.egg-info/

# Node
frontend/node_modules/
frontend/dist/
frontend/.env

# OS
.DS_Store
```

Save to `ai-therapist/.gitignore`.

- [ ] **Step 4: Create tests package**

Create empty file `backend/tests/__init__.py`.

- [ ] **Step 5: Install dependencies**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Expected: all packages install without errors. DeepFace will download model weights (~600MB) on first use — this is normal.

- [ ] **Step 6: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add backend/ .gitignore
git commit -m "feat: add backend project setup and dependencies"
```

---

## Task 2: FastAPI Application Skeleton

**Files:**
- Create: `backend/main.py`

**Interfaces:**
- Produces: `GET /api/health` → `{"status": "ok"}`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source venv/bin/activate
pytest tests/test_api.py::test_health_check -v
```

Expected: `FAILED` — `ImportError: cannot import name 'app' from 'main'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/main.py`:

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py::test_health_check -v
```

Expected: `PASSED`

- [ ] **Step 5: Manually verify the server runs**

```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` in your browser. Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py
git commit -m "feat: add FastAPI skeleton with health check and CORS"
```

---

## Task 3: Safety Filter Module

**Files:**
- Create: `backend/safety_filter.py`
- Modify: `backend/tests/test_safety_filter.py`

**Interfaces:**
- Produces: `analyze_message(text: str) -> dict`
  - Returns: `{"level": "SAFE" | "WARNING" | "CRISIS", "message": str}`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_safety_filter.py`:

```python
from safety_filter import analyze_message


def test_crisis_suicidal_ideation():
    result = analyze_message("I want to kill myself")
    assert result["level"] == "CRISIS"


def test_crisis_self_harm():
    result = analyze_message("I've been cutting myself lately")
    assert result["level"] == "CRISIS"


def test_crisis_end_it():
    result = analyze_message("I just want to end it all")
    assert result["level"] == "CRISIS"


def test_warning_hopeless():
    result = analyze_message("I just can't go on anymore, everything feels hopeless")
    assert result["level"] == "WARNING"


def test_warning_cant_cope():
    result = analyze_message("I don't know how to cope with this")
    assert result["level"] == "WARNING"


def test_safe_message():
    result = analyze_message("I've been feeling stressed at work lately")
    assert result["level"] == "SAFE"


def test_safe_empty():
    result = analyze_message("")
    assert result["level"] == "SAFE"


def test_result_has_message_key():
    result = analyze_message("hello")
    assert "message" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_safety_filter.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'safety_filter'`

- [ ] **Step 3: Implement safety_filter.py**

Create `backend/safety_filter.py`:

```python
import re

CRISIS_PATTERNS = [
    r"\bkill\s+(my)?self\b",
    r"\bend\s+(it|my life|everything)\b",
    r"\bsuicid(e|al)\b",
    r"\bwant to die\b",
    r"\bnot worth living\b",
    r"\b(cutting|cut)\s+my(self)?\b",
    r"\bhurt(ing)?\s+my(self)?\b",
    r"\bself.harm\b",
    r"\boverdos(e|ing)\b",
    r"\bhang\s+my(self)?\b",
]

WARNING_PATTERNS = [
    r"\bcan'?t\s+go on\b",
    r"\bcan'?t\s+cope\b",
    r"\bhopeless\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bno\s+point\b",
    r"\bgive\s+up\b",
    r"\bdon'?t\s+want\s+to\s+be\s+here\b",
    r"\bwish\s+I\s+(was|were)\s+dead\b",
    r"\bnumb(ness)?\b",
    r"\bcan'?t\s+take\s+it\b",
]

CRISIS_RESPONSE = (
    "I hear you, and I'm really glad you reached out. "
    "What you're feeling matters deeply. Please connect with someone who can help right now."
)

WARNING_INJECTION = (
    "[SAFETY FLAG: User showing distress signals. "
    "Validate feelings only. Do NOT offer solutions or advice. "
    "Gently remind them that professional support is available.]"
)


def analyze_message(text: str) -> dict:
    lowered = text.lower()

    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, lowered):
            return {"level": "CRISIS", "message": CRISIS_RESPONSE}

    for pattern in WARNING_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "level": "WARNING",
                "message": WARNING_INJECTION,
            }

    return {"level": "SAFE", "message": ""}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_safety_filter.py -v
```

Expected: all 8 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/safety_filter.py backend/tests/test_safety_filter.py
git commit -m "feat: add safety filter with crisis and warning detection"
```

---

## Task 4: Face Analyzer Module

**Files:**
- Create: `backend/face_analyzer.py`
- Create: `backend/tests/test_face_analyzer.py`

**Interfaces:**
- Produces: `analyze_frame(image_base64: str) -> dict`
  - Returns:
    ```json
    {
      "dominant_emotion": "sad",
      "emotion_intensity": 0.78,
      "eye_contact": "low" | "moderate" | "direct",
      "head_position": "forward" | "tilted_down" | "tilted_up" | "turned",
      "engagement_level": "engaged" | "moderate" | "withdrawn",
      "face_detected": true
    }
    ```

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_face_analyzer.py`:

```python
import base64
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from face_analyzer import analyze_frame, _compute_engagement, _smooth_emotion


def _make_blank_frame_b64():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf).decode()


def test_no_face_returns_defaults():
    b64 = _make_blank_frame_b64()
    with patch("face_analyzer.DeepFace.analyze", side_effect=Exception("No face")):
        result = analyze_frame(b64)
    assert result["face_detected"] is False
    assert result["dominant_emotion"] == "neutral"
    assert result["emotion_intensity"] == 0.0


def test_compute_engagement_high_contact():
    level = _compute_engagement("direct", "forward")
    assert level == "engaged"


def test_compute_engagement_low_contact():
    level = _compute_engagement("low", "tilted_down")
    assert level == "withdrawn"


def test_compute_engagement_moderate():
    level = _compute_engagement("moderate", "forward")
    assert level == "moderate"


def test_smooth_emotion_rolling_average():
    history = [80.0, 70.0, 90.0, 60.0, 75.0]
    result = _smooth_emotion(history)
    assert abs(result - 0.75) < 0.01


def test_analyze_frame_with_mocked_deepface():
    b64 = _make_blank_frame_b64()
    mock_result = [{
        "dominant_emotion": "happy",
        "emotion": {
            "angry": 1.0, "disgust": 0.5, "fear": 0.5,
            "happy": 85.0, "sad": 5.0, "surprise": 3.0, "neutral": 5.0
        },
        "region": {"x": 100, "y": 50, "w": 200, "h": 200}
    }]
    with patch("face_analyzer.DeepFace.analyze", return_value=mock_result):
        with patch("face_analyzer._estimate_gaze", return_value=("direct", "forward")):
            result = analyze_frame(b64)
    assert result["face_detected"] is True
    assert result["dominant_emotion"] == "happy"
    assert result["emotion_intensity"] > 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_face_analyzer.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'face_analyzer'`

- [ ] **Step 3: Implement face_analyzer.py**

Create `backend/face_analyzer.py`:

```python
import base64
from collections import deque
import numpy as np
import cv2
from deepface import DeepFace
import mediapipe as mp

# Rolling history for smoothing — last 5 frames
_emotion_history: deque = deque(maxlen=5)

mp_face_mesh = mp.solutions.face_mesh
_face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,  # enables iris landmarks
    min_detection_confidence=0.5,
)

# MediaPipe iris landmark indices
_LEFT_IRIS = [468, 469, 470, 471, 472]
_RIGHT_IRIS = [473, 474, 475, 476, 477]
_LEFT_EYE_CORNERS = [33, 133]
_RIGHT_EYE_CORNERS = [362, 263]


def _decode_image(image_base64: str) -> np.ndarray:
    img_bytes = base64.b64decode(image_base64)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _estimate_gaze(img_rgb: np.ndarray) -> tuple[str, str]:
    """Return (eye_contact, head_position) using MediaPipe FaceMesh."""
    results = _face_mesh.process(img_rgb)
    if not results.multi_face_landmarks:
        return "low", "forward"

    landmarks = results.multi_face_landmarks[0].landmark
    h, w = img_rgb.shape[:2]

    def lm(idx):
        return np.array([landmarks[idx].x * w, landmarks[idx].y * h])

    # Gaze: how centered iris is within eye horizontally
    left_center = np.mean([lm(i) for i in _LEFT_IRIS], axis=0)
    left_inner, left_outer = lm(_LEFT_EYE_CORNERS[0]), lm(_LEFT_EYE_CORNERS[1])
    left_eye_w = abs(left_outer[0] - left_inner[0])
    left_ratio = (left_center[0] - left_inner[0]) / (left_eye_w + 1e-6)

    right_center = np.mean([lm(i) for i in _RIGHT_IRIS], axis=0)
    right_inner, right_outer = lm(_RIGHT_EYE_CORNERS[0]), lm(_RIGHT_EYE_CORNERS[1])
    right_eye_w = abs(right_outer[0] - right_inner[0])
    right_ratio = (right_center[0] - right_inner[0]) / (right_eye_w + 1e-6)

    avg_ratio = (left_ratio + right_ratio) / 2.0
    centered = 0.3 < avg_ratio < 0.7

    if centered:
        eye_contact = "direct"
    elif 0.2 < avg_ratio < 0.8:
        eye_contact = "moderate"
    else:
        eye_contact = "low"

    # Head pitch: compare nose tip (1) to midpoint between eyes (168)
    nose_tip_y = landmarks[1].y
    eye_mid_y = (landmarks[33].y + landmarks[362].y) / 2
    pitch = nose_tip_y - eye_mid_y

    if pitch > 0.15:
        head_position = "tilted_down"
    elif pitch < -0.05:
        head_position = "tilted_up"
    else:
        head_position = "forward"

    return eye_contact, head_position


def _smooth_emotion(history: list[float]) -> float:
    if not history:
        return 0.0
    return sum(history) / (len(history) * 100.0)


def _compute_engagement(eye_contact: str, head_position: str) -> str:
    if eye_contact == "direct" and head_position in ("forward", "tilted_up"):
        return "engaged"
    if eye_contact == "low" or head_position == "tilted_down":
        return "withdrawn"
    return "moderate"


def analyze_frame(image_base64: str) -> dict:
    """Analyze a base64-encoded JPEG frame and return emotional context."""
    img_bgr = _decode_image(image_base64)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    try:
        results = DeepFace.analyze(
            img_path=img_bgr,
            actions=["emotion"],
            enforce_detection=True,
            silent=True,
        )
        face_data = results[0]
        dominant = face_data["dominant_emotion"]
        dominant_score = face_data["emotion"][dominant]

        _emotion_history.append(dominant_score)
        intensity = _smooth_emotion(list(_emotion_history))

        eye_contact, head_position = _estimate_gaze(img_rgb)
        engagement = _compute_engagement(eye_contact, head_position)

        return {
            "face_detected": True,
            "dominant_emotion": dominant,
            "emotion_intensity": round(intensity, 2),
            "eye_contact": eye_contact,
            "head_position": head_position,
            "engagement_level": engagement,
        }

    except Exception:
        return {
            "face_detected": False,
            "dominant_emotion": "neutral",
            "emotion_intensity": 0.0,
            "eye_contact": "low",
            "head_position": "forward",
            "engagement_level": "moderate",
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_face_analyzer.py -v
```

Expected: all 6 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/face_analyzer.py backend/tests/test_face_analyzer.py
git commit -m "feat: add face analyzer with DeepFace emotion detection and MediaPipe gaze"
```

---

## Task 5: Therapy Engine (Gemini + Session Memory)

**Files:**
- Create: `backend/therapy_engine.py`
- Create: `backend/tests/test_therapy_engine.py`

**Interfaces:**
- Consumes: `analyze_message(text)` from `safety_filter.py`
- Produces:
  - `create_session() -> dict` — `{"session_id": str, "current_style": str}`
  - `get_response(session_id: str, user_message: str, emotional_context: dict) -> str`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_therapy_engine.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from therapy_engine import TherapyEngine


@pytest.fixture
def engine():
    return TherapyEngine()


def test_create_session(engine):
    session = engine.create_session()
    assert "session_id" in session
    assert session["current_style"] == "active_listening"
    assert session["emotional_arc"] == []


def test_session_stored_after_creation(engine):
    session = engine.create_session()
    sid = session["session_id"]
    assert sid in engine.sessions


def test_get_response_returns_string(engine):
    session = engine.create_session()
    sid = session["session_id"]
    emotional_ctx = {
        "dominant_emotion": "sad",
        "emotion_intensity": 0.6,
        "eye_contact": "low",
        "engagement_level": "withdrawn",
    }
    mock_response = MagicMock()
    mock_response.text = "I hear that you're feeling sad. Would you like to talk about it?"

    with patch.object(engine.model, "generate_content", return_value=mock_response):
        result = engine.get_response(sid, "I feel really sad today", emotional_ctx)

    assert isinstance(result, str)
    assert len(result) > 0


def test_style_switches_to_cbt_on_negative_belief(engine):
    session = engine.create_session()
    sid = session["session_id"]
    emotional_ctx = {"dominant_emotion": "sad", "emotion_intensity": 0.5,
                     "eye_contact": "moderate", "engagement_level": "moderate"}

    mock_response = MagicMock()
    mock_response.text = "That sounds really difficult."

    with patch.object(engine.model, "generate_content", return_value=mock_response):
        engine.get_response(sid, "I'm completely worthless", emotional_ctx)

    assert engine.sessions[sid]["current_style"] == "cbt"


def test_emotional_arc_updated(engine):
    session = engine.create_session()
    sid = session["session_id"]
    emotional_ctx = {"dominant_emotion": "fearful", "emotion_intensity": 0.7,
                     "eye_contact": "low", "engagement_level": "withdrawn"}

    mock_response = MagicMock()
    mock_response.text = "I'm here with you."

    with patch.object(engine.model, "generate_content", return_value=mock_response):
        engine.get_response(sid, "I'm scared", emotional_ctx)

    assert "fearful" in engine.sessions[sid]["emotional_arc"]


def test_unknown_session_raises(engine):
    with pytest.raises(KeyError):
        engine.get_response("nonexistent", "hello", {})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_therapy_engine.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'therapy_engine'`

- [ ] **Step 3: Implement therapy_engine.py**

Create `backend/therapy_engine.py`:

```python
import os
import uuid
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

STYLE_DESCRIPTIONS = {
    "active_listening": (
        "You listen deeply, reflect feelings back, and ask open-ended questions. "
        "You never rush to solutions. You validate before advising."
    ),
    "cbt": (
        "You gently challenge negative automatic thoughts using Cognitive Behavioral Therapy. "
        "You help the user examine evidence for and against their beliefs. "
        "You are warm but you do not let harmful beliefs go unchallenged."
    ),
    "solution_focused": (
        "The user has asked for practical guidance. You offer concrete, compassionate suggestions "
        "while still validating their feelings. You focus on what they can control."
    ),
}

NEGATIVE_BELIEF_PHRASES = [
    "i'm worthless", "i'm a failure", "nobody cares",
    "i'm useless", "i hate myself", "i'm stupid",
    "i'm a burden", "i ruin everything", "i can't do anything right",
]

ADVICE_REQUEST_PHRASES = [
    "what should i do", "what do you think i should",
    "give me advice", "how do i", "can you help me figure out",
]

SYSTEM_PROMPT_TEMPLATE = """You are a compassionate AI therapist named Mira.
Your current therapeutic style: {style}
{style_description}

User's current emotional state:
- Dominant emotion: {dominant_emotion} (intensity: {intensity_label})
- Eye contact: {eye_contact}
- Engagement level: {engagement_level}

Emotional arc this session: {emotional_arc}
Topics discussed: {topics}

RULES:
- Never diagnose any condition.
- Never replace professional mental health care.
- Always end responses with one open-ended question or gentle reflection.
- Keep responses under 4 sentences unless the user needs more.
- If the user seems to be in distress, slow down and hold space.
- You may gently mention that a therapist or counselor can provide deeper support.
{safety_injection}"""


def _intensity_label(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "moderate"
    return "mild"


def _detect_style(message: str, current_style: str) -> str:
    lowered = message.lower()
    if any(p in lowered for p in NEGATIVE_BELIEF_PHRASES):
        return "cbt"
    if any(p in lowered for p in ADVICE_REQUEST_PHRASES):
        return "solution_focused"
    return current_style


class TherapyEngine:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.sessions: dict[str, dict] = {}

    def create_session(self) -> dict:
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "history": [],
            "emotional_arc": [],
            "current_style": "active_listening",
            "topics_mentioned": [],
            "intensity_trend": "stable",
            "high_intensity_turns": 0,
        }
        self.sessions[session_id] = session
        return {"session_id": session_id, "current_style": "active_listening"}

    def get_response(
        self,
        session_id: str,
        user_message: str,
        emotional_context: dict,
        safety_injection: str = "",
    ) -> str:
        session = self.sessions[session_id]  # raises KeyError if not found

        # Update style
        new_style = _detect_style(user_message, session["current_style"])

        # Track high-intensity turns to decide whether to stay in active_listening
        intensity = emotional_context.get("emotion_intensity", 0.0)
        if intensity >= 0.6:
            session["high_intensity_turns"] += 1
        else:
            session["high_intensity_turns"] = 0

        if session["high_intensity_turns"] >= 3:
            new_style = "active_listening"

        session["current_style"] = new_style

        # Update emotional arc
        emotion = emotional_context.get("dominant_emotion", "neutral")
        session["emotional_arc"].append(emotion)

        arc_str = " → ".join(session["emotional_arc"][-6:]) if session["emotional_arc"] else "none yet"
        topics_str = ", ".join(session["topics_mentioned"]) if session["topics_mentioned"] else "none yet"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            style=new_style,
            style_description=STYLE_DESCRIPTIONS[new_style],
            dominant_emotion=emotion,
            intensity_label=_intensity_label(intensity),
            eye_contact=emotional_context.get("eye_contact", "unknown"),
            engagement_level=emotional_context.get("engagement_level", "unknown"),
            emotional_arc=arc_str,
            topics=topics_str,
            safety_injection=safety_injection,
        )

        # Build conversation for Gemini
        history_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Mira'}: {m['content']}"
            for m in session["history"][-10:]
        )
        full_prompt = f"{system_prompt}\n\n{history_text}\nUser: {user_message}\nMira:"

        response = self.model.generate_content(full_prompt)
        reply = response.text.strip()

        # Update history
        session["history"].append({"role": "user", "content": user_message})
        session["history"].append({"role": "assistant", "content": reply})

        return reply
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_therapy_engine.py -v
```

Expected: all 6 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/therapy_engine.py backend/tests/test_therapy_engine.py
git commit -m "feat: add therapy engine with Gemini integration and session memory"
```

---

## Task 6: TTS Module + API Endpoints

**Files:**
- Create: `backend/tts.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `analyze_frame()`, `analyze_message()`, `TherapyEngine`
- Produces:
  - `text_to_audio(text: str) -> bytes` — MP3 bytes
  - `POST /api/session/new` → `{"session_id": str}`
  - `POST /api/analyze-face` body: `{"image": str}` → emotional context dict
  - `POST /api/chat` body: `{"session_id": str, "message": str, "emotional_context": dict}` → `{"text": str, "audio": str, "crisis": bool}`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_new_session_returns_session_id():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/session/new")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


@pytest.mark.asyncio
async def test_chat_safe_message():
    # First create a session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        session_resp = await client.post("/api/session/new")
        session_id = session_resp.json()["session_id"]

        mock_text = "I hear you. Tell me more about how you're feeling."
        mock_audio = b"fake_audio_bytes"

        with patch("main.therapy_engine.get_response", return_value=mock_text):
            with patch("main.text_to_audio", return_value=mock_audio):
                response = await client.post("/api/chat", json={
                    "session_id": session_id,
                    "message": "I feel stressed",
                    "emotional_context": {
                        "dominant_emotion": "sad",
                        "emotion_intensity": 0.4,
                        "eye_contact": "moderate",
                        "engagement_level": "moderate",
                    }
                })

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "audio" in data
    assert data["crisis"] is False


@pytest.mark.asyncio
async def test_chat_crisis_message_bypasses_gemini():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        session_resp = await client.post("/api/session/new")
        session_id = session_resp.json()["session_id"]

        mock_audio = b"fake_audio_bytes"
        with patch("main.text_to_audio", return_value=mock_audio):
            response = await client.post("/api/chat", json={
                "session_id": session_id,
                "message": "I want to kill myself",
                "emotional_context": {}
            })

    assert response.status_code == 200
    data = response.json()
    assert data["crisis"] is True
    assert "988" in data["text"] or "Crisis" in data["text"] or "reach out" in data["text"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```

Expected: health check `PASSED`, others `FAILED` — routes don't exist yet

- [ ] **Step 3: Create tts.py**

Create `backend/tts.py`:

```python
import io
from gtts import gTTS


def text_to_audio(text: str) -> bytes:
    """Convert text to MP3 audio bytes using gTTS."""
    tts = gTTS(text=text, lang="en", slow=False)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()
```

- [ ] **Step 4: Update main.py with all routes**

Replace `backend/main.py` with:

```python
import os
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/tts.py backend/main.py backend/tests/test_api.py
git commit -m "feat: add TTS module and all API endpoints with crisis bypass"
```

---

## Task 7: Frontend Project Setup

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/index.css`
- Create: `frontend/.env.example`

**Interfaces:**
- Produces: React app running at `http://localhost:5173`

- [ ] **Step 1: Scaffold React app with Vite**

```bash
cd /Users/Alex/Documents/ai-therapist
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

- [ ] **Step 2: Install all dependencies**

```bash
npm install react-router-dom axios framer-motion \
  @react-three/fiber @react-three/drei three \
  @radix-ui/react-dialog @radix-ui/react-slot \
  class-variance-authority clsx tailwind-merge lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: Configure Tailwind**

Replace `frontend/tailwind.config.js` with:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 4: Set up global CSS**

Replace `frontend/src/index.css` with:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-slate-950 text-slate-100 font-sans;
}
```

- [ ] **Step 5: Create .env.example**

```
VITE_API_URL=http://localhost:8000
```

Save to `frontend/.env.example`. Copy to `frontend/.env`.

- [ ] **Step 6: Verify dev server starts**

```bash
npm run dev
```

Expected: server starts at `http://localhost:5173` with default Vite React page.

- [ ] **Step 7: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/
git commit -m "feat: scaffold React frontend with Vite, Tailwind, and all dependencies"
```

---

## Task 8: API Client + App Routing

**Files:**
- Create: `frontend/src/lib/api.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/main.jsx`

**Interfaces:**
- Produces:
  - `api.newSession() -> {session_id}`
  - `api.analyzeFrame(base64) -> emotional_context`
  - `api.chat(session_id, message, emotional_context) -> {text, audio, crisis}`
  - Routes: `/` → Welcome, `/session` → Session

- [ ] **Step 1: Create API client**

Create `frontend/src/lib/api.js`:

```js
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: BASE })

export const api = {
  async newSession() {
    const { data } = await client.post('/api/session/new')
    return data // { session_id }
  },

  async analyzeFrame(imageBase64) {
    const { data } = await client.post('/api/analyze-face', {
      image: imageBase64,
    })
    return data // emotional context
  },

  async chat(sessionId, message, emotionalContext = {}) {
    const { data } = await client.post('/api/chat', {
      session_id: sessionId,
      message,
      emotional_context: emotionalContext,
    })
    return data // { text, audio, crisis }
  },
}
```

- [ ] **Step 2: Set up React Router in main.jsx**

Replace `frontend/src/main.jsx` with:

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
```

- [ ] **Step 3: Set up routes in App.jsx**

Replace `frontend/src/App.jsx` with:

```jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Session from './pages/Session'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/session" element={<Session />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
```

- [ ] **Step 4: Create placeholder pages so routing works**

Create `frontend/src/pages/Welcome.jsx`:

```jsx
export default function Welcome() {
  return <div className="text-white p-8">Welcome — coming in next task</div>
}
```

Create `frontend/src/pages/Session.jsx`:

```jsx
export default function Session() {
  return <div className="text-white p-8">Session — coming soon</div>
}
```

- [ ] **Step 5: Verify routing works**

```bash
cd frontend && npm run dev
```

Visit `http://localhost:5173` → sees "Welcome" text.
Visit `http://localhost:5173/session` → sees "Session" text.
Visit `http://localhost:5173/unknown` → redirects to `/`.

- [ ] **Step 6: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/
git commit -m "feat: add API client and React Router with Welcome and Session routes"
```

---

## Task 9: Welcome Page

**Files:**
- Modify: `frontend/src/pages/Welcome.jsx`

**Interfaces:**
- Consumes: `api.newSession()`
- Produces: Navigates to `/session?sid=<session_id>` on click

- [ ] **Step 1: Implement Welcome.jsx**

Replace `frontend/src/pages/Welcome.jsx` with:

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../lib/api'

export default function Welcome() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleBegin() {
    setLoading(true)
    setError(null)
    try {
      const { session_id } = await api.newSession()
      navigate(`/session?sid=${session_id}`)
    } catch {
      setError('Could not connect to the server. Make sure the backend is running.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-slate-950">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-lg w-full text-center space-y-8"
      >
        {/* Logo / Title */}
        <div className="space-y-2">
          <h1 className="text-5xl font-bold text-brand-500 tracking-tight">
            MindMirror
          </h1>
          <p className="text-slate-400 text-lg">
            An AI companion that sees how you feel
          </p>
        </div>

        {/* Disclaimer Card */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 text-left space-y-3">
          <h2 className="text-amber-400 font-semibold text-sm uppercase tracking-wider">
            Important Notice
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            MindMirror is an AI tool for emotional support and reflection only.
            It is <strong className="text-white">not a substitute</strong> for
            professional mental health care, diagnosis, or treatment.
          </p>
          <p className="text-slate-300 text-sm leading-relaxed">
            If you are in crisis or feel you may harm yourself or others, please
            call or text{' '}
            <a href="tel:988" className="text-brand-500 font-bold hover:underline">
              988
            </a>{' '}
            (Suicide &amp; Crisis Lifeline) immediately.
          </p>
        </div>

        {/* Begin Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleBegin}
          disabled={loading}
          className="w-full py-4 rounded-2xl bg-brand-600 hover:bg-brand-500
                     text-white font-semibold text-lg transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting session…' : 'Begin Session'}
        </motion.button>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <p className="text-slate-600 text-xs">
          By continuing you acknowledge the above notice.
        </p>
      </motion.div>
    </div>
  )
}
```

- [ ] **Step 2: Verify the page looks correct**

Make sure the backend is running (`uvicorn main:app --reload --port 8000`), then start the frontend (`npm run dev`) and visit `http://localhost:5173`. You should see the MindMirror welcome screen with the disclaimer and a "Begin Session" button. Clicking it should redirect to `/session?sid=<uuid>`.

- [ ] **Step 3: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/pages/Welcome.jsx
git commit -m "feat: add Welcome page with disclaimer and session initialization"
```

---

## Task 10: Webcam Feed Component + useWebcam Hook

**Files:**
- Create: `frontend/src/hooks/useWebcam.js`
- Create: `frontend/src/components/WebcamFeed.jsx`

**Interfaces:**
- Produces:
  - `useWebcam(onEmotionUpdate, intervalMs)` — starts webcam, polls backend every `intervalMs`
  - `<WebcamFeed emotionContext={...} />` — renders video + emotion badge

- [ ] **Step 1: Create useWebcam.js**

Create `frontend/src/hooks/useWebcam.js`:

```js
import { useEffect, useRef, useCallback } from 'react'
import { api } from '../lib/api'

export function useWebcam(onEmotionUpdate, intervalMs = 2000) {
  const videoRef = useRef(null)
  const canvasRef = useRef(document.createElement('canvas'))
  const streamRef = useRef(null)
  const intervalRef = useRef(null)

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || video.readyState < 2) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)

    // Remove the "data:image/jpeg;base64," prefix
    const base64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]
    api.analyzeFrame(base64)
      .then(onEmotionUpdate)
      .catch(() => {}) // silently ignore analysis errors
  }, [onEmotionUpdate])

  useEffect(() => {
    let active = true

    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        if (!active) { stream.getTracks().forEach(t => t.stop()); return }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch(console.error)

    intervalRef.current = setInterval(captureFrame, intervalMs)

    return () => {
      active = false
      clearInterval(intervalRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [captureFrame, intervalMs])

  return videoRef
}
```

- [ ] **Step 2: Create WebcamFeed.jsx**

Create `frontend/src/components/WebcamFeed.jsx`:

```jsx
const EMOTION_EMOJI = {
  happy: '😊', sad: '😔', angry: '😠', fearful: '😨',
  disgusted: '🤢', surprised: '😲', neutral: '😐',
}

const INTENSITY_COLOR = {
  high: 'text-red-400',
  moderate: 'text-amber-400',
  mild: 'text-green-400',
}

function intensityLabel(score) {
  if (score >= 0.6) return 'high'
  if (score >= 0.3) return 'moderate'
  return 'mild'
}

export default function WebcamFeed({ videoRef, emotionContext }) {
  const emotion = emotionContext?.dominant_emotion || 'neutral'
  const intensity = emotionContext?.emotion_intensity || 0
  const eyeContact = emotionContext?.eye_contact || '—'
  const label = intensityLabel(intensity)

  return (
    <div className="flex flex-col gap-3">
      {/* Video */}
      <div className="relative rounded-2xl overflow-hidden bg-slate-800 aspect-video">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover scale-x-[-1]" // mirror effect
        />
        {!emotionContext?.face_detected && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-500 text-sm">No face detected</p>
          </div>
        )}
      </div>

      {/* Emotion Badge */}
      <div className="bg-slate-800 rounded-xl p-3 grid grid-cols-2 gap-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{EMOTION_EMOJI[emotion] || '😐'}</span>
          <div>
            <p className="text-slate-400 text-xs">Emotion</p>
            <p className={`font-semibold capitalize ${INTENSITY_COLOR[label]}`}>
              {emotion} ({label})
            </p>
          </div>
        </div>
        <div>
          <p className="text-slate-400 text-xs">Eye contact</p>
          <p className="font-semibold capitalize text-slate-200">{eyeContact}</p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Verify components exist and have no syntax errors**

```bash
cd frontend && npm run build
```

Expected: build succeeds (even though the components aren't wired into a page yet).

- [ ] **Step 4: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/hooks/useWebcam.js frontend/src/components/WebcamFeed.jsx
git commit -m "feat: add webcam hook and WebcamFeed component with emotion badge"
```

---

## Task 11: Chat Window + Voice Input

**Files:**
- Create: `frontend/src/components/ChatWindow.jsx`
- Create: `frontend/src/components/VoiceInput.jsx`
- Create: `frontend/src/hooks/useSpeech.js`

**Interfaces:**
- Produces:
  - `<ChatWindow messages={[{role, content}]} />` — scrollable bubble list
  - `<VoiceInput onSend={fn} disabled={bool} />` — mic + text input + send
  - `useSpeech(onTranscript)` — Web Speech API voice input hook

- [ ] **Step 1: Create useSpeech.js**

Create `frontend/src/hooks/useSpeech.js`:

```js
import { useRef, useState } from 'react'

export function useSpeech(onTranscript) {
  const recognitionRef = useRef(null)
  const [listening, setListening] = useState(false)

  function start() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Your browser does not support voice input. Please use Chrome.')
      return
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      onTranscript(transcript)
    }
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stop() {
    recognitionRef.current?.stop()
    setListening(false)
  }

  return { listening, start, stop }
}
```

- [ ] **Step 2: Create ChatWindow.jsx**

Create `frontend/src/components/ChatWindow.jsx`:

```jsx
import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ChatWindow({ messages }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
      <AnimatePresence initial={false}>
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white rounded-br-sm'
                  : 'bg-slate-700 text-slate-100 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 3: Create VoiceInput.jsx**

Create `frontend/src/components/VoiceInput.jsx`:

```jsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mic, MicOff, Send } from 'lucide-react'
import { useSpeech } from '../hooks/useSpeech'

export default function VoiceInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const { listening, start, stop } = useSpeech((transcript) => {
    setText(transcript)
  })

  function handleSend() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function toggleMic() {
    listening ? stop() : start()
  }

  return (
    <div className="flex items-end gap-2 p-3 bg-slate-800 rounded-2xl border border-slate-700">
      {/* Mic button */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={toggleMic}
        disabled={disabled}
        className={`p-2 rounded-xl transition-colors ${
          listening
            ? 'bg-red-500 text-white'
            : 'bg-slate-700 text-slate-400 hover:text-white hover:bg-slate-600'
        } disabled:opacity-40`}
        title={listening ? 'Stop recording' : 'Start voice input'}
      >
        {listening ? <MicOff size={20} /> : <Mic size={20} />}
      </motion.button>

      {/* Text input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
        placeholder={listening ? 'Listening…' : 'Type or speak…'}
        className="flex-1 bg-transparent text-slate-100 placeholder-slate-500
                   resize-none outline-none text-sm leading-relaxed
                   disabled:opacity-40"
      />

      {/* Send button */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="p-2 rounded-xl bg-brand-600 text-white hover:bg-brand-500
                   transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        title="Send"
      >
        <Send size={20} />
      </motion.button>
    </div>
  )
}
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/components/ frontend/src/hooks/useSpeech.js
git commit -m "feat: add ChatWindow, VoiceInput, and useSpeech hook"
```

---

## Task 12: 3D Avatar Component

**Files:**
- Create: `frontend/src/components/Avatar.jsx`
- Create: `frontend/public/avatar.glb` (downloaded from Ready Player Me)

**Interfaces:**
- Consumes: `audioBase64: string | null`, `emotion: string`
- Produces: `<Avatar audioBase64={...} emotion={...} />` — animated 3D avatar with lip sync

**Note:** Before coding, visit [readyplayer.me](https://readyplayer.me), create a cartoon-style avatar, download the `.glb` file, and save it to `frontend/public/avatar.glb`. Make sure to select a **full body** or **half body** avatar.

- [ ] **Step 1: Download your Ready Player Me avatar**

1. Go to `https://readyplayer.me`
2. Click "Try for Free"
3. Create a cartoon-style avatar
4. When done, click "Download" and choose `.glb`
5. Save the file to `frontend/public/avatar.glb`

- [ ] **Step 2: Create Avatar.jsx**

Create `frontend/src/components/Avatar.jsx`:

```jsx
import { useRef, useEffect, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF, OrbitControls, Environment } from '@react-three/drei'

const EMOTION_EXPRESSIONS = {
  happy: { mouthSmileLeft: 0.6, mouthSmileRight: 0.6, eyeSquintLeft: 0.3, eyeSquintRight: 0.3 },
  sad:   { mouthFrownLeft: 0.5, mouthFrownRight: 0.5, browInnerUp: 0.4 },
  angry: { browDownLeft: 0.6, browDownRight: 0.6, mouthFrownLeft: 0.3, mouthFrownRight: 0.3 },
  fearful: { browInnerUp: 0.7, eyeWideLeft: 0.5, eyeWideRight: 0.5 },
  surprised: { eyeWideLeft: 0.8, eyeWideRight: 0.8, mouthOpen: 0.3, jawOpen: 0.2 },
  neutral: {},
  disgusted: { noseSneerLeft: 0.5, noseSneerRight: 0.5 },
}

function AvatarModel({ audioRef, analyserRef, emotion }) {
  const { scene } = useGLTF('/avatar.glb')
  const meshRef = useRef(null)

  // Find the mesh with morph targets (blend shapes)
  useEffect(() => {
    scene.traverse((child) => {
      if (child.isMesh && child.morphTargetDictionary) {
        meshRef.current = child
      }
    })
  }, [scene])

  useFrame(() => {
    const mesh = meshRef.current
    if (!mesh || !mesh.morphTargetDictionary) return

    // Lip sync from audio amplitude
    if (analyserRef.current) {
      const data = new Uint8Array(analyserRef.current.frequencyBinCount)
      analyserRef.current.getByteFrequencyData(data)
      const avg = data.reduce((a, b) => a + b, 0) / data.length
      const mouthOpen = Math.min(avg / 128, 1)
      const jawIdx = mesh.morphTargetDictionary['jawOpen']
      if (jawIdx !== undefined) {
        mesh.morphTargetInfluences[jawIdx] = mouthOpen * 0.6
      }
    }

    // Emotion expression blend shapes
    const expressions = EMOTION_EXPRESSIONS[emotion] || {}
    Object.entries(mesh.morphTargetDictionary).forEach(([name, idx]) => {
      const target = expressions[name] ?? 0
      const current = mesh.morphTargetInfluences[idx]
      // Smooth interpolation toward target
      mesh.morphTargetInfluences[idx] = current + (target - current) * 0.05
    })
  })

  return (
    <primitive
      object={scene}
      scale={2}
      position={[0, -1.5, 0]}
    />
  )
}

export default function Avatar({ audioBase64, emotion = 'neutral' }) {
  const analyserRef = useRef(null)
  const audioCtxRef = useRef(null)

  useEffect(() => {
    if (!audioBase64) return

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    audioCtxRef.current = audioCtx

    const analyser = audioCtx.createAnalyser()
    analyser.fftSize = 256
    analyserRef.current = analyser

    const binary = atob(audioBase64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

    audioCtx.decodeAudioData(bytes.buffer).then((buffer) => {
      const source = audioCtx.createBufferSource()
      source.buffer = buffer
      source.connect(analyser)
      analyser.connect(audioCtx.destination)
      source.start()
      source.onended = () => {
        analyserRef.current = null
      }
    })

    return () => audioCtx.close()
  }, [audioBase64])

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-slate-900">
      <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[2, 4, 2]} intensity={1} />
        <Environment preset="city" />
        <Suspense fallback={null}>
          <AvatarModel
            audioRef={null}
            analyserRef={analyserRef}
            emotion={emotion}
          />
        </Suspense>
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>
    </div>
  )
}

useGLTF.preload('/avatar.glb')
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds. If you see warnings about missing morph targets, that's okay — the avatar will still render; it just won't have every blend shape the code references.

- [ ] **Step 4: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/components/Avatar.jsx frontend/public/avatar.glb
git commit -m "feat: add 3D RPM avatar with lip sync and emotion expressions"
```

---

## Task 13: Crisis Card Component

**Files:**
- Create: `frontend/src/components/CrisisCard.jsx`

**Interfaces:**
- Consumes: `visible: bool`, `onDismiss: fn` (goes to Welcome, not closed in-session)
- Produces: Full-screen overlay with crisis resources

- [ ] **Step 1: Create CrisisCard.jsx**

Create `frontend/src/components/CrisisCard.jsx`:

```jsx
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Phone, MessageSquare, Globe } from 'lucide-react'

const RESOURCES = [
  {
    icon: Phone,
    label: 'Call or Text',
    name: 'Suicide & Crisis Lifeline',
    value: '988',
    href: 'tel:988',
    color: 'text-red-400',
  },
  {
    icon: MessageSquare,
    label: 'Text',
    name: 'Crisis Text Line',
    value: 'HOME to 741741',
    href: 'sms:741741?body=HOME',
    color: 'text-amber-400',
  },
  {
    icon: Globe,
    label: 'International',
    name: 'Find A Helpline',
    value: 'findahelpline.com',
    href: 'https://findahelpline.com',
    color: 'text-blue-400',
  },
]

export default function CrisisCard({ visible }) {
  const navigate = useNavigate()

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center
                     bg-slate-950/95 backdrop-blur-sm px-6"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="max-w-md w-full bg-slate-800 border border-slate-600
                       rounded-3xl p-8 space-y-6"
          >
            <div className="text-center space-y-2">
              <div className="text-4xl">💙</div>
              <h2 className="text-2xl font-bold text-white">
                You're not alone
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                I hear you, and I'm really glad you reached out.
                Please connect with someone who can help right now.
              </p>
            </div>

            <div className="space-y-3">
              {RESOURCES.map((r) => (
                <a
                  key={r.name}
                  href={r.href}
                  target={r.href.startsWith('http') ? '_blank' : undefined}
                  rel="noreferrer"
                  className="flex items-center gap-4 bg-slate-700 hover:bg-slate-600
                             rounded-2xl p-4 transition-colors"
                >
                  <r.icon className={`${r.color} flex-shrink-0`} size={24} />
                  <div>
                    <p className="text-slate-400 text-xs">{r.label}</p>
                    <p className="text-white font-semibold text-sm">{r.name}</p>
                    <p className={`${r.color} font-bold`}>{r.value}</p>
                  </div>
                </a>
              ))}
            </div>

            <button
              onClick={() => navigate('/')}
              className="w-full py-3 rounded-2xl bg-slate-700 hover:bg-slate-600
                         text-slate-300 text-sm transition-colors"
            >
              Return to home
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/components/CrisisCard.jsx
git commit -m "feat: add full-screen crisis card with hotline resources"
```

---

## Task 14: Session Page — Full Integration

**Files:**
- Modify: `frontend/src/pages/Session.jsx`

**Interfaces:**
- Consumes: All components (Avatar, WebcamFeed, ChatWindow, VoiceInput, CrisisCard), `useWebcam`, `api`
- Produces: Complete working session screen

- [ ] **Step 1: Implement Session.jsx**

Replace `frontend/src/pages/Session.jsx` with:

```jsx
import { useState, useCallback, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Avatar from '../components/Avatar'
import WebcamFeed from '../components/WebcamFeed'
import ChatWindow from '../components/ChatWindow'
import VoiceInput from '../components/VoiceInput'
import CrisisCard from '../components/CrisisCard'
import { useWebcam } from '../hooks/useWebcam'
import { api } from '../lib/api'

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: "Hello, I'm Mira. I'm here to listen and support you. How are you feeling today?",
}

export default function Session() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('sid')

  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [emotionContext, setEmotionContext] = useState(null)
  const [currentAudio, setCurrentAudio] = useState(null)
  const [crisis, setCrisis] = useState(false)
  const [sending, setSending] = useState(false)

  const latestEmotionRef = useRef(null)

  const handleEmotionUpdate = useCallback((ctx) => {
    setEmotionContext(ctx)
    latestEmotionRef.current = ctx
  }, [])

  const videoRef = useWebcam(handleEmotionUpdate, 2000)

  async function handleSend(message) {
    if (!sessionId || sending) return

    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', content: message }])

    try {
      const response = await api.chat(
        sessionId,
        message,
        latestEmotionRef.current || {}
      )

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.text },
      ])
      setCurrentAudio(response.audio)

      if (response.crisis) {
        setCrisis(true)
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I had trouble responding. Please try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  if (!sessionId) {
    navigate('/')
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800">
        <h1 className="text-brand-500 font-bold text-xl tracking-tight">MindMirror</h1>
        <button
          onClick={() => navigate('/')}
          className="text-slate-400 hover:text-white text-sm transition-colors"
        >
          End Session
        </button>
      </header>

      {/* Main layout */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left column: webcam + avatar */}
        <div className="w-72 flex-shrink-0 flex flex-col gap-4">
          <WebcamFeed videoRef={videoRef} emotionContext={emotionContext} />
          <div className="flex-1 min-h-0">
            <Avatar
              audioBase64={currentAudio}
              emotion={emotionContext?.dominant_emotion || 'neutral'}
            />
          </div>
        </div>

        {/* Right column: chat */}
        <div className="flex-1 flex flex-col bg-slate-900 rounded-2xl overflow-hidden border border-slate-800">
          <ChatWindow messages={messages} />
          <div className="p-3 border-t border-slate-800">
            <VoiceInput onSend={handleSend} disabled={sending || crisis} />
          </div>
        </div>
      </div>

      {/* Crisis overlay */}
      <CrisisCard visible={crisis} />
    </div>
  )
}
```

- [ ] **Step 2: Start backend and frontend, do an end-to-end test**

Terminal 1:
```bash
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000
```

Terminal 2:
```bash
cd frontend && npm run dev
```

Walk through the full flow:
1. Visit `http://localhost:5173` → Welcome screen with disclaimer
2. Click "Begin Session" → redirected to `/session?sid=<uuid>`
3. Allow camera access → webcam feed appears with emotion badge
4. Type "I've been feeling stressed at work" → message appears, Mira responds, avatar speaks
5. Test crisis: type "I want to end it all" → crisis card appears with 988 hotline

- [ ] **Step 3: Commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add frontend/src/pages/Session.jsx
git commit -m "feat: complete Session page wiring all components end-to-end"
```

---

## Task 15: Deployment

**Files:**
- Create: `backend/render.yaml`
- Create: `frontend/vercel.json`

**Interfaces:**
- Produces: Live app accessible via Vercel URL

- [ ] **Step 1: Create Render config for backend**

Create `backend/render.yaml`:

```yaml
services:
  - type: web
    name: ai-therapist-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: FRONTEND_URL
        sync: false
```

- [ ] **Step 2: Create Vercel config for frontend**

Create `frontend/vercel.json`:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [ ] **Step 3: Push code to GitHub**

1. Go to `https://github.com/new` and create a new repository named `ai-therapist`
2. Copy the remote URL (e.g. `https://github.com/yourusername/ai-therapist.git`)

```bash
cd /Users/Alex/Documents/ai-therapist
git remote add origin <your-github-url>
git push -u origin main
```

- [ ] **Step 4: Deploy backend to Render**

1. Go to `https://render.com` → sign up → "New Web Service"
2. Connect your GitHub repo
3. Set **Root Directory** to `backend`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` → your Gemini API key
   - `FRONTEND_URL` → (leave blank for now, fill in after Vercel deploy)
7. Click "Create Web Service"
8. Wait for deploy to finish. Copy your Render URL (e.g. `https://ai-therapist-backend.onrender.com`)

- [ ] **Step 5: Deploy frontend to Vercel**

1. Go to `https://vercel.com` → sign up → "Add New Project"
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Under **Environment Variables**, add:
   - `VITE_API_URL` → your Render backend URL from Step 4
5. Click "Deploy"
6. Copy your Vercel URL (e.g. `https://ai-therapist.vercel.app`)

- [ ] **Step 6: Update FRONTEND_URL on Render**

Go back to Render → your service → Environment → update `FRONTEND_URL` with your Vercel URL → trigger a redeploy.

- [ ] **Step 7: Final end-to-end test on live URLs**

Visit your Vercel URL and run through the complete flow:
1. Welcome screen loads
2. Begin session creates a session on the live backend
3. Webcam works (may require HTTPS — Vercel provides this automatically)
4. Chat with Mira, avatar speaks and lip-syncs
5. Crisis card appears on crisis message

- [ ] **Step 8: Final commit**

```bash
cd /Users/Alex/Documents/ai-therapist
git add backend/render.yaml frontend/vercel.json
git commit -m "feat: add Render and Vercel deployment configs"
git push
```

---

## Self-Review

**Spec coverage:**
- ✅ Facial emotion detection (DeepFace) — Task 4
- ✅ Eye contact + engagement signals (MediaPipe) — Task 4
- ✅ Emotion intensity with rolling average — Task 4
- ✅ Safety filter with CRISIS bypass — Task 3
- ✅ Crisis resources (988, 741741, findahelpline) — Task 13
- ✅ Gemini therapy engine + session memory — Task 5
- ✅ Style switching (active_listening → cbt → solution_focused) — Task 5
- ✅ TTS with gTTS — Task 6
- ✅ React frontend with Tailwind + shadcn + Framer Motion — Task 7
- ✅ Welcome page with disclaimer — Task 9
- ✅ Webcam feed with emotion badge — Task 10
- ✅ Chat window with bubbles — Task 11
- ✅ Voice input with Web Speech API — Task 11
- ✅ 3D RPM avatar with lip sync — Task 12
- ✅ Crisis card full-screen overlay — Task 13
- ✅ Session page full integration — Task 14
- ✅ Deployment to Vercel + Render — Task 15

**Placeholder scan:** No TBDs. All steps have real code.

**Type consistency:** `analyze_frame` returns same dict shape consumed by `emotional_context` in chat endpoint. `TherapyEngine.get_response` signature matches call in `main.py`. `api.chat()` return shape `{text, audio, crisis}` matches destructuring in `Session.jsx`.
