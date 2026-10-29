"""완성본 목소리(out/stems/voice.wav)를 말소리 덩어리마다 따로 받아 적어 마지막으로 검수한다.

- 0.6초보다 짧은 덩어리: 앞뒤 말 끝이 묻은 조각일 수 있음 ('…고요')
- 이웃한 덩어리가 같은 말로 시작: 다시 말한 부분이 남았을 수 있음
출력: out/final_burst.txt (전체 + 의심 목록)
사용: python3 tools/final_burst.py
"""
import re
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
with wave.open(str(ROOT / "out/stems/voice.wav")) as w:
    sr, ch = w.getframerate(), w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
x = x.reshape(-1, ch).mean(axis=1)[:: sr // 16000]
SR = 16000
hop = 160
n = len(x) // hop
env = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
env = np.convolve(env, np.ones(3) / 3, mode="same")
on = env > max(0.004, np.percentile(env, 30) * 2.0)

bursts, start, quiet = [], None, 0
for i, v in enumerate(on):
    if v:
        start = i if start is None else start
        quiet = 0
    elif start is not None:
        quiet += 1
        if quiet >= 25:
            bursts.append((start / 100, (i - quiet + 1) / 100))
            start, quiet = None, 0
bursts = [(a, b) for a, b in bursts if b - a > 0.08]

model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
rows, sus = [], []
prev = ""
for a, b in bursts:
    seg, _ = model.transcribe(x[int(max(0, a - 0.05) * SR): int((b + 0.05) * SR)], language="ko", vad_filter=False,
                              condition_on_previous_text=False, temperature=0)
    t = " ".join(s.text.strip() for s in seg)
    rows.append(f"{a:8.2f}-{b:8.2f}  {t}")
    w0 = re.sub(r"[^\w]", "", t.split(" ")[0]) if t else ""
    p0 = re.sub(r"[^\w]", "", prev.split(" ")[0]) if prev else ""
    if b - a < 0.6 and t:
        sus.append(f"짧은 조각 {a:8.2f}  '{t}'")
    if w0 and w0 == p0 and len(w0) > 1:
        sus.append(f"같은 말로 시작 {a:8.2f}  '{prev}' → '{t}'")
    prev = t
(ROOT / "out/final_burst.txt").write_text("\n".join(["# 의심", *(sus or ["없음"]), "", "# 전체", *rows]))
print("\n".join(sus) or "의심 없음")
