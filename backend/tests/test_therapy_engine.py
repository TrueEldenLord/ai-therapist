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
