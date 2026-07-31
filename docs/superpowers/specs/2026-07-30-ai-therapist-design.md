# AI Therapist — Design Spec
**Date:** 2026-07-30
**Status:** Approved

---

## Overview

A full-stack AI therapist web application that uses real-time facial recognition to detect the user's emotional state and engagement, then drives a conversational AI therapist that responds with text, voice, and a 3D animated avatar. Built as a resume project to demonstrate ML, backend, frontend, and deployment skills in one cohesive system.

---

## System Architecture

**Decoupled frontend + backend (Option B):**

- **React frontend** hosted on Vercel
- **FastAPI backend** hosted on Render
- Communication via REST API (JSON + audio blobs)

```
┌─────────────────────────────────────────┐
│           React Frontend (Vercel)        │
│  Webcam Feed │ Chat UI │ Voice I/O       │
└───────────────────┬─────────────────────┘
                    │ frames / messages / audio
┌───────────────────▼─────────────────────┐
│          FastAPI Backend (Render)        │
│  Face Analyzer │ Therapy Engine │ TTS   │
└─────────────────────────────────────────┘
```

**Data flow:**
1. Browser captures webcam frames every ~2 seconds → POST to `/analyze-face`
2. Backend returns structured emotional context JSON
3. User speaks or types → POST to `/chat` with message + emotional context
4. Backend builds Gemini prompt → returns text response + audio file
5. Frontend plays audio, avatar lip-syncs, chat bubble appears

---

## Facial Analysis Pipeline

Runs on the backend every ~2 seconds using **DeepFace + OpenCV**.

**Emotion Detection (DeepFace)**
Detects 7 emotions: angry, disgust, fear, happy, sad, surprise, neutral.
Returns probability distribution summing to 100%.

**Intensity Calculation**
- Dominant emotion = highest scoring emotion
- Raw intensity = dominant score / 100 (normalized 0–1)
- Smoothed intensity = rolling average of last 5 frames (eliminates blink/lighting noise)

| Intensity Range | Label | Therapist Behavior |
|---|---|---|
| 0.0 – 0.3 | Mild | Gentle check-in |
| 0.3 – 0.6 | Moderate | Active reflection |
| 0.6 – 1.0 | High | Prioritize immediately |

**Engagement Signals (OpenCV)**
- Eye contact: facial landmark gaze estimation (toward camera = engaged)
- Head position: nodding, tilting, looking down
- Presence: confirms face is in frame

**Emotional Context Output (sent to Gemini)**
```json
{
  "dominant_emotion": "sad",
  "emotion_intensity": 0.78,
  "eye_contact": "low",
  "head_position": "tilted_down",
  "engagement_level": "withdrawn"
}
```

---

## Therapy Engine

**Session Memory**
```json
{
  "session_id": "abc123",
  "history": [],
  "emotional_arc": ["neutral", "sad", "sad", "fearful"],
  "current_style": "active_listening",
  "topics_mentioned": ["work", "family"],
  "intensity_trend": "escalating"
}
```

**Therapeutic Styles**
- `active_listening` — default; reflects feelings, asks open-ended questions
- `cbt` — gently challenges negative thought patterns
- `solution_focused` — offers practical suggestions when user asks for advice

**Style Switching Logic**
| Signal | Switch To |
|---|---|
| User expresses negative self-belief | `cbt` |
| High intensity sustained > 3 turns | Stay in `active_listening` |
| User explicitly asks for advice | `solution_focused` |
| Intensity drops, user stable | Return to `active_listening` |

**Gemini Prompt Structure**
```
[SYSTEM]
You are a compassionate AI therapist. Current style: active_listening.
Emotional state: sad (intensity: high), low eye contact, withdrawn.
Emotional arc: neutral → sad → sad.
Topics discussed: work stress.
Never diagnose. Never replace professional help. Always validate before advising.

[HISTORY]
(last N turns of conversation)

[CURRENT MESSAGE]
User: "..."
```

**LLM:** Google Gemini 2.0 Flash (free tier)

---

## Safety & Crisis Detection Layer

Runs as a filter on EVERY user message BEFORE Gemini is called. Cannot be bypassed.

**Trigger Categories**
| Category | Examples | Level |
|---|---|---|
| Suicidal ideation | "want to end it", "not worth living" | CRISIS |
| Self-harm | "hurt myself", "cutting" | CRISIS |
| Harm to others | "hurt someone" | CRISIS |
| Severe distress | "can't go on", "hopeless" | WARNING |

**CRISIS Response**
1. Gemini is bypassed — hardcoded compassionate response fires
2. UI renders full-screen crisis card with hotlines:
   - National Suicide Prevention Lifeline: **988**
   - Crisis Text Line: **Text HOME to 741741**
   - International: **findahelpline.com**
3. Session flagged; remainder of session gently encourages professional help

**WARNING Response**
Gemini prompt injected with:
```
[SAFETY FLAG: User showing distress — validate feelings only,
do NOT offer solutions, gently mention professional support]
```

**Session Disclaimer (shown on Welcome screen)**
> "This is an AI tool for emotional support only. It is not a substitute for professional mental health care. If you are in crisis, please contact 988."

---

## 3D Avatar

**Style:** Stylized cartoon human (approachable, avoids uncanny valley)

**Tech Stack**
- **Ready Player Me** — free avatar creation platform, exports `.glb` file
- **React Three Fiber** — renders 3D avatar inside React
- **@readyplayerme/visage** — handles avatar + facial animations

**Lip Sync Pipeline**
```
Gemini text → gTTS audio → Web Audio API amplitude analysis
→ mouth shape driven by amplitude in real-time
```

**Emotional Expressions**
Avatar expression changes based on user's detected emotion:
- User is sad → avatar shows soft, concerned expression
- User makes progress → avatar smiles warmly
- Crisis detected → avatar expression becomes gentle and serious

---

## React Frontend UI

**Tech Stack**
| Tool | Purpose |
|---|---|
| React + Vite | Framework + build tool |
| Tailwind CSS | Styling |
| shadcn/ui | Pre-built components |
| Framer Motion | Animations |
| React Three Fiber | 3D avatar rendering |
| Web Speech API | Voice input |

**Color palette:** Deep blues/teals with soft whites — calm, clinical, trustworthy

**Screens**

1. **Welcome Screen** — app name, tagline, crisis disclaimer, "Begin Session" button
2. **Session Screen** — webcam feed (left) + 3D avatar + chat window (right), emotion indicator, mic/text input
3. **Crisis Card** — full-screen overlay, cannot be accidentally dismissed, clickable hotline links

**Session Screen Layout**
```
┌─────────────────────────────────────────────┐
│  MindMirror                        [End]    │
├──────────────────┬──────────────────────────┤
│  Webcam Feed     │   3D Avatar              │
│                  │                          │
│  😔 Sad (High)   ├──────────────────────────┤
│  👁 Low contact  │   Chat Window            │
│                  │                          │
│                  │  [🎤 Speak] [Type] [Send]│
└──────────────────┴──────────────────────────┘
```

---

## Project Structure

```
ai-therapist/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Avatar.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── WebcamFeed.jsx
│   │   │   ├── VoiceInput.jsx
│   │   │   └── CrisisCard.jsx
│   │   ├── pages/
│   │   │   ├── Welcome.jsx
│   │   │   └── Session.jsx
│   │   ├── hooks/
│   │   │   ├── useWebcam.js
│   │   │   └── useSpeech.js
│   │   └── App.jsx
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/
│   ├── main.py
│   ├── face_analyzer.py
│   ├── therapy_engine.py
│   ├── safety_filter.py
│   ├── tts.py
│   └── requirements.txt
│
├── docs/superpowers/specs/
│   └── 2026-07-30-ai-therapist-design.md
└── README.md
```

---

## Deployment

| Layer | Platform | Cost |
|---|---|---|
| React frontend | Vercel | Free |
| FastAPI backend | Render | Free tier |
| LLM | Gemini 2.0 Flash | Free tier |
| Avatar | Ready Player Me | Free |

---

## Build Order

1. FastAPI skeleton + face analyzer (DeepFace + OpenCV)
2. Safety filter
3. Gemini therapy engine + session memory
4. TTS integration
5. React UI shell + webcam feed
6. Chat window + voice I/O
7. 3D avatar + lip sync
8. Wire frontend ↔ backend
9. Deploy to Vercel + Render
