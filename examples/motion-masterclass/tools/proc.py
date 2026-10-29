"""단아쌤 무음 규칙(EDIT-001): -60dB/0.3s로 찾고, 앞 무음은 첫소리 앞 0.12s만 남기고,
뒤 무음은 0.6s 넘을 때만 무음 시작 + 0.3s에서 자른다. 10ms 페이드인, 80ms 페이드아웃."""
import json, re, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
out = {}
for wav in sorted((root / "raw").glob("B*.wav")):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                               capture_output=True, text=True).stdout)
    log = subprocess.run(["ffmpeg", "-i", str(wav), "-af", "silencedetect=noise=-60dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    a, b = 0.0, dur
    if starts and starts[0] <= 0.01 and ends and ends[0] > 0.3:
        a = max(0.0, ends[0] - 0.12)
    if starts and starts[-1] > a and (len(ends) < len(starts) or ends[-1] >= dur - 0.01) and dur - starts[-1] > 0.6:
        b = starts[-1] + 0.3
    length = b - a
    dst = root / "assets" / "audio" / wav.name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ss", f"{a:.3f}", "-t", f"{length:.3f}",
                    "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(0, length - 0.08):.3f}:d=0.08",
                    "-ar", "48000", "-ac", "1", str(dst)], check=True)
    out[wav.stem] = round(length, 3)
    print(f"{wav.stem}: raw {dur:.2f}s -> {length:.2f}s (cut {a:.2f}..{b:.2f})")
(root / "assets" / "audio" / "durations.json").write_text(json.dumps(out, indent=1))
