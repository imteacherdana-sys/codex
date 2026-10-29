"""배경음악과 효과음을 numpy로 직접 합성한다 (외부 음원·라이선스 없음).

- bgm_wuxia.wav: 오음계 뜯는 현(카플러스-스트롱) + 낮은 북 + 패드, 96 BPM, 약 64초 루프
- bgm_calm.wav: 같은 음계의 느린 패드와 드문 현, 설명 구간용
- sfx_*.wav: 휙(전환), 쾅(도장), 딩(공개), 틱(숫자), 붓(먹물 번짐)

사용: python3 tools/synth_audio.py assets/audio
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(20261028)


def write(path, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 0.89
    data = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def onepole_lp(x, a):
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        s += a * (v - s)
        y[i] = s
    return y


def pluck(freq, dur, bright=0.5, decay=0.996):
    n = int(SR * dur)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    buf = onepole_lp(buf, bright)
    out = np.empty(n)
    idx = 0
    for i in range(n):
        out[i] = buf[idx]
        nxt = (idx + 1) % period
        buf[idx] = decay * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    env = np.minimum(1.0, np.arange(n) / (0.003 * SR))
    return out * env


def tone(freq, dur, kind="sine"):
    t = np.arange(int(SR * dur)) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * freq * t)
    # 부드러운 패드: 약간 어긋난 사인 3개
    return (np.sin(2 * np.pi * freq * t) + 0.6 * np.sin(2 * np.pi * freq * 1.003 * t + 1.1)
            + 0.4 * np.sin(2 * np.pi * freq * 2.001 * t + 0.4)) / 2.0


def adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.linspace(1, 0, nr)
    return e


def drum(dur=0.6, f0=95, f1=45):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.15 * rng.uniform(-1, 1, n) * np.exp(-t * 40)


def place(track, clip, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    j = min(len(track), i + len(clip))
    if i >= len(track):
        return
    l, r = (1 - max(0, pan)), (1 + min(0, pan))
    track[i:j, 0] += clip[: j - i] * gain * l
    track[i:j, 1] += clip[: j - i] * gain * r


# D 오음계 (D E F# A B)
SCALE = [146.83, 164.81, 185.00, 220.00, 246.94, 293.66, 329.63, 369.99, 440.00, 493.88]


def bgm_wuxia(seconds=64.0, bpm=96):
    tr = np.zeros((int(SR * seconds), 2))
    beat = 60 / bpm
    bars = int(seconds / (beat * 4))
    # 패드: 두 마디마다 D / B 근음 교대
    for b in range(0, bars, 2):
        root = 73.42 if (b // 2) % 2 == 0 else 61.74
        d = beat * 8
        p = (tone(root, d, "pad") + 0.5 * tone(root * 1.5, d, "pad")) * adsr(int(SR * d), 1.2, 1.5)
        place(tr, p, b * beat * 4, 0.16)
    # 북: 1·3박 + 마디 끝 장식
    for b in range(bars):
        t0 = b * beat * 4
        place(tr, drum(), t0, 0.55)
        place(tr, drum(0.4, 120, 60), t0 + beat * 2, 0.35)
        if b % 4 == 3:
            place(tr, drum(0.25, 160, 80), t0 + beat * 3.5, 0.3)
    # 현: 8분음표 패턴, 마디마다 음형이 조금씩 바뀜
    motif = [0, 2, 3, 2, 4, 3, 2, 1]
    for b in range(bars):
        shift = [0, 2, 1, 3][b % 4]
        for k, m in enumerate(motif):
            if (b + k) % 5 == 4:
                continue
            f = SCALE[min(len(SCALE) - 1, m + shift)]
            place(tr, pluck(f, 1.4, 0.55, 0.9965), b * beat * 4 + k * beat / 2, 0.32, pan=(-0.3 if k % 2 else 0.3))
    # 루프 경계 페이드
    fade = int(SR * 0.05)
    tr[:fade] *= np.linspace(0, 1, fade)[:, None]
    tr[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return tr


def bgm_calm(seconds=64.0):
    tr = np.zeros((int(SR * seconds), 2))
    chords = [(73.42, 110.0, 146.83), (61.74, 92.5, 123.47), (82.41, 123.47, 164.81), (73.42, 110.0, 185.0)]
    seg = seconds / len(chords)
    for i, ch in enumerate(chords):
        for f in ch:
            p = tone(f, seg + 2, "pad") * adsr(int(SR * (seg + 2)), 2.0, 2.5)
            place(tr, p, i * seg, 0.12)
    t = 0.0
    k = 0
    while t < seconds - 3:
        place(tr, pluck(SCALE[[5, 7, 6, 8, 4, 6][k % 6]], 2.5, 0.35, 0.9975), t, 0.22, pan=(0.25 if k % 2 else -0.25))
        t += [2.0, 1.5, 3.0, 2.5][k % 4]
        k += 1
    fade = int(SR * 0.05)
    tr[:fade] *= np.linspace(0, 1, fade)[:, None]
    tr[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return tr


def sfx_whoosh(dur=0.7):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.uniform(-1, 1, n)
    # 빠르게 열렸다 닫히는 저역통과
    a = 0.02 + 0.5 * np.sin(np.pi * t / dur) ** 2
    y = np.empty(n)
    s = 0.0
    for i in range(n):
        s += a[i] * (noise[i] - s)
        y[i] = s
    return y * np.sin(np.pi * t / dur) ** 1.5


def sfx_stamp():
    return drum(0.5, 140, 50)


def sfx_ding():
    d = 1.6
    return (tone(1318.5, d) + 0.5 * tone(1975.5, d) + 0.25 * tone(2637, d)) * np.exp(-np.arange(int(SR * d)) / SR * 3.5)


def sfx_tick():
    n = int(SR * 0.05)
    return rng.uniform(-1, 1, n) * np.exp(-np.arange(n) / SR * 120)


def sfx_brush():
    n = int(SR * 0.9)
    t = np.arange(n) / SR
    y = onepole_lp(rng.uniform(-1, 1, n), 0.08)
    return y * np.exp(-((t - 0.25) ** 2) / 0.04)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/audio")
    out.mkdir(parents=True, exist_ok=True)
    write(out / "bgm_wuxia.wav", bgm_wuxia())
    write(out / "bgm_calm.wav", bgm_calm())
    write(out / "sfx_whoosh.wav", sfx_whoosh())
    write(out / "sfx_stamp.wav", sfx_stamp())
    write(out / "sfx_ding.wav", sfx_ding())
    write(out / "sfx_tick.wav", sfx_tick())
    write(out / "sfx_brush.wav", sfx_brush())
    print("done", sorted(p.name for p in out.glob("*.wav")))
