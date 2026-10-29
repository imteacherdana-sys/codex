"""편집표의 문장 조각을 하나씩 짧게 잘라 다시 받아 적는다.

긴 녹음을 한 번에 받아 적으면 말을 절거나 다시 한 부분이 한 단어로 뭉개져 안 보인다.
조각을 따로 받아 적으면 반복이 그대로 남아서, 같은 말이 두 번 나온 곳을 찾을 수 있다.

출력: assets/face/pieces.json  ({장면: [{k, a, b, text, words:[{start,end,word}]}]}), 시각은 원본 기준
사용: python3 tools/piece_check.py
"""
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_edit as F  # noqa: E402

ROOT = F.ROOT
with wave.open(str(ROOT / "assets/face/face16k.wav")) as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
SR = 16000
model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)

out = {}
for s in F.scene_list():
    name = s["name"]
    rows = []
    for k, ((a, b), (_, _, text, _)) in enumerate(zip(F.source_cuts(name), F.pieces_of(name))):
        clip = audio[int(a * SR): int(b * SR)]
        segs, _ = model.transcribe(clip, language="ko", word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False, beam_size=5, temperature=0)
        ws = [{"start": a + x.start, "end": a + x.end, "word": x.word.strip()} for sg in segs for x in sg.words]
        rows.append({"k": k, "a": a, "b": b, "text": text, "words": ws})
        heard = " ".join(x["word"] for x in ws)
        norm = [re.sub(r"[^\w]", "", x["word"]) for x in ws]
        rep = [norm[j] for j in range(1, len(norm)) if norm[j] and norm[j] == norm[j - 1]]
        flag = " ◀반복" if rep else ""
        print(f"{name:28s} {a:7.2f}-{b:7.2f} {heard}{flag}", flush=True)
    out[name] = rows
(ROOT / "assets/face/pieces.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("DONE")
