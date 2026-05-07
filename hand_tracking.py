# ─────────────────────────────────────────────
#  hand_tracking.py  –  Vision Cursor
#  Uses mp.solutions.hands (stable, accurate)
#  Works with mediapipe 0.10.9 + Python 3.10
# ─────────────────────────────────────────────

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp

from config import MIN_DETECTION_CONF, MIN_TRACKING_CONF, INDEX_FINGER_TIP


@dataclass
class HandResult:
    tip_x: float
    tip_y: float
    annotated_frame: Optional[object] = None
    landmarks: Optional[object] = None


class HandTracker:
    def __init__(self):
        self._mp_hands   = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_styles  = mp.solutions.drawing_styles

        self._hands = self._mp_hands.Hands(
            static_image_mode        = False,
            max_num_hands            = 1,
            min_detection_confidence = MIN_DETECTION_CONF,
            min_tracking_confidence  = MIN_TRACKING_CONF,
        )
        print("[HandTracker] Using MediaPipe mp.solutions backend ✓")

    def process(self, bgr_frame) -> Optional[HandResult]:
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)
        rgb.flags.writeable = True

        annotated = bgr_frame.copy()

        if not result.multi_hand_landmarks:
            return None

        hand_landmarks = result.multi_hand_landmarks[0]

        # Draw skeleton
        self._mp_drawing.draw_landmarks(
            annotated,
            hand_landmarks,
            self._mp_hands.HAND_CONNECTIONS,
            self._mp_styles.get_default_hand_landmarks_style(),
            self._mp_styles.get_default_hand_connections_style(),
        )

        # Highlight index fingertip
        tip = hand_landmarks.landmark[INDEX_FINGER_TIP]
        h, w = bgr_frame.shape[:2]
        cx, cy = int(tip.x * w), int(tip.y * h)
        cv2.circle(annotated, (cx, cy), 10, (0, 255, 0), -1)
        cv2.circle(annotated, (cx, cy), 14, (255, 255, 255), 2)

        return HandResult(
            tip_x=tip.x,
            tip_y=tip.y,
            annotated_frame=annotated,
            landmarks=hand_landmarks,
        )

    def release(self):
        self._hands.close()