"""얼굴 녹화본 음성을 단어 시간까지 받아 적는다.

입력: assets/face/face16k.wav
출력: assets/face/transcript.json  ({segments: [{start, end, text, words: [{start, end, word}]}]})
사용: python3 tools/transcribe.py [모델 이름, 기본 large-v3-turbo]
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
name = sys.argv[1] if len(sys.argv) > 1 else "large-v3-turbo"
model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=4)
# 대본에 나오는 영어 이름을 미리 알려주면 받아 적기가 정확해진다
hint = ("단아쌤, Higgsfield, Kling 4.0, Seedance 2.5, Seedance 2.0, MiniMax H3, Wan 3.0, Grok Imagine 1.5, FLUX 3, Gemini Omni 1.1, "
        "Reference, 장풍, 경공, 비무, 현판, 단아객잔, 서소저, 귀공자, 크레딧")
with wave.open(str(ROOT / "assets/face/face16k.wav")) as w:  # 설치된 PyAV가 오래돼 파일 대신 배열로 넘긴다
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
segs, info = model.transcribe(audio, language="ko", word_timestamps=True, vad_filter=True,
                              initial_prompt=hint, condition_on_previous_text=False, beam_size=5)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                "words": [{"start": w.start, "end": w.end, "word": w.word} for w in (s.words or [])]})
    print(f"{s.start:7.2f} {s.end:7.2f} {s.text.strip()}", flush=True)
(ROOT / "assets/face/transcript.json").write_text(json.dumps({"model": name, "segments": out}, ensure_ascii=False, indent=1))
print("DONE", len(out))
