# 단아쌤TV 영상 자동 제작 하네스 (danasam-video-harness) v0.1

주제 하나를 넣으면 **리서치 → 기획 → 대본 → (단아쌤 촬영) → 컷 편집 → 모션그래픽 → 합성 → 검수 → 패키징**까지
에이전트가 진행하고, 사람은 **정해진 3개의 관문**에서만 개입하는 제작 시스템의 설계서다.

| 뼈대 | 출처 |
|---|---|
| 기획·집필·PD 검수 계약, 상태값, 반려 기준 | 노션 「스킬｜세진 PD 영상 제작 하네스 v1.2」 |
| 파이프라인 7단계, 피드백→규칙화, Human-on-the-loop, 크레딧 상한 | 커리어해커 알렉스 「영상 하나에 30시간 작업하던 일을 전부 자동화한 방법」 |
| 모션 문법 (고정 무대·스포트라이트·드로우온·수식 카드·로드맵·라운드 카드) | 코드깎는노인 「최신 AI 모델들의 미적 감각 비교」 |
| 색·폰트·컴포넌트 | 단아쌤 디자인 시스템 (`danasam-tech-explainer`, `danasam-motion-inserts`) |
| 촬영 형식 | 단아쌤 상반신 촬영 + 프롬프터 낭독, 얼굴은 우측 하단 PiP |

## 파일 지도

| 파일 | 내용 |
|---|---|
| [HARNESS.md](HARNESS.md) | **본체.** 파이프라인, 상태 머신, 관문, 역할, 인계 계약, 실패 처리 |
| [design/layout.md](design/layout.md) | 화면 레이아웃 5종과 얼굴 PiP 규격, 안전 영역, 자막 위치 |
| [design/motion-grammar.md](design/motion-grammar.md) | 모션 문법 사전, 컴포넌트 매핑, 빈도 규칙 |
| [design/tokens.json](design/tokens.json) | 색·폰트·PiP 좌표 등 기계가 읽는 디자인 토큰 |
| [shoot/shooting-guide.md](shoot/shooting-guide.md) | 상반신 촬영·프롬프터·재촬영 신호 규칙 |
| [schemas/beat.schema.json](schemas/beat.schema.json) | 대본 비트(제작의 최소 단위) 스키마 |
| [schemas/run-state.schema.json](schemas/run-state.schema.json) | 실행 상태 기록 스키마 |
| [prompts/agents.md](prompts/agents.md) | 역할별 인계 프롬프트 |
| [rules/feedback-rules.md](rules/feedback-rules.md) | 피드백을 규칙으로 바꿔 쌓는 장부 |
| [docs/references.md](docs/references.md) | 레퍼런스 영상 2편 분석 요약 |
| [runs/_template/](runs/_template/) | 새 영상 1편을 시작할 때 복사하는 폴더 |

## 한 편 시작하기

```
runs/_template 을 runs/YYYYMMDD-주제 로 복사하고,
"danasam-video-harness 로 '주제' 영상 진행해줘. 길이 10분, 광고 아님." 이라고 요청한다.
```

에이전트는 `state.json`의 `state`와 `next_action`을 읽어 마지막 단계부터 이어서 진행한다.
