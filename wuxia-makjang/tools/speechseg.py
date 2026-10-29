"""Find voiced (speech-like) segments in a clip's native audio. Prints JSON list of [start, end]."""
import sys, json, subprocess, numpy as np

p = sys.argv[1]
SR = 16000
raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-af', 'highpass=f=80,lowpass=f=3500', '-f', 's16le', '-'],
                     capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
hop, win = 320, 640
flags = []
for i in range(0, len(x) - win, hop):
    f = x[i:i + win] - x[i:i + win].mean()
    r = np.sqrt((f ** 2).mean())
    if r < 0.015:
        flags.append(0); continue
    ac = np.correlate(f, f, 'full')[win - 1:]
    lo, hi = SR // 400, SR // 75
    k = lo + np.argmax(ac[lo:hi])
    flags.append(1 if ac[k] > 0.45 * ac[0] else 0)
fl = np.array(flags)
# smooth: majority over 5 frames
sm = np.convolve(fl, np.ones(5) / 5, 'same') > 0.4
segs, st = [], None
for i, v in enumerate(sm):
    t = i * hop / SR
    if v and st is None: st = t
    if not v and st is not None:
        segs.append([st, t]); st = None
if st is not None: segs.append([st, len(sm) * hop / SR])
merged = []
for s in segs:
    if merged and s[0] - merged[-1][1] < 0.3: merged[-1][1] = s[1]
    else: merged.append(s)
merged = [[round(a, 2), round(b, 2)] for a, b in merged if b - a >= 0.35]
print(json.dumps(merged))
