import io
from gtts import gTTS


def text_to_audio(text: str) -> bytes:
    """Convert text to MP3 audio bytes using gTTS."""
    tts = gTTS(text=text, lang="en", slow=False)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()
