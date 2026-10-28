"""media.json에 적힌 클립을 assets/clips/<key>.mp4로 내려받는다. 이미 있으면 건너뛴다.

사용: python3 tools/fetch.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
media = json.loads((ROOT / "media.json").read_text())
out = ROOT / "assets" / "clips"
out.mkdir(parents=True, exist_ok=True)
for key, item in media.items():
    if key.startswith("_"):
        continue
    dest = out / f"{key}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        continue
    subprocess.run(["curl", "-sSf", "-o", str(dest), item["url"]], check=True)
    print("got", key)
