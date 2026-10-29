"""블럭 스타일 쇼츠 엔진 (9:16, 1080x1920).

토킹헤드 녹화 + 설명표(JSON) → 귀여운 블럭 모션그래픽 쇼츠 MP4.
스타일: 두꺼운 테두리 · 파스텔 블럭 · 오프셋 그림자 · 통통 튀며 쌓이는 등장 · 한 글자씩 떨어지는 블럭 제목.

설명표(spec) 예시는 ../runs/20261027-wuxia-showdown/shorts/*.json, 문법은 SKILL.md 참고.

사용:
  python3 block_shorts.py spec.json            # 만들기 (렌더 + 소리 섞기)
  python3 block_shorts.py spec.json --preview  # 렌더 없이 장면 정지 화면 6장만
"""
import html
import json
import math
import os
import subprocess
import sys
import wave
from pathlib import Path
from statistics import median

import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "templates/_assets"
NODE_MODULES = HERE.parent.parent / "examples/motion-masterclass/node_modules"
W, H, FPS, SR = 1080, 1920, 30, 48000
GAP = 0.14  # 조각 사이 숨 쉴 틈

PALETTE = {"ink": "#1d1b2e", "paper": "#fff7e8", "dot": "rgba(29,27,46,.07)", "yellow": "#ffd43b", "mint": "#63e6be",
           "coral": "#ff8787", "sky": "#74c0fc", "lilac": "#b197fc", "white": "#ffffff"}
BLOCK_COLORS = ["yellow", "mint", "sky", "coral", "lilac"]


def esc(t):
    return html.escape(str(t), quote=True)


def run(cmd):
    subprocess.run(cmd, check=True)


# ------------------------------------------------------------------ 소리 효과 (직접 합성 · 저작권 걱정 없음)
def synth_sfx(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)

    def save(name, x):
        p = out_dir / f"{name}.wav"
        if p.exists():
            return
        x = np.clip(x, -1, 1)
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((x * 32767).astype("<i2").tobytes())

    t = np.arange(int(0.16 * SR)) / SR
    f = 900 * np.exp(-t * 18) + 380  # 뽁: 높은 음이 빠르게 떨어짐
    save("pop", 0.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30))
    t = np.arange(int(0.35 * SR)) / SR
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 6)  # 뽀잉
    save("boing", 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7))
    t = np.arange(int(0.05 * SR)) / SR
    save("click", 0.7 * np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 160))
    t = np.arange(int(0.09 * SR)) / SR
    save("brick", 0.5 * (np.sin(2 * np.pi * 520 * t) + 0.5 * np.sin(2 * np.pi * 780 * t)) * np.exp(-t * 45))  # 블럭 딸깍
    t = np.arange(int(0.6 * SR)) / SR
    save("tada", 0.35 * sum(np.sin(2 * np.pi * fr * t) * np.exp(-t * 5) for fr in (523, 659, 784, 1047)))


# ------------------------------------------------------------------ 시간표
def plan(spec):
    """beat마다 [시작, 길이]와 목소리 조각의 장면 안 위치를 계산한다."""
    t = 0.0
    for b in spec["beats"]:
        pieces = b.get("voice", [])
        vlen = sum(y - x for x, y in pieces) + GAP * max(0, len(pieces) - 1)
        b["_start"] = round(t, 3)
        b["_dur"] = round(max(vlen + 0.18, b.get("min", 0.0)), 3)
        b["_vlen"] = vlen
        t += b["_dur"]
    spec["_total"] = round(t, 3)
    return spec


def face_box(spec, beat):
    track = json.loads(Path(spec["face"]["track"]).read_text())
    ts = [p for p in track if any(x - 0.5 <= p["t"] <= y + 0.5 for x, y in beat.get("voice", []))] or track
    return median(p["cx"] for p in ts)


def build_face_and_voice(spec, work):
    """목소리 조각을 이어 붙인 voice.wav와, 같은 구간의 얼굴을 9:16으로 자른 face.mp4를 만든다."""
    src = spec["face"]["src"]
    vparts, aparts, inputs, n = [], [], [], 0
    for b in spec["beats"]:
        pieces = b.get("voice", [])
        cx = face_box(spec, b) if pieces else 960
        x = int(min(max(0, cx - 304), 1920 - 608)) // 2 * 2
        if not pieces:  # 목소리 없는 구간: 무음 + 직전 얼굴 정지 대신 검정 (그 구간은 전체 화면 클립이 덮음)
            inputs += ["-f", "lavfi", "-t", f"{b['_dur']:.3f}", "-i", f"color=c=black:s={W}x{H}:r={FPS}",
                       "-f", "lavfi", "-t", f"{b['_dur']:.3f}", "-i", f"anullsrc=r={SR}:cl=mono"]
            vparts.append(f"[{n}:v]setsar=1[v{n}]")
            aparts.append(f"[{n + 1}:a]aformat=sample_rates={SR}:channel_layouts=mono[a{n}]")
            n += 2
            continue
        for k, (a0, b0) in enumerate(pieces):
            post = GAP if k < len(pieces) - 1 else (b["_dur"] - b["_vlen"])
            dur = b0 - a0 + post
            inputs += ["-ss", f"{a0:.3f}", "-t", f"{dur:.3f}", "-i", src]
            vparts.append(f"[{n}:v]fps={FPS},crop=608:1080:{x}:0,scale={W}:{H},setsar=1[v{n}]")
            # 말이 끝난 뒤 여유 구간은 소리를 줄여 다음 말이 새지 않게
            aparts.append(f"[{n}:a]aformat=sample_rates={SR}:channel_layouts=mono,afade=t=in:d=0.02,"
                          f"afade=t=out:st={max(0.0, b0 - a0 - 0.02):.3f}:d=0.06[a{n}]")
            n += 1
    vl = "".join(p[p.rindex("["):] for p in vparts)
    al = "".join(p[p.rindex("["):] for p in aparts)
    k = len(vparts)
    fv = ";".join(vparts + [vl + f"concat=n={k}:v=1:a=0[vo]"])
    fa = ";".join(aparts + [al + f"concat=n={k}:v=0:a=1[ao]"])
    run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", fv, "-map", "[vo]", "-an", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-t", f"{spec['_total']:.3f}", str(work / "assets/face.mp4")])
    run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", fa, "-map", "[ao]", "-t", f"{spec['_total']:.3f}",
         "-c:a", "pcm_s16le", str(work / "voice.wav")])


# ------------------------------------------------------------------ 화면
CSS = """
@font-face { font-family: "Jua"; src: url("assets/Jua-Regular.ttf"); }
@font-face { font-family: "Pretendard"; src: url("assets/PretendardVariable.woff2") format("woff2"); font-weight: 100 900; }
:root { --ink: %(ink)s; --paper: %(paper)s; --yellow: %(yellow)s; --mint: %(mint)s; --coral: %(coral)s; --sky: %(sky)s; --lilac: %(lilac)s; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--paper); font-family: "Jua", "Pretendard", sans-serif; color: var(--ink); word-break: keep-all; }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--paper); }
.dots { position: absolute; inset: 0; background-image: radial-gradient(%(dot)s 3px, transparent 3.5px); background-size: 44px 44px; }
.blk { border: 7px solid var(--ink); border-radius: 26px; box-shadow: 10px 12px 0 var(--ink); }
.facewrap { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; transform-origin: 0 0; }
.facewrap video { width: 100%%; height: 100%%; object-fit: cover; }
.tile { position: absolute; display: flex; align-items: center; justify-content: center; font-size: 132px; line-height: 1;
  border: 8px solid var(--ink); border-radius: 30px; box-shadow: 10px 12px 0 var(--ink); }
.cap { position: absolute; left: 70px; right: 70px; top: 1150px; display: flex; flex-direction: column; align-items: center; gap: 14px; }
.capline { display: flex; gap: 12px; flex-wrap: nowrap; }
.cw { display: inline-block; padding: 10px 18px 6px; background: #fff; border: 6px solid var(--ink); border-radius: 20px;
  box-shadow: 6px 8px 0 var(--ink); font-size: 66px; line-height: 1.05; white-space: nowrap; }
.cw.hl { background: var(--yellow); }
.win { position: absolute; overflow: hidden; background: #000; }
.win video { width: 100%%; height: 100%%; object-fit: cover; }
.chip { position: absolute; padding: 10px 26px 6px; font-size: 58px; white-space: nowrap; }
.num { position: absolute; left: 14px; top: 12px; width: 64px; height: 64px; border-radius: 16px; border: 5px solid var(--ink);
  background: var(--yellow); font-size: 44px; display: flex; align-items: center; justify-content: center; }
.bar { position: absolute; height: 74px; display: flex; gap: 6px; }
.brick { width: 46px; height: 74px; border: 5px solid var(--ink); border-radius: 10px; box-shadow: 4px 5px 0 var(--ink); }
.blab { position: absolute; font-size: 44px; white-space: nowrap; }
.bval { position: absolute; font-size: 54px; white-space: nowrap; font-family: "Pretendard"; font-weight: 900; }
""" % PALETTE


def split_lines(text, limit=12):
    """세로 화면용 자막 줄 나누기 (한 줄 약 11자, 쉼표·마침표에서 먼저 끊고 단어는 쪼개지 않음)."""
    import re
    # 'Seedance 2.5는'처럼 영어 이름과 숫자는 한 덩어리로 (줄이 바뀌어도 떨어지지 않게)
    text = re.sub(r"([A-Za-z]+) (\d)", lambda m: m.group(1) + "\u00a0" + m.group(2), text.strip())
    clauses = [c for c in re.split(r"(?<=[,.?!])\s+", text) if c]
    lines = []
    for c in clauses:
        cur = ""
        for w in c.split():
            if cur and len(cur) + 1 + len(w) > limit:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            lines.append(cur)
    merged = []
    for ln in lines:
        if merged and len(merged[-1]) + 1 + len(ln) <= limit and (len(ln) <= 4 or len(merged[-1]) <= 4):
            merged[-1] += " " + ln
        else:
            merged.append(ln)
    return [m.replace("\u00a0", " ") for m in merged]


def caption_blocks(b, i, hl_words):
    """자막: 두 줄씩 묶어 블럭 단어로. 단어는 말한 순서대로 '뽁' 튀어나온다."""
    lines = split_lines(b.get("caption", ""))
    if not lines:
        return "", [], []
    groups = [lines[k:k + 2] for k in range(0, len(lines), 2)]
    total_chars = sum(len(x.replace(" ", "")) for x in lines)
    body, js, sfx = [], [], []
    t0, dur = b["_start"] + 0.05, b["_vlen"]
    c = 0
    for g, grp in enumerate(groups):
        gid = f"c{i}_{g}"
        g_chars = sum(len(x.replace(" ", "")) for x in grp)
        gs = t0 + dur * c / total_chars
        ge = t0 + dur * (c + g_chars) / total_chars if g < len(groups) - 1 else b["_start"] + b["_dur"] - 0.02
        body.append(f'<div class="cap" id="{gid}" style="opacity:0">')
        wc = c
        for li, ln in enumerate(grp):
            body.append('<div class="capline">')
            for wi, w in enumerate(ln.split()):
                hl = any(h in w for h in hl_words)
                wid = f"{gid}_{li}_{wi}"
                body.append(f'<span class="cw{" hl" if hl else ""}" id="{wid}">{esc(w)}</span>')
                wt = t0 + dur * wc / total_chars
                js.append(f'tl.fromTo("#{wid}", {{scale: 0.2, y: 40, rotation: {(-5, 4, -3, 5)[wi % 4]}}}, '
                          f'{{scale: 1, y: 0, rotation: {(-2, 1.5, -1, 2)[wi % 4]}, duration: 0.32, ease: "back.out(2.6)"}}, {wt:.3f});')
                wc += len(w)
            body.append("</div>")
        body.append("</div>")
        js.append(f'tl.set("#{gid}", {{opacity: 1}}, {gs:.3f}); tl.to("#{gid}", {{opacity: 0, y: -10, duration: 0.12}}, {max(gs + 0.3, ge - 0.12):.3f});')
        c += g_chars
    return "\n".join(body), js, sfx


def visual(b, i, total):
    """beat 화면 사건. 반환: (html, js, sfx[(t, 이름)], face_mode)"""
    v = b.get("visual", {"type": "face"})
    s, d = b["_start"], b["_dur"]
    typ = v["type"]
    body, js, sfx = [], [], []
    if typ == "title":
        # 블럭 제목: 한 글자씩 블럭이 위에서 떨어져 쌓인다 (머리 위 빈 공간)
        rows = v["rows"]
        y = v.get("y", 300)
        k = 0
        for r, word in enumerate(rows):
            size = 150 if len(word) <= 4 else 118
            gap = 14
            wsum = len(word) * size + (len(word) - 1) * gap
            x0 = (W - wsum) / 2
            for ci, ch in enumerate(word):
                col = PALETTE[BLOCK_COLORS[(k + r) % len(BLOCK_COLORS)]]
                tid = f"t{i}_{k}"
                rot = (-6, 4, -3, 6, -4)[k % 5]
                body.append(f'<div class="tile" id="{tid}" style="left:{x0 + ci * (size + gap):.0f}px; top:{y + r * (size + 26)}px; '
                            f'width:{size}px; height:{size}px; background:{col}; font-size:{int(size * 0.72)}px; transform: rotate({rot}deg); opacity:0">{esc(ch)}</div>')
                at = s + 0.08 + k * 0.09
                js.append(f'tl.fromTo("#{tid}", {{y: -900, opacity: 1, rotation: {rot * 3}}}, {{y: 0, rotation: {rot}, duration: 0.42, ease: "bounce.out"}}, {at:.3f});')
                js.append(f'tl.to("#{tid}", {{y: -40, scale: 0.8, opacity: 0, duration: 0.25, ease: "power2.in"}}, {s + d - 0.3 + k * 0.015:.3f});')
                sfx.append((at + 0.3, "brick"))
                k += 1
        return "\n".join(body), js, sfx, v.get("face", "full")
    if typ in ("clip", "full"):
        full = typ == "full"
        ww, hh = (W, H) if full else (980, 551)
        x, y = (0, 0) if full else ((W - ww) / 2, v.get("y", 560))
        cls = "win" if full else "win blk"
        body.append(f'<div class="{cls}" id="w{i}" style="left:{x:.0f}px; top:{y}px; width:{ww}px; height:{hh}px; opacity:0">'
                    + (f'<img src="assets/{Path(v["src"]).name}" alt="" style="width:100%; height:100%; object-fit:cover" />'
                       if v["src"].endswith((".png", ".jpg")) else
                       f'<video class="clip" src="assets/{Path(v["src"]).name}" data-start="{s:.3f}" data-duration="{d:.3f}" '
                       f'data-media-start="{v.get("from", 0)}" data-track-index="{3 + i % 3}" muted playsinline></video>') + '</div>')
        if full:
            js.append(f'tl.fromTo("#w{i}", {{opacity: 0, scale: 1.08}}, {{opacity: 1, scale: 1, duration: 0.25}}, {s:.3f});')
        else:
            rot = (-3, 3)[i % 2]
            js.append(f'tl.fromTo("#w{i}", {{opacity: 1, scale: 0.4, rotation: {rot * 4}, y: 120}}, {{scale: 1, rotation: {rot / 2}, y: 0, duration: 0.5, ease: "back.out(1.8)"}}, {s:.3f});')
            js.append(f'tl.to("#w{i}", {{rotation: {-rot / 3}, duration: {max(0.5, d - 0.8):.2f}, ease: "sine.inOut"}}, {s + 0.5:.3f});')
            sfx.append((s + 0.05, "pop"))
        js.append(f'tl.to("#w{i}", {{opacity: 0, scale: 0.9, duration: 0.18}}, {s + d - 0.18:.3f});')
        if v.get("label"):
            col = v.get("color", PALETTE["mint"])
            ly = y - 60 if not full else 300
            body.append(f'<div class="chip blk" id="l{i}" style="left:{70 if not full else 60}px; top:{ly}px; background:{col}; opacity:0; transform: rotate(-4deg)">{esc(v["label"])}</div>')
            js.append(f'tl.fromTo("#l{i}", {{opacity: 1, scale: 0, rotation: -20}}, {{scale: 1, rotation: -4, duration: 0.38, ease: "back.out(3)"}}, {s + 0.25:.3f});')
            js.append(f'tl.to("#l{i}", {{opacity: 0, duration: 0.12}}, {s + d - 0.15:.3f});')
            sfx.append((s + 0.3, "pop"))
        if v.get("badge"):
            by = y + 24 if not full else 1000
            body.append(f'<div class="chip blk" id="b{i}" style="right:70px; top:{by}px; background:{v.get("badge_color", PALETTE["yellow"])}; opacity:0; transform: rotate(4deg)">{esc(v["badge"])}</div>')
            at = s + v.get("badge_at", 0.7)
            js.append(f'tl.fromTo("#b{i}", {{opacity: 1, scale: 0, rotation: 30}}, {{scale: 1, rotation: 4, duration: 0.4, ease: "back.out(3)"}}, {at:.3f});')
            js.append(f'tl.to("#b{i}", {{opacity: 0, duration: 0.12}}, {s + d - 0.15:.3f});')
            sfx.append((at + 0.05, "boing"))
        if v.get("stamp"):
            body.append(f'<div class="chip blk" id="st{i}" style="left:50%; top:{y + hh / 2 - 60:.0f}px; background:{PALETTE["coral"]}; color:#fff; '
                        f'font-size:84px; opacity:0; transform: translateX(-50%) rotate(-8deg)">{esc(v["stamp"])}</div>')
            at = s + v.get("stamp_at", 1.2)
            js.append(f'tl.fromTo("#st{i}", {{opacity: 1, scale: 2.6}}, {{scale: 1, duration: 0.25, ease: "power4.in"}}, {at:.3f});')
            js.append(f'tl.to("#st{i}", {{opacity: 0, duration: 0.12}}, {s + d - 0.15:.3f});')
            sfx.append((at + 0.22, "brick"))
        return "\n".join(body), js, sfx, ("hide" if full else v.get("face", "pip"))
    if typ == "grid":
        clips = v["clips"]
        cw, ch, gx, gy = 470, 200, 26, 22
        x0, y0 = (W - 2 * cw - gx) / 2, v.get("y", 250)
        for k, c in enumerate(clips):
            col, row = k % 2, k // 2
            gid = f"g{i}_{k}"
            at = s + 0.1 + k * 0.12
            body.append(f'<div class="win blk" id="{gid}" style="left:{x0 + col * (cw + gx):.0f}px; top:{y0 + row * (ch + gy):.0f}px; width:{cw}px; height:{ch}px; '
                        f'border-width:6px; box-shadow: 7px 8px 0 var(--ink); opacity:0">'
                        f'<video class="clip" src="assets/{Path(c["src"]).name}" data-start="{s:.3f}" data-duration="{d:.3f}" data-media-start="{c.get("from", 2)}" '
                        f'data-track-index="{10 + k}" muted playsinline></video><div class="num">{k + 1}</div></div>')
            js.append(f'tl.fromTo("#{gid}", {{opacity: 1, scale: 0, rotation: {(-8, 8)[k % 2]}}}, {{scale: 1, rotation: {(-1.5, 1.5)[k % 2]}, duration: 0.35, ease: "back.out(2.2)"}}, {at:.3f});')
            js.append(f'tl.to("#{gid}", {{opacity: 0, scale: 0.7, duration: 0.18}}, {s + d - 0.2:.3f});')
            sfx.append((at + 0.05, "pop"))
            if v.get("winner") == k:
                js.append(f'tl.to("#{gid}", {{scale: 1.12, zIndex: 5, boxShadow: "12px 14px 0 #1d1b2e", borderColor: "{PALETTE["yellow"]}", duration: 0.3, ease: "back.out(3)"}}, {s + v.get("winner_at", 1.5):.3f});')
                sfx.append((s + v.get("winner_at", 1.5), "tada"))
        return "\n".join(body), js, sfx, v.get("face", "hide")
    if typ == "bars":
        # 크레딧 막대를 장난감 블럭을 하나씩 끼우듯 쌓는다 (블럭 1개 = unit 크레딧)
        items, unit = v["items"], v.get("unit", 20)
        y0 = v.get("y", 980)
        if v.get("title"):
            body.append(f'<div class="chip blk" id="bt{i}" style="left:70px; top:{y0 - 120}px; background:{PALETTE["sky"]}; opacity:0; transform: rotate(-3deg)">{esc(v["title"])}</div>')
            js.append(f'tl.fromTo("#bt{i}", {{opacity: 1, scale: 0}}, {{scale: 1, duration: 0.35, ease: "back.out(3)"}}, {s:.3f});')
            js.append(f'tl.to("#bt{i}", {{opacity: 0, duration: 0.12}}, {s + d - 0.15:.3f});')
        step = min(0.06, (d * 0.55) / max(1, sum(math.ceil(val / unit) for _, val, *_ in items)))
        t = s + 0.4
        for r, (name, val, *rest) in enumerate(items):
            hl = bool(rest and rest[0])
            yy = y0 + r * 96
            col = PALETTE["yellow"] if hl else PALETTE[BLOCK_COLORS[(r + 1) % len(BLOCK_COLORS)]]
            n = math.ceil(val / unit)
            body.append(f'<div class="blab" id="bl{i}_{r}" style="left:70px; top:{yy + 10}px; opacity:0; {"color:#e8590c;" if hl else ""}">{esc(name)}</div>')
            body.append(f'<div class="bar" id="br{i}_{r}" style="left:400px; top:{yy}px">' +
                        "".join(f'<div class="brick" id="k{i}_{r}_{q}" style="background:{col}; opacity:0"></div>' for q in range(n)) + "</div>")
            body.append(f'<div class="bval" id="bv{i}_{r}" style="left:{400 + n * 52 + 16}px; top:{yy + 6}px; opacity:0">{val}</div>')
            js.append(f'tl.to("#bl{i}_{r}", {{opacity: 1, duration: 0.15}}, {t:.3f});')
            for q in range(n):
                js.append(f'tl.fromTo("#k{i}_{r}_{q}", {{opacity: 1, y: -60, scale: 0.6}}, {{y: 0, scale: 1, duration: 0.18, ease: "back.out(3)"}}, {t:.3f});')
                if q % 2 == 0:
                    sfx.append((t + 0.05, "brick"))
                t += step
            js.append(f'tl.fromTo("#bv{i}_{r}", {{opacity: 1, scale: 0}}, {{scale: 1, duration: 0.25, ease: "back.out(3)"}}, {t:.3f});')
            if hl:
                js.append(f'tl.to("#br{i}_{r}", {{y: -8, repeat: 3, yoyo: true, duration: 0.12}}, {t + 0.2:.3f});')
        js.append(f'tl.to("[id^=bl{i}_], [id^=br{i}_], [id^=bv{i}_]", {{opacity: 0, duration: 0.15}}, {s + d - 0.18:.3f});')
        return "\n".join(body), js, sfx, v.get("face", "pip")
    if typ == "sticker":
        body.append(f'<div class="chip blk" id="sk{i}" style="left:50%; top:{v.get("y", 360)}px; background:{v.get("color", PALETTE["yellow"])}; '
                    f'font-size:{v.get("size", 92)}px; opacity:0; transform: translateX(-50%) rotate(-4deg)">{esc(v["text"])}</div>')
        js.append(f'tl.fromTo("#sk{i}", {{opacity: 1, scale: 0, rotation: -25}}, {{scale: 1, rotation: -4, duration: 0.45, ease: "back.out(3)"}}, {s + v.get("at", 0.2):.3f});')
        js.append(f'tl.to("#sk{i}", {{rotation: 3, yoyo: true, repeat: {max(1, int(d / 0.6))}, duration: 0.3, ease: "sine.inOut"}}, {s + 0.7:.3f});')
        js.append(f'tl.to("#sk{i}", {{opacity: 0, scale: 0.6, duration: 0.15}}, {s + d - 0.18:.3f});')
        sfx.append((s + v.get("at", 0.2) + 0.05, "boing"))
        return "\n".join(body), js, sfx, v.get("face", "full")
    return "", [], [], "full"


def face_js(modes, spec):
    """얼굴 창: full(전체) / pip(위쪽 작은 블럭 창) / hide. 바뀔 때 통통 튀며 줄었다 커진다."""
    js, prev = [], "full"
    pip = {"x": 640, "y": 250, "s": 0.34}
    for b, m in zip(spec["beats"], modes):
        s = b["_start"]
        if m == prev:
            continue
        if m == "pip":
            js.append(f'tl.to("#face", {{x: {pip["x"]}, y: {pip["y"]}, scale: {pip["s"]}, borderRadius: 60, duration: 0.42, ease: "back.out(1.6)"}}, {s:.3f});')
            js.append(f'tl.to("#facebox", {{opacity: 1, duration: 0.1}}, {s + 0.3:.3f});')
        elif m == "full":
            js.append(f'tl.to("#facebox", {{opacity: 0, duration: 0.08}}, {s:.3f});')
            js.append(f'tl.to("#face", {{x: 0, y: 0, scale: 1, borderRadius: 0, opacity: 1, duration: 0.42, ease: "back.out(1.4)"}}, {s:.3f});')
        elif m == "hide":
            js.append(f'tl.to("#facebox", {{opacity: 0, duration: 0.08}}, {s:.3f});')
            js.append(f'tl.to("#face", {{opacity: 0, duration: 0.15}}, {s:.3f});')
        if prev == "hide" and m != "hide":
            js.append(f'tl.to("#face", {{opacity: 1, duration: 0.15}}, {s:.3f});')
        prev = m
    box = (f'<div id="facebox" class="blk" style="position:absolute; left:{pip["x"] - 8}px; top:{pip["y"] - 8}px; width:{W * pip["s"] + 16:.0f}px; '
           f'height:{H * pip["s"] + 16:.0f}px; border-radius:66px; opacity:0; background:transparent"></div>')
    return js, box


def no_immediate(line):
    """fromTo는 기본으로 시작 값을 바로 칠해서, 아직 나올 차례가 아닌 블럭이 미리 보인다. 차례가 될 때만 칠하게 한다."""
    if not line.startswith("tl.fromTo("):
        return line
    k = line.index("}, {") + 4
    return line[:k] + "immediateRender: false, " + line[k:]


def compose(spec, work):
    beats = spec["beats"]
    bodies, js, sfx, modes = [], [], [], []
    hl = spec.get("highlight_words", [])
    for i, b in enumerate(beats):
        h, j, s, m = visual(b, i, spec["_total"])
        bodies.append(h)
        js += j
        sfx += s
        modes.append(m)
        ch, cj, _ = caption_blocks(b, i, hl)
        bodies.append(ch)
        js += cj
    fjs, fbox = face_js(modes, spec)
    total = spec["_total"]
    page = f"""<!doctype html>
<html lang="ko" data-resolution="portrait">
<head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="short" data-start="0" data-duration="{total:.3f}" data-width="1080" data-height="1920">
<div class="dots"></div>
<div class="facewrap" id="face"><video class="clip" src="assets/face.mp4" data-start="0" data-duration="{total:.3f}" data-track-index="1" muted playsinline></video></div>
{fbox}
{chr(10).join(bodies)}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(fjs + [no_immediate(x) for x in js])}
tl.set({{}}, {{}}, {total:.3f});
window.__timelines = window.__timelines || {{}};
window.__timelines["short"] = tl;
}})();
</script>
</body></html>
"""
    (work / "index.html").write_text(page)
    return sfx


def mix(spec, work, sfx, out):
    total = spec["_total"]
    n = int(total * SR)
    bed = np.zeros(n, dtype=np.float32)

    def rd(p):
        with wave.open(str(p)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
            if w.getnchannels() == 2:
                x = x.reshape(-1, 2).mean(axis=1)
            if w.getframerate() != SR:
                x = np.interp(np.arange(0, len(x), w.getframerate() / SR), np.arange(len(x)), x)
            return x

    voice = rd(work / "voice.wav")[:n]
    if spec.get("music"):
        m = rd(spec["music"])
        m = np.take(m, np.arange(n) % len(m))
        env = np.convolve(np.abs(np.pad(voice, (0, n - len(voice)))), np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
        bed += m * spec.get("music_gain", 0.16) * (1 - 0.55 * np.clip(env / 0.01, 0, 1))
    for t, name in sfx:
        x = rd(HERE / "sfx" / f"{name}.wav") * {"pop": 0.35, "boing": 0.3, "click": 0.4, "brick": 0.22, "tada": 0.35}[name]
        i = int(t * SR)
        if 0 <= i < n:
            bed[i:i + len(x)] += x[: n - i]
    for b in spec["beats"]:  # 전체 화면 클립 소리
        v = b.get("visual", {})
        if v.get("type") == "full" and v.get("audio"):
            tmp = work / f"clip_{b['_start']:.0f}.wav"
            run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(v.get("from", 0)), "-t", f"{b['_dur']:.3f}", "-i", v["src"], "-vn", "-ac", "1", "-ar", str(SR), str(tmp)])
            x = rd(tmp) * 0.6
            i = int(b["_start"] * SR)
            bed[i:i + len(x)] += x[: n - i]
    full = np.pad(voice, (0, max(0, n - len(voice))))[:n] + bed
    with wave.open(str(work / "mix.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(full, -1, 1) * 32767).astype("<i2").tobytes())
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(work / "render.mp4"), "-i", str(work / "mix.wav"),
         "-filter_complex", "[1:a]highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.89:level=false[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)])


def main():
    spec_path = Path(sys.argv[1]).resolve()
    spec = plan(json.loads(spec_path.read_text()))
    work = spec_path.parent / f"work_{spec['id']}"
    (work / "assets").mkdir(parents=True, exist_ok=True)
    synth_sfx(HERE / "sfx")
    for f in (ASSETS / "fonts/Jua-Regular.ttf", HERE.parent / "runs/20261027-wuxia-showdown/edit/assets/fonts/PretendardVariable.woff2"):
        dst = work / "assets" / f.name
        if not dst.exists():
            os.symlink(f, dst)
    for b in spec["beats"]:
        v = b.get("visual", {})
        for c in ([v] if "src" in v else []) + v.get("clips", []):
            dst = work / "assets" / Path(c["src"]).name
            if not dst.exists():
                os.symlink(Path(c["src"]).resolve(), dst)
    if not (work / "node_modules").is_symlink():
        os.symlink(NODE_MODULES, work / "node_modules")
    build_face_and_voice(spec, work)
    sfx = compose(spec, work)
    print(f"{spec['id']}: {spec['_total']:.1f}s, beats {len(spec['beats'])}")
    if "--preview" in sys.argv:
        return
    env = dict(os.environ)
    env.setdefault("HYPERFRAMES_BROWSER_PATH", "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell")
    env.setdefault("PRODUCER_HEADLESS_SHELL_PATH", env["HYPERFRAMES_BROWSER_PATH"])
    subprocess.run(["npx", "hyperframes", "render", "--output", str(work / "render.mp4")], cwd=work, env=env, check=True)
    out = spec_path.parent / f"{spec['id']}.mp4"
    mix(spec, work, sfx, out)
    print("done", out)


if __name__ == "__main__":
    main()
