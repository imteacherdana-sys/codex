"""말을 절거나 같은 말을 두 번 한 조각을 소리 크기로 찾는다.

whisper는 반복을 한 단어로 뭉개 버려서, 글자 수에 비해 말한 시간이 긴 조각을 먼저 고른 뒤
그 조각을 소리 덩어리(말소리 사이 0.25초 이상 쉼으로 나눈 것)마다 따로 받아 적는다.

출력: logs/burst_check.txt
사용: python3 tools/burst_check.py [장면 이름 ...]
"""
import re
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_edit as F  # noqa: E402

with wave.open(str(F.ROOT / "assets/face/face16k.wav")) as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
SR = 16000
env = F.energy()
model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)


def bursts(a, b, gap=0.25):
    e = env[int(a * 100): int(b * 100)]
    thr = max(0.004, np.percentile(e, 20) * 2.5)
    on = e > thr
    out, start, quiet = [], None, 0
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet >= gap * 100:
                out.append((a + start / 100, a + (i - quiet + 1) / 100))
                start, quiet = None, 0
    if start is not None:
        out.append((a + start / 100, b))
    return [(x, y) for x, y in out if y - x > 0.12]


only = set(sys.argv[1:])
lines = []
for s in F.scene_list():
    name = s["name"]
    if only and name not in only:
        continue
    for (a, b), (_, _, text, _) in zip(F.source_cuts(name), F.pieces_of(name)):
        chars = len(re.sub(r"[^가-힣A-Za-z0-9]", "", text))
        bs = bursts(a, b)
        talk = sum(y - x for x, y in bs)
        expect = chars / 6.0
        # 전체 검사 때도 모든 조각을 본다 (앞뒤에 남의 말 끝이 묻은 짧은 덩어리도 잡으려고)
        lines.append(f"\n## {name} {a:.2f}-{b:.2f} 말한 시간 {talk:.1f}s / 예상 {expect:.1f}s · {text}")
        for x, y in bs:
            seg, _ = model.transcribe(audio[int((x - 0.05) * SR): int((y + 0.05) * SR)], language="ko",
                                      vad_filter=False, condition_on_previous_text=False, temperature=0)
            heard = " ".join(z.text.strip() for z in seg)
            lines.append(f"   {x:7.2f}-{y:7.2f}  {heard}")
        print("\n".join(lines[-len(bs) - 1:]), flush=True)
(F.ROOT / "logs/burst_check.txt").write_text("\n".join(lines))
print("DONE")
