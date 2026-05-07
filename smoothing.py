# ─────────────────────────────────────────────
#  smoothing.py  –  Vision Cursor
#  Removes jitter from raw landmark coordinates
#  before they are mapped to screen pixels.
# ─────────────────────────────────────────────

from collections import deque
from config import SMOOTH_BUFFER_SIZE


class PositionSmoother:
    """
    Two-stage smoother:
      1. Rolling average  – averages the last N raw positions.
      2. Exponential (EMA) – blends the rolling average with the
         previous smoothed value for extra silkiness.

    Usage
    -----
        smoother = PositionSmoother()
        sx, sy = smoother.update(raw_x, raw_y)
    """

    def __init__(self, buffer_size: int = SMOOTH_BUFFER_SIZE, alpha: float = 0.35):
        """
        Parameters
        ----------
        buffer_size : int
            Number of past positions kept for the rolling average.
        alpha : float  (0 < alpha ≤ 1)
            EMA weight for the *new* value.
            Lower = smoother but laggier; higher = more responsive.
        """
        self._buf   = deque(maxlen=buffer_size)
        self._alpha = alpha
        self._prev  = None          # last EMA result

    # ------------------------------------------------------------------ #
    def update(self, x: float, y: float) -> tuple[float, float]:
        """Feed one new raw position; returns the smoothed position."""

        # Stage 1 – rolling average
        self._buf.append((x, y))
        avg_x = sum(p[0] for p in self._buf) / len(self._buf)
        avg_y = sum(p[1] for p in self._buf) / len(self._buf)

        # Stage 2 – exponential moving average
        if self._prev is None:
            self._prev = (avg_x, avg_y)
        else:
            smooth_x = self._alpha * avg_x + (1 - self._alpha) * self._prev[0]
            smooth_y = self._alpha * avg_y + (1 - self._alpha) * self._prev[1]
            self._prev = (smooth_x, smooth_y)

        return self._prev

    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        """Clear history (call this after calibration or a long pause)."""
        self._buf.clear()
        self._prev = None
