"""완성본 목소리(out/stems/voice.wav)를 다시 받아 적어, 같은 말이 두 번 들어간 곳을 찾는다.

출력: out/voice_check.txt (받아 적은 전체 + 의심 구간 목록)
사용: python3 tools/check_voice.py
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
x = x.reshape(-1, ch).mean(axis=1)
x = x[:: sr // 16000]  # 48k → 16k

model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = model.transcribe(x, language="ko", word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
words = []
lines = []
for s in segs:
    lines.append(f"{s.start:7.2f} {s.end:7.2f} {s.text.strip()}")
    words += [(w.start, re.sub(r"[^\w]", "", w.word)) for w in s.words if re.sub(r"[^\w]", "", w.word)]

# 3단어 이상이 10초 안에 그대로 다시 나오면 의심
sus = []
for n in (4, 3):
    seen = {}
    for k in range(len(words) - n + 1):
        key = " ".join(t for _, t in words[k:k + n])
        t = words[k][0]
        if key in seen and t - seen[key] < 10:
            sus.append(f"{seen[key]:7.2f} → {t:7.2f}  '{key}'")
        seen[key] = t
out = ["# 의심 구간 (같은 말이 10초 안에 다시 나옴)", *(sorted(set(sus)) or ["없음"]), "", "# 받아 적은 전체", *lines]
(ROOT / "out/voice_check.txt").write_text("\n".join(out))
print("\n".join(out[: len(sus) + 3]))
