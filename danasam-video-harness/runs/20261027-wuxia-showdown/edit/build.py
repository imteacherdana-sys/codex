"""무협 쇼다운 완성본 생성기.

장면(segment)마다 HyperFrames 프로젝트 하나를 segments/NN-이름/에 만든다.
렌더링은 tools/render.sh, 이어 붙이기와 음악·효과음 믹스는 tools/assemble.py.

자막(cap)은 단아쌤이 나중에 녹음할 멘트 그대로다. 녹음본으로 덮어쓸 때 장면 길이를 바꾸려면
아래 SCENES의 문장만 고치고 다시 실행한다.

사용: python3 build.py            # 전체 생성
      python3 build.py 07 12      # 번호가 07, 12인 장면만
"""
import html
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEG = ROOT / "segments"
NODE_MODULES = (ROOT / "../../../../examples/motion-masterclass/node_modules").resolve()

MODELS = {
    "kling4_0": ("Kling 4.0", "#b4e61d"),
    "seedance_2_5": ("Seedance 2.5", "#ff6b5b"),
    "seedance_2_0": ("Seedance 2.0", "#ffa58f"),
    "minimax_h3": ("MiniMax H3", "#3fd6c6"),
    "wan3_0": ("Wan 3.0", "#ffbf3c"),
    "grok_video_v15": ("Grok Imagine 1.5", "#c9a7ff"),
    "flux_3_video": ("FLUX 3", "#e8e8f2"),
    "gemini_omni_flash_1_1": ("Gemini Omni 1.1", "#5b8cff"),
}
# 8초 한 클립 견적 (Higgsfield, 2026-10-27~28). R4는 Reference 모드 가격
CREDITS = {
    "r1": {"kling4_0": 4, "seedance_2_5": 56, "seedance_2_0": 36, "minimax_h3": 16, "wan3_0": 14, "grok_video_v15": 36,
           "flux_3_video": 48, "gemini_omni_flash_1_1": 24},
}
CREDITS["r2"] = CREDITS["r3"] = CREDITS["r5"] = CREDITS["r1"]
# R4 Gemini는 안전 필터로 2회 거절, 크레딧 환불 → 0
CREDITS["r4"] = dict(CREDITS["r1"], kling4_0=18, gemini_omni_flash_1_1=0)
TOTAL = {m: sum(CREDITS[r][m] for r in ("r1", "r2", "r3", "r4", "r5")) for m in MODELS}
# 결과가 없는 칸
FAILED = {("r4", "gemini_omni_flash_1_1"): "안전 필터로 생성 거절 (2회 시도)"}
# 블라인드 번호 (1..8) → 모델 (라운드마다 다르게 섞음)
BLIND = {
    "r1": ["seedance_2_0", "minimax_h3", "flux_3_video", "gemini_omni_flash_1_1", "seedance_2_5", "grok_video_v15", "wan3_0", "kling4_0"],
    "r2": ["wan3_0", "kling4_0", "flux_3_video", "minimax_h3", "seedance_2_0", "grok_video_v15", "seedance_2_5", "gemini_omni_flash_1_1"],
    "r3": ["flux_3_video", "seedance_2_5", "grok_video_v15", "kling4_0", "gemini_omni_flash_1_1", "seedance_2_0", "wan3_0", "minimax_h3"],
    "r4": ["flux_3_video", "gemini_omni_flash_1_1", "seedance_2_0", "kling4_0", "minimax_h3", "grok_video_v15", "seedance_2_5", "wan3_0"],
    "r5": ["seedance_2_0", "grok_video_v15", "gemini_omni_flash_1_1", "seedance_2_5", "wan3_0", "flux_3_video", "kling4_0", "minimax_h3"],
}
ROUND_NAME = {"r1": "시험 1 · 장풍", "r2": "시험 2 · 경공", "r3": "시험 3 · 비무", "r4": "시험 4 · Reference", "r5": "시험 5 · 현판"}
# 라운드 1등 (1차 채점, 단아쌤 확인 필요)
WINNERS = {"r1": ["flux_3_video"], "r2": ["seedance_2_0"], "r3": ["kling4_0"], "r4": ["kling4_0", "flux_3_video", "wan3_0"], "r5": ["kling4_0"]}
# 현판 글자를 정확히 쓴 모델 (1등과 별개)
R5_CORRECT = ["kling4_0", "seedance_2_5", "grok_video_v15", "flux_3_video", "gemini_omni_flash_1_1"]

PROMPTS = {
    "r1": ("A Chinese woman in her early 20s ... stands in a misty bamboo forest at dawn. She draws a slow breath, "
           "then thrusts both palms forward. A visible wave of air bursts from her palms, bending the bamboo stalks "
           "and sending a storm of green leaves flying away from her. ... Low-angle shot, slow motion at the moment of release.",
           ["visible wave of air", "bending the bamboo", "Low-angle shot"]),
    "r2": ("A Chinese woman in her early 20s ... runs lightly across the curved gray tile roofs of an ancient Chinese town "
           "at sunset, leaps from one eave to the next with her robe trailing, lands softly, then sprints across the surface "
           "of a lotus pond, each step leaving small ripples without sinking.",
           ["runs lightly across", "leaps from one eave", "sprints across the surface"]),
    "r3": ("Two martial artists face each other ... Both hold wooden practice swords. First they bow. Then they exchange "
           "exactly five fast strikes and parries. On the fifth strike time freezes for a moment with falling autumn leaves "
           "suspended in the air while the camera circles around them, then time resumes and they salute each other.",
           ["First they bow", "exactly five", "time freezes", "camera circles", "salute each other"]),
    "r4": ("Use the two reference images for the woman in white and the man in dark navy. Shot 1: she walks onto an arched "
           "stone bridge. Shot 2: he approaches and stops facing her. Shot 3: close-up, they look at each other. "
           "Keep both faces, hair and clothes exactly as in the references in every shot.",
           ["two reference images", "Shot 3: close-up", "exactly as in the references"]),
    "r5": ("Inside an old wooden inn in a wuxia town, a wooden signboard above the door reads \"단아객잔\" in black Korean "
           "letters. Below it, a Chinese woman pours tea from a clay teapot into a small cup with one hand, steam rising. "
           "Close-up on her hands and the cup, then tilt up to the signboard.",
           ["\"단아객잔\"", "Korean letters", "tilt up to the signboard"]),
}

CPS = 6.2  # 자막 읽기 속도 (글자/초) — 녹음 멘트 길이의 추정치


CAP_MAX_PX = 1560  # 자막 한 줄 최대 폭 (42px Pretendard 기준 추정)


def cap_width(t):
    w = 0.0
    for ch in t:
        if "\uac00" <= ch <= "\ud7a3":
            w += 41
        elif ch == " ":
            w += 12
        elif ch.isdigit():
            w += 25
        elif ch.isascii() and ch.isalpha():
            w += 25 if ch.isupper() else 22
        else:
            w += 16
    return w + 56


def line_dur(t):
    return max(2.4, len(t.replace(" ", "")) / CPS + 0.7)


def esc(t):
    return html.escape(t, quote=True)


def clip_len(key):
    p = ROOT / "assets" / "clips" / f"{key}.mp4"
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


# ------------------------------------------------------------------ 공통 HTML
HEAD = """<!doctype html>
<html lang="ko" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face { font-family: "Pretendard"; src: url("assets/fonts/PretendardVariable.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "NanumPen"; src: url("assets/fonts/NanumPenScript-korean.woff2") format("woff2"); }
@font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"); }
:root { --bg0: #0b1026; --bg1: #05060f; --grid: rgba(124,58,237,.12); --violet: #7c3aed; --purple: #4a33a6;
  --lime: #b4e61d; --coral: #ff6b5b; --fg: #f5f3ff; --mute: #a5a3c7; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--bg1); font-family: "Pretendard", sans-serif; color: var(--fg); word-break: keep-all; }
#root { position: relative; width: 1920px; height: 1080px; overflow: hidden; }
.ground { position: absolute; inset: 0; background: linear-gradient(var(--bg0), var(--bg1)); }
.gridbg { position: absolute; inset: -80px; background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 48px 48px; -webkit-mask-image: radial-gradient(ellipse at 50% 50%, #000 25%, transparent 72%); mask-image: radial-gradient(ellipse at 50% 50%, #000 25%, transparent 72%); }
.cam { position: absolute; inset: 0; transform-origin: 50% 50%; }
.cap { position: absolute; left: 160px; right: 160px; bottom: 64px; display: flex; justify-content: center; }
.cap span { display: inline-block; white-space: nowrap; padding: 14px 28px 16px; border-radius: 14px; background: rgba(5,6,15,.78);
  font-size: 42px; font-weight: 700; line-height: 1.38; text-align: center; letter-spacing: -0.01em; box-shadow: 0 10px 30px rgba(0,0,0,.35); }
.chip { display: inline-flex; align-items: center; gap: 10px; padding: 10px 18px; border-radius: 12px; font-weight: 800; font-size: 30px; }
.tag { position: absolute; left: 60px; top: 44px; font-size: 24px; font-weight: 700; color: var(--mute); letter-spacing: .04em; }
.frame { position: absolute; border-radius: 22px; overflow: hidden; background: #000; box-shadow: 0 30px 80px rgba(0,0,0,.5), inset 0 0 0 2px rgba(255,255,255,.08); }
.frame video, .frame img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }
.hl { background: linear-gradient(transparent 55%, rgba(180,230,29,.55) 55%); }
</style>
</head>
<body>
"""


def page(cid, dur, body, script, extra_style=""):
    return (HEAD.replace("</style>", extra_style + "\n</style>") +
            f'<div id="root" data-composition-id="{cid}" data-start="0" data-duration="{dur:.2f}" data-width="1920" data-height="1080">\n'
            f'<div class="ground"></div><div class="gridbg" id="gridbg"></div>\n{body}\n</div>\n'
            '<script>\n(function(){\nconst tl = gsap.timeline({ paused: true });\n'
            f'{script}\nwindow.__timelines = window.__timelines || {{}};\nwindow.__timelines["{cid}"] = tl;\n}})();\n</script>\n</body>\n</html>\n')


class Scene:
    def __init__(self, num, name, kind, caps=(), min_dur=0.0, lead=0.4, tail=0.5, sfx=(), music="calm", **kw):
        self.num, self.name, self.kind, self.caps = num, name, kind, list(caps)
        self.kw = kw
        self.sfx = list(sfx)
        self.music = music
        t = lead
        self.cap_times = []
        for c in self.caps:
            if cap_width(c) > CAP_MAX_PX:
                raise ValueError(f"자막이 한 줄을 넘습니다 ({cap_width(c):.0f}px): {c}")
            d = line_dur(c)
            self.cap_times.append((t, d))
            t += d
        self.dur = max(min_dur, t + tail)
        self.lead = lead

    @property
    def cid(self):
        return f"s{self.num:02d}"

    def caption_html(self):
        out = []
        for i, (c, (t, d)) in enumerate(zip(self.caps, self.cap_times)):
            out.append(f'<div class="cap clip" id="cap{i}" data-start="{t:.2f}" data-duration="{d:.2f}" data-track-index="9"><span>{esc(c)}</span></div>')
        return "\n".join(out)

    def caption_js(self):
        js = []
        for i, (t, d) in enumerate(self.cap_times):
            js.append(f'tl.fromTo("#cap{i} span", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: 0.25, ease: "power2.out"}}, {t:.2f});')
        return "\n".join(js)


def cam_js(move, dur):
    """장면마다 카메라 동작 하나 (MOTION-006)."""
    if move == "push":
        return f'tl.fromTo("#cam", {{scale: 1.0}}, {{scale: 1.06, duration: {dur:.2f}, ease: "sine.inOut"}}, 0);'
    if move == "pull":
        return f'tl.fromTo("#cam", {{scale: 1.07}}, {{scale: 1.0, duration: {dur:.2f}, ease: "sine.inOut"}}, 0);'
    if move == "pan":
        return f'tl.fromTo("#cam", {{x: 40, scale: 1.04}}, {{x: -40, scale: 1.04, duration: {dur:.2f}, ease: "sine.inOut"}}, 0);'
    if move == "punch":
        return (f'tl.fromTo("#cam", {{scale: 1.0}}, {{scale: 1.05, duration: 0.35, ease: "power2.out"}}, 0.6);'
                f'tl.to("#cam", {{scale: 1.02, duration: {max(0.5, dur - 1.2):.2f}, ease: "sine.inOut"}}, 0.95);')
    return ""


def gridbg_js(dur):
    return f'tl.fromTo("#gridbg", {{x: 0, y: 0}}, {{x: -48, y: -24, duration: {dur:.2f}, ease: "none"}}, 0);'


# ------------------------------------------------------------------ 장면 종류
def render_talk(s):
    k = s.kw
    kicker = esc(k.get("kicker", ""))
    title = k.get("title", "")
    sub = esc(k.get("sub", ""))
    img = k.get("img")
    title_html = esc(title)
    for h in k.get("hl", []):
        title_html = title_html.replace(esc(h), f'<span class="hl">{esc(h)}</span>')
    body = ['<div class="cam" id="cam">']
    if img:
        body.append(f'<div class="frame" id="img" style="left:{k.get("img_x", 1060)}px; top:150px; width:{k.get("img_w", 760)}px; height:{k.get("img_h", 560)}px;">'
                    f'<img src="assets/images/{img}" alt="" style="object-fit:{k.get("fit", "cover")}" /></div>')
        tx, tw, align = 140, 860, "left"
    else:
        tx, tw, align = 160, 1600, "center"
    body.append(f'<div id="txt" style="position:absolute; left:{tx}px; width:{tw}px; top:{k.get("top", 300 if img else 380)}px; text-align:{align};">'
                f'<div id="kicker" style="display:inline-block; padding:10px 18px; border-radius:10px; background:var(--lime); color:#05060f; font-size:30px; font-weight:800;">{kicker}</div>'
                f'<div id="title" style="margin-top:28px; font-size:{k.get("size", 88)}px; font-weight:900; line-height:1.18; letter-spacing:-0.02em;">{title_html}</div>'
                f'<div id="sub" style="margin-top:26px; font-size:36px; font-weight:600; color:var(--mute); line-height:1.4;">{sub}</div></div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js(k.get("cam", "push"), s.dur),
          'tl.fromTo("#kicker", {opacity: 0, x: -30}, {opacity: 1, x: 0, duration: 0.4, ease: "expo.out"}, 0.15);',
          'tl.fromTo("#title", {opacity: 0, y: 40, filter: "blur(8px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out"}, 0.3);',
          'tl.fromTo("#sub", {opacity: 0}, {opacity: 1, duration: 0.5}, 0.8);']
    if img:
        js.append('tl.fromTo("#img", {opacity: 0, y: 60, rotation: 3}, {opacity: 1, y: 0, rotation: 1.2, duration: 0.8, ease: "expo.out"}, 0.2);')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_clip(s):
    k = s.kw
    key = k["key"]
    model = k.get("model")
    if key is None:
        # 생성 결과가 없는 칸 (안전 필터 거절 등)
        body = ['<div class="cam" id="cam">',
                '<div class="frame" id="fr" style="left:160px; top:60px; width:1600px; height:900px; background:#10142e;">'
                f'<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:18px;">'
                f'<div style="font-size:64px; font-weight:900; color:var(--coral);">{esc(k.get("failed", "결과 없음"))}</div>'
                '<div style="font-size:30px; color:var(--mute); font-weight:600;">생성 결과가 없어 이 시험은 채점에서 제외합니다</div></div></div>']
    else:
        vlen = clip_len(key) - k.get("media_start", 0)
        vdur = min(vlen, s.dur)
        still = f"assets/images/last_{key}.png"
        make_last_frame(key)
        body = ['<div class="cam" id="cam">',
                f'<div class="frame" id="fr" style="left:160px; top:60px; width:1600px; height:900px;">'
                f'<img src="{still}" alt="" />'
                f'<video id="v" class="clip" src="assets/clips/{key}.mp4" data-start="0" data-duration="{vdur:.2f}" data-media-start="{k.get("media_start", 0)}" '
                f'data-track-index="1" playsinline {"data-has-audio=\"true\" data-volume=\"0.8\"" if k.get("audio", True) else "muted"}></video></div>']
    if k.get("mark"):
        x, y, r = k["mark"]
        body.append(f'<svg id="mark" style="position:absolute; left:{x - r - 20}px; top:{y - r - 20}px; width:{2 * r + 40}px; height:{2 * r + 40}px; overflow:visible;">'
                    f'<ellipse cx="{r + 20}" cy="{r + 20}" rx="{r}" ry="{r * 0.86}" fill="none" stroke="{k.get("mark_color", "#b4e61d")}" stroke-width="8" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1" /></svg>')
    body.append("</div>")
    if model:
        name, col = MODELS[model]
        body.append(f'<div class="chip" id="mchip" style="position:absolute; left:190px; top:90px; background:rgba(5,6,15,.82); color:{col}; box-shadow: inset 0 0 0 2px {col};">{esc(name)}</div>')
        if k.get("credits") is not None:
            body.append(f'<div class="chip" id="cchip" style="position:absolute; right:190px; top:90px; background:rgba(5,6,15,.82); color:var(--fg);">{k["credits"]} 크레딧</div>')
    if k.get("note"):
        body.append(f'<div id="note" style="position:absolute; left:190px; top:160px; font-size:22px; color:var(--mute); background:rgba(5,6,15,.7); padding:4px 10px; border-radius:6px;">{esc(k["note"])}</div>')
    if k.get("label"):
        body.append(f'<div class="tag" id="lbl" style="top:16px">{esc(k["label"])}</div>')
    if k.get("stamp"):
        body.append(f'<div id="stamp" style="position:absolute; right:240px; top:300px; transform:rotate(-12deg); padding:14px 30px; border:8px solid var(--coral); color:var(--coral); border-radius:16px; font-size:64px; font-weight:900; background:rgba(5,6,15,.35);">{esc(k["stamp"])}</div>')
    body.append(s.caption_html())
    js = [cam_js(k.get("cam", "push"), s.dur),
          'tl.fromTo("#fr", {opacity: 0, scale: 0.96}, {opacity: 1, scale: 1, duration: 0.45, ease: "expo.out"}, 0);']
    if model:
        js.append('tl.fromTo("#mchip", {opacity: 0, x: -30}, {opacity: 1, x: 0, duration: 0.35, ease: "back.out(2)"}, 0.3);')
        if k.get("credits") is not None:
            js.append('tl.fromTo("#cchip", {opacity: 0, x: 30}, {opacity: 1, x: 0, duration: 0.35, ease: "back.out(2)"}, 0.45);')
    if k.get("note"):
        js.append('tl.fromTo("#note", {opacity: 0}, {opacity: 1, duration: 0.3}, 0.6);')
    if k.get("mark"):
        js.append(f'tl.to("#mark ellipse", {{strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut"}}, {k.get("mark_at", 2.0)});')
    if k.get("stamp"):
        js.append(f'tl.fromTo("#stamp", {{opacity: 0, scale: 2.2}}, {{opacity: 1, scale: 1, duration: 0.25, ease: "power4.in"}}, {k.get("stamp_at", 2.5)});'
                  f'tl.fromTo("#cam", {{x: -8}}, {{x: 8, duration: 0.05, repeat: 3, yoyo: true}}, {k.get("stamp_at", 2.5) + 0.25});')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


GRID = dict(W=420, H=236, gx=32, gy=44, y0=220, cols=4)


def grid_pos(i):
    W, H, gx, gy = GRID["W"], GRID["H"], GRID["gx"], GRID["gy"]
    c = GRID["cols"]
    x0 = (1920 - (c * W + (c - 1) * gx)) // 2
    return x0 + (i % c) * (W + gx), GRID["y0"] + (i // c) * (H + gy)


def make_grid(rnd, prefix):
    """8개 클립을 1920x1080 한 장으로 미리 합친다 (브라우저에서 영상 여러 개를 동시에 돌리면 렌더가 매우 느림). 결과가 없는 칸은 빈 칸."""
    out = ROOT / "assets" / "clips" / f"grid_{prefix}.mp4"
    if out.exists():
        return f"grid_{prefix}"
    W, H = GRID["W"], GRID["H"]
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x070a1c:s=1920x1080:r=30:d=8.4"]
    for m in BLIND[rnd]:
        src = ROOT / "assets" / "clips" / f"{prefix}_{m}.mp4"
        if src.exists():
            cmd += ["-i", str(src)]
        else:
            cmd += ["-f", "lavfi", "-i", "color=c=0x10142e:s=1280x720:r=30:d=8"]
    fl = []
    last = "0:v"
    for i in range(len(BLIND[rnd])):
        x, y = grid_pos(i)
        fl.append(f"[{i + 1}:v]fps=30,scale={W}:{H},setsar=1,tpad=stop_mode=clone:stop_duration=2[c{i}]")
        fl.append(f"[{last}][c{i}]overlay={x}:{y}:eof_action=repeat[o{i}]")
        last = f"o{i}"
    cmd += ["-filter_complex", ";".join(fl), "-map", f"[{last}]", "-t", "8.4", "-an", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True)
    return f"grid_{prefix}"


def render_grid(s):
    k = s.kw
    rnd = k["round"]
    order = BLIND[rnd]
    gkey = make_grid(rnd, k.get("prefix", rnd))
    make_last_frame(gkey)
    W, H = GRID["W"], GRID["H"]
    vdur = min(clip_len(gkey), s.dur)
    body = ['<div class="cam" id="cam">',
            f'<img src="assets/images/last_{gkey}.png" alt="" style="position:absolute; inset:0; width:1920px; height:1080px;" />',
            f'<video id="gv" class="clip" src="assets/clips/{gkey}.mp4" data-start="0" data-duration="{vdur:.2f}" data-track-index="1" muted playsinline '
            'style="position:absolute; left:0; top:0; width:1920px; height:1080px;"></video>']
    for i, m in enumerate(order):
        x, y = grid_pos(i)
        name, col = MODELS[m]
        fail = FAILED.get((rnd, m))
        failhtml = (f'<div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; text-align:center; padding:0 30px; font-size:24px; font-weight:800; color:var(--coral);">{esc(fail)}</div>' if fail else "")
        body.append(f'<div id="g{i}" style="position:absolute; left:{x}px; top:{y}px; width:{W}px; height:{H}px; border-radius:14px; box-shadow: 0 0 0 6px #070a1c, inset 0 0 0 2px rgba(255,255,255,.08);">'
                    f'{failhtml}<div style="position:absolute; left:10px; top:10px; width:46px; height:46px; border-radius:10px; background:var(--lime); color:#05060f; font-size:30px; font-weight:900; display:flex; align-items:center; justify-content:center;">{i + 1}</div>'
                    f'<div id="gn{i}" style="position:absolute; left:0; right:0; bottom:0; padding:7px 12px; background:rgba(5,6,15,.85); display:flex; justify-content:space-between; font-size:21px; font-weight:800; opacity:0; border-radius:0 0 12px 12px;">'
                    f'<span style="color:{col}">{esc(name)}</span><span>{"거절" if fail else str(CREDITS[rnd][m]) + " 크레딧"}</span></div>'
                    f'<div id="gw{i}" style="position:absolute; inset:0; border:6px solid var(--lime); border-radius:16px; opacity:0;"></div></div>')
    body.append("</div>")
    body.append(f'<div class="tag" id="ttl" style="font-size:30px; color:var(--fg); top:60px;">{esc(k.get("title", ROUND_NAME.get(rnd, "")))}</div>')
    body.append(s.caption_html())
    js = [cam_js(k.get("cam", "pull"), s.dur),
          'tl.fromTo("#ttl", {opacity: 0, y: -20}, {opacity: 1, y: 0, duration: 0.4}, 0.1);',
          'tl.fromTo("#cam", {opacity: 0}, {opacity: 1, duration: 0.4}, 0);']
    if k.get("reveal") is not None:
        for i in range(len(order)):
            js.append(f'tl.to("#gn{i}", {{opacity: 1, duration: 0.3}}, {k["reveal"] + i * 0.15:.2f});')
    if k.get("winners_at") is not None:
        for i, m in enumerate(order):
            if m in k.get("winners", []):
                js.append(f'tl.to("#gw{i}", {{opacity: 1, duration: 0.25}}, {k["winners_at"]:.2f});')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_prompt(s):
    k = s.kw
    rnd = k["round"]
    text, hls = PROMPTS[rnd]
    t = esc(text)
    for h in hls:
        t = t.replace(esc(h), f'<span class="hlw">{esc(h)}</span>')
    body = ['<div class="cam" id="cam">',
            f'<div id="rt" style="position:absolute; left:160px; top:110px; font-size:72px; font-weight:900;">{esc(ROUND_NAME[rnd])}</div>',
            f'<div id="rs" style="position:absolute; left:160px; top:205px; font-size:34px; color:var(--mute); font-weight:600;">{esc(k.get("sub", ""))}</div>',
            '<div id="card" style="position:absolute; left:160px; top:290px; width:1600px; padding:44px 52px; border-radius:24px; background:rgba(16,20,46,.92); box-shadow: inset 0 0 0 2px rgba(124,58,237,.6);">'
            '<div style="font-size:22px; color:var(--mute); font-weight:700; letter-spacing:.08em; margin-bottom:18px;">PROMPT · 6개 모델 공통</div>'
            f'<div id="ptxt" style="font-family: ui-monospace, Menlo, monospace; font-size:34px; line-height:1.55; color:#e9e6ff;">{t}</div></div>',
            "</div>", s.caption_html()]
    style = ".hlw { background-image: linear-gradient(rgba(255,213,0,.55), rgba(255,213,0,.55)); background-repeat: no-repeat; background-position: 0 90%; background-size: 0% 40%; box-decoration-break: clone; -webkit-box-decoration-break: clone; color: #fff; }"
    js = [gridbg_js(s.dur), cam_js(k.get("cam", "pan"), s.dur),
          'tl.fromTo("#rt", {opacity: 0, x: -40}, {opacity: 1, x: 0, duration: 0.5, ease: "expo.out"}, 0.1);',
          'tl.fromTo("#rs", {opacity: 0}, {opacity: 1, duration: 0.4}, 0.4);',
          'tl.fromTo("#card", {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: 0.6, ease: "expo.out"}, 0.5);',
          'document.querySelectorAll(".hlw").forEach(function(el, i){ tl.to(el, {backgroundSize: "100% 40%", duration: 0.5, ease: "power2.out"}, 1.4 + i * 0.6); });',
          s.caption_js()]
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js), style)


def render_verdict(s):
    k = s.kw
    rnd = k["round"]
    names = " · ".join(MODELS[m][0] for m in WINNERS[rnd])
    col = MODELS[WINNERS[rnd][0]][1] if len(WINNERS[rnd]) == 1 else "#b4e61d"
    body = ['<div class="cam" id="cam">',
            f'<div id="vr" style="position:absolute; left:0; right:0; top:250px; text-align:center; font-size:44px; color:var(--mute); font-weight:700;">{esc(ROUND_NAME[rnd])} · 1등</div>',
            f'<div id="vw" style="position:absolute; left:0; right:0; top:330px; text-align:center;"><span style="display:inline-block; padding:24px 60px; border:10px solid {col}; border-radius:24px; color:{col}; font-size:{110 if len(WINNERS[rnd]) == 1 else 76}px; font-weight:900; transform:rotate(-4deg);">{esc(names)}</span></div>',
            f'<div id="vn" style="position:absolute; left:0; right:0; top:560px; text-align:center; font-family:NanumPen; font-size:64px; color:var(--lime);">{esc(k.get("hand", ""))}</div>',
            "</div>", s.caption_html()]
    js = [gridbg_js(s.dur), cam_js("punch", s.dur),
          'tl.fromTo("#vr", {opacity: 0}, {opacity: 1, duration: 0.3}, 0.1);',
          'tl.fromTo("#vw span", {opacity: 0, scale: 2.4}, {opacity: 1, scale: 1, duration: 0.28, ease: "power4.in"}, 0.4);',
          'tl.fromTo("#vn", {opacity: 0, y: 20}, {opacity: 1, y: 0, duration: 0.4}, 1.0);',
          s.caption_js()]
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_specs(s):
    rows = [
        ("kling4_0", "3~30초 멀티샷 · Keyframe 10장 · Omni Reference 15개 · 영상 편집"),
        ("seedance_2_5", "30초 멀티샷 · Reference 50개 · 생성 후 편집"),
        ("seedance_2_0", "최대 15초 · Seedance 2.5의 이전 버전 (기준점)"),
        ("minimax_h3", "4~15초 · 2K 고정 (화질이 다른 모델보다 높음)"),
        ("wan3_0", "2~30초 · 1080p · 소리 생성"),
        ("grok_video_v15", "2~15초 · 1080p"),
        ("flux_3_video", "5~20초 · 최대 4K · 소리 생성"),
        ("gemini_omni_flash_1_1", "3~10초 · 최대 4K · 소리 생성"),
    ]
    body = ['<div class="cam" id="cam">',
            '<div id="st" style="position:absolute; left:160px; top:90px; font-size:64px; font-weight:900;">오늘의 여덟 모델 <span style="font-size:30px; color:var(--mute); font-weight:600;">· 모두 8초 · 16:9 · 720p로 통일</span></div>']
    for i, (m, desc) in enumerate(rows):
        name, col = MODELS[m]
        y = 186 + i * 84
        body.append(f'<div id="row{i}" style="position:absolute; left:160px; top:{y}px; width:1600px; height:72px; border-radius:16px; background:rgba(16,20,46,.9); display:flex; align-items:center; gap:36px; padding:0 36px; box-shadow: inset 6px 0 0 {col};">'
                    f'<span style="width:340px; font-size:34px; font-weight:900; color:{col};">{esc(name)}</span><span style="font-size:29px; font-weight:600;">{esc(desc)}</span></div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("pull", s.dur), 'tl.fromTo("#st", {opacity: 0, y: -20}, {opacity: 1, y: 0, duration: 0.4}, 0.1);']
    for i in range(len(rows)):
        js.append(f'tl.fromTo("#row{i}", {{opacity: 0, x: -60}}, {{opacity: 1, x: 0, duration: 0.45, ease: "expo.out"}}, {0.3 + i * 0.12:.2f});')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_rules(s):
    items = s.kw["items"]
    body = ['<div class="cam" id="cam">',
            f'<div id="rt" style="position:absolute; left:0; right:0; top:150px; text-align:center; font-size:72px; font-weight:900;">{esc(s.kw["title"])}</div>']
    for i, it in enumerate(items):
        y = 310 + i * 120
        body.append(f'<div id="it{i}" style="position:absolute; left:460px; top:{y}px; display:flex; align-items:center; gap:28px; font-size:52px; font-weight:800;">'
                    f'<span style="width:64px; height:64px; border-radius:14px; background:var(--lime); color:#05060f; display:flex; align-items:center; justify-content:center; font-size:44px;">✓</span>{esc(it)}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("push", s.dur), 'tl.fromTo("#rt", {opacity: 0, y: -20}, {opacity: 1, y: 0, duration: 0.4}, 0.1);']
    for i in range(len(items)):
        js.append(f'tl.fromTo("#it{i}", {{opacity: 0, x: -40}}, {{opacity: 1, x: 0, duration: 0.4, ease: "back.out(1.6)"}}, {0.5 + i * 0.35:.2f});')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_board(s):
    rounds = ["r1", "r2", "r3", "r4", "r5"]
    order = sorted(MODELS, key=lambda m: (-sum(1 for r in rounds if m in WINNERS[r]), TOTAL[m]))
    body = ['<div class="cam" id="cam">',
            '<div id="bt" style="position:absolute; left:160px; top:70px; font-size:60px; font-weight:900;">다섯 시험 성적표 <span style="font-size:30px; color:var(--mute); font-weight:600;">· 단아쌤 1차 채점</span></div>']
    cols = ["장풍", "경공", "비무", "Reference", "현판", "1등 횟수"]
    x0, cw = 520, 200
    for j, c in enumerate(cols):
        body.append(f'<div id="h{j}" style="position:absolute; left:{x0 + j * cw}px; top:180px; width:{cw}px; text-align:center; font-size:30px; font-weight:800; color:var(--mute);">{c}</div>')
    for i, m in enumerate(order):
        name, col = MODELS[m]
        y = 228 + i * 80
        wins = sum(1 for r in rounds if m in WINNERS[r])
        body.append(f'<div id="br{i}" style="position:absolute; left:160px; top:{y}px; width:1600px; height:68px; border-radius:14px; background:rgba(16,20,46,.9);"></div>')
        body.append(f'<div id="bn{i}" style="position:absolute; left:196px; top:{y + 14}px; font-size:32px; font-weight:900; color:{col};">{esc(name)}</div>')
        for j, r in enumerate(rounds):
            mark = "🏆" if m in WINNERS[r] else ("—" if (r, m) in FAILED else "")
            body.append(f'<div class="cell" id="c{i}_{j}" style="position:absolute; left:{x0 + j * cw}px; top:{y + 8}px; width:{cw}px; text-align:center; font-size:40px; color:var(--mute); font-family:Pretendard, \"Noto Color Emoji\";">{mark}</div>')
        body.append(f'<div id="w{i}" style="position:absolute; left:{x0 + 5 * cw}px; top:{y + 6}px; width:{cw}px; text-align:center; font-size:46px; font-weight:900; color:{"#b4e61d" if wins >= 2 else "#f5f3ff"};">{wins}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("push", s.dur), 'tl.fromTo("#bt", {opacity: 0}, {opacity: 1, duration: 0.4}, 0.1);']
    for j in range(len(cols)):
        js.append(f'tl.fromTo("#h{j}", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, 0.3);')
    for i in range(len(order)):
        js.append(f'tl.fromTo(["#br{i}", "#bn{i}"], {{opacity: 0, x: -40}}, {{opacity: 1, x: 0, duration: 0.4, ease: "expo.out"}}, {0.4 + i * 0.1:.2f});')
    for j in range(5):
        js.append(f'tl.fromTo(".cell[id$=\'_{j}\']", {{opacity: 0, scale: 0.4}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)"}}, {1.4 + j * 0.45:.2f});')
    for i in range(len(order)):
        js.append(f'tl.fromTo("#w{i}", {{opacity: 0, scale: 0.5}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)"}}, 3.9);')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_credits(s):
    order = sorted(MODELS, key=lambda m: TOTAL[m])
    mx = max(TOTAL.values())
    body = ['<div class="cam" id="cam">',
            '<div id="ct" style="position:absolute; left:160px; top:80px; font-size:60px; font-weight:900;">시험 5개에 든 크레딧</div>',
            '<div id="cs" style="position:absolute; left:160px; top:160px; font-size:28px; color:var(--mute); font-weight:600;">8초 클립 5개 합계 · Higgsfield 견적 · 2026년 10월 27~28일 기준 · Kling은 출시 할인가</div>']
    for i, m in enumerate(order):
        name, col = MODELS[m]
        y = 214 + i * 78
        w = int(1050 * TOTAL[m] / mx)
        body.append(f'<div id="cn{i}" style="position:absolute; left:160px; top:{y + 14}px; width:380px; font-size:34px; font-weight:900; color:{col};">{esc(name)}</div>')
        body.append(f'<div id="cb{i}" style="position:absolute; left:550px; top:{y + 10}px; width:{max(w, 14)}px; height:52px; border-radius:10px; background:{col}; transform-origin:left center;"></div>')
        body.append(f'<div id="cv{i}" style="position:absolute; left:{570 + max(w, 14)}px; top:{y + 10}px; font-size:40px; font-weight:900; font-variant-numeric: tabular-nums;" data-v="{TOTAL[m]}">0</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("punch", s.dur), 'tl.fromTo(["#ct", "#cs"], {opacity: 0}, {opacity: 1, duration: 0.4}, 0.1);']
    for i in range(len(order)):
        t0 = 0.6 + i * 0.3
        js.append(f'tl.fromTo("#cn{i}", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, {t0:.2f});')
        js.append(f'tl.fromTo("#cb{i}", {{scaleX: 0}}, {{scaleX: 1, duration: 0.8, ease: "power3.out"}}, {t0:.2f});')
        js.append(f'(function(){{ const el = document.getElementById("cv{i}"); const o = {{v: 0}}; tl.to(o, {{v: +el.dataset.v, duration: 0.8, ease: "power3.out", onUpdate: function(){{ el.textContent = Math.round(o.v); }}}}, {t0:.2f}); tl.set(el, {{textContent: el.dataset.v}}, {t0 + 0.81:.2f}); }})();')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_faces(s):
    """R4 마지막 클로즈업 8칸 + 원본 시트 (결과 없는 모델은 거절 표시)."""
    order = ["kling4_0", "wan3_0", "flux_3_video", "minimax_h3", "grok_video_v15", "seedance_2_0", "seedance_2_5", "gemini_omni_flash_1_1"]
    body = ['<div class="cam" id="cam">',
            '<div id="ref" class="frame" style="left:120px; top:120px; width:520px; height:600px;"><img src="assets/images/ref_pair.png" alt="" style="object-fit:cover" /></div>',
            '<div id="reft" style="position:absolute; left:120px; top:730px; width:520px; text-align:center; font-size:32px; font-weight:800; color:var(--lime);">원본 Reference</div>']
    for i, m in enumerate(order):
        key = f"r4_{m}"
        name, col = MODELS[m]
        x = 690 + (i % 4) * 285
        y = 150 + (i // 4) * 290
        if ("r4", m) in FAILED:
            inner = f'<div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; text-align:center; padding:0 18px; font-size:22px; font-weight:800; color:var(--coral); background:#10142e;">{esc(FAILED[("r4", m)])}</div>'
        else:
            make_last_frame(key)
            inner = f'<img src="assets/images/last_{key}.png" alt="" style="object-fit:cover" />'
        body.append(f'<div class="frame" id="f{i}" style="left:{x}px; top:{y}px; width:270px; height:210px; border-radius:12px;">{inner}</div>'
                    f'<div id="fn{i}" style="position:absolute; left:{x}px; top:{y + 216}px; width:270px; text-align:center; font-size:22px; font-weight:800; color:{col};">{esc(name)}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("pan", s.dur), 'tl.fromTo(["#ref", "#reft"], {opacity: 0, x: -40}, {opacity: 1, x: 0, duration: 0.5, ease: "expo.out"}, 0.1);']
    for i in range(len(order)):
        js.append(f'tl.fromTo(["#f{i}", "#fn{i}"], {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.4, ease: "expo.out"}}, {0.5 + i * 0.12:.2f});')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_split(s):
    k = s.kw
    a, b = k["a"], k["b"]
    body = ['<div class="cam" id="cam">']
    for i, (key, label) in enumerate((a, b)):
        make_last_frame(key)
        x = 80 + i * 900
        vdur = min(clip_len(key) - k.get("ms", [0, 0])[i], s.dur)
        body.append(f'<div class="frame" id="sp{i}" style="left:{x}px; top:170px; width:860px; height:484px;"><img src="assets/images/last_{key}.png" alt="" />'
                    f'<video id="sv{i}" class="clip" src="assets/clips/{key}.mp4" data-start="0" data-duration="{vdur:.2f}" data-media-start="{k.get("ms", [0, 0])[i]}" data-track-index="{i + 1}" muted playsinline></video></div>'
                    f'<div id="sl{i}" style="position:absolute; left:{x}px; top:100px; width:860px; text-align:center; font-size:36px; font-weight:900; color:{k.get("colors", ["#a5a3c7", "#b4e61d"])[i]};">{esc(label)}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("push", s.dur),
          'tl.fromTo(["#sp0", "#sl0"], {opacity: 0, x: -40}, {opacity: 1, x: 0, duration: 0.5, ease: "expo.out"}, 0.1);',
          'tl.fromTo(["#sp1", "#sl1"], {opacity: 0, x: 40}, {opacity: 1, x: 0, duration: 0.5, ease: "expo.out"}, 0.25);',
          s.caption_js()]
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_film(s):
    shots = s.kw["shots"]  # [(key, media_start, dur)]
    body = []
    js = []
    t = 0.6
    for i, (key, ms, d) in enumerate(shots):
        body.append(f'<video id="fv{i}" class="clip" src="assets/clips/{key}.mp4" data-start="{t:.2f}" data-duration="{d:.2f}" data-media-start="{ms}" data-track-index="{1 + i % 2}" '
                    f'playsinline data-has-audio="true" data-volume="0.9" style="position:absolute; left:0; top:0; width:1920px; height:1080px; object-fit:cover;"></video>')
        t += d
    end = t
    body.append('<div style="position:absolute; left:0; right:0; top:0; height:110px; background:#000; z-index:5"></div>'
                '<div style="position:absolute; left:0; right:0; bottom:0; height:110px; background:#000; z-index:5"></div>')
    body.append(f'<div id="ftitle" class="clip" data-start="{end - 3.0:.2f}" data-duration="{3.0:.2f}" data-track-index="8" style="position:absolute; left:0; right:0; top:420px; text-align:center; z-index:6;">'
                '<div style="font-size:120px; font-weight:900; letter-spacing:.3em; text-shadow: 0 6px 30px rgba(0,0,0,.8);">단아검법</div>'
                '<div style="margin-top:10px; font-size:34px; font-weight:700; color:var(--lime); letter-spacing:.2em; text-shadow: 0 4px 20px rgba(0,0,0,.8);">MADE WITH KLING 4.0 · HIGGSFIELD</div></div>')
    body.append('<div id="fcard" class="clip" data-start="0" data-duration="0.6" data-track-index="7" style="position:absolute; inset:0; background:#000; z-index:7"></div>')
    js.append('tl.fromTo("#ftitle > div", {opacity: 0, y: 20}, {opacity: 1, y: 0, duration: 0.6, stagger: 0.2, ease: "expo.out"}, ' + f"{end - 3.0 + 0.05:.2f});")
    s.dur = end + 0.4
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_screen(s):
    """Higgsfield 작업 화면 녹화가 들어갈 자리. 녹화본으로 이 장면을 덮어쓴다."""
    body = ['<div class="cam" id="cam">',
            '<div id="slot" style="position:absolute; left:160px; top:70px; width:1600px; height:860px; border-radius:24px; border:4px dashed rgba(180,230,29,.7); background:rgba(16,20,46,.6); display:flex; flex-direction:column; align-items:center; justify-content:center; gap:22px;">'
            '<div style="font-size:30px; font-weight:800; color:var(--lime); letter-spacing:.08em;">SCREEN RECORDING</div>'
            '<div style="font-size:64px; font-weight:900;">Higgsfield 작업 화면이 들어갈 자리</div>'
            '<div style="font-size:32px; color:var(--mute); font-weight:600;">모델 선택기 전환 · 프롬프트 붙여넣기 · 생성 버튼 · 크레딧 표시</div></div>',
            "</div>", s.caption_html()]
    js = [gridbg_js(s.dur), 'tl.fromTo("#slot", {opacity: 0, scale: 0.97}, {opacity: 1, scale: 1, duration: 0.5, ease: "expo.out"}, 0.1);', s.caption_js()]
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


RENDER = {"screen": render_screen, "talk": render_talk, "clip": render_clip, "grid": render_grid, "prompt": render_prompt, "verdict": render_verdict,
          "specs": render_specs, "rules": render_rules, "board": render_board, "credits": render_credits, "faces": render_faces,
          "split": render_split, "film": render_film}


def make_last_frame(key):
    out = ROOT / "assets" / "images" / f"last_{key}.png"
    if out.exists():
        return
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-sseof", "-0.3", "-i", str(ROOT / "assets" / "clips" / f"{key}.mp4"),
                    "-frames:v", "1", str(out)], check=True)


# ------------------------------------------------------------------ 대본 (장면 목록)
# 시험별 모델 반응 (자막 한 줄씩). 시험 2~5는 단아쌤 판정 반영
OBS = {
    "r1": {
        "seedance_2_0": ["Seedance 2.0은 로우앵글로 대나무가 휘는 모습을 살렸습니다.", "다만 장풍 파동은 보이지 않습니다."],
        "minimax_h3": ["MiniMax는 손바닥을 카메라 쪽으로 미는 구도가 시원합니다.", "대나무가 렌즈처럼 휘어 보이는 점은 아쉽습니다."],
        "flux_3_video": ["FLUX 3는 공기 파동이 눈에 보입니다!", "카메라가 밀고 들어가는 연출까지 제일 장풍답습니다."],
        "gemini_omni_flash_1_1": ["Gemini는 로우앵글과 낙엽은 좋습니다.", "다만 파동은 약하게 보입니다."],
        "seedance_2_5": ["Seedance 2.5는 숨 고르는 장면까지 살렸습니다.", "그런데 옷감이 얇게 비쳐 보입니다."],
        "grok_video_v15": ["Grok은 공기 소용돌이를 또렷하게 그렸습니다.", "다만 옆모습에 입을 벌린 표정이 조금 과합니다."],
        "wan3_0": ["Wan은 정면 구도로 안정적입니다.", "소매와 낙엽이 바람 방향대로 움직입니다."],
        "kling4_0": ["Kling은 마보 자세가 무협답습니다.", "그런데 정작 장풍 파동이 잘 보이지 않습니다."],
    },
    "r2": {
        "wan3_0": ["Wan은 세 단계를 모두 해냈고,", "연못 위를 끝까지 달립니다!"],
        "kling4_0": ["Kling도 지붕, 처마, 연못까지 순서대로 해냈습니다.", "다만 마지막은 뛰기보다 걷는 느낌입니다."],
        "flux_3_video": ["FLUX 3는 지붕 위 도약은 좋습니다.", "하지만 연못에서는 물속에 서 있는 것처럼 보입니다."],
        "minimax_h3": ["MiniMax는 걷는 느낌이라", "경공의 맛이 약합니다."],
        "seedance_2_0": ["Seedance 2.0은 세 단계를 모두 해냈고,", "수면 위를 달리는 반사까지 가장 경공답습니다!"],
        "grok_video_v15": ["Grok은 수면 물결 표현이 좋습니다.", "지붕 위에서 잠깐 멈칫하는 점은 아쉽습니다."],
        "seedance_2_5": ["Seedance 2.5는 노을빛이 정말 영화 같습니다.", "그런데 걷다가 연못에 서서 끝납니다. 건너지 않았습니다."],
        "gemini_omni_flash_1_1": ["Gemini도 지붕에서 연못까지", "세 단계를 모두 해냈습니다."],
    },
    "r3": {
        "flux_3_video": ["FLUX 3는 카메라가 두 사람 사이로 파고듭니다.", "다만 첫 인사가 없습니다."],
        "seedance_2_5": ["Seedance 2.5는 목검이 부딪히는 클로즈업이 영화 같습니다.", "하지만 시간 정지와 카메라 회전은 없습니다."],
        "grok_video_v15": ["Grok은 순서는 잘 따랐지만,", "손에 목검이 두 자루씩 나옵니다."],
        "kling4_0": ["Kling은 각도를 바꿔가며 합을 또렷하게 보여줍니다.", "목검과 두 사람의 동작이 가장 자연스럽습니다!"],
        "gemini_omni_flash_1_1": ["Gemini는 순서는 끝까지 지켰지만,", "낙엽이 엉뚱한 곳에서 생겨납니다."],
        "seedance_2_0": ["Seedance 2.0은 빙글빙글 도는 동작이 화려하고,", "시간 정지까지 해냈습니다!"],
        "wan3_0": ["Wan은 정면 구도로 안정적이지만,", "합이 적고 시간 정지가 없습니다."],
        "minimax_h3": ["MiniMax는 합이 시원시원합니다.", "다만 시간 정지는 없었습니다."],
    },
    "r4": {
        "flux_3_video": ["FLUX 3는 세 컷 순서를 지켰고,", "귀공자의 옥비녀와 옷 자수까지 그대로입니다!"],
        "gemini_omni_flash_1_1": ["Gemini는 인물 사진을 넣자 안전 필터로 거절했습니다.", "같은 설정으로 한 번 더 시도했지만 또 거절됐습니다."],
        "seedance_2_0": ["Seedance 2.0은 분위기는 좋지만,", "귀공자의 상투가 풀렸습니다."],
        "kling4_0": ["Kling은 걷기, 다가오기, 클로즈업 순서를 지켰고,", "옥비녀와 자수까지 그대로입니다!"],
        "minimax_h3": ["MiniMax는 두 사람의 얼굴을 잘 지켰지만,", "상투가 작게 바뀌었습니다."],
        "grok_video_v15": ["Grok은 세 컷 구성은 좋지만,", "귀공자의 머리 모양이 조금 달라졌습니다."],
        "seedance_2_5": ["Seedance 2.5는 화면이 가장 예쁩니다.", "그런데 귀공자의 상투가 풀리고 표정이 달라졌습니다."],
        "wan3_0": ["Wan도 옥비녀 상투와 자수를", "거의 그대로 지켰습니다!"],
    },
    "r5": {
        "seedance_2_0": ["Seedance 2.0은 '단야객잔'.", "한 글자가 틀렸습니다."],
        "grok_video_v15": ["Grok은 '단아객잔' 네 글자를", "정확히 썼습니다!"],
        "gemini_omni_flash_1_1": ["Gemini도 '단아객잔'을", "정확히 썼습니다!"],
        "seedance_2_5": ["Seedance 2.5도 정확합니다.", "차 따르는 손까지 자연스럽습니다."],
        "wan3_0": ["Wan은 '단야객잔'.", "한 글자가 틀렸습니다."],
        "flux_3_video": ["FLUX 3도 '단아객잔'을", "정확히 썼습니다!"],
        "kling4_0": ["Kling도 네 글자를 정확히 썼고,", "현판 화면이 가장 예쁩니다!"],
        "minimax_h3": ["MiniMax는 글자는 맞지만,", "현판이 비스듬히 기울어 보입니다."],
    },
}
STAMP = {("r3", "grok_video_v15"): "검 2개?", ("r3", "gemini_omni_flash_1_1"): "낙엽?", ("r5", "seedance_2_0"): "단야?", ("r5", "wan3_0"): "단야?", ("r4", "gemini_omni_flash_1_1"): "거절"}


def scenes():
    """대본. 자막은 한 줄씩, 의미 단위로 끊는다. 말투는 '~입니다!' (합쇼체). 모델·서비스 이름은 영어 그대로."""
    S = []
    n = [0]

    def add(name, kind, caps=(), **kw):
        n[0] += 1
        S.append(Scene(n[0], name, kind, caps, **kw))

    def round_clips(rnd, cams=("push", "pan", "pull")):
        for i, m in enumerate(BLIND[rnd]):
            fail = FAILED.get((rnd, m))
            kw = dict(model=m, credits=CREDITS[rnd][m], label=f"{ROUND_NAME[rnd]} · {i + 1}번", cam=cams[i % 3], music="wuxia" if rnd in ("r1", "r2", "r3") else "calm", min_dur=8.6)
            if fail:
                kw.update(key=None, failed=fail, credits=None)
            else:
                kw.update(key=f"{rnd}_{m}")
            if (rnd, m) in STAMP:
                kw.update(stamp=STAMP[(rnd, m)], stamp_at=2.6 if not fail else 0.8, sfx=[("stamp", 2.6 if not fail else 0.8)])
            if m == "minimax_h3":
                kw.update(note="2K 고정 (다른 모델은 720p)")
            add(f"{rnd}-{i + 1}-{m}", "clip", OBS[rnd][m], **kw)

    # 1. 훅 · 질문 · 소개
    add("hook-grid", "grid", ["같은 프롬프트 하나로 만든 장풍 영상 여덟 개입니다.",
                              "만든 AI만 다릅니다.",
                              "이 중 진짜 무협 영화 같은 건 몇 번일까요?",
                              "정답은 마지막에 공개합니다!"],
        round="r1", title="같은 프롬프트 · 다른 AI 여덟 개", cam="push", music="wuxia", sfx=[("whoosh", 0.1)])
    add("hook-question", "talk", ["Kling 4.0이 나왔습니다.",
                                  "Seedance 2.5보다 낫다는 사람도 있습니다.",
                                  "정말일까요, 그냥 과장일까요?",
                                  "여덟 개 모델로 직접 확인했습니다!"],
        kicker="NEW · Kling 4.0", title="Kling 4.0, 진짜 최고일까?", hl=["진짜 최고"], sub="Seedance 2.5 · Seedance 2.0 · MiniMax H3 · Wan 3.0 · Grok Imagine 1.5 · FLUX 3 · Gemini Omni 1.1", cam="push", music="wuxia", sfx=[("ding", 0.3)])
    add("authority", "clip", ["경희대 경영대학원 AI/이커머스 겸임교수,",
                              "단아쌤 김경은입니다!"],
        key="authority", audio=False, cam="punch", music="wuxia", min_dur=7.0)
    add("stakes", "talk", ["시험은 무협으로 냈습니다.",
                           "쉬운 장면은 다 잘하기 때문입니다.",
                           "장풍, 경공, 비무, 같은 인물 유지,",
                           "그리고 마지막에 함정 하나입니다!"],
        kicker="AI 교수의 시험지", title="영상 AI 8개 × 무협 시험 5개", hl=["무협 시험 5개"], sub="장풍 · 경공 · 비무 · Reference · 현판(함정)", cam="pan", music="wuxia", sfx=[("brush", 0.2)])
    add("rules", "rules", ["조건은 모두 같습니다.",
                           "여덟 개 모델 모두 Higgsfield에서 돌렸고,",
                           "모두 똑같은 프롬프트와 똑같은 설정을 넣었습니다.",
                           "8초, 16:9, 다시 뽑기 없이 첫 결과만 씁니다.",
                           "MiniMax만 2K로 고정돼 화질이 다릅니다.",
                           "모델별 비용은 마지막에 공개합니다!"],
        title="공정 조건", items=["8개 모델 모두 Higgsfield에서", "같은 프롬프트 · 같은 설정", "8초 · 16:9 · 첫 결과만", "가격은 마지막에 공개"], music="calm", sfx=[("tick", 0.85), ("tick", 1.2), ("tick", 1.55), ("tick", 1.9)])
    add("screen", "screen", ["Higgsfield에서는 모델 선택기에서 모델만 바꾸면 됩니다.",
                             "프롬프트는 그대로 남아 있어서",
                             "여덟 번 복사할 필요가 없습니다.",
                             "지금 Kling 4.0 출시 할인도 진행 중입니다.",
                             "링크는 설명란 맨 위에 있습니다!"],
        min_dur=20.0, music="calm")
    add("specs", "specs", ["시작 전에 여덟 모델을 짧게 보겠습니다.",
                           "Kling 4.0은 Reference를 15개까지 넣을 수 있고,",
                           "만든 영상을 고치는 편집 기능도 있습니다.",
                           "Seedance 2.0은 2.5의 이전 버전이라",
                           "한 세대 사이에 얼마나 달라졌는지도 보겠습니다!"],
        music="calm")

    # 2. 시험 1 장풍
    add("r1-prompt", "prompt", ["첫 번째 시험, 장풍입니다!",
                                "손바닥에서 바람이 나가 대나무가 휘어야 하고,",
                                "낙엽이 날아가야 합니다."],
        round="r1", sub="보이지 않는 힘을 보이게 만드는 시험", music="wuxia", sfx=[("brush", 0.1)])
    add("r1-grid", "grid", ["크레딧부터 보겠습니다.",
                            "같은 8초인데 Kling은 4, Seedance 2.5는 56입니다.",
                            "한 편씩 보겠습니다!"],
        round="r1", reveal=1.0, music="wuxia", sfx=[("tick", 1.0), ("tick", 1.3), ("tick", 1.6), ("tick", 1.9)])
    round_clips("r1")
    add("r1-verdict", "verdict", ["장풍은 FLUX 3가 가져갑니다!",
                                  "그런데 서서 쏘는 장풍은 쉬운 편입니다.",
                                  "지붕 위를 날아다니면 어떨까요?"],
        round="r1", hand="공기 파동 + 카메라 푸시인", music="wuxia", sfx=[("stamp", 0.65)])

    # 3. 시험 2 경공
    add("r2-prompt", "prompt", ["두 번째 시험, 경공입니다!",
                                "지붕을 달리고, 처마에서 처마로 뛰고,",
                                "연못 위를 밟고 건너야 합니다."],
        round="r2", sub="순서 세 단계 · 하나라도 빠지면 바로 보입니다", music="wuxia", sfx=[("brush", 0.1)])
    add("r2-grid", "grid", ["이번에는 번호를 섞었습니다.",
                            "몇 번이 세 단계를 다 해냈을까요?"], round="r2", reveal=3.2, music="wuxia",
        sfx=[("whoosh", 3.1)])
    round_clips("r2")
    add("r2-verdict", "verdict", ["경공은 Seedance 2.0이 가장 잘 표현했습니다!",
                                  "재미있는 건 Seedance 2.0은 연못을 건넜는데,",
                                  "2.5는 건너지 않았다는 점입니다.",
                                  "새 버전이 늘 시킨 대로 하는 건 아닙니다.",
                                  "이제 두 사람이 붙으면 어떨까요?"],
        round="r2", hand="예쁜 것 ≠ 시킨 대로 한 것", music="wuxia", sfx=[("stamp", 0.65)])

    # 4. 시험 3 비무
    add("r3-prompt", "prompt", ["세 번째 시험, 비무입니다!",
                                "인사하고, 정확히 다섯 번 겨루고,",
                                "시간이 멈추며 카메라가 돌고,",
                                "마지막에 서로 포권합니다.",
                                "순서대로 다 해내는지 보겠습니다."],
        round="r3", sub="지시 이행 시험 · 서소저 vs 귀공자", music="wuxia", sfx=[("brush", 0.1)])
    add("r3-grid", "grid", ["여덟 개 모두 두 사람의 옷과 머리는 잘 지켰습니다.",
                            "차이는 디테일에서 났습니다."], round="r3", reveal=2.6, music="wuxia",
        sfx=[("whoosh", 2.5)])
    round_clips("r3")
    add("r3-verdict", "verdict", ["비무는 Kling이 가장 잘했습니다!",
                                  "Grok은 검이 두 자루, Gemini는 낙엽이 엉뚱했습니다.",
                                  "그렇다면 같은 사람을 끝까지 유지하는 건",
                                  "누가 가장 잘할까요?"],
        round="r3", hand="검 하나, 낙엽 하나까지 자연스럽게", music="wuxia", sfx=[("stamp", 0.65)])

    # 5. 시험 4 Reference
    add("r4-intro", "talk", ["네 번째는 가장 실용적인 시험입니다.",
                             "서소저와 귀공자 사진을 먼저 만들어",
                             "모든 모델에 똑같이 넣었습니다.",
                             "세 컷 내내 같은 얼굴, 같은 옷이 나와야 합니다!"],
        kicker="시험 4 · Reference", title="같은 사람으로 끝까지", hl=["끝까지"], sub="인물 사진 시트 2장 → 8개 모델 공통", img="ref_sheets.png", img_w=780, img_h=620, fit="contain", cam="pan", music="calm", sfx=[("brush", 0.1)])
    add("r4-grid", "grid", ["다리 위를 걷고, 다가와 멈추고,",
                            "클로즈업으로 마주 보는 세 컷 구성입니다."], round="r4", reveal=2.4, music="calm",
        sfx=[("whoosh", 2.3)])
    round_clips("r4")
    add("r4-faces", "faces", ["마지막 클로즈업을 원본 사진과 비교해 보겠습니다.",
                              "옥비녀 상투와 옷 자수까지 지킨 건",
                              "Kling, FLUX 3, Wan 세 모델입니다.",
                              "가장 예쁜 화면은 Seedance였지만,",
                              "귀공자의 상투가 풀린 건 아쉽습니다."], music="calm")
    add("r4-verdict", "verdict", ["Reference 시험은 Kling, FLUX 3, Wan 공동 1등입니다!",
                                  "마지막 시험은 함정입니다."],
        round="r4", hand="옥비녀 하나까지 그대로", music="wuxia", sfx=[("stamp", 0.65)])

    # 6. 시험 5 현판 (함정)
    add("r5-prompt", "prompt", ["객잔 현판에 '단아객잔' 네 글자를 쓰고,",
                                "차를 따르는 손을 보여줘야 합니다.",
                                "영상 AI는 글자에 약하다고 알려져 있습니다."],
        round="r5", sub="함정 · 한글 글자", music="calm", sfx=[("brush", 0.1)])
    add("r5-grid", "grid", ["결과는 반전입니다!",
                            "여덟 개 중 다섯 개가 네 글자를 정확히 썼습니다."],
        round="r5", reveal=2.0, winners=R5_CORRECT, winners_at=3.6, music="calm", sfx=[("ding", 3.6)])
    round_clips("r5")
    add("r5-twist", "talk", ["더 재미있는 일이 있었습니다.",
                             "함정을 피하려고 이미지 AI로 현판을 먼저 만들었는데,",
                             "이미지 AI가 '단'을 '탄'으로 틀렸습니다.",
                             "결론은 하나입니다.",
                             "글자는 어떤 AI든 꼭 눈으로 확인하십시오!"],
        kicker="함정의 함정", title="글자는 꼭 눈으로 확인", hl=["눈으로 확인"], sub="이미지 AI도 틀립니다: 단 → 탄", img="r5_signboard.png", img_w=780, img_h=440, cam="push", music="calm")
    add("r5-verdict", "verdict", ["다섯 모델이 글자를 맞췄지만,",
                                  "가장 예쁜 현판은 Kling 4.0입니다!"],
        round="r5", hand="Wan · Seedance 2.0은 단야, MiniMax는 기울어짐", music="wuxia", sfx=[("stamp", 0.65)])

    # 7. 점수 · 반전 · 강점
    add("board", "board", ["다섯 시험 결과입니다.",
                           "1등을 가장 많이 한 모델은 Kling, 세 번입니다!",
                           "FLUX 3가 두 번, Seedance 2.0과 Wan이 한 번입니다.",
                           "가장 영화 같은 화면은 Seedance 2.5였습니다.",
                           "그런데 Seedance 2.5는 1등이 한 번도 없습니다.",
                           "이제 비용을 보겠습니다!"], music="calm", sfx=[("tick", 1.4), ("tick", 1.85), ("tick", 2.3), ("tick", 2.75), ("tick", 3.2), ("ding", 3.9)])
    add("credits", "credits", ["다섯 시험에 든 크레딧입니다.",
                               "Kling 34, Wan 70, MiniMax 80, Gemini 96,",
                               "Seedance 2.0 180, Grok 180, FLUX 3 240, Seedance 2.5 280.",
                               "FLUX 3는 Kling의 7배,",
                               "Seedance 2.5는 Kling의 8배를 썼습니다!",
                               "다만 Kling은 지금 출시 할인가입니다.",
                               "할인이 끝나면 가격이 오를 수 있습니다."],
        music="wuxia", sfx=[("tick", 0.6), ("tick", 0.9), ("tick", 1.2), ("tick", 1.5), ("tick", 1.8), ("tick", 2.1), ("tick", 2.4), ("tick", 2.7)])
    add("kling-why", "talk", ["Kling은 1등 세 번을 가장 싼 값에 해냈습니다.",
                              "비무, Reference, 현판에서 1등입니다.",
                              "같은 인물로 여러 컷을 시킨 대로 만드는 일,",
                              "우리가 실제로 가장 많이 하는 일입니다!"],
        kicker="그래서 Kling", title="싸고, 사람을 기억하고, 글자도 맞게", hl=["사람을 기억"], sub="비무 1등 · Reference 공동 1등 · 현판 1등 · 크레딧 최저", cam="push", music="wuxia")
    add("edit-demo", "split", ["Kling에는 만든 영상을 고치는 편집 기능도 있습니다.",
                               "장풍 파동이 안 보였던 부분만 고쳐봤습니다.",
                               "솔직히 이번에는 바람 번짐만 살짝 생겼습니다.",
                               "편집도 한 번에 완벽하지는 않습니다."],
        a=("r1_kling4_0", "원본 (시험 1)"), b=("edit_r1_kling", "Kling 편집 후"), music="calm")
    add("edit-fix", "split", ["대신 처음부터 '눈에 보이는 충격파'라고 쓰고,",
                              "서소저 사진을 Reference로 넣었습니다.",
                              "그랬더니 이렇게 나왔습니다!"],
        a=("r1_kling4_0", "시험 1 · 글만"), b=("film_s2b", "단편 샷 · Reference + 구체적 문장"), music="calm")
    add("film-intro", "talk", ["그래서 오늘 결과를 바탕으로",
                               "Kling 하나만으로 30초 무협 단편을 만들었습니다.",
                               "비교가 아닌 작품이라,",
                               "샷마다 두 번씩 뽑아 좋은 것을 골랐습니다."],
        kicker="Kling 4.0 단편", title="단아검법", sub="Reference · 1080p · 샷당 2회 생성", img="ref_sheets.png", img_w=780, img_h=620, fit="contain", cam="pull", music="calm")
    FILM = [("film_s1", 0, 4.0), ("film_s2b", 0, 5.0), ("film_s3a", 0, 6.0), ("film_s4b", 0, 8.0), ("film_s5", 0, 4.0), ("r5_kling4_0", 4.6, 3.4)]
    add("film", "film", [], min_dur=0.6 + sum(d for _, _, d in FILM) + 0.4, shots=FILM, music="none")

    # 8. 추천 · CTA
    add("recommend", "talk", ["정리하겠습니다.",
                              "한 컷의 완성도가 가장 중요하다면 Seedance 2.5나 FLUX 3,",
                              "같은 인물로 여러 컷을 싸게 만든다면 Kling 4.0입니다!",
                              "꼭 하나만 고를 필요는 없습니다.",
                              "장면마다 갈아타면 됩니다.",
                              "그래서 저는 여덟 개를 한 곳에서 쓰는 Higgsfield를 씁니다."],
        kicker="이럴 땐 이 모델", title="한 컷 승부는 FLUX · Seedance, 시리즈는 Kling", hl=["시리즈는 Kling"], sub="장면마다 갈아타기 · Higgsfield 한 계정", cam="push", music="wuxia")
    add("cta", "talk", ["오늘 여덟 모델은 모두 Higgsfield에서 돌렸습니다.",
                        "설명란 링크에서 같은 프롬프트를 붙여넣고",
                        "여러분의 1등을 직접 골라보십시오!",
                        "장풍 하나에 Kling은 4크레딧입니다."],
        kicker="설명란 링크", title="같은 프롬프트, 여러분의 1등은?", hl=["여러분의 1등"], sub="Kling 4.0 출시 할인 중 · 크레딧은 2026년 10월 기준", cam="punch", music="wuxia", sfx=[("ding", 0.4)])
    add("answer", "grid", ["처음 문제의 정답입니다!",
                           "1번 Seedance 2.0, 2번 MiniMax, 3번 FLUX 3, 4번 Gemini,",
                           "5번 Seedance 2.5, 6번 Grok, 7번 Wan, 8번 Kling입니다.",
                           "여러분이 고른 번호는 어떤 모델이었습니까?"], round="r1", reveal=0.8, title="첫 문제 정답", cam="push", music="wuxia",
        sfx=[("ding", 0.8)])
    add("outro", "talk", ["여러분이 채점했다면 1등은 누구입니까?",
                          "댓글로 알려주십시오.",
                          "다음 영상에서는 오늘 단편을 3분으로 늘려보겠습니다!"],
        kicker="다음 영상", title="단아검법, 3분으로", sub="구독하고 기다려 주십시오", cam="pull", music="wuxia", tail=1.5)
    return S


def write_scene(s):
    d = SEG / f"{s.num:02d}-{s.name}"
    d.mkdir(parents=True, exist_ok=True)
    for name, target in (("assets", ROOT / "assets"), ("node_modules", NODE_MODULES)):
        link = d / name
        if not link.exists():
            os.symlink(os.path.relpath(target, d), link)
    (d / "index.html").write_text(RENDER[s.kind](s))
    return d


def main(only):
    SEG.mkdir(exist_ok=True)
    all_s = scenes()
    plan = []
    t = 0.0
    for s in all_s:
        if not only or f"{s.num:02d}" in only:
            write_scene(s)
        plan.append({"num": s.num, "name": s.name, "kind": s.kind, "dir": f"segments/{s.num:02d}-{s.name}", "start": round(t, 2),
                     "dur": round(s.dur, 2), "music": s.music, "sfx": s.sfx, "caps": [{"text": c, "start": round(t + a, 2), "dur": round(b, 2)} for c, (a, b) in zip(s.caps, s.cap_times)]})
        t += s.dur
    (ROOT / "plan.json").write_text(json.dumps({"total": round(t, 2), "scenes": plan}, ensure_ascii=False, indent=1))
    print(f"{len(all_s)} scenes, {t / 60:.1f} min")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
