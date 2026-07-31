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
