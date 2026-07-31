from __future__ import annotations

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


def reset_emotion_history() -> None:
    """Clear the rolling emotion history. Call in test teardown to prevent state bleed."""
    _emotion_history.clear()


def analyze_frame(image_base64: str) -> dict:
    """Analyze a base64-encoded JPEG frame and return emotional context."""
    try:
        img_bgr = _decode_image(image_base64)
        if img_bgr is None:
            _emotion_history.clear()
            return {
                "face_detected": False,
                "dominant_emotion": "neutral",
                "emotion_intensity": 0.0,
                "eye_contact": "low",
                "head_position": "forward",
                "engagement_level": "moderate",
            }
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

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
        _emotion_history.clear()
        return {
            "face_detected": False,
            "dominant_emotion": "neutral",
            "emotion_intensity": 0.0,
            "eye_contact": "low",
            "head_position": "forward",
            "engagement_level": "moderate",
        }
