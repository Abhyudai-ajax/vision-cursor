# ─────────────────────────────────────────────
#  calibration.py  –  Vision Cursor
#
#  Guided 4-corner calibration:
#    1. Shows each corner target on screen.
#    2. User hovers finger on it for 2 s.
#    3. Builds an affine/perspective transform
#       from camera-space → screen-space.
# ─────────────────────────────────────────────

from __future__ import annotations
import time
import numpy as np
import cv2
import pyautogui

from config import (
    SHOW_PREVIEW,
    PREVIEW_WINDOW_NAME,
    DWELL_TIME_SEC,
    DWELL_RADIUS_PX,
)


# ── Corner definitions ──────────────────────────────────────────────────
# Screen corners (normalised 0→1) that the user must point at.
# Order: top-left, top-right, bottom-right, bottom-left  (clockwise)
_SCREEN_CORNERS_NORM = [
    (0.05, 0.05),   # top-left
    (0.95, 0.05),   # top-right
    (0.95, 0.95),   # bottom-right
    (0.05, 0.95),   # bottom-left
]

_CORNER_LABELS = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]


class Calibrator:
    """
    Collects 4 hand positions (one per screen corner) and builds a
    perspective transform matrix used by ScreenMapper.

    Usage
    -----
        cal = Calibrator(tracker)
        transform = cal.run()           # blocks until done
        mapper = ScreenMapper(transform=transform)
    """

    def __init__(self, tracker):
        """
        Parameters
        ----------
        tracker : HandTracker
            A live HandTracker instance (camera must be open).
        """
        self._tracker = tracker

    # ------------------------------------------------------------------ #
    def run(self, cap: cv2.VideoCapture) -> np.ndarray:
        """
        Interactive calibration loop.

        Parameters
        ----------
        cap : cv2.VideoCapture
            Open camera capture object.

        Returns
        -------
        np.ndarray
            3×3 perspective-transform matrix (camera-norm → screen-pixels).
        """
        screen_w, screen_h = pyautogui.size()
        cam_points    = []    # collected normalised camera coords
        screen_points = []    # matching screen pixel coords

        for idx, (sx_norm, sy_norm) in enumerate(_SCREEN_CORNERS_NORM):
            sx_px = int(sx_norm * screen_w)
            sy_px = int(sy_norm * screen_h)
            screen_points.append([sx_px, sy_px])

            label      = _CORNER_LABELS[idx]
            dwell_start: float | None = None
            last_pos   = None

            print(f"\n[Calibration] Point your index finger at the {label} corner …")

            while True:
                ok, frame = cap.read()
                if not ok:
                    continue
                frame = cv2.flip(frame, 1)   # mirror so it feels natural

                result = self._tracker.process(frame)
                display = result.annotated_frame if result else frame.copy()

                # ── Draw calibration overlay ──────────────────────────
                self._draw_overlay(
                    display, label, idx, dwell_start,
                    sx_norm, sy_norm, screen_w, screen_h
                )

                if result:
                    cx, cy = result.tip_x, result.tip_y

                    # Check dwell
                    if last_pos is not None:
                        dx = (cx - last_pos[0]) * screen_w
                        dy = (cy - last_pos[1]) * screen_h
                        moved = (dx**2 + dy**2) ** 0.5 > DWELL_RADIUS_PX
                    else:
                        moved = True

                    last_pos = (cx, cy)

                    if moved:
                        dwell_start = time.time()
                    elif dwell_start and (time.time() - dwell_start) >= DWELL_TIME_SEC:
                        cam_points.append([cx, cy])
                        print(f"  ✓ Captured {label}: cam=({cx:.3f}, {cy:.3f})")
                        self._flash(display)
                        break

                if SHOW_PREVIEW:
                    cv2.imshow(PREVIEW_WINDOW_NAME, display)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    raise KeyboardInterrupt("Calibration aborted by user.")

        # ── Build perspective transform ───────────────────────────────
        src = np.array(cam_points,    dtype=np.float32)   # (4,2) normalised
        dst = np.array(screen_points, dtype=np.float32)   # (4,2) pixels
        M = cv2.getPerspectiveTransform(src, dst)
        print("\n[Calibration] Complete ✓")
        return M

    # ------------------------------------------------------------------ #
    @staticmethod
    def _draw_overlay(frame, label, idx, dwell_start, sx_norm, sy_norm, sw, sh):
        h, w = frame.shape[:2]
        # Draw target circle in camera frame (mirrored corner)
        tx = int(sx_norm * w)
        ty = int(sy_norm * h)
        progress = 0.0
        if dwell_start:
            progress = min((time.time() - dwell_start) / DWELL_TIME_SEC, 1.0)

        cv2.circle(frame, (tx, ty), 24, (0, 200, 255), 2)
        cv2.circle(frame, (tx, ty), int(24 * progress), (0, 200, 255), -1)

        # Text prompt
        text = f"[{idx+1}/4] Hold at: {label}"
        cv2.putText(frame, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Hold still … {progress*100:.0f}%", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 120), 2)

    @staticmethod
    def _flash(frame):
        """Quick visual confirmation flash."""
        flash = np.full_like(frame, 200)
        cv2.addWeighted(frame, 0.4, flash, 0.6, 0, frame)


# ── ScreenMapper ────────────────────────────────────────────────────────

class ScreenMapper:
    """
    Maps normalised camera coordinates to screen pixel coordinates.

    If a perspective-transform matrix M is provided (from Calibrator),
    it is used. Otherwise a simple linear mapping with configurable
    margins is used as a fallback.
    """

    def __init__(
        self,
        transform: np.ndarray | None = None,
        cam_margin: float = 0.15,
    ):
        self._M        = transform
        self._margin   = cam_margin
        self._sw, self._sh = pyautogui.size()

    # ------------------------------------------------------------------ #
    def to_screen(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        """Convert normalised camera position → screen pixels (clamped)."""
        if self._M is not None:
            pt  = np.array([[[norm_x, norm_y]]], dtype=np.float32)
            dst = cv2.perspectiveTransform(pt, self._M)
            sx, sy = dst[0][0]
        else:
            # Fallback: linear stretch with margin
            m = self._margin
            sx = (norm_x - m) / (1 - 2 * m) * self._sw
            sy = (norm_y - m) / (1 - 2 * m) * self._sh

        # Clamp to valid screen area
        sx = int(max(0, min(sx, self._sw - 1)))
        sy = int(max(0, min(sy, self._sh - 1)))
        return sx, sy
