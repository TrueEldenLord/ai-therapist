import os
import uuid
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

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
    "worthless", "i'm a failure", "nobody cares",
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
        return {"session_id": session_id, "current_style": "active_listening", "emotional_arc": []}

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
