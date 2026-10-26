"""HyperFrames 레지스트리 템플릿을 단아쌤 색·폰트·한국어 문구로 바꿔 템플릿 폴더를 만든다.

사용: python3 _tools/danaize.py <templates 폴더>
원본은 _registry/ 에 있고, 결과는 <slug>/index.html (+ assets -> ../_assets) 로 나온다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
REG = ROOT / "_registry"

# 단아쌤 Tech Dark 토큰. 레지스트리 컴포넌트는 var(--bg), var(--brand) … 를 읽는다.
TOKENS = """
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard.woff2") format("woff2"); font-weight: 100 900; font-display: block; }
      @font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"); }
      @font-face { font-family: "NanumPen"; src: url("assets/fonts/NanumPenScript-korean.woff2") format("woff2"); font-display: block; }
      :root {
        --bg: #0b1026; --fg: #f5f3ff; --surface: #131838; --border: #3b3a6b; --muted: #a5a3c7;
        --brand: #b4e61d; --accent: #22d3ee; --accent-2: #7c3aed;
        --font-display: "Pretendard", sans-serif; --font-body: "Pretendard", sans-serif; --font-mono: "Pretendard", sans-serif;
        --hw-ink: #f5f3ff; --hw-accent: #b4e61d; --hw-accent-warm: #b4e61d;
        --hw-font-print: "NanumPen", "Caveat", cursive; --hw-font-script: "NanumPen", "Caveat", cursive;
      }
      html, body { background: linear-gradient(#0b1026, #05060f); }
"""

# 공통 색 치환: 레지스트리 기본 배경·강조색 → 단아쌤
COMMON_HEX = {
    "#35604a": "#131838", "#14231c": "#05060f",  # 초록 칠판 배경
    "#274060": "#131838", "#123 ": "#05060f ", "#123)": "#05060f)",
    "#17161a": "#0b1026", "#1b1a1e": "#0b1026",
    "#ffb020": "#b4e61d", "#f4f2ec": "#f5f3ff",
}

TEMPLATES = {
    "typed-prompt": {
        "src": "components/typed-prompt.html",
        "title": "프롬프트 입력", "group": "chat",
        "text": {'"Generate a product launch video"': '"이 대본으로 10분 영상 기획해줘"'},
    },
    "caption-emoji-pop": {
        "src": "components/caption-emoji-pop.html",
        "title": "이모지 자막 팝", "group": "emoji",
        "regex": [
            (r"var TRANSCRIPT = \[.*?\];", """var TRANSCRIPT = [
        { text: "오늘은", start: 0.0, end: 0.4 },
        { text: "모션그래픽", start: 0.4, end: 1.0 },
        { text: "완전정복", start: 1.0, end: 1.6 },
        { text: "1편이에요.", start: 1.6, end: 2.2 },
        { text: "자막에", start: 2.4, end: 2.8 },
        { text: "이모지를", start: 2.8, end: 3.3 },
        { text: "붙이면", start: 3.3, end: 3.8 },
        { text: "시선이", start: 3.9, end: 4.4 },
        { text: "확", start: 4.4, end: 4.7 },
        { text: "모여요.", start: 4.7, end: 5.3 },
        { text: "핵심", start: 5.5, end: 5.9 },
        { text: "단어에만", start: 5.9, end: 6.4 },
        { text: "붙이세요.", start: 6.4, end: 7.2 },
      ];"""),
            (r"var WORD_EMOJI = \{.*?\};", """var WORD_EMOJI = {
        모션그래픽: "🎬",
        이모지를: "😀",
        시선이: "👀",
        핵심: "🎯",
      };"""),
            (r'"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif', '"Noto Color Emoji", sans-serif'),
            (r'var KEYWORDS = new Set\(\[.*?\]\);', 'var KEYWORDS = new Set(["모션그래픽", "핵심", "시선이"]);'),
        ],
        "text": {'"Gabarito", Arial, sans-serif': '"Pretendard", sans-serif', '"900 " + fontSize + "px Gabarito"': '"900 " + fontSize + "px Pretendard"', '"Gabarito",': '"Pretendard",'},
    },
    "spring-pop": {
        "src": "components/spring-pop.html",
        "title": "배지 스프링 팝", "group": "emoji",
        "text": {'"default": "New"': '"default": "🎉 오늘의 꿀팁"', '>New<': '>🎉 오늘의 꿀팁<'},
    },
    "hw-frame": {
        "src": "hw-frame.html",
        "title": "손그림 사진 프레임", "group": "image",
        "text": {'src: null, // IMAGE path': 'src: "assets/images/desk.jpg", // IMAGE path', 'caption: "our trip!"': 'caption: "오늘의 작업 공간!"'},
    },
    "before-after-wipe": {
        "src": "components/before-after-wipe.html",
        "title": "전후 비교 와이프", "group": "image",
        "regex": [
            (r'(<div class="baw-slot" data-slot="before">).*?(</div>\s*<div class="baw-chip baw-chip-a">)',
             r'\1<img src="assets/images/desk-flat.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">\n              \2'),
            (r'(<div class="baw-slot" data-slot="after">).*?(</div>\s*<div class="baw-chip baw-chip-b">)',
             r'\1<img src="assets/images/desk.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">\n              \2'),
        ],
        "text": {'"default": "Before"': '"default": "보정 전"', '"default": "After"': '"default": "보정 후"'},
    },
    "hw-callout-circle": {
        "src": "components/hw-callout-circle.html",
        "title": "손그림 동그라미", "group": "draw",
        "text": {">subject<": ">핵심 포인트<", '"look here!"': '"여기!"', '"Inter", ui-sans-serif, sans-serif': '"Pretendard", sans-serif'},
    },
    "hw-arrow": {
        "src": "components/hw-arrow.html",
        "title": "손그림 화살표", "group": "draw",
        "text": {">point at things<": ">여기를 보세요<", '"point at things"': '"여기를 보세요"'},
    },
    "hw-underline": {
        "src": "components/hw-underline.html",
        "title": "손그림 밑줄·취소선", "group": "draw",
        "text": {">underline the point<": ">핵심에 밑줄<", ">cross this out<": ">이건 지우고<", ">bracket the aside<": ">곁가지는 괄호로<"},
    },
    "hw-text-cloud": {
        "src": "hw-text-cloud.html",
        "title": "손그림 말풍선", "group": "draw",
        "text": {'"what are you looking at?"': '"이거 어떻게 만들었어요?"', "#26241f": "#0b1026"},
    },
    "marker-highlight": {
        "src": "components/marker-highlight.html",
        "title": "형광펜 강조", "group": "draw",
        "text": {'"Ship it with confidence"': '"강조는 딱 하나만"', '"default": "confidence"': '"default": "하나만"', '"confidence"': '"하나만"'},
    },
    "whiteboard-ink": {
        "src": "components/whiteboard-ink.html",
        "title": "화이트보드 스케치", "group": "draw",
        "text": {'"Draw the idea"': '"아이디어를 그려요"'},
    },
    "count-up": {
        "src": "components/count-up.html",
        "title": "숫자 카운트업", "group": "data",
        "text": {'"id": "end", "type": "number"': '"id": "end", "type": "number"'},
    },
    "marker-checklist-card": {
        "src": "components/marker-checklist-card.html",
        "title": "손글씨 체크리스트 카드", "group": "data",
        "text": {
            '"default": "THE POWER"': '"default": "오늘 할 일"', '>THE POWER<': '>오늘 할 일<',
            '"default": "OF"': '"default": "딱"', '>OF<': '>딱<',
            '"default": "ONE"': '"default": "세"', '>ONE<': '>세<',
            '"default": "FILE"': '"default": "가지"', '>FILE<': '>가지<',
            '"default": "WRITE"': '"default": "대본"', '>WRITE<': '>대본<',
            '"default": "HTML"': '"default": "쓰기"', '>HTML<': '>쓰기<',
            '"default": "RENDER"': '"default": "촬영"', '>RENDER<': '>촬영<',
            '"default": "IN 4K"': '"default": "하기"', '>IN 4K<': '>하기<',
            '"default": "SHIP"': '"default": "업로드"', '>SHIP<': '>업로드<',
            '"default": "TODAY"': '"default": "끝!"', '>TODAY<': '>끝!<',
            '"Permanent Marker", cursive': '"NanumPen", "Permanent Marker", cursive',
            '"Courier Prime", monospace': '"Pretendard", "Courier Prime", monospace',
            "#602640": "#4a33a6",
        },
    },
    "lt-kicker-name": {
        "src": "lt-kicker-name.html",
        "title": "키커 로워서드", "group": "data",
        "text": {">Episode 47<": ">단아쌤TV<", ">Maya Chen<": ">모션그래픽 완전정복<", "#46e5b7": "#b4e61d",
                 '"Archivo Black", sans-serif': '"Pretendard", sans-serif', '"Space Mono", monospace': '"Pretendard", sans-serif'},
    },
}


def danaize(slug, cfg):
    s = (REG / cfg["src"]).read_text(encoding="utf-8")
    for pat, rep in cfg.get("regex", []):
        s, n = re.subn(pat, rep, s, count=1, flags=re.S)
        if n != 1:
            print(f"  ! {slug}: regex did not match: {pat[:40]}")
    for a, b in cfg.get("text", {}).items():
        if a not in s:
            print(f"  ! {slug}: text not found: {a}")
            continue
        s = s.replace(a, b)
    for a, b in COMMON_HEX.items():
        s = s.replace(a, b)
    s = s.replace('lang="en"', 'lang="ko"', 1)
    # 앞머리 레지스트리 주석은 doctype 뒤로 (lint: html wrapper)
    m = re.match(r"\s*(<!--.*?-->)\s*(<!doctype html>)", s, flags=re.S | re.I)
    if m:
        s = m.group(2) + "\n" + m.group(1) + s[m.end():]
    # 엔트리 루트에는 화면 크기가 있어야 한다
    m = re.search(r"<div\b[^>]*data-composition-id=[^>]*>", s, flags=re.S)
    if m and "data-width" not in m.group(0):
        tag = m.group(0)[:-1] + ' data-width="1920" data-height="1080">'
        s = s[:m.start()] + tag + s[m.end():]
    if "gsap" in s and "gsap.min.js" not in s:
        s = s.replace("<head>", '<head>\n    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>', 1)
    # 토큰은 원본 스타일 뒤에 넣어 같은 선택자일 때 단아쌤 값이 이기게 한다
    s = s.replace("</style>", TOKENS + "    </style>", 1)
    out = ROOT / slug
    out.mkdir(exist_ok=True)
    link = out / "assets"
    if not link.exists():
        link.symlink_to("../_assets")
    (out / "index.html").write_text(s, encoding="utf-8")
    print("ok", slug)


for slug, cfg in TEMPLATES.items():
    danaize(slug, cfg)
