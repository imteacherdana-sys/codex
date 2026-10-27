"""단아쌤 전용 HyperFrames 템플릿 5종을 만든다: 채팅창 2종, 이모지, 사진, 도형.

사용: python3 _tools/make_custom.py <templates 폴더>
각 템플릿은 <slug>/index.html (+ assets -> ../_assets) 한 편짜리 HyperFrames 프로젝트다.
채팅창은 공식 claude-exchange / chatgpt-exchange 블록의 다크 팔레트를 16:9 창으로 옮긴 '예시 화면'이다.
"""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])

HEAD = """<!doctype html>
<html lang="ko" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard.woff2") format("woff2"); font-weight: 100 900; font-display: block; }
      @font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"); }
      @font-face { font-family: "NanumPen"; src: url("assets/fonts/NanumPenScript-korean.woff2") format("woff2"); font-display: block; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #05060f; }
      #root { position: relative; width: 1920px; height: 1080px; overflow: hidden; font-family: "Pretendard", sans-serif; color: #f5f3ff; word-break: keep-all; }
      .ground { position: absolute; inset: 0; background: linear-gradient(#0b1026, #05060f); }
      .grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(124,58,237,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,.12) 1px, transparent 1px); background-size: 40px 40px; -webkit-mask-image: radial-gradient(ellipse at 50% 50%, #000 20%, transparent 70%); mask-image: radial-gradient(ellipse at 50% 50%, #000 20%, transparent 70%); }
"""


def page(cid, dur, style, body, script, variables=None):
    vars_attr = ""
    if variables:
        vars_attr = " data-composition-variables='" + json.dumps(variables, ensure_ascii=False).replace("'", "&#39;") + "'"
    html = HEAD.replace('<html lang="ko" data-resolution="landscape">', f'<html lang="ko" data-resolution="landscape"{vars_attr}>')
    return (html + style + """    </style>
  </head>
  <body>
    <div id="root" data-composition-id=\"""" + cid + f"""\" data-start="0" data-duration="{dur}" data-width="1920" data-height="1080">
      <div class="ground"></div>
      <div class="grid"></div>
""" + body + f"""
      <div id="{cid}-drv" class="clip" data-start="0" data-duration="{dur}" data-track-index="0" style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none"></div>
    </div>
    <script>
      (function () {{
        window.__timelines = window.__timelines || {{}};
        const vars = (window.__hyperframes && window.__hyperframes.getVariables && window.__hyperframes.getVariables()) || {{}};
        const tl = gsap.timeline({{ paused: true }});
""" + script + f"""
        window.__timelines["{cid}"] = tl;
      }})();
    </script>
  </body>
</html>
""")


def write(slug, html):
    out = ROOT / slug
    out.mkdir(exist_ok=True)
    link = out / "assets"
    if not link.exists():
        link.symlink_to("../_assets")
    (out / "index.html").write_text(html, encoding="utf-8")
    print("ok", slug)


# ---------------------------------------------------------------- 채팅창 2종
def chat(slug, cid, theme):
    t = theme
    style = f"""
      .win {{ position: absolute; left: 240px; top: 100px; width: 1440px; height: 880px; border-radius: 26px; background: {t['bg']}; box-shadow: 0 0 0 2px {t['hair']}, 0 40px 100px rgba(0,0,0,.55); overflow: hidden; }}
      .bar {{ position: absolute; left: 0; right: 0; top: 0; height: 72px; display: flex; align-items: center; gap: 14px; padding: 0 32px; border-bottom: 1px solid {t['hair']}; }}
      .bar b {{ font-size: 28px; font-weight: 700; color: {t['ink']}; }}
      .bar i {{ width: 18px; height: 18px; border-radius: {t['mark_radius']}; background: {t['accent']}; display: block; }}
      .bar small {{ margin-left: auto; font-size: 20px; color: {t['muted']}; }}
      .user {{ position: absolute; right: 64px; top: 120px; max-width: 900px; padding: 22px 30px; border-radius: 26px; background: {t['bubble']}; font-size: 32px; line-height: 1.5; color: {t['ink']}; }}
      .think {{ position: absolute; left: 64px; top: 270px; display: flex; align-items: center; gap: 16px; font-size: 28px; color: {t['muted']}; }}
      .think i {{ width: 18px; height: 18px; border-radius: 50%; background: {t['think']}; display: block; }}
      .answer {{ position: absolute; left: 64px; top: 260px; width: 1200px; font-size: 32px; line-height: 1.7; color: {t['ink']}; }}
      .answer p {{ margin-bottom: 10px; }}
      .answer span {{ display: inline; }}
      .hlw {{ position: relative; display: inline-block; isolation: isolate; }}
      .mark {{ position: absolute; left: -6px; right: -6px; top: 4px; bottom: 2px; border-radius: 10px; z-index: -1; background: rgba(180,230,29,.26); box-shadow: inset 0 -6px 0 #b4e61d; transform-origin: left center; }}
      .input {{ position: absolute; left: 120px; right: 120px; bottom: 40px; height: 118px; border-radius: {t['input_radius']}; background: {t['input']}; box-shadow: 0 0 0 1px {t['hair']}; display: flex; align-items: center; padding: 0 130px 0 40px; font-size: 32px; color: {t['ink']}; }}
      .ph {{ position: absolute; left: 40px; color: {t['muted']}; }}
      .typed {{ white-space: pre; }}
      .typed span {{ display: none; }}
      .caret {{ display: inline-block; width: 3px; height: 38px; margin-left: 2px; background: {t['ink']}; vertical-align: -6px; }}
      .send {{ position: absolute; right: 26px; top: 26px; width: 66px; height: 66px; border-radius: {t['send_radius']}; background: {t['send_bg']}; color: {t['send_fg']}; display: grid; place-items: center; font-size: 34px; font-weight: 800; }}
      .tag {{ position: absolute; left: 240px; top: 52px; font-size: 22px; color: #a5a3c7; }}
"""
    body = f"""      <div class="tag" id="{cid}-tag">예시 화면 · 실제 시연은 화면 녹화로</div>
      <div class="win" id="{cid}-win">
        <div class="bar"><i></i><b>{t['name']}</b><small>새 대화</small></div>
        <div class="user" id="{cid}-user"></div>
        <div class="think" id="{cid}-think"><i id="{cid}-dot"></i><span>{t['thinking']}</span></div>
        <div class="answer" id="{cid}-answer"></div>
        <div class="input"><span class="ph" id="{cid}-ph">{t['placeholder']}</span><span class="typed" id="{cid}-typed"></span><span class="caret" id="{cid}-caret"></span><div class="send" id="{cid}-send">↑</div></div>
      </div>
"""
    script = f"""
        const prompt = vars.prompt || {json.dumps(t['prompt'], ensure_ascii=False)};
        const lines = (vars.answer || {json.dumps(t['answer'], ensure_ascii=False)}).split("\\n");
        const mark = vars.highlight || {json.dumps(t['highlight'], ensure_ascii=False)};
        const typed = document.getElementById("{cid}-typed");
        const chars = Array.from(prompt).map(function (ch) {{ const s = document.createElement("span"); s.textContent = ch; typed.appendChild(s); return s; }});
        document.getElementById("{cid}-user").textContent = prompt;
        const ans = document.getElementById("{cid}-answer");
        const words = [];
        let hl = null;
        function addWords(parent, text) {{
          text.split(/(\\s+)/).forEach(function (w) {{ if (!w) return; const s = document.createElement("span"); s.textContent = w; parent.appendChild(s); if (w.trim()) words.push(s); }});
        }}
        lines.forEach(function (line) {{
          const p = document.createElement("p");
          const at = mark ? line.indexOf(mark) : -1;
          if (at > -1 && !hl) {{
            addWords(p, line.slice(0, at));
            const wrap = document.createElement("span"); wrap.className = "hlw";
            hl = document.createElement("i"); hl.className = "mark"; wrap.appendChild(hl);
            addWords(wrap, mark); p.appendChild(wrap);
            addWords(p, line.slice(at + mark.length));
          }} else addWords(p, line);
          ans.appendChild(p);
        }});
        gsap.set(["#{cid}-user", "#{cid}-think"], {{ opacity: 0 }});
        gsap.set(words, {{ opacity: 0 }});
        if (hl) gsap.set(hl, {{ scaleX: 0 }});
        tl.fromTo("#{cid}-win", {{ opacity: 0, scale: 0.97 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "expo.out" }}, 0.2);
        tl.fromTo("#{cid}-tag", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 0.4);
        // 입력: 글자마다 0.05초
        tl.set("#{cid}-ph", {{ opacity: 0 }}, 1.0);
        chars.forEach(function (c, i) {{ tl.set(c, {{ display: "inline" }}, 1.0 + i * 0.05); }});
        const sendAt = 1.0 + chars.length * 0.05 + 0.45;
        tl.to("#{cid}-send", {{ scale: 0.86, duration: 0.08, ease: "power2.in" }}, sendAt);
        tl.to("#{cid}-send", {{ scale: 1, duration: 0.3, ease: "back.out(2)" }}, sendAt + 0.08);
        tl.set("#{cid}-typed", {{ opacity: 0 }}, sendAt + 0.1);
        tl.set("#{cid}-ph", {{ opacity: 1 }}, sendAt + 0.1);
        tl.fromTo("#{cid}-user", {{ opacity: 0, y: 24, scale: 0.96 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "expo.out" }}, sendAt + 0.15);
        // 생각 중
        const th = sendAt + 0.6;
        tl.fromTo("#{cid}-think", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, th);
        tl.fromTo("#{cid}-dot", {{ scale: 0.7 }}, {{ scale: 1.15, duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 3 }}, th);
        tl.to("#{cid}-think", {{ opacity: 0, duration: 0.15 }}, th + 1.45);
        // 답변 스트리밍: 단어 묶음이 0.06초 간격
        const st = th + 1.6;
        words.forEach(function (w, i) {{ tl.fromTo(w, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.12, ease: "power1.out" }}, st + i * 0.06); }});
        if (hl) tl.to(hl, {{ scaleX: 1, duration: 0.45, ease: "expo.out" }}, st + words.length * 0.06 + 0.3);
"""
    variables = [
        {"id": "prompt", "type": "string", "label": "입력할 프롬프트", "default": t["prompt"]},
        {"id": "answer", "type": "string", "label": "답변 (줄바꿈으로 문단)", "default": t["answer"]},
        {"id": "highlight", "type": "string", "label": "라임으로 강조할 문구", "default": t["highlight"]},
    ]
    write(slug, page(cid, t["dur"], style, body, script, variables))


chat("chat-claude", "chat-claude", {
    "name": "Claude", "bg": "#20201f", "hair": "#424240", "ink": "#f8f8f4", "muted": "#94948c", "accent": "#d97757",
    "bubble": "#2f2f2c", "input": "#2a2a28", "think": "#d97757", "mark_radius": "5px", "input_radius": "26px",
    "send_bg": "#d97757", "send_fg": "#1c1c1b", "send_radius": "14px", "thinking": "생각하는 중…",
    "placeholder": "오늘 무엇을 도와드릴까요?", "dur": 12,
    "prompt": "유튜브 롱폼 대본을 10분 분량으로 써줘. 주제는 모션그래픽 완전정복",
    "answer": "좋아요. 10분 대본은 이렇게 나눠볼게요.\n1. 훅 · 밋밋한 자막 한 줄 (0:00–0:30)\n2. 원리 네 가지 · 타이밍, 이징, 위계, 전환\n3. 정리와 다음 편 예고",
    "highlight": "원리 네 가지",
})
chat("chat-chatgpt", "chat-chatgpt", {
    "name": "ChatGPT", "bg": "#212121", "hair": "#303030", "ink": "#fcfcfc", "muted": "#a8a8ac", "accent": "#fcfcfc",
    "bubble": "#303030", "input": "#303030", "think": "#fcfcfc", "mark_radius": "50%", "input_radius": "60px",
    "send_bg": "#fcfcfc", "send_fg": "#0b0b0c", "send_radius": "50%", "thinking": "생각 중",
    "placeholder": "무엇이든 물어보세요", "dur": 11,
    "prompt": "썸네일 문구 3개만 추천해줘. 주제는 모션그래픽 완전정복",
    "answer": "이렇게 써보세요.\n1. 자막 한 줄이 살아나는 4가지 원리\n2. 편집 초보도 바로 쓰는 모션 공식\n3. 밋밋한 영상, 이것만 바꾸세요",
    "highlight": "4가지 원리",
})

# ---------------------------------------------------------------- 이모지 버스트
EMO = ["✨", "🎉", "💡", "👍", "🔥", "⭐", "💯", "🙌"]
burst = "\n".join(f'      <div class="bit" id="emoji-burst-b{i}">{e}</div>' for i, e in enumerate(EMO))
write("emoji-burst", page("emoji-burst", 5, """
      .hero { position: absolute; left: 860px; top: 280px; width: 200px; height: 200px; display: grid; place-items: center; font-size: 180px; font-family: "Noto Color Emoji", sans-serif; }
      .bit { position: absolute; left: 920px; top: 340px; width: 80px; height: 80px; display: grid; place-items: center; font-size: 64px; font-family: "Noto Color Emoji", sans-serif; }
      .line { position: absolute; left: 0; right: 0; top: 600px; text-align: center; font-size: 96px; font-weight: 800; letter-spacing: -0.02em; }
      .line b { color: #b4e61d; font-weight: 800; }
      .sub { position: absolute; left: 0; right: 0; top: 740px; text-align: center; font-size: 36px; font-weight: 600; color: #a5a3c7; }
""", f"""      <div class="hero" id="emoji-burst-hero">🎯</div>
{burst}
      <div class="line" id="emoji-burst-line">핵심은 <b>딱 하나</b></div>
      <div class="sub" id="emoji-burst-sub">이모지는 의미가 바로 읽히는 것 하나만</div>""", f"""
        const bits = {json.dumps([f"#emoji-burst-b{i}" for i in range(len(EMO))])};
        gsap.set(bits.concat(["#emoji-burst-line", "#emoji-burst-sub"]), {{ opacity: 0 }});
        tl.fromTo("#emoji-burst-hero", {{ scale: 0, rotation: -20 }}, {{ scale: 1, rotation: 0, duration: 0.7, ease: "back.out(2.2)" }}, 0.3);
        bits.forEach(function (b, i) {{
          const a = (i / bits.length) * Math.PI * 2 - Math.PI / 2, r = 300 + (i % 2) * 70;
          tl.fromTo(b, {{ opacity: 0, x: 0, y: 0, scale: 0.4 }}, {{ opacity: 1, x: Math.cos(a) * r, y: Math.sin(a) * r * 0.62, scale: 1, duration: 0.7, ease: "expo.out" }}, 0.55 + i * 0.03);
          tl.to(b, {{ opacity: 0, scale: 0.6, duration: 0.4, ease: "power2.in" }}, 2.6 + i * 0.03);
        }});
        tl.fromTo("#emoji-burst-line", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }}, 1.1);
        tl.fromTo("#emoji-burst-sub", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 1.6);
""", [{"id": "line", "type": "string", "label": "문장", "default": "핵심은 딱 하나"}]))

# ---------------------------------------------------------------- 사진 + 스티커 + 손그림
write("image-drop", page("image-drop", 7, """
      .card { position: absolute; left: 470px; top: 150px; width: 980px; height: 620px; padding: 22px 22px 90px; background: #f5f3ff; border-radius: 6px; box-shadow: 0 30px 80px rgba(0,0,0,.55); }
      .card img { width: 936px; height: 508px; object-fit: cover; display: block; }
      .cap { position: absolute; left: 0; right: 0; bottom: 18px; text-align: center; font-family: "NanumPen", cursive; font-size: 64px; color: #4a33a6; }
      .tape { position: absolute; left: 400px; top: -26px; width: 180px; height: 52px; background: rgba(180,230,29,.75); transform: rotate(-4deg); }
      .sticker { position: absolute; left: 1370px; top: 110px; font-size: 120px; font-family: "Noto Color Emoji", sans-serif; }
      .draw { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: visible; }
      .label { position: absolute; left: 1490px; top: 560px; font-family: "NanumPen", cursive; font-size: 60px; color: #b4e61d; }
""", """      <div class="card" id="image-drop-card"><div class="tape"></div><img src="assets/images/desk.jpg" alt="" /><div class="cap">오늘의 작업 공간</div></div>
      <div class="sticker" id="image-drop-sticker">📸</div>
      <svg class="draw" viewBox="0 0 1920 1080">
        <ellipse id="image-drop-ring" cx="1090" cy="420" rx="250" ry="150" fill="none" stroke="#b4e61d" stroke-width="10" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1" transform="rotate(-6 1090 420)"/>
        <path id="image-drop-arrow" d="M1480 590 C1420 560 1380 540 1330 500 M1330 500 L1350 540 M1330 500 L1372 506" fill="none" stroke="#b4e61d" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/>
      </svg>
      <div class="label" id="image-drop-label">편집 화면</div>""", """
        gsap.set(["#image-drop-label"], { opacity: 0 });
        tl.fromTo("#image-drop-card", { opacity: 0, y: -260, rotation: -9 }, { opacity: 1, y: 0, rotation: -2, duration: 0.9, ease: "expo.out" }, 0.2);
        tl.fromTo("#image-drop-sticker", { opacity: 0, scale: 0, rotation: -30 }, { opacity: 1, scale: 1, rotation: 12, duration: 0.5, ease: "back.out(2.4)" }, 1.1);
        tl.fromTo("#image-drop-ring", { strokeDashoffset: 1.1 }, { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }, 2.0);
        tl.fromTo("#image-drop-arrow", { strokeDashoffset: 1.1 }, { strokeDashoffset: 0, duration: 0.6, ease: "power2.out" }, 2.9);
        tl.fromTo("#image-drop-label", { opacity: 0, x: 20 }, { opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }, 3.3);
"""))

# ---------------------------------------------------------------- 도형 키트
SHAPES = [
    ("circle", '<circle cx="110" cy="110" r="96"/>', "#b4e61d", "원"),
    ("square", '<rect x="16" y="16" width="188" height="188" rx="20"/>', "#7c3aed", "사각형"),
    ("tri", '<path d="M110 14 L206 204 L14 204 Z"/>', "#ff6b5b", "삼각형"),
    ("star", '<path d="M110 10 L136 80 L210 82 L152 128 L172 202 L110 160 L48 202 L68 128 L10 82 L84 80 Z"/>', "#22d3ee", "별"),
]
shape_html = "\n".join(
    f'      <div class="shp" id="shape-kit-{k}" style="left:{300 + i * 360}px"><svg viewBox="0 0 220 220"><g class="g" style="--c:{c}" id="shape-kit-{k}-g">{svg}</g></svg><b id="shape-kit-{k}-l">{lab}</b></div>'
    for i, (k, svg, c, lab) in enumerate(SHAPES))
shape_js = "\n".join(
    f'''        tl.fromTo("#shape-kit-{k}-g > *", {{ strokeDashoffset: 1.1, fillOpacity: 0 }}, {{ strokeDashoffset: 0, duration: 0.8, ease: "power2.inOut" }}, {0.3 + i * 0.35});
        tl.to("#shape-kit-{k}-g > *", {{ fillOpacity: 0.9, duration: 0.4, ease: "power1.out" }}, {1.1 + i * 0.35});
        tl.fromTo("#shape-kit-{k}", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.15, ease: "power2.out", yoyo: true, repeat: 1 }}, {1.1 + i * 0.35});
        tl.fromTo("#shape-kit-{k}-l", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, {1.2 + i * 0.35});'''
    for i, (k, _, _, _) in enumerate(SHAPES))
write("shape-kit", page("shape-kit", 5, """
      .shp { position: absolute; top: 330px; width: 240px; display: flex; flex-direction: column; align-items: center; gap: 30px; }
      .shp svg { width: 220px; height: 220px; overflow: visible; }
      .g > * { fill: var(--c); fill-opacity: 0; stroke: var(--c); stroke-width: 10; stroke-linejoin: round; stroke-dasharray: 1 1.2; stroke-dashoffset: 1.1; }
      .shp b { font-size: 44px; font-weight: 800; }
      .title { position: absolute; left: 0; right: 0; top: 150px; text-align: center; font-size: 64px; font-weight: 800; }
""", '      <div class="title" id="shape-kit-title">선으로 그리고, 색으로 채우고</div>\n' + shape_html, """
        document.querySelectorAll(".g > *").forEach(function (el) { el.setAttribute("pathLength", "1"); });
        gsap.set(["#shape-kit-circle-l", "#shape-kit-square-l", "#shape-kit-tri-l", "#shape-kit-star-l"], { opacity: 0 });
        tl.fromTo("#shape-kit-title", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }, 0.1);
""" + shape_js + "\n"))

# ---------------------------------------------------------------- 권위 카드 (단아쌤 소개)
# 경력 문구는 변수다. 기본값은 세진 PD 기획서에 나온 표현만 쓴 예시이며, 촬영 전 본인 확인 후 바꾼다.
AUTH_CHIPS = ["경희대 교수", "기업 운영", "AI 생산성 강의"]
chips_html = "\n".join(f'          <span class="chip" id="authority-card-c{i}">{c}</span>' for i, c in enumerate(AUTH_CHIPS))
write("authority-card", page("authority-card", 7, """
      .plate { position: absolute; inset: -60px; background: url("assets/images/desk.jpg") center / cover; transform-origin: 62% 45%; }
      .shade { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(5,6,15,.92) 0%, rgba(5,6,15,.72) 38%, rgba(5,6,15,.15) 75%), linear-gradient(0deg, rgba(5,6,15,.75), transparent 45%); }
      .cam { position: absolute; inset: 0; transform-origin: 30% 70%; }
      .card { position: absolute; left: 120px; top: 520px; width: 980px; padding: 40px 48px 44px; border-radius: 28px; background: rgba(11,16,38,.72); box-shadow: inset 0 0 0 2px rgba(255,255,255,.12), 0 30px 80px rgba(0,0,0,.45); -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px); }
      .eyebrow { display: inline-flex; align-items: center; gap: 10px; padding: 10px 18px; border-radius: 10px; background: #b4e61d; color: #05060f; font-size: 28px; font-weight: 800; letter-spacing: .04em; }
      .name { margin-top: 22px; display: flex; font-size: 132px; font-weight: 900; letter-spacing: -0.03em; line-height: 1; }
      .name i { font-style: normal; display: inline-block; }
      .uline { margin-top: 18px; width: 420px; height: 10px; border-radius: 6px; background: #b4e61d; transform-origin: left center; }
      .title { margin-top: 24px; font-size: 40px; font-weight: 700; color: #f5f3ff; }
      .chips { margin-top: 26px; display: flex; gap: 14px; flex-wrap: wrap; }
      .chip { padding: 12px 20px; border-radius: 12px; background: rgba(124,58,237,.28); box-shadow: inset 0 0 0 2px rgba(124,58,237,.75); font-size: 30px; font-weight: 700; }
      .tag { position: absolute; right: 60px; top: 48px; font-size: 22px; color: #a5a3c7; }
""", f"""      <div class="cam" id="authority-card-cam">
        <div class="plate" id="authority-card-plate"></div>
        <div class="shade"></div>
        <div class="card" id="authority-card-card">
          <span class="eyebrow" id="authority-card-eyebrow">AI 교수</span>
          <div class="name" id="authority-card-name"></div>
          <div class="uline" id="authority-card-uline"></div>
          <div class="title" id="authority-card-title">경희대 교수 · 기업 대표</div>
          <div class="chips">
{chips_html}
          </div>
        </div>
      </div>
      <div class="tag" id="authority-card-tag">예시 문구 · 경력은 본인 확인 후 확정</div>""", f"""
        const nameText = vars.name || "단아쌤";
        if (vars.eyebrow) document.getElementById("authority-card-eyebrow").textContent = vars.eyebrow;
        if (vars.title) document.getElementById("authority-card-title").textContent = vars.title;
        if (vars.chips) vars.chips.split(",").forEach(function (c, i) {{ const el = document.getElementById("authority-card-c" + i); if (el) el.textContent = c.trim(); }});
        const nameEl = document.getElementById("authority-card-name");
        const letters = Array.from(nameText).map(function (ch) {{ const s = document.createElement("i"); s.textContent = ch; nameEl.appendChild(s); return s; }});
        const chips = {json.dumps([f"#authority-card-c{i}" for i in range(len(AUTH_CHIPS))])};
        gsap.set(["#authority-card-eyebrow", "#authority-card-title"].concat(chips, letters), {{ opacity: 0 }});
        gsap.set("#authority-card-uline", {{ scaleX: 0 }});
        // 푸티지 자리: 느린 켄번즈 푸시인 (실제 영상에서는 단아쌤 촬영본이 이 자리에 온다)
        tl.fromTo("#authority-card-plate", {{ scale: 1.0 }}, {{ scale: 1.14, duration: 7, ease: "sine.inOut" }}, 0);
        // 카드: 아래에서 마스크로 열림
        tl.fromTo("#authority-card-card", {{ clipPath: "inset(100% 0% 0% 0% round 28px)", y: 40 }}, {{ clipPath: "inset(0% 0% 0% 0% round 28px)", y: 0, duration: 0.7, ease: "expo.out" }}, 0.4);
        tl.fromTo("#authority-card-eyebrow", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }}, 0.8);
        letters.forEach(function (l, i) {{ tl.fromTo(l, {{ opacity: 0, y: 60, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, 1.0 + i * 0.08); }});
        const landed = 1.0 + letters.length * 0.08 + 0.2;
        // 이름이 자리 잡는 순간 카메라 펀치인
        tl.fromTo("#authority-card-cam", {{ scale: 1 }}, {{ scale: 1.045, duration: 0.35, ease: "power2.out" }}, landed);
        tl.to("#authority-card-uline", {{ scaleX: 1, duration: 0.55, ease: "expo.out" }}, landed);
        tl.fromTo("#authority-card-title", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.25, ease: "power4.out" }}, landed + 0.3);
        chips.forEach(function (c, i) {{ tl.fromTo(c, {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }}, landed + 0.6 + i * 0.12); }});
        // 퇴장: 카드가 아래로 접히며 사라지고 카메라는 원래대로
        tl.to("#authority-card-card", {{ clipPath: "inset(0% 0% 100% 0% round 28px)", duration: 0.4, ease: "power3.in" }}, 6.3);
        tl.to("#authority-card-cam", {{ scale: 1, duration: 0.5, ease: "power2.inOut" }}, 6.2);
""", [
    {"id": "name", "type": "string", "label": "이름", "default": "단아쌤"},
    {"id": "eyebrow", "type": "string", "label": "머리표", "default": "AI 교수"},
    {"id": "title", "type": "string", "label": "직함 한 줄", "default": "경희대 교수 · 기업 대표"},
    {"id": "chips", "type": "string", "label": "이력 칩 (쉼표로 3개)", "default": ", ".join(AUTH_CHIPS)},
]))

# ---------------------------------------------------------------- X 뉴스 카드 (최신 반응 3장 + 카메라 이동)
# 실제 영상에서는 원본 게시물 캡처를 shot 변수로 넣는다. 미리보기 문구는 "예시 게시물"이다.
POSTS = [
    {"who": "AI 크리에이터 A", "handle": "@example_a", "date": "2026.05.20", "tone": "혹평",
     "text": "출시 첫날 써봤는데 영상 생성은 기대 이하네요. 이럴 거면 다른 툴 쓰죠.", "mark": "기대 이하", "color": "#ff6b5b"},
    {"who": "영상 편집러 B", "handle": "@example_b", "date": "2026.05.22", "tone": "반전",
     "text": "근데 이거 편집에 쓰니까 완전 다르네요. 배경만 바꾸고 사람은 그대로 유지됩니다.", "mark": "편집에 쓰니까 완전 다르네요", "color": "#b4e61d"},
    {"who": "디자이너 C", "handle": "@example_c", "date": "2026.05.24", "tone": "재평가",
     "text": "전광판 광고만 교체해봤습니다. 건물이랑 거리는 그대로.", "mark": "광고만 교체", "color": "#22d3ee", "media": True},
]
CARD_X = [120, 690, 1260]
post_html = []
for i, p in enumerate(POSTS):
    t = p["text"].replace(p["mark"], f'<span class="mk" id="news-card-m{i}" style="--c:{p["color"]}">{p["mark"]}</span>')
    media = '<div class="media"><img src="assets/images/desk.jpg" alt="" /></div>' if p.get("media") else ""
    post_html.append(f"""        <div class="post" id="news-card-p{i}" style="left:{CARD_X[i]}px">
          <div class="who"><i style="background:{p['color']}">{p['who'][0]}</i><div><b>{p['who']}</b><span>{p['handle']} · {p['date']}</span></div><em style="color:{p['color']};box-shadow:inset 0 0 0 2px {p['color']}">{p['tone']}</em></div>
          <p>{t}</p>{media}
          <div class="src">X · {p['date']} · 예시 게시물</div>
        </div>""")
focus = [{"cx": CARD_X[i] + 270, "cy": 300 + (300 if POSTS[i].get("media") else 200)} for i in range(3)]
write("news-card", page("news-card", 9, """
      .head { position: absolute; left: 0; right: 0; top: 120px; text-align: center; font-size: 64px; font-weight: 800; letter-spacing: -0.02em; }
      .head b { color: #b4e61d; font-weight: 800; }
      .world { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
      .post { position: absolute; top: 300px; width: 540px; padding: 30px 32px 26px; border-radius: 24px; background: #0f1430; box-shadow: inset 0 0 0 2px rgba(255,255,255,.12), 0 24px 60px rgba(0,0,0,.5); }
      .who { display: flex; align-items: center; gap: 16px; }
      .who i { width: 56px; height: 56px; border-radius: 50%; display: grid; place-items: center; font-style: normal; font-size: 26px; font-weight: 800; color: #05060f; flex: none; }
      .who div { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
      .who b { font-size: 26px; }
      .who span { font-size: 20px; color: #a5a3c7; }
      .who em { margin-left: auto; font-style: normal; font-size: 22px; font-weight: 800; padding: 6px 12px; border-radius: 10px; }
      .post p { margin-top: 22px; font-size: 30px; line-height: 1.55; font-weight: 600; }
      .mk { --s: 0; background-image: linear-gradient(color-mix(in srgb, var(--c) 42%, transparent), color-mix(in srgb, var(--c) 42%, transparent)); background-repeat: no-repeat; background-position: 0 88%; background-size: calc(var(--s) * 100%) 44%; -webkit-box-decoration-break: clone; box-decoration-break: clone; border-radius: 4px; }
      .media { margin-top: 18px; border-radius: 16px; overflow: hidden; height: 220px; }
      .media img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .src { margin-top: 18px; font-size: 20px; color: #a5a3c7; }
      .arrow { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: visible; }
      .foot { position: absolute; left: 0; right: 0; bottom: 70px; text-align: center; font-size: 24px; color: #a5a3c7; }
""", """      <div class="head" id="news-card-head">출시 직후 <b>혹평</b>에서, 며칠 만에 <b>재평가</b>로</div>
      <div class="world" id="news-card-world">
""" + "\n".join(post_html) + """
        <svg class="arrow" viewBox="0 0 1920 1080"><path id="news-card-arrow" d="M 640 920 C 900 990, 1300 990, 1560 900" fill="none" stroke="#b4e61d" stroke-width="8" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1"/></svg>
      </div>
      <div class="foot" id="news-card-foot">예시 게시물 · 실제 영상에서는 원본 캡처와 링크를 씁니다</div>""", f"""
        const F = {json.dumps(focus)};
        const S = 1.55;
        function cam(i) {{ return {{ x: 960 - F[i].cx * S, y: 540 - F[i].cy * S, scale: S }}; }}
        const posts = ["#news-card-p0", "#news-card-p1", "#news-card-p2"];
        gsap.set(["#news-card-head", "#news-card-foot"], {{ opacity: 0 }});
        // 1) 세 장이 차례로 떨어진다 (전체 보기)
        posts.forEach(function (p, i) {{ tl.fromTo(p, {{ opacity: 0, y: 80, rotation: (i - 1) * 3 }}, {{ opacity: 1, y: 0, rotation: (i - 1) * 1.2, duration: 0.6, ease: "expo.out" }}, 0.2 + i * 0.15); }});
        // 2) 카메라: 카드 1로 푸시인
        tl.fromTo("#news-card-world", {{ x: 0, y: 0, scale: 1 }}, Object.assign(cam(0), {{ duration: 0.8, ease: "power3.inOut" }}), 1.1);
        tl.fromTo("#news-card-m0", {{ "--s": 0 }}, {{ "--s": 1, duration: 0.45, ease: "expo.out" }}, 2.0);
        // 3) 카드 2로 휩팬 (빠른 이동 + 가로 블러)
        tl.to("#news-card-world", Object.assign(cam(1), {{ duration: 0.45, ease: "power3.inOut" }}), 3.0);
        tl.fromTo("#news-card-world", {{ filter: "blur(0px)" }}, {{ filter: "blur(6px)", duration: 0.2, ease: "power2.in", yoyo: true, repeat: 1 }}, 3.02);
        tl.fromTo("#news-card-m1", {{ "--s": 0 }}, {{ "--s": 1, duration: 0.5, ease: "expo.out" }}, 3.6);
        // 4) 카드 3으로 패닝, 사진에 살짝 더 줌
        tl.to("#news-card-world", Object.assign(cam(2), {{ duration: 0.7, ease: "power2.inOut" }}), 4.8);
        tl.fromTo("#news-card-p2 .media img", {{ scale: 1 }}, {{ scale: 1.12, duration: 1.4, ease: "sine.out" }}, 5.1);
        tl.fromTo("#news-card-m2", {{ "--s": 0 }}, {{ "--s": 1, duration: 0.45, ease: "expo.out" }}, 5.4);
        // 5) 풀아웃: 전체 흐름 + 화살표 + 헤드라인
        tl.to("#news-card-world", {{ x: 0, y: 70, scale: 0.9, duration: 0.9, ease: "power3.inOut" }}, 6.4);
        tl.fromTo("#news-card-arrow", {{ strokeDashoffset: 1.1 }}, {{ strokeDashoffset: 0, duration: 0.7, ease: "power2.out" }}, 7.0);
        tl.fromTo("#news-card-head", {{ opacity: 0, y: -20, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }}, 7.1);
        tl.fromTo("#news-card-foot", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 7.4);
"""))
