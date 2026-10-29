"""본편 편집표(edit/tools/voice_edl.py)의 목소리 조각으로 블럭 쇼츠 3개의 설명표를 만든다.

목소리는 본편과 같은 편집점(말 절은 곳·중복 제거, 무음에 맞춘 경계)을 그대로 쓴다.
사용: python3 gen_specs.py  →  short1.json, short2.json, short3.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDIT = HERE.parent / "edit"
sys.path.insert(0, str(EDIT / "tools"))
import final_edit as F  # noqa: E402

CLIPS = EDIT / "assets/clips"
COL = {"Kling 4.0": "#b4e61d", "Seedance 2.5": "#ff8787", "Seedance 2.0": "#ffc9a9", "MiniMax H3": "#63e6be", "Wan 3.0": "#ffd43b",
       "Grok Imagine 1.5": "#d0bfff", "FLUX 3": "#ffffff", "Gemini Omni 1.1": "#74c0fc"}
R1 = ["seedance_2_0", "minimax_h3", "flux_3_video", "gemini_omni_flash_1_1", "seedance_2_5", "grok_video_v15", "wan3_0", "kling4_0"]
R5 = ["seedance_2_0", "grok_video_v15", "gemini_omni_flash_1_1", "seedance_2_5", "wan3_0", "flux_3_video", "kling4_0", "minimax_h3"]


def V(scene, *ks):
    """본편 장면의 k번째 목소리 조각 (원본 녹화 기준 [시작, 끝])."""
    cuts = F.source_cuts(scene)
    return [[round(cuts[k][0], 3), round(cuts[k][1], 3)] for k in ks]


def C(scene, *ks):
    ps = F.pieces_of(scene)
    return " ".join(ps[k][2] for k in ks)


def beat(scene, ks, visual, **kw):
    return {"voice": V(scene, *ks), "caption": C(scene, *ks), "visual": visual, **kw}


def clip(name, label, badge=None, **kw):
    v = {"type": "clip", "src": str(CLIPS / f"{name}.mp4"), "label": label, "color": COL.get(label, "#63e6be"), **kw}
    if badge:
        v["badge"] = badge
    return v


BASE = {"face": {"src": str(EDIT / "assets/face/face_all.mp4"), "track": str(EDIT / "assets/face/track.json")},
        "music": str(EDIT / "assets/audio/bgm_wuxia.wav"), "music_gain": 0.14}

short1 = {**BASE, "id": "short1-jangpung", "highlight_words": ["8개", "FLUX", "Kling", "18", "56", "민망"],
          "beats": [
              beat("hook-grid", [0], {"type": "title", "rows": ["장풍", "대결"], "y": 330}),
              beat("hook-grid", [1, 2], {"type": "grid", "clips": [{"src": str(CLIPS / f"r1_{m}.mp4"), "from": 2.5} for m in R1]}),
              beat("r1-3-flux_3_video", [0, 1], clip("r1_flux_3_video", "FLUX 3", "48 크레딧", **{"from": 2.0, "stamp": "장풍 1등!", "stamp_at": 3.2})),
              beat("r1-8-kling4_0", [0, 1], clip("r1_kling4_0", "Kling 4.0", "18 크레딧", **{"from": 1.5, "stamp": "파동 어디?", "stamp_at": 3.0})),
              beat("r1-5-seedance_2_5", [1], clip("r1_seedance_2_5", "Seedance 2.5", "56 크레딧", **{"from": 2.5})),
              beat("r1-grid", [2], {"type": "bars", "title": "8초 한 편 크레딧", "unit": 6, "items": [["Kling 4.0", 18, True], ["Seedance 2.5", 56]]}),
              beat("cta", [3], {"type": "sticker", "text": "전체 결과는 본편에서!", "y": 380}),
          ]}

short2 = {**BASE, "id": "short2-signboard", "highlight_words": ["단아객잔", "5개", "단야", "탄", "눈으로"],
          "beats": [
              beat("r5-prompt", [0], {"type": "title", "rows": ["단아", "객잔"], "y": 330}),
              beat("r5-prompt", [2], {"type": "sticker", "text": "AI는 글자에 약하다?", "y": 400}),
              beat("r5-grid", [0, 1], {"type": "grid", "clips": [{"src": str(CLIPS / f"r5_{m}.mp4"), "from": 5.2} for m in R5]}),
              beat("r5-1-seedance_2_0", [0], clip("r5_seedance_2_0", "Seedance 2.0", **{"from": 5.0, "stamp": "단야?", "stamp_at": 0.8})),
              beat("r5-7-kling4_0", [0], clip("r5_kling4_0", "Kling 4.0", "18 크레딧", **{"from": 4.8, "stamp": "제일 예쁨!", "stamp_at": 2.4})),
              beat("r5-twist", [0, 1], {"type": "clip", "src": str(EDIT / "assets/images/r5_signboard.png"), "label": "이미지 AI", "color": "#d0bfff",
                                          "stamp": "단 → 탄", "stamp_at": 4.2}),
              beat("r5-twist", [3], {"type": "sticker", "text": "글자는 꼭 눈으로 확인!", "y": 380}),
          ]}

short3 = {**BASE, "id": "short3-value", "highlight_words": ["Kling", "3번", "1등", "30", "22", "18", "작품"],
          "beats": [
              beat("board", [1], {"type": "title", "rows": ["가성비", "1등"], "y": 330}),
              beat("credits", [2], {"type": "sticker", "text": "최저가 MiniMax = 1등 0번", "size": 74, "y": 400}),
              beat("credits", [3], {"type": "bars", "title": "1등 한 번에 든 크레딧", "unit": 20,
                                    "items": [["Kling 4.0", 30, True], ["FLUX 3", 120], ["Seedance 2.0", 180]]}),
              beat("credits", [4], {"type": "sticker", "text": "지금 22 → 18 할인 중", "y": 400}),
              beat("film-intro", [0, 1], clip("film_s2b", "Kling 4.0 단편", **{"from": 0.0})),
              {"voice": [], "caption": "", "min": 5.0, "visual": {"type": "full", "src": str(CLIPS / "film_s4b.mp4"), "from": 1.5, "audio": True}},
              {"voice": [], "caption": "", "min": 3.2, "visual": {"type": "full", "src": str(CLIPS / "r5_kling4_0.mp4"), "from": 4.6, "audio": True}},
              beat("recommend", [0], {"type": "sticker", "text": "8개 전체 비교는 본편에서!", "size": 76, "y": 380}),
          ]}

for sp in (short1, short2, short3):
    (HERE / f"{sp['id']}.json").write_text(json.dumps(sp, ensure_ascii=False, indent=1))
    print("written", sp["id"], len(sp["beats"]), "beats")
