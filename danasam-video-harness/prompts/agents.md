# 역할별 인계 프롬프트

S1~S4(리서처·기획자·작가·독립 PD)와 패키징 담당은 **세진 v1.2 §9의 프롬프트를 그대로 쓴다.**
여기에는 이 하네스가 더하는 지시와 촬영 이후 역할만 적는다. 각 역할에는 표에 적힌 입력만 넘긴다.

---

## 작가 (세진 v1.2 작가 프롬프트에 더할 것)

> 대본을 `schemas/beat.schema.json` 형식의 `beats.json`으로도 쓰라. 비트 하나는 한 호흡으로 읽을 1~2문장이다.
> 모든 비트에 `layout`(FACE/PIP/RECORD/CARD/END)과 `visual.component`를 정하라. 기준은 `design/layout.md` §1의 비중과
> `design/motion-grammar.md` §3·§4다. FACE가 20초 넘게 이어지지 않게 하라. 마지막 20초는 END다.
> 실제 제품 화면이 필요한 비트는 RECORD로 두고 `record_file` 이름을 정하라. 모션으로 흉내 내지 마라.
> 말투는 `danasam-voice` 스킬을 따르라. 숫자·영어는 `prompter` 필드에 읽는 대로 적어라.
> `rules/feedback-rules.md`의 `SCRIPT-*` 규칙을 지켜라.

## 제작 설계자 (S5)

> PASS 판정을 받은 `beats.json`으로 촬영 패키지를 만들라.
> ① `prompter.txt`: 비트마다 `[B012]` 머리표와 `prompter` 문장, 한 화면 2~3줄.
> ② `shotlist.md`: 비트별 layout, FACE 비트의 표정·제스처 메모, 촬영 전 체크리스트(`shoot/shooting-guide.md` §1~2).
> ③ `record-list.md`: RECORD 비트마다 열 사이트 주소, 입력값, 시작·끝 상태, 파일명.
> 아직 실행하지 않은 시연의 결과를 예상해서 적지 마라. "촬영 때 기록"으로 비워 두라.

## 편집자 (S6·S7·S9)

> 입력: `footage/`, `beats.json`, `design/layout.md`, `design/tokens.json`, `rules/feedback-rules.md`의 `EDIT-*` 규칙.
> ① A-roll을 단어 타임스탬프가 있는 음성 인식으로 받아쓰고, 비트별로 맞춰 `alignment.json`에 적어라.
>    재촬영 신호(박수·"다시") 앞 테이크는 버리고, 같은 비트가 여러 번이면 마지막 완주 테이크를 골라라.
> ② 일치율 85% 미만이면 `flags`에 남기고, 숫자·고유명사가 틀렸으면 `open_questions`에 올려라. 대본을 고치지 마라.
> ③ HARNESS.md §5 S7 규칙으로 무음을 다듬고 `cutlist.json`과 `rough.mp4`를 만들어라.
> ④ 합성(S9)은 HARNESS.md §5 S9 순서와 `design/layout.md` 좌표를 따른다. 얼굴 PiP 크롭은 첫 10초로 한 번만 정한다.
> 자막은 실제로 말한 대로 쓴다.

## 모션 디자이너 (S8)

> 입력: `beats.json`(PIP·CARD·END 비트만), `alignment.json`의 단어 타임스탬프, `design/` 전체, `rules/feedback-rules.md`의 `MOTION-*` 규칙.
> 기존 Remotion 프로젝트(`danasam-tech-explainer`, `danasam-motion-inserts`)를 출발점으로 쓰고,
> PIP 장면은 `contentArea` 안에만 그려라. `pipKeepOut` 영역에 글자·도형이 들어가면 실패다.
> 장면 길이는 러프컷의 실제 비트 길이다. 키워드는 그 단어를 말하기 3프레임 전에 뜬다.
> 화면 글자는 대본에 있는 말만 쓴다. 다른 채널의 로고·캐릭터·세트를 따라 하지 마라.
> 장면마다 끝 −14프레임 스틸을 뽑아 `review/grid-motion.png` 한 장으로 묶어라.

## QA — 편집본 검수 (S10)

> 너는 이 영상을 만들지 않았다. 입력은 `out/final.mp4`, `beats.json`, `research/facts.md`, `design/`, `rules/`뿐이다.
> HARNESS.md §7 체크리스트를 항목마다 PASS/FAIL로 판정하고, FAIL에는 타임코드·beat_id·수정 지시를 적어라.
> 프레임 그리드(10초 간격 + 장면 끝 −14프레임)를 직접 뽑아 보고 판정하라. 보지 않은 것은 "미확인"이다.
> 세진 v1.2 §8 심각도(P0/P1/P2)를 쓰고, P0/P1이 하나라도 열려 있으면 REVISE다.
> 가능하면 다른 모델로 한 번 더 검수하고, 두 판정이 다르면 둘 다 기록하라.

## 총괄 — 회고 (S13)

> H3에서 받은 수정 지시와 공개 후 반응(댓글 상위 5개, 시청 지속 그래프에서 이탈이 큰 구간)을 읽어라.
> 지시 하나마다 `rules/feedback-rules.md`에 규칙 한 줄을 추가하라: ID, 출처 run_id, 규칙, 적용 단계, 검사 방법.
> 같은 지시가 두 번 나왔으면 규칙이 약한 것이다. 검사 방법을 더 기계적으로 바꿔라.
