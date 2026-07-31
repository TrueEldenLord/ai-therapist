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
