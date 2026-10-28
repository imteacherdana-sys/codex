"""캠페인 브리프 기준 업로드 키트를 만든다 (plan.json의 장면 시작 시간으로 챕터를 채움).

출력: out/upload-kit.md
사용: python3 tools/upload_kit.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTM = "https://higgsfield.ai/s/video-model-showdown-kling-4-danasam-kewFHC"

# 챕터: 장면 이름 → 질문형 제목 (브리프: 3개 이상, 그 구간이 답하는 질문 + 제품명)
CHAPTERS = [
    ("hook-grid", "8개 영상 AI 중 어떤 장풍이 진짜 같을까?"),
    ("rules", "같은 프롬프트로 어떻게 공정하게 비교했을까?"),
    ("screen", "Higgsfield에서 8개 모델은 어떻게 돌렸을까?"),
    ("r1-prompt", "장풍 이펙트는 어떤 AI가 가장 잘 그릴까?"),
    ("r2-prompt", "경공처럼 빠른 동작, Kling 4.0과 Seedance 2.5 중 누가 나을까?"),
    ("r3-prompt", "비무 장면, 목검과 낙엽까지 자연스러운 AI는?"),
    ("r4-intro", "같은 인물을 끝까지 유지하는 AI는? (Reference 시험)"),
    ("r5-prompt", "영상 AI는 한글 간판 글자를 쓸 수 있을까?"),
    ("board", "8개 모델 최종 성적표, 1등은 누구일까?"),
    ("credits", "같은 시험에 크레딧은 얼마나 들었을까? Kling 4.0 vs Seedance 2.5"),
    ("film-intro", "Kling 4.0 하나로 무협 단편을 만들 수 있을까?"),
    ("recommend", "결국 어떤 영상 AI를 써야 할까?"),
]

TITLES = [
    ("추천 · 대결형", "Kling 4.0 vs Seedance 2.5, 그리고 6개 모델. 똑같은 무협 장면으로 붙였습니다", "Kling 4.0 vs Seedance 2.5 and Six Rivals on the Exact Same Shot"),
    ("전체 공개형", "영상 AI 8개에 같은 프롬프트를 넣었습니다. 결과 전부 보여드립니다", "I Gave 8 AI Video Models the Same Prompt. Here's Every Result"),
    ("물리 법칙형", "같은 프롬프트, 영상 AI 8개. 물리를 지킨 건 몇 개뿐이었습니다", "Same Prompt, Eight Models. Only a Few Got the Physics Right"),
    ("선택 가이드형", "영상 AI 고르는 법: 8개 모델을 한 프롬프트로 시험했습니다", "How to Choose an AI Video Model: 8 Tested on One Prompt"),
]

INTRO = (
    "장풍, 경공, 비무, 그리고 한글 현판까지. 영상 AI 8개에 똑같은 프롬프트를 넣고 무협 시험을 치렀습니다!\n"
    f"👉 직접 같은 프롬프트로 돌려보기: {UTM}\n"
    "8개 모델 모두 Higgsfield AI 한 곳에서, 같은 프롬프트와 같은 설정으로 돌렸습니다. "
    "여러분도 같은 프롬프트로 돌려보고, 1등을 직접 골라보십시오!"
)

TAGS = [
    "AI video model comparison", "Seedance 2.5", "Kling 4.0", "best AI video generator", "same prompt AI test",
    "Higgsfield AI", "text to video AI", "AI video models", "Seedance 2.0", "MiniMax H3", "Wan 3.0",
    "Grok Imagine 1.5", "FLUX 3", "Gemini Omni 1.1", "AI 영상 비교", "영상 AI 추천", "AI 영상 생성",
    "무협 AI 영상", "Kling 4.0 리뷰", "Seedance 2.5 리뷰", "단아쌤", "AI 교수",
]



def tc(t):
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    plan = json.loads((ROOT / "plan.json").read_text())
    start = {s["name"]: s["start"] for s in plan["scenes"]}
    chapters = [(0.0 if name == "hook-grid" else start[name], q) for name, q in CHAPTERS if name in start]
    chapters.sort()
    prompts = json.loads((ROOT / "prompts.json").read_text())
    ch_txt = "\n".join(f"{tc(t)} {q}" for t, q in chapters)

    desc = f"""{INTRO}

━━━━━━━━━━━━━━━━━━
🏯 오늘의 시험 (same prompt AI test)
오늘 비교한 AI video models 8개입니다. 같은 프롬프트, 8초, 16:9, 다시 뽑기 없이 첫 결과만 썼습니다.
Kling 4.0 · Seedance 2.5 · Seedance 2.0 · MiniMax H3 · Wan 3.0 · Grok Imagine 1.5 · FLUX 3 · Gemini Omni 1.1
이번 AI video model comparison에서는 text to video AI로 장풍·경공·비무·현판 네 장면을 만들고,
같은 인물 사진을 넣는 Reference 시험까지 더해 총 다섯 번 겨뤘습니다.
best AI video generator는 결국 무엇을 만드느냐에 따라 달라집니다. 결과를 보고 직접 판단해 보십시오!

🔗 모델 바로가기
• Seedance 2.5: https://higgsfield.ai/seedance/2.5
• Kling 4.0: https://higgsfield.ai/kling/4.0

⏱ 챕터
{ch_txt}

📝 시험별 프롬프트 (8개 모델 공통, 수정 없이 그대로)
[시험 1 · 장풍] {prompts['r1']}
[시험 2 · 경공] {prompts['r2']}
[시험 3 · 비무] {prompts['r3']}
[시험 4 · Reference] {prompts['r4']}
[시험 5 · 현판] {prompts['r5']}

※ 크레딧은 2026년 10월 Higgsfield 기준입니다. Kling 4.0은 출시 할인가입니다.
※ 등장인물과 장소는 모두 AI로 만든 가상 인물·가상 장소입니다.

#AIvideomodels #Kling4 #Seedance25 #HiggsfieldAI #AI영상비교"""

    pinned = f"""{INTRO}

같은 프롬프트로 직접 돌려보고, 여러분의 1등을 댓글로 알려주십시오! 🏆"""

    title_rows = "\n".join(f"| {k} | {ko} | {en} |" for k, ko, en in TITLES)
    kit = f"""# 업로드 키트 · Video Model Showdown (Kling 4)

유료 광고 표시는 업로드할 때 YouTube의 **"유료 프로모션 포함"** 체크로 합니다 (영상 안에는 넣지 않음).

## 1. 제목 (브리프: 실험이나 결과를 앞에, 플랫폼 이름으로 시작하지 않기)

| 유형 | 한국어 제목 | 영어 제목 (자동 더빙용 번역 제목) |
|---|---|---|
{title_rows}

추천: 1번 (검색어 Kling 4.0 · Seedance 2.5가 앞에 옴). 영상 내용에 없는 약속은 하지 않습니다.

## 2. 썸네일 (브리프: 8개 결과 그리드 또는 강한 두 모델의 분할, **제목 글자는 넣지 않기**)

- A안 `thumbnail-grid8.jpg`: 장풍 시험 8개 결과 4×2 그리드, 번호만 표시
- B안 `thumbnail-split.jpg`: Kling 4.0 vs Seedance 2.5 반반 분할, 모델 이름 작은 라벨만
- 추천: A안 (한 프롬프트 · 8개 결과라는 실험이 한눈에 보임)

## 3. 설명란 (UTM 링크는 첫 두 줄 안에, 더보기 없이 보이게)

```text
{desc}
```

## 4. 고정 댓글 (브리프: 설명란과 같은 소개 문구 + 링크 + 짧은 행동 유도)

```text
{pinned}
```

## 5. 태그

```text
{', '.join(TAGS)}
```

## 6. 제출 전 체크리스트 (브리프 요구사항)

- [ ] 6분 이상 전용 영상 (완성본 {plan['total'] / 60:.1f}분)
- [ ] Higgsfield 웹사이트 작업 화면 녹화를 영상의 화면 녹화 자리에 넣기 (모델 선택기 전환, 프롬프트 입력·생성)
- [ ] 영상에서 "8개 모델 모두 Higgsfield에서, 같은 프롬프트와 같은 설정으로 돌렸다"고 말하기 (대본 포함)
- [ ] 필수 모델 8개 모두 등장: Kling 4.0 · Seedance 2.5 · Seedance 2.0 · MiniMax H3 · Wan 3.0 · Grok Imagine 1.5 · FLUX 3 · Gemini Omni 1.1
- [ ] 같은 길이·비율을 못 맞춘 모델은 영상에서 말하기 (MiniMax H3는 2K 고정, 대본 포함)
- [ ] 재시도한 생성은 영상에서 말하기 (Gemini Omni 1.1 Reference 시험 1회 재시도, 대본 포함)
- [ ] 공식 Media Kit 에셋 사용 (크리에이터 대시보드에서 받아 넣기)
- [ ] 영어 자동 더빙(English voiceover) 켜기
- [ ] 설명란 첫 줄 근처에 UTM 링크, 키워드 8개 포함, 질문형 챕터 3개 이상
- [ ] 고정 댓글에 설명란 소개 문구 + 링크
- [ ] YouTube "유료 프로모션 포함" 체크
- [ ] 브리프 내용 자체는 영상·설명란에 공개하지 않기
"""
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "upload-kit.md").write_text(kit)
    print("written out/upload-kit.md")


if __name__ == "__main__":
    main()
