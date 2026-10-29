"""Procedural SFX + BGM for the 60s drama (no AI models, numpy only)."""
import sys, wave, numpy as np

SR = 48000
OUT = sys.argv[1]
END = 4 * 15.0417
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(d * SR)) / SR


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.exp(-np.linspace(0, 6, nr))
    return e


def lp(x, k):  # simple one-pole lowpass, k in (0,1)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc); y[i] = acc
    return y


def noise(d):
    return rng.standard_normal(int(d * SR))


def drum(f0=58, d=0.9, amp=1.0):  # taiko-ish
    tt = t(d)
    f = f0 * (1 + 1.5 * np.exp(-tt * 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5)
    hit = lp(noise(d), 0.15) * np.exp(-tt * 40) * 0.6
    return (body + hit) * amp


def whoosh(d=0.7):
    tt = t(d); n = noise(d)
    k = 0.02 + 0.25 * np.sin(np.pi * tt / d) ** 2
    y = np.empty_like(n); acc = 0.0
    for i, v in enumerate(n):
        acc += k[i] * (v - acc); y[i] = acc
    return y * np.sin(np.pi * tt / d) ** 1.5 * 2.2


def snap():
    tt = t(0.12)
    return (noise(0.12) - lp(noise(0.12), 0.3)) * np.exp(-tt * 60) * 1.4 + np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 80) * 0.5


def thud():
    return drum(70, 0.4, 0.9)


def boom(d=1.6):
    tt = t(d)
    sub = np.sin(2 * np.pi * (42 + 30 * np.exp(-tt * 8)) * tt) * np.exp(-tt * 2.5)
    crack = lp(noise(d), 0.35) * np.exp(-tt * 9) * 0.9
    return (sub * 1.3 + crack)


def ding():
    tt = t(0.6)
    return (np.sin(2 * np.pi * 1320 * tt) + 0.4 * np.sin(2 * np.pi * 2640 * tt)) * np.exp(-tt * 7) * 0.45


def puff():
    tt = t(0.35)
    return lp(noise(0.35), 0.06) * np.sin(np.pi * tt / 0.35) * 0.9


def blowout(d=0.9):
    tt = t(d)
    return lp(noise(d), 0.08) * np.sin(np.pi * tt / d) ** 0.7 * 1.6


def tension(d=1.4):
    tt = t(d)
    return (np.sin(2 * np.pi * 41 * tt) + 0.5 * np.sin(2 * np.pi * 61.5 * tt)) * np.minimum(tt / 0.3, 1) * np.exp(-tt * 1.2) * 0.9


def place(buf, x, at, gain=1.0):
    i = int(at * SR); j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * gain


N = int(END * SR) + SR
sfx = np.zeros(N)
O = [k * 15.0417 for k in range(4)]
# C1 bamboo night
place(sfx, whoosh(0.8), O[0] + 0.0, 0.8)
place(sfx, whoosh(0.6), O[0] + 2.4, 0.6)
place(sfx, whoosh(0.6), O[0] + 4.3, 0.5)
place(sfx, thud(), O[0] + 6.1, 0.8)
# C2
place(sfx, snap(), O[1] + 3.55, 1.0)
place(sfx, ding(), 22.49, 0.9)
# C3
place(sfx, drum(90, 0.5, 1.0) + 0, O[2] + 0.25, 1.0)  # door slam
place(sfx, boom(), O[2] + 4.1, 1.0)                      # palm wind
place(sfx, tension(), 43.6, 0.9)
# C4
place(sfx, puff(), 47.62, 0.9)
place(sfx, boom(1.2), 52.0, 0.8)   # reveal hit
place(sfx, blowout(), O[3] + 10.25, 1.0)
place(sfx, drum(52, 2.0, 1.4), END - 0.75, 1.0)  # final 둥

# wind bed for C1
w = lp(noise(15.0), 0.01) * 3.0
w *= np.minimum(t(15.0) / 1.0, 1) * np.minimum((15.0 - t(15.0)) / 1.0, 1)
place(sfx, w, 0.0, 0.35)

# BGM: drone + drum patterns
bgm = np.zeros(N)
tt = np.arange(N) / SR
drone = (np.sin(2 * np.pi * 73.42 * tt) + 0.6 * np.sin(2 * np.pi * 110.0 * tt + 0.3) +
         0.3 * np.sin(2 * np.pi * 146.8 * tt * 1.003)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt))
lvl = np.interp(tt, [0, 2, 15, 30, 45, 55.3, 56.0, END + 1], [0, .22, .25, .2, .22, .26, 0, 0])
bgm += drone * lvl


def pattern(start, end, bpm, accents, gain):
    beat = 60 / bpm; b = 0; x = start
    while x < end:
        a = accents[b % len(accents)]
        if a: place(bgm, drum(58 if a > 1 else 75, 0.6, 0.5 * a), x, gain)
        x += beat / 2; b += 1


pattern(1.0, 15.0, 60, [1, 0, 0, 0, 1, 0, 0, 0], 0.35)                 # heartbeat
pattern(15.04, 30.0, 100, [2, 0, 1, 0, 0, 1, 1, 0], 0.4)               # light groove
pattern(30.08, 45.0, 120, [2, 0, 1, 1, 2, 0, 1, 0], 0.5)               # heavy
pattern(45.13, 55.3, 120, [2, 1, 1, 1, 2, 1, 2, 1], 0.55)              # intensify

for name, x in [('sfx', sfx), ('bgm', bgm)]:
    x = x / max(1e-9, np.abs(x).max()) * 0.9
    st = np.stack([x, x], 1)
    st = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(f'{OUT}/{name}.wav', 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(st.tobytes())
print('ok')
