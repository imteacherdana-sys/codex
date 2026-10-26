# 예시 영상: 모션그래픽 완전정복 (HyperFrames)

단아쌤 디자인 시스템 + HeyGen **HyperFrames** 스킬로 만든 71초 설명 영상 예시예요.
얼굴 없이 모션그래픽과 단아쌤 클론 목소리로만 진행해요.

| 항목 | 내용 |
|---|---|
| 스토리 | A안 「밋밋한 자막 한 줄이 살아나기까지」 (`STORYLINES.md`) |
| 연출 설계 | `SPEC.md` |
| 대본 | `SCRIPT.md` (비트 12개) |
| 목소리 | Higgsfield seed_audio, 「단아쌤 내레이션-1」, 사용 크레딧 약 3.6 |
| 장면 | `compositions/` 8개 (hook, timing, easing, hierarchy, transition, compare, claim, outro) |
| 타이밍 | `tools/schedule.json` (비트 = 음성 + 앞 0.2초 + 뒤 0.4초) |

## 설치된 스킬

`.claude/skills/`에 HyperFrames 공식 스킬 4종(hyperframes, hyperframes-cli, hyperframes-registry, media-use)을
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) 저장소에서 복사해 두었어요.
원본 커밋은 `.claude/skills/HYPERFRAMES-SOURCE`, 라이선스(Apache-2.0)는 `.claude/skills/HYPERFRAMES-LICENSE`에 있어요.
CLI는 `package.json`에 `hyperframes@0.8.203`으로 고정했어요.

## 다시 만들기

```bash
npm install
# 이 클라우드 환경처럼 Chrome이 따로 있으면 경로를 알려준다 (일반 PC에서는 필요 없음: npx hyperframes browser ensure)
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell
export PRODUCER_HEADLESS_SHELL_PATH=$HYPERFRAMES_BROWSER_PATH

npm run check     # lint + 실행 + 레이아웃 + 대비 검사
npm run preview   # 브라우저 미리보기 (HyperFrames Studio)
npm run render    # renders/motion-masterclass.mp4
```

목소리를 다시 만들면 `raw/`에 받은 뒤 `python3 tools/proc.py .`로 무음을 다듬고(EDIT-001 규칙),
`assets/audio/durations.json`이 바뀌면 `tools/schedule.json`과 `index.html`의 시작 시간을 다시 맞춰요.

## 폰트

`assets/fonts/Pretendard.woff2`는 Pretendard 가변 폰트(SIL OFL 1.1)에서 이 영상에 쓰인 글자만 남긴 파일이에요.
화면 글자를 바꾸면 새 글자가 빠져 보일 수 있으니 원본 폰트로 다시 서브셋하세요.
