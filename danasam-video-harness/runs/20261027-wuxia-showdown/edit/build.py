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
    "veo3_1": ("Veo 3.1", "#5b8cff"),
    "wan3_0": ("Wan 3.0", "#ffbf3c"),
    "minimax_h3": ("MiniMax H3", "#3fd6c6"),
    "grok_video_v15": ("Grok 1.5", "#c9a7ff"),
}
MODEL_KO = {"kling4_0": "클링", "seedance_2_5": "시댄스", "veo3_1": "비오", "wan3_0": "완",
            "minimax_h3": "미니맥스", "grok_video_v15": "그록"}
# 8초 한 클립 견적 (힉스필드, 2026-10-27~28). R4는 레퍼런스 모드 가격
CREDITS = {
    "r1": {"kling4_0": 4, "seedance_2_5": 56, "veo3_1": 80, "wan3_0": 14, "minimax_h3": 16, "grok_video_v15": 36},
    "r4": {"kling4_0": 18, "seedance_2_5": 56, "veo3_1": 80, "wan3_0": 14, "minimax_h3": 16, "grok_video_v15": 36},
}
for r in ("r2", "r3", "r5"):
    CREDITS[r] = CREDITS["r1"]
TOTAL = {m: sum(CREDITS[r][m] for r in ("r1", "r2", "r3", "r4", "r5")) for m in MODELS}
# 블라인드 번호 (1..6) → 모델
BLIND = {
    "r1": ["wan3_0", "veo3_1", "minimax_h3", "grok_video_v15", "kling4_0", "seedance_2_5"],
    "r2": ["seedance_2_5", "wan3_0", "veo3_1", "kling4_0", "grok_video_v15", "minimax_h3"],
    "r3": ["minimax_h3", "kling4_0", "grok_video_v15", "seedance_2_5", "veo3_1", "wan3_0"],
    "r4": ["veo3_1", "grok_video_v15", "kling4_0", "wan3_0", "seedance_2_5", "minimax_h3"],
    "r5": ["grok_video_v15", "minimax_h3", "seedance_2_5", "kling4_0", "wan3_0", "veo3_1"],
}
ROUND_NAME = {"r1": "시험 1 · 장풍", "r2": "시험 2 · 경공", "r3": "시험 3 · 비무", "r4": "시험 4 · 레퍼런스", "r5": "시험 5 · 현판"}
# 라운드 1등 (1차 채점, 단아쌤 확인 필요)
WINNERS = {"r1": ["veo3_1"], "r2": ["wan3_0"], "r3": ["grok_video_v15"], "r4": ["kling4_0"],
           "r5": ["kling4_0", "seedance_2_5", "grok_video_v15"]}

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
.cap span { display: inline-block; max-width: 1500px; padding: 14px 28px 16px; border-radius: 14px; background: rgba(5,6,15,.78);
  font-size: 42px; font-weight: 700; line-height: 1.38; text-align: center; letter-spacing: -0.01em; box-shadow: 0 10px 30px rgba(0,0,0,.35); }
.chip { display: inline-flex; align-items: center; gap: 10px; padding: 10px 18px; border-radius: 12px; font-weight: 800; font-size: 30px; }
.tag { position: absolute; left: 60px; top: 44px; font-size: 24px; font-weight: 700; color: var(--mute); letter-spacing: .04em; }
.ad { position: absolute; right: 60px; top: 44px; font-size: 22px; font-weight: 700; color: var(--mute); padding: 6px 12px; border: 2px solid rgba(165,163,199,.5); border-radius: 8px; }
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
    if k.get("ad"):
        body.append('<div class="ad">유료 광고 포함</div>')
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


GRID = dict(W=560, H=315, gx=60, gy=40, y0=150)


def grid_pos(i):
    W, H, gx, gy = GRID["W"], GRID["H"], GRID["gx"], GRID["gy"]
    x0 = (1920 - (3 * W + 2 * gx)) // 2
    return x0 + (i % 3) * (W + gx), GRID["y0"] + (i // 3) * (H + gy)


def make_grid(rnd, prefix):
    """6개 클립을 1920x1080 한 장으로 미리 합친다 (브라우저에서 영상 6개를 동시에 돌리면 렌더가 매우 느림)."""
    out = ROOT / "assets" / "clips" / f"grid_{prefix}.mp4"
    if out.exists():
        return f"grid_{prefix}"
    W, H = GRID["W"], GRID["H"]
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x070a1c:s=1920x1080:r=30:d=8.4"]
    for m in BLIND[rnd]:
        cmd += ["-i", str(ROOT / "assets" / "clips" / f"{prefix}_{m}.mp4")]
    fl = []
    last = "0:v"
    for i in range(6):
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
        body.append(f'<div id="g{i}" style="position:absolute; left:{x}px; top:{y}px; width:{W}px; height:{H}px; border-radius:16px; box-shadow: 0 0 0 6px #070a1c, inset 0 0 0 2px rgba(255,255,255,.08);">'
                    f'<div style="position:absolute; left:12px; top:12px; width:56px; height:56px; border-radius:12px; background:var(--lime); color:#05060f; font-size:36px; font-weight:900; display:flex; align-items:center; justify-content:center;">{i + 1}</div>'
                    f'<div id="gn{i}" style="position:absolute; left:0; right:0; bottom:0; padding:10px 14px; background:rgba(5,6,15,.82); display:flex; justify-content:space-between; font-size:26px; font-weight:800; opacity:0; border-radius:0 0 14px 14px;">'
                    f'<span style="color:{col}">{esc(name)}</span><span>{CREDITS[rnd][m]} 크레딧</span></div>'
                    f'<div id="gw{i}" style="position:absolute; inset:0; border:6px solid var(--lime); border-radius:16px; opacity:0;"></div></div>')
    body.append("</div>")
    body.append(f'<div class="tag" id="ttl" style="font-size:30px; color:var(--fg); top:60px;">{esc(k.get("title", ROUND_NAME.get(rnd, "")))}</div>')
    if k.get("ad"):
        body.append('<div class="ad">유료 광고 포함</div>')
    body.append(s.caption_html())
    js = [cam_js(k.get("cam", "pull"), s.dur),
          'tl.fromTo("#ttl", {opacity: 0, y: -20}, {opacity: 1, y: 0, duration: 0.4}, 0.1);',
          'tl.fromTo("#cam", {opacity: 0}, {opacity: 1, duration: 0.4}, 0);']
    if k.get("reveal") is not None:
        for i in range(6):
            js.append(f'tl.to("#gn{i}", {{opacity: 1, duration: 0.3}}, {k["reveal"] + i * 0.18:.2f});')
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
        ("kling4_0", "최대 30초 · 1080p · 레퍼런스 · 키프레임 · 영상 편집"),
        ("seedance_2_5", "최대 30초 · 1080p · 레퍼런스 · 영상 이어 붙이기"),
        ("veo3_1", "4·6·8초 · 시작 이미지 1장 · 힉스필드 자동 문장 보정"),
        ("wan3_0", "최대 30초 · 1080p · 레퍼런스 · 소리 생성"),
        ("minimax_h3", "최대 15초 · 2K 고정 · 레퍼런스"),
        ("grok_video_v15", "최대 15초 · 1080p · 레퍼런스"),
    ]
    body = ['<div class="cam" id="cam">',
            '<div id="st" style="position:absolute; left:160px; top:90px; font-size:64px; font-weight:900;">오늘의 여섯 모델</div>']
    for i, (m, desc) in enumerate(rows):
        name, col = MODELS[m]
        y = 190 + i * 104
        body.append(f'<div id="row{i}" style="position:absolute; left:160px; top:{y}px; width:1600px; height:92px; border-radius:18px; background:rgba(16,20,46,.9); display:flex; align-items:center; gap:36px; padding:0 36px; box-shadow: inset 6px 0 0 {col};">'
                    f'<span style="width:300px; font-size:38px; font-weight:900; color:{col};">{esc(name)}</span><span style="font-size:32px; font-weight:600;">{esc(desc)}</span></div>')
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
    order = ["kling4_0", "grok_video_v15", "veo3_1", "wan3_0", "seedance_2_5", "minimax_h3"]
    body = ['<div class="cam" id="cam">',
            '<div id="bt" style="position:absolute; left:160px; top:70px; font-size:60px; font-weight:900;">다섯 시험 성적표 <span style="font-size:30px; color:var(--mute); font-weight:600;">· 단아쌤 1차 채점</span></div>']
    cols = ["장풍", "경공", "비무", "레퍼런스", "현판", "1등 횟수"]
    x0, cw = 520, 200
    for j, c in enumerate(cols):
        body.append(f'<div id="h{j}" style="position:absolute; left:{x0 + j * cw}px; top:180px; width:{cw}px; text-align:center; font-size:30px; font-weight:800; color:var(--mute);">{c}</div>')
    for i, m in enumerate(order):
        name, col = MODELS[m]
        y = 240 + i * 108
        wins = sum(1 for r in rounds if m in WINNERS[r])
        body.append(f'<div id="br{i}" style="position:absolute; left:160px; top:{y}px; width:1600px; height:90px; border-radius:16px; background:rgba(16,20,46,.9);"></div>')
        body.append(f'<div id="bn{i}" style="position:absolute; left:196px; top:{y + 22}px; font-size:38px; font-weight:900; color:{col};">{esc(name)}</div>')
        for j, r in enumerate(rounds):
            mark = "🏆" if m in WINNERS[r] else ""
            body.append(f'<div class="cell" id="c{i}_{j}" style="position:absolute; left:{x0 + j * cw}px; top:{y + 16}px; width:{cw}px; text-align:center; font-size:46px; font-family:Pretendard, \"Noto Color Emoji\";">{mark}</div>')
        body.append(f'<div id="w{i}" style="position:absolute; left:{x0 + 5 * cw}px; top:{y + 14}px; width:{cw}px; text-align:center; font-size:52px; font-weight:900; color:{"#b4e61d" if wins >= 2 else "#f5f3ff"};">{wins}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("push", s.dur), 'tl.fromTo("#bt", {opacity: 0}, {opacity: 1, duration: 0.4}, 0.1);']
    for j in range(len(cols)):
        js.append(f'tl.fromTo("#h{j}", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, 0.3);')
    for i in range(6):
        js.append(f'tl.fromTo(["#br{i}", "#bn{i}"], {{opacity: 0, x: -40}}, {{opacity: 1, x: 0, duration: 0.4, ease: "expo.out"}}, {0.4 + i * 0.1:.2f});')
    for j in range(5):
        js.append(f'tl.fromTo(".cell[id$=\'_{j}\']", {{opacity: 0, scale: 0.4}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)"}}, {1.4 + j * 0.45:.2f});')
    for i in range(6):
        js.append(f'tl.fromTo("#w{i}", {{opacity: 0, scale: 0.5}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)"}}, 3.9);')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_credits(s):
    order = sorted(MODELS, key=lambda m: TOTAL[m])
    mx = max(TOTAL.values())
    body = ['<div class="cam" id="cam">',
            '<div id="ct" style="position:absolute; left:160px; top:80px; font-size:60px; font-weight:900;">시험 5개에 든 크레딧</div>',
            '<div id="cs" style="position:absolute; left:160px; top:160px; font-size:28px; color:var(--mute); font-weight:600;">8초 클립 5개 합계 · 힉스필드 견적 · 2026년 10월 27~28일 기준 · 클링은 출시 할인가</div>']
    for i, m in enumerate(order):
        name, col = MODELS[m]
        y = 220 + i * 100
        w = int(1100 * TOTAL[m] / mx)
        body.append(f'<div id="cn{i}" style="position:absolute; left:160px; top:{y + 20}px; width:330px; font-size:38px; font-weight:900; color:{col};">{esc(name)}</div>')
        body.append(f'<div id="cb{i}" style="position:absolute; left:500px; top:{y + 14}px; width:{max(w, 14)}px; height:64px; border-radius:12px; background:{col}; transform-origin:left center;"></div>')
        body.append(f'<div id="cv{i}" style="position:absolute; left:{520 + max(w, 14)}px; top:{y + 18}px; font-size:46px; font-weight:900; font-variant-numeric: tabular-nums;" data-v="{TOTAL[m]}">0</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("punch", s.dur), 'tl.fromTo(["#ct", "#cs"], {opacity: 0}, {opacity: 1, duration: 0.4}, 0.1);']
    for i in range(6):
        t0 = 0.6 + i * 0.35
        js.append(f'tl.fromTo("#cn{i}", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, {t0:.2f});')
        js.append(f'tl.fromTo("#cb{i}", {{scaleX: 0}}, {{scaleX: 1, duration: 0.8, ease: "power3.out"}}, {t0:.2f});')
        js.append(f'(function(){{ const el = document.getElementById("cv{i}"); const o = {{v: 0}}; tl.to(o, {{v: +el.dataset.v, duration: 0.8, ease: "power3.out", onUpdate: function(){{ el.textContent = Math.round(o.v); }}}}, {t0:.2f}); tl.set(el, {{textContent: el.dataset.v}}, {t0 + 0.81:.2f}); }})();')
    js.append(s.caption_js())
    return page(s.cid, s.dur, "\n".join(body), "\n".join(js))


def render_faces(s):
    """R4 마지막 클로즈업 6장 + 원본 시트."""
    order = ["kling4_0", "wan3_0", "minimax_h3", "grok_video_v15", "seedance_2_5", "veo3_1"]
    body = ['<div class="cam" id="cam">',
            '<div id="ref" class="frame" style="left:120px; top:120px; width:520px; height:600px;"><img src="assets/images/ref_pair.png" alt="" style="object-fit:cover" /></div>',
            '<div id="reft" style="position:absolute; left:120px; top:730px; width:520px; text-align:center; font-size:32px; font-weight:800; color:var(--lime);">원본 레퍼런스</div>']
    for i, m in enumerate(order):
        key = f"r4_{m}"
        make_last_frame(key)
        name, col = MODELS[m]
        x = 700 + (i % 3) * 380
        y = 120 + (i // 3) * 330
        body.append(f'<div class="frame" id="f{i}" style="left:{x}px; top:{y}px; width:360px; height:250px; border-radius:14px;"><img src="assets/images/last_{key}.png" alt="" style="object-fit:cover" /></div>'
                    f'<div id="fn{i}" style="position:absolute; left:{x}px; top:{y + 258}px; width:360px; text-align:center; font-size:28px; font-weight:800; color:{col};">{esc(name)}</div>')
    body.append("</div>")
    body.append(s.caption_html())
    js = [gridbg_js(s.dur), cam_js("pan", s.dur), 'tl.fromTo(["#ref", "#reft"], {opacity: 0, x: -40}, {opacity: 1, x: 0, duration: 0.5, ease: "expo.out"}, 0.1);']
    for i in range(6):
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


RENDER = {"talk": render_talk, "clip": render_clip, "grid": render_grid, "prompt": render_prompt, "verdict": render_verdict,
          "specs": render_specs, "rules": render_rules, "board": render_board, "credits": render_credits, "faces": render_faces,
          "split": render_split, "film": render_film}


def make_last_frame(key):
    out = ROOT / "assets" / "images" / f"last_{key}.png"
    if out.exists():
        return
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-sseof", "-0.3", "-i", str(ROOT / "assets" / "clips" / f"{key}.mp4"),
                    "-frames:v", "1", str(out)], check=True)


# ------------------------------------------------------------------ 대본 (장면 목록)
def scenes():
    S = []
    n = [0]

    def add(name, kind, caps=(), **kw):
        n[0] += 1
        S.append(Scene(n[0], name, kind, caps, **kw))

    # 1. 훅 · 판돈 · 소개
    add("hook-grid", "grid", ["같은 문장 하나로 만든 장풍 영상 여섯 개예요. 만든 AI만 달라요.",
                              "이 중에 진짜 무협 영화 같은 건 몇 번일까요? 정답은 끝에서 알려드릴게요."],
        round="r1", title="같은 문장 · 다른 AI 여섯 개", cam="push", ad=True, music="wuxia", sfx=[("whoosh", 0.1)])
    add("hook-question", "talk", ["클링 4.0이 나왔어요. 역대 최고 영상 AI라는 말까지 나와요.",
                                  "시댄스 2.5보다 낫다는 사람도 있고요. 진짜일까요, 그냥 과장일까요?"],
        kicker="NEW · KLING 4.0", title="클링 4.0, 진짜 최고일까?", hl=["진짜 최고"], sub="시댄스 2.5 · 비오 3.1 · 완 3.0 · 미니맥스 H3 · 그록 1.5", cam="push", ad=True, music="wuxia", sfx=[("ding", 0.3)])
    add("authority", "clip", ["저는 대학에서 AI를 가르치고, 회사를 운영하면서 매일 AI로 일하는 단아쌤이에요."],
        key="authority", audio=False, cam="punch", music="wuxia", min_dur=7.0)
    add("stakes", "talk", ["그래서 직접 확인했어요. 영상 AI 여섯 개에 똑같은 문장을 넣고, 크레딧을 천 개 넘게 썼어요.",
                           "시험은 무협으로 냈어요. 쉬운 장면은 다 잘하거든요."],
        kicker="AI 교수의 시험지", title="영상 AI 6개 × 무협 시험 5개", hl=["무협 시험 5개"], sub="장풍 · 경공 · 비무 · 레퍼런스 · 현판(함정)", cam="pan", music="wuxia", sfx=[("brush", 0.2)])
    add("rules", "rules", ["조건은 똑같아요. 같은 문장, 8초, 다시 뽑기 없이 첫 결과만.",
                           "각 모델이 얼마 들었는지는 마지막에 보여드릴게요. 솔직히 그게 결론을 바꿔요."],
        title="공정 조건", items=["6개 모델에 같은 문장", "8초 · 16:9 · 같은 설정", "다시 뽑기 없이 첫 결과만", "가격은 마지막에 공개"], music="calm", sfx=[("tick", 0.85), ("tick", 1.2), ("tick", 1.55), ("tick", 1.9)])
    add("sponsor", "talk", ["먼저 말씀드릴게요. 이 영상에는 힉스필드 유료 광고가 포함돼 있어요.",
                            "여섯 개 모델을 전부 힉스필드 한 계정에서 돌렸어요. 모델만 바꾸면 문장은 그대로예요.",
                            "지금 클링 4.0 출시 할인도 하고 있어요. 링크는 설명란에 있어요."],
        kicker="유료 광고 포함", title="여섯 모델을 한 계정에서", hl=["한 계정"], sub="힉스필드 · 모델만 바꾸면 문장은 그대로", cam="push", ad=True, music="calm")
    add("specs", "specs", ["시작 전에 여섯 모델을 30초만 볼게요.",
                           "클링 4.0은 기억할 사진, 즉 레퍼런스를 여러 장 넣을 수 있고, 만든 영상을 고치는 편집 기능이 있어요.",
                           "비오는 힉스필드가 문장을 자동으로 다듬어서 넣고, 미니맥스는 2K로만 나와요. 화면에 표시해 둘게요."],
        music="calm")

    # 2. 시험 1 장풍
    add("r1-prompt", "prompt", ["첫 번째 시험, 장풍이에요. 손바닥에서 바람이 나가서 대나무가 휘고 낙엽이 날아가야 해요."],
        round="r1", sub="보이지 않는 힘을 보이게 만드는 시험", music="wuxia", sfx=[("brush", 0.1)])
    add("r1-grid", "grid", ["크레딧부터 볼게요. 클링 4, 완 14, 미니맥스 16, 그록 36, 시댄스 56, 비오 80.",
                            "같은 8초인데 스무 배 차이예요."],
        round="r1", reveal=1.0, music="wuxia", sfx=[("tick", 1.0), ("tick", 1.18), ("tick", 1.36), ("tick", 1.54), ("tick", 1.72), ("tick", 1.9)])
    add("r1-veo", "clip", ["비오는 제가 부탁한 로우앵글을 지켰고, 낙엽 폭풍이 제일 극적이에요. 대신 화면 위아래에 검은 띠가 생겼어요."],
        key="r1_veo3_1", model="veo3_1", credits=80, note="힉스필드 자동 문장 보정 적용", music="wuxia")
    add("r1-grok", "clip", ["그록은 유일하게 공기 소용돌이를 눈에 보이게 그렸어요. 다만 옆모습에 입을 벌린 표정이라 조금 과해요."],
        key="r1_grok_video_v15", model="grok_video_v15", credits=36, mark=(1240, 420, 170), mark_at=4.5, cam="pull", music="wuxia")
    add("r1-seedance", "clip", ["시댄스는 숨 고르는 장면까지 살렸어요. 그런데 옷감이 얇게 비쳐 보여서 바로 쓰기는 조금 망설여져요."],
        key="r1_seedance_2_5", model="seedance_2_5", credits=56, cam="push", music="wuxia")
    add("r1-kling", "clip", ["클링은 마보 자세가 무협다운데, 정작 장풍 파동이 잘 안 보여요. 이건 아쉬워요."],
        key="r1_kling4_0", model="kling4_0", credits=4, cam="pan", music="wuxia")
    add("r1-split", "split", ["완은 안정적이고, 미니맥스는 손바닥을 카메라 쪽으로 미는 구도가 시원해요."],
        a=("r1_wan3_0", "Wan 3.0 · 14"), b=("r1_minimax_h3", "MiniMax H3 · 16 (2K)"), colors=["#ffbf3c", "#3fd6c6"], music="wuxia")
    add("r1-verdict", "verdict", ["장풍은 비오가 가져가요. 그런데 서서 쏘는 장풍은 쉬운 편이에요. 지붕 위를 날아다니면 어떨까요?"],
        round="r1", hand="로우앵글 + 낙엽 폭풍", music="wuxia", sfx=[("stamp", 0.65)])

    # 3. 시험 2 경공
    add("r2-prompt", "prompt", ["두 번째, 경공이에요. 지붕을 달리고, 처마에서 처마로 뛰고, 연못 위를 밟고 건너야 해요."],
        round="r2", sub="순서 세 단계 · 하나라도 빠지면 바로 보여요", music="wuxia", sfx=[("brush", 0.1)])
    add("r2-grid", "grid", ["이번 번호는 섞었어요. 몇 번이 세 단계를 다 했을까요?"], round="r2", reveal=3.2, music="wuxia",
        sfx=[("whoosh", 3.1)])
    add("r2-seedance", "clip", ["시댄스는 노을빛이 정말 영화 같아요. 그런데 옷자락이 웨딩드레스처럼 길어지고, 걷다가 연못에 서서 끝나요. 연못을 건너지 않았어요."],
        key="r2_seedance_2_5", model="seedance_2_5", credits=56, cam="push", music="wuxia")
    add("r2-veo", "clip", ["비오는 제일 역동적으로 뛰어요. 그런데 착지할 때 물보라가 커서 물에 빠지는 것처럼 보여요."],
        key="r2_veo3_1", model="veo3_1", credits=80, cam="pan", music="wuxia")
    add("r2-kling", "clip", ["클링은 지붕, 처마, 연못까지 세 단계를 순서대로 다 했어요. 다만 마지막엔 뛰기보다 걷는 느낌이에요."],
        key="r2_kling4_0", model="kling4_0", credits=4, cam="pull", music="wuxia")
    add("r2-wan", "clip", ["완도 세 단계를 다 했고, 연못 위를 끝까지 달려요. 이번 시험에서 제일 경공다웠어요."],
        key="r2_wan3_0", model="wan3_0", credits=14, cam="push", music="wuxia")
    add("r2-split", "split", ["미니맥스는 걷는 느낌이라 경공 맛이 약하고, 그록은 수면 물결 표현이 좋아요."],
        a=("r2_minimax_h3", "MiniMax H3 · 16 (2K)"), b=("r2_grok_video_v15", "Grok 1.5 · 36"), colors=["#3fd6c6", "#c9a7ff"], music="wuxia")
    add("r2-verdict", "verdict", ["경공은 완, 클링은 근소한 2등이에요. 화면이 제일 예쁜 건 시댄스였지만, 시킨 걸 다 한 건 완과 클링이었어요.",
                                  "이 차이, 끝까지 기억해 주세요. 이제 두 사람이 붙으면 어떨까요?"],
        round="r2", hand="예쁜 것 ≠ 시킨 대로 한 것", music="wuxia", sfx=[("stamp", 0.65)])

    # 4. 시험 3 비무
    add("r3-prompt", "prompt", ["세 번째는 비무예요. 인사하고, 정확히 다섯 번 겨루고, 시간이 멈추며 카메라가 돌고, 서로 포권.",
                                "시킨 게 제일 많은 시험이에요. 순서대로 다 하는지 볼게요."],
        round="r3", sub="지시 이행 시험 · 서소저 vs 귀공자", music="wuxia", sfx=[("brush", 0.1)])
    add("r3-grid", "grid", ["여섯 개 모두 두 사람의 옷과 머리는 잘 지켰어요. 차이는 순서에서 났어요."], round="r3", reveal=2.6, music="wuxia",
        sfx=[("whoosh", 2.5)])
    add("r3-grok", "clip", ["그록은 인사로 시작해서, 목검이 부딪히는 순간 낙엽이 공중에 멈추고, 마지막에 다시 마주 서요. 순서를 제일 잘 따랐어요."],
        key="r3_grok_video_v15", model="grok_video_v15", credits=36, cam="push", music="wuxia")
    add("r3-seedance", "clip", ["시댄스는 클로즈업으로 목검이 부딪히는 장면이 정말 영화 같아요. 하지만 시간 정지와 카메라 회전은 없었어요."],
        key="r3_seedance_2_5", model="seedance_2_5", credits=56, cam="pan", music="wuxia")
    add("r3-kling", "clip", ["클링은 각도를 바꿔가며 보여줬지만, 인사와 시간 정지는 빠졌어요. 이번 시험은 클링이 약했어요."],
        key="r3_kling4_0", model="kling4_0", credits=4, cam="pull", music="wuxia")
    add("r3-split", "split", ["비오는 낙엽이 화려하고, 미니맥스는 합이 시원시원해요. 둘 다 시간 정지는 없었어요."],
        a=("r3_veo3_1", "Veo 3.1 · 80"), b=("r3_minimax_h3", "MiniMax H3 · 16 (2K)"), colors=["#5b8cff", "#3fd6c6"], music="wuxia")
    add("r3-verdict", "verdict", ["비무는 그록이에요. 그럼 같은 사람을 끝까지 유지하는 건 누가 잘할까요?"],
        round="r3", hand="인사 → 합 → 정지 → 마주 서기", music="wuxia", sfx=[("stamp", 0.65)])

    # 5. 시험 4 레퍼런스
    add("r4-intro", "talk", ["네 번째는 제일 실용적인 시험이에요. 서소저와 귀공자 사진을 먼저 만들어서, 모든 모델에 똑같이 넣었어요.",
                             "세 컷 내내 같은 얼굴, 같은 옷으로 나오는지 볼게요. 같은 인물로 이어 찍어야 하는 영상이라면 이게 제일 중요해요.",
                             "비오는 시작 이미지 한 장만 받을 수 있어서, 두 사람이 함께 있는 첫 장면을 따로 만들어 넣었어요."],
        kicker="시험 4 · 레퍼런스", title="같은 사람으로 끝까지", hl=["끝까지"], sub="인물 사진 시트 2장 → 6개 모델 공통", img="ref_sheets.png", img_w=780, img_h=620, fit="contain", cam="pan", music="calm", sfx=[("brush", 0.1)])
    add("r4-grid", "grid", ["다리 위를 걷고, 다가와서 멈추고, 클로즈업으로 마주 보기. 세 컷 구성이에요."], round="r4", reveal=2.4, music="calm",
        sfx=[("whoosh", 2.3)])
    add("r4-faces", "faces", ["마지막 클로즈업을 원본 사진과 나란히 볼게요.",
                              "클링은 귀공자의 옥비녀 상투와 옷 자수까지 그대로예요. 완도 거의 같아요.",
                              "시댄스와 비오는 귀공자의 상투가 풀려버렸고, 얼굴도 조금씩 달라졌어요."], music="calm")
    add("r4-kling", "clip", ["클링은 세 컷 순서도 그대로 지켰어요. 걷기, 다가오기, 클로즈업."],
        key="r4_kling4_0", model="kling4_0", credits=18, note="레퍼런스 모드 · 720p", cam="push", music="calm")
    add("r4-verdict", "verdict", ["레퍼런스는 클링이에요. 마지막은 함정이에요."],
        round="r4", hand="옥비녀 하나까지 그대로", music="wuxia", sfx=[("stamp", 0.65)])

    # 6. 시험 5 현판 (함정)
    add("r5-prompt", "prompt", ["객잔 현판에 '단아객잔' 네 글자, 그리고 차를 따르는 손. 영상 AI는 글자에 약하다고 알려져 있죠."],
        round="r5", sub="함정 · 한글 글자", music="calm", sfx=[("brush", 0.1)])
    add("r5-grid", "grid", ["결과는 반전이에요. 클링, 시댄스, 그록, 미니맥스는 네 글자를 정확히 썼어요."],
        round="r5", reveal=2.0, winners=["kling4_0", "seedance_2_5", "grok_video_v15", "minimax_h3"], winners_at=3.2, music="calm", sfx=[("ding", 3.2)])
    add("r5-wan", "clip", ["완은 '단야객잔'. 한 글자가 틀렸어요."],
        key="r5_wan3_0", model="wan3_0", credits=14, stamp="단야?", stamp_at=2.6, cam="push", music="calm", sfx=[("stamp", 2.6)], min_dur=8.0)
    add("r5-veo", "clip", ["비오는 아예 한자로 바꿔버렸어요. 힉스필드가 문장을 자동으로 다듬는 과정에서 바뀐 것으로 보여요."],
        key="r5_veo3_1", model="veo3_1", credits=80, stamp="한자?", stamp_at=5.6, cam="pan", music="calm", sfx=[("stamp", 5.6)], min_dur=8.0)
    add("r5-twist", "talk", ["더 재밌는 건 이거예요. 함정을 피하려고 이미지 AI로 현판을 먼저 만들었는데요,",
                             "이미지 AI가 '단'을 '탄'으로 틀렸어요. '탄아객잔'이 됐어요.",
                             "결론은 하나예요. 글자는 어떤 AI든 꼭 눈으로 확인하세요."],
        kicker="함정의 함정", title="글자는 꼭 눈으로 확인", hl=["눈으로 확인"], sub="이미지 AI도 틀린다: 단 → 탄", img="r5_signboard.png", img_w=780, img_h=440, cam="push", music="calm")
    add("r5-verdict", "verdict", ["현판은 클링, 시댄스, 그록 공동 1등이에요."],
        round="r5", hand="미니맥스는 글자가 기울어서 아깝게 탈락", music="wuxia", sfx=[("stamp", 0.65)])

    # 7. 점수 · 반전 · 강점
    add("board", "board", ["다섯 시험 결과예요. 1등을 두 번 한 모델은 클링과 그록이에요.",
                           "솔직히 제일 영화 같은 화면은 시댄스였어요. 그런데 시킨 걸 끝까지 따르는 모델은 시험마다 달랐어요.",
                           "그럼 누가 정답일까요? 아직 돈 얘기를 안 했어요."], music="calm", sfx=[("tick", 1.4), ("tick", 1.85), ("tick", 2.3), ("tick", 2.75), ("tick", 3.2), ("ding", 3.9)])
    add("credits", "credits", ["다섯 시험에 든 크레딧이에요. 클링 34, 완 70, 미니맥스 80, 그록 180, 시댄스 280, 비오 400.",
                               "같은 시험을 클링은 시댄스의 8분의 1, 비오의 12분의 1 가격으로 끝냈어요.",
                               "지금은 출시 할인가라는 것도 꼭 말씀드릴게요. 할인이 끝나면 가격은 오를 수 있어요."],
        music="wuxia", sfx=[("tick", 0.6), ("tick", 0.95), ("tick", 1.3), ("tick", 1.65), ("tick", 2.0), ("tick", 2.35)])
    add("kling-why", "talk", ["그리고 클링은 싸기만 한 게 아니에요. 레퍼런스 시험 1등, 현판 글자도 정확했어요.",
                              "같은 인물로 여러 컷을 시킨 대로 만드는 일, 우리가 실제로 제일 많이 하는 일이죠."],
        kicker="그래서 클링", title="싸고, 사람을 기억하고, 글자도 맞게", hl=["사람을 기억"], sub="레퍼런스 1등 · 현판 공동 1등 · 크레딧 최저", cam="push", music="wuxia")
    add("edit-demo", "split", ["클링에는 만든 영상을 고치는 편집 기능도 있어요. 장풍 파동이 안 보였던 영상을 그 부분만 고쳐봤는데요,",
                               "솔직히 이번엔 바람 번짐만 살짝 생겼어요. 편집도 한 번에 되진 않아요."],
        a=("r1_kling4_0", "원본 (시험 1)"), b=("edit_r1_kling", "클링 편집 후"), music="calm")
    add("edit-fix", "split", ["대신 처음부터 '눈에 보이는 충격파'라고 쓰고, 서소저 사진을 레퍼런스로 넣었더니 이렇게 나왔어요."],
        a=("r1_kling4_0", "시험 1 · 글만"), b=("film_s2b", "단편 샷 · 레퍼런스 + 구체적 문장"), music="calm")
    add("film-intro", "talk", ["그래서 오늘 결과로 클링 하나만 써서 30초 무협 단편을 만들어봤어요.",
                               "이건 비교가 아니라 작품이라, 샷마다 두 번씩 뽑아서 좋은 걸 골랐어요."],
        kicker="클링 4.0 단편", title="단아검법", sub="레퍼런스 · 1080p · 샷당 2회 생성", img="ref_sheets.png", img_w=780, img_h=620, fit="contain", cam="pull", music="calm")
    FILM = [("film_s1", 0, 4.0), ("film_s2b", 0, 5.0), ("film_s3a", 0, 6.0), ("film_s4b", 0, 8.0), ("film_s5", 0, 4.0), ("r5_kling4_0", 4.6, 3.4)]
    add("film", "film", [], min_dur=0.6 + sum(d for _, _, d in FILM) + 0.4, shots=FILM, music="none")

    # 8. 추천 · CTA
    add("recommend", "talk", ["정리할게요. 제일 영화 같은 한 컷이 필요하고 예산이 넉넉하면 시댄스.",
                              "같은 인물로 여러 컷을, 시킨 대로, 싸게 만들 거면 클링 4.0.",
                              "꼭 하나만 고를 필요는 없어요. 장면마다 갈아타면 돼요. 그래서 저는 여섯 개를 한 곳에서 쓰는 힉스필드를 써요."],
        kicker="이럴 땐 이 모델", title="한 컷 승부는 시댄스, 시리즈는 클링", hl=["시리즈는 클링"], sub="장면마다 갈아타기 · 힉스필드 한 계정", cam="push", music="wuxia")
    add("cta", "talk", ["클링 4.0 할인은 지금 진행 중이에요. 설명란 링크로 들어가서 오늘 프롬프트 그대로 돌려보세요.",
                        "장풍 하나에 4크레딧이에요."],
        kicker="설명란 링크", title="오늘 프롬프트 그대로 돌려보세요", hl=["그대로"], sub="클링 4.0 출시 할인 중 · 크레딧은 2026년 10월 기준", cam="punch", ad=True, music="wuxia", sfx=[("ding", 0.4)])
    add("answer", "grid", ["처음 문제 정답이에요. 1번 완, 2번 비오, 3번 미니맥스, 4번 그록, 5번 클링, 6번 시댄스.",
                           "여러분이 고른 번호는 어떤 모델이었어요?"], round="r1", reveal=0.8, title="첫 문제 정답", cam="push", music="wuxia",
        sfx=[("ding", 0.8)])
    add("outro", "talk", ["여러분이 채점했다면 1등은 누구예요? 댓글로 알려주세요.",
                          "다음 영상에서는 오늘 단편을 3분짜리로 늘려볼게요."],
        kicker="다음 영상", title="단아검법, 3분으로", sub="구독하고 기다려 주세요", cam="pull", music="wuxia", tail=1.5)
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
