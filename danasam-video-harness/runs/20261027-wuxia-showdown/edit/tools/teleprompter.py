"""plan.json의 대본으로 텔레프롬프터 페이지를 만든다.

출력: upload/teleprompter.html (Artifact로 올려 휴대폰·태블릿에서 띄워 읽는다)
사용: python3 tools/teleprompter.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MODEL_KO = {"kling4_0": "Kling 4.0", "seedance_2_5": "Seedance 2.5", "seedance_2_0": "Seedance 2.0", "minimax_h3": "MiniMax H3",
            "wan3_0": "Wan 3.0", "grok_video_v15": "Grok Imagine 1.5", "flux_3_video": "FLUX 3", "gemini_omni_flash_1_1": "Gemini Omni 1.1"}
ROUND = {"r1": "시험 1 · 장풍", "r2": "시험 2 · 경공", "r3": "시험 3 · 비무", "r4": "시험 4 · Reference", "r5": "시험 5 · 현판"}
LABEL = {"hook-grid": "첫 화면 · 장풍 8개", "hook-question": "질문", "authority": "자기소개", "stakes": "시험 소개", "rules": "공정 조건",
         "screen": "Higgsfield 화면 녹화", "specs": "모델 소개", "prompt": "프롬프트", "grid": "8개 한눈에", "verdict": "판정",
         "r4-intro": "Reference 소개", "r4-faces": "얼굴 비교", "r5-twist": "함정의 함정", "board": "성적표", "credits": "크레딧",
         "kling-why": "그래서 Kling", "edit-demo": "Kling 편집 기능", "edit-fix": "구체적으로 쓰면", "film-intro": "단편 소개",
         "film": "단편 「단아검법」", "recommend": "정리 · 추천", "cta": "설명란 링크", "answer": "첫 문제 정답", "outro": "마무리"}


def part_of(name):
    if name.startswith(("hook", "authority", "stakes")):
        return "오프닝"
    if name in ("rules", "screen", "specs"):
        return "조건 · 화면"
    if name[:2] in ROUND:
        return ROUND[name[:2]]
    if name in ("board", "credits", "kling-why", "edit-demo", "edit-fix"):
        return "결과 · 가격"
    if name.startswith("film"):
        return "Kling 단편"
    return "마무리"


def label_of(name):
    if name in LABEL:
        return LABEL[name]
    head = name[:2]
    if head in ROUND:
        rest = name[3:]
        if rest in LABEL:
            return LABEL[rest]
        num, model = rest.split("-", 1)
        return f"{num}번 · {MODEL_KO.get(model, model)}"
    return name


def main():
    plan = json.loads((ROOT / "plan.json").read_text())
    scenes = []
    for s in plan["scenes"]:
        scenes.append({"id": s["name"], "part": part_of(s["name"]), "label": label_of(s["name"]), "start": s["start"],
                       "lines": [c["text"] for c in s["caps"]], "kind": s["kind"]})
    tpl = (ROOT / "tools" / "teleprompter.tpl.html").read_text()
    out = tpl.replace("/*__DATA__*/[]", json.dumps(scenes, ensure_ascii=False)).replace("__TOTAL__", f"{plan['total'] / 60:.1f}")
    (ROOT / "upload" / "teleprompter.html").write_text(out)
    print("written upload/teleprompter.html", len(scenes), "scenes")


if __name__ == "__main__":
    main()
