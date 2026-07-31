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
    r"\bcope\b",
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
