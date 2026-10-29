# 단아쌤 모션 템플릿 팩 (HyperFrames)

단아쌤 Tech Dark 색(남색 배경 · 보라 · 라임)과 한국어 문구로 맞춘 HyperFrames 템플릿 19종이에요.
폴더 하나가 한 편짜리 HyperFrames 프로젝트이고, 공용 폰트·사진은 `_assets/`를 함께 써요 (`<폴더>/assets` → `../_assets`).

| 분류 | 템플릿 (폴더) | 출처 |
|---|---|---|
| 채팅창 | `chat-claude`, `chat-chatgpt` | 직접 제작 (공식 claude-exchange / chatgpt-exchange 팔레트를 16:9 창으로) |
| 채팅창 | `typed-prompt` | 레지스트리 |
| 이모지 | `emoji-burst` | 직접 제작 |
| 이모지 | `caption-emoji-pop`, `spring-pop` | 레지스트리 |
| 이미지 | `image-drop` (사진 + 스티커 + 동그라미·화살표) | 직접 제작 |
| 이미지 | `hw-frame`, `before-after-wipe` | 레지스트리 |
| 도형·그림 | `shape-kit` | 직접 제작 |
| 도형·그림 | `hw-callout-circle`, `hw-arrow`, `hw-underline`, `hw-text-cloud`, `marker-highlight`, `whiteboard-ink` | 레지스트리 |
| 데이터·이름표 | `count-up`, `marker-checklist-card`, `lt-kicker-name` | 레지스트리 |

## 만들기·렌더링

```bash
python3 _tools/danaize.py .       # 레지스트리 원본(_registry/)을 단아쌤 버전으로 변환
python3 _tools/make_custom.py .   # 직접 만든 5종 생성
./_tools/render_all.sh            # 전부 렌더링 → _previews/*.mp4 (960x540 미리보기)
./_tools/render_all.sh chat-claude  # 하나만
```

문구는 각 템플릿의 변수(`data-composition-variables`)로 바꿔요. 예: 채팅창은 `prompt`, `answer`, `highlight`.

## 주의

- 채팅창 템플릿은 실제 제품 화면이 아닌 **예시 화면**이에요. 화면에 "예시 화면" 표시가 있고, 실제 시연은 화면 녹화로 넣어요 (하네스 MOTION-002).
- 손글씨 라벨은 나눔손글씨 펜(OFL, `_assets/fonts/NanumPenScript-OFL.txt`), 본문은 Pretendard(OFL)예요.
- `marker-checklist-card`는 영어 길이에 맞춘 배치라 한글 문구가 길면 겹칠 수 있어요. 문구를 짧게 쓰세요.
- 레지스트리 원본: heygen-com/hyperframes (Apache-2.0), `hyperframes add`로 설치 (`hyperframes.lock.json`).
