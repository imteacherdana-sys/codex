"""얼굴 녹화본에서 1초마다 얼굴 위치를 찾아 둔다 (작은 창을 자를 때 얼굴이 가운데 오도록).

출력: assets/face/track.json  ([{t, cx, cy, w}], 1920×1080 기준 픽셀, 못 찾은 초는 앞뒤 값으로 채움)
사용: python3 tools/face_track.py
"""
import json
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
cap = cv2.VideoCapture(str(ROOT / "assets/face/face_all.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
pts = []
for sec in range(int(n / fps)):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ok, fr = cap.read()
    if not ok:
        break
    g = cv2.cvtColor(cv2.resize(fr, (960, 540)), cv2.COLOR_BGR2GRAY)
    faces = det.detectMultiScale(g, 1.1, 6, minSize=(60, 60))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        pts.append({"t": sec, "cx": float(x + w / 2) * 2, "cy": float(y + h / 2) * 2, "w": float(w) * 2})
    else:
        pts.append({"t": sec, "cx": None, "cy": None, "w": None})
# 빈칸 채우기
last = next(p for p in pts if p["cx"] is not None)
for p in pts:
    if p["cx"] is None:
        p.update(cx=last["cx"], cy=last["cy"], w=last["w"])
    else:
        last = p
(ROOT / "assets/face/track.json").write_text(json.dumps(pts))
xs = [p["cx"] for p in pts]
print(len(pts), "sec", "cx min/max", min(xs), max(xs), "w avg", sum(p["w"] for p in pts) / len(pts))
