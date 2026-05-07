# 👁️ Vision Cursor

> **Hands-free mouse control using only your webcam.**  
> Built with MediaPipe, OpenCV, and PyAutoGUI.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🖐 Cursor control | Index-finger tip drives the mouse in real time |
| ⏸ Dwell click | Stay still for ~2 s → automatic left click |
| 🎯 Calibration | 4-corner guided calibration for pixel-perfect accuracy |
| 🧹 Smoothing | Rolling-average + EMA removes camera jitter |
| ⚙️ Config file | All thresholds tweakable in `config.py` |

---

## 📁 Project Structure

```
vision-cursor/
├── main.py           # Entry point & main loop
├── hand_tracking.py  # MediaPipe wrapper
├── calibration.py    # Guided 4-corner calibration + ScreenMapper
├── smoothing.py      # Jitter removal (rolling avg + EMA)
├── config.py         # All tuneable constants
├── requirements.txt  # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Linux users** – PyAutoGUI needs a display server:
> ```bash
> sudo apt install python3-tk python3-dev scrot
> ```

### 2. Run (no calibration)

```bash
python main.py
```

A webcam preview window opens.  
Move your **index finger** in front of the camera – the cursor follows.  
**Hold still for 2 seconds** to click.  
Press **`q`** to quit.

### 3. Run with calibration (recommended)

```bash
python main.py --calibrate
```

Follow the on-screen prompts:
1. A target circle appears in each corner of the camera preview.
2. Point your finger at the matching screen corner and **hold still**.
3. After all 4 corners are captured the system starts automatically.

### 4. Headless / no preview

```bash
python main.py --no-preview
```

---

## ⚙️ Tuning (`config.py`)

| Constant | Default | What it does |
|---|---|---|
| `SMOOTH_BUFFER_SIZE` | `6` | Larger = smoother, more lag |
| `DWELL_RADIUS_PX` | `18` | Smaller = more sensitive to movement |
| `DWELL_TIME_SEC` | `2.0` | Seconds still before a click |
| `CLICK_COOLDOWN_SEC` | `1.5` | Minimum time between clicks |
| `MIN_DETECTION_CONF` | `0.75` | Lower if hand detection is unreliable |

---

## 🗺️ Data Flow

```
Webcam frame
    │
    ▼
HandTracker.process()          ← MediaPipe landmarks
    │  tip_x, tip_y  (0-1)
    ▼
PositionSmoother.update()      ← rolling avg + EMA
    │  smooth_x, smooth_y
    ▼
ScreenMapper.to_screen()       ← perspective transform (or linear)
    │  screen_x, screen_y  (pixels)
    ▼
pyautogui.moveTo()             ← OS cursor move
    │
    ▼
Dwell timer check
    │  still for ≥ DWELL_TIME_SEC?
    ▼
pyautogui.click()              ← left click
```

---

## 🛡️ Safety

- **PyAutoGUI failsafe**: Move the mouse to the **top-left screen corner** to immediately abort the program.
- Press **`q`** in the preview window for a clean shutdown.

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| Camera not found | Change `CAMERA_INDEX` in `config.py` |
| Cursor jittery | Increase `SMOOTH_BUFFER_SIZE`; improve lighting |
| Click fires too easily | Increase `DWELL_RADIUS_PX` or `DWELL_TIME_SEC` |
| Hand not detected | Lower `MIN_DETECTION_CONF`; use better lighting |
| Linux: `_tkinter` error | `sudo apt install python3-tk` |

---

## 📄 License

MIT – free for personal and commercial use.
