# ─────────────────────────────────────────────
#  config.py  –  Vision Cursor  (all tunables)
# ─────────────────────────────────────────────

# ── Camera ──────────────────────────────────
CAMERA_INDEX        = 0          # webcam device index (0 = default)
FRAME_WIDTH         = 640
FRAME_HEIGHT        = 480

# ── Hand-tracking (MediaPipe) ────────────────
MIN_DETECTION_CONF  = 0.75       # initial hand-detection confidence
MIN_TRACKING_CONF   = 0.70       # landmark tracking confidence

# Landmark index for the fingertip used to drive the cursor
# MediaPipe Hand landmarks: https://mediapipe.dev/solutions/hands
INDEX_FINGER_TIP    = 8

# ── Smoothing ────────────────────────────────
# How many past positions to average (higher = smoother but slower)
SMOOTH_BUFFER_SIZE  = 6

# ── Dwell / Auto-click ───────────────────────
# Pixel radius: if the finger stays inside this circle it counts as "still"
DWELL_RADIUS_PX     = 18

# Seconds the finger must stay still before a click fires
DWELL_TIME_SEC      = 2.0

# Minimum seconds between two successive dwell-clicks (debounce)
CLICK_COOLDOWN_SEC  = 1.5

# ── Calibration ──────────────────────────────
# Default active-zone fraction of the camera frame used for hand movement
# (set automatically during calibration, kept here as fall-back)
DEFAULT_CAM_MARGIN  = 0.15       # 15 % margin on each side

# ── Debug / Preview window ──────────────────
SHOW_PREVIEW        = True       # show the webcam feed with overlays
PREVIEW_WINDOW_NAME = "Vision Cursor – Preview (q to quit)"
