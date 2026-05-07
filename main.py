# ─────────────────────────────────────────────
#  main.py  –  Vision Cursor
#  Entry point.  Ties all modules together.
#
#  Run:
#      python main.py              # no calibration (linear fallback)
#      python main.py --calibrate  # run guided 4-corner calibration first
# ─────────────────────────────────────────────

import argparse
import sys
import time

import cv2
import pyautogui

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    SHOW_PREVIEW,
    PREVIEW_WINDOW_NAME,
    DWELL_TIME_SEC,
    DWELL_RADIUS_PX,
    CLICK_COOLDOWN_SEC,
)
from hand_tracking import HandTracker
from calibration   import Calibrator, ScreenMapper
from smoothing     import PositionSmoother


# ── PyAutoGUI safety settings ────────────────────────────────────────────
pyautogui.FAILSAFE  = False   # move mouse to top-left corner to abort
pyautogui.PAUSE     = 0.0     # no artificial delay between GUI calls


# ── CLI ──────────────────────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser(description="Vision Cursor – hands-free mouse")
    ap.add_argument(
        "--calibrate", action="store_true",
        help="Run guided 4-corner calibration before starting."
    )
    ap.add_argument(
        "--no-preview", action="store_true",
        help="Disable the webcam preview window."
    )
    return ap.parse_args()


# ── Helpers ──────────────────────────────────────────────────────────────
def open_camera() -> cv2.VideoCapture:
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        sys.exit(f"[ERROR] Cannot open camera index {CAMERA_INDEX}.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return cap


def draw_dwell_indicator(frame, cx_px: int, cy_px: int, progress: float):
    """Draw a shrinking circle around the fingertip while dwelling."""
    radius = max(4, int(DWELL_RADIUS_PX * (1 - progress)))
    colour = (
        int(255 * progress),          # R: grows red as we approach click
        int(255 * (1 - progress)),    # G: fades from green
        80,
    )
    cv2.circle(frame, (cx_px, cy_px), radius + 8, colour, 2)
    # Progress arc (approximate with text for simplicity)
    cv2.putText(
        frame,
        f"Click in {DWELL_TIME_SEC*(1-progress):.1f}s",
        (cx_px + 16, cy_px - 8),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1,
    )


# ── Main loop ─────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    show_preview = SHOW_PREVIEW and not args.no_preview

    cap     = open_camera()
    tracker = HandTracker()
    smoother= PositionSmoother()

    # ── Optional calibration ─────────────────────────────────────────────
    transform = None
    if args.calibrate:
        print("[Vision Cursor] Starting calibration …")
        cal       = Calibrator(tracker)
        transform = cal.run(cap)
        smoother.reset()

    mapper = ScreenMapper(transform=transform)

    # ── Dwell-click state ────────────────────────────────────────────────
    dwell_start:  float | None = None
    last_cam_pos: tuple | None = None
    last_click_t: float        = 0.0

    print("[Vision Cursor] Running. Press  q  in the preview window to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[WARN] Frame grab failed – skipping.")
            continue

        frame = cv2.flip(frame, 1)     # mirror: natural feel
        result = tracker.process(frame)
        display = result.annotated_frame if result else frame.copy()

        # ── Process hand ──────────────────────────────────────────────
        if result:
            # 1. Smooth raw coordinates
            sx, sy = smoother.update(result.tip_x, result.tip_y)

            # 2. Map to screen
            screen_x, screen_y = mapper.to_screen(sx, sy)

            # 3. Move the cursor
            pyautogui.moveTo(screen_x, screen_y)

            # 4. Dwell-click logic
            if last_cam_pos is not None:
                dx = (sx - last_cam_pos[0]) * FRAME_WIDTH
                dy = (sy - last_cam_pos[1]) * FRAME_HEIGHT
                moved = (dx**2 + dy**2) ** 0.5 > DWELL_RADIUS_PX
            else:
                moved = True

            last_cam_pos = (sx, sy)

            if moved:
                dwell_start = time.time()          # reset dwell timer
            else:
                # Finger is steady
                if dwell_start is None:
                    dwell_start = time.time()

                elapsed  = time.time() - dwell_start
                progress = min(elapsed / DWELL_TIME_SEC, 1.0)

                # Draw dwell indicator on preview
                h, w = display.shape[:2]
                cam_px = int(sx * w)
                cam_py = int(sy * h)
                if show_preview:
                    draw_dwell_indicator(display, cam_px, cam_py, progress)

                # Fire click if dwell complete + cooldown elapsed
                if (elapsed >= DWELL_TIME_SEC and
                        time.time() - last_click_t >= CLICK_COOLDOWN_SEC):
                    pyautogui.click()
                    last_click_t = time.time()
                    dwell_start  = None
                    print(f"[Click] @ screen ({screen_x}, {screen_y})")
        else:
            # No hand detected – reset dwell
            dwell_start  = None
            last_cam_pos = None
            smoother.reset()

        # ── HUD overlay ───────────────────────────────────────────────
        if show_preview:
            status = "Hand detected" if result else "No hand"
            colour = (0, 255, 80) if result else (0, 80, 255)
            cv2.putText(display, f"Vision Cursor  |  {status}",
                        (10, display.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, colour, 1)
            cv2.imshow(PREVIEW_WINDOW_NAME, display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ── Cleanup ───────────────────────────────────────────────────────
    cap.release()
    tracker.release()
    cv2.destroyAllWindows()
    print("[Vision Cursor] Stopped.")


if __name__ == "__main__":
    main()
