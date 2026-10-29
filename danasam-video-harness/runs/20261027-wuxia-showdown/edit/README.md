# 무협 쇼다운 완성본 (편집 생성기)

클링 AI Video Showdown 캠페인 영상. 영상 AI 6개 무협 시험 5개 + 클링 4.0 단편 "단아검법".
내레이션은 비워 두고 대본을 자막으로 넣었다. 단아쌤 녹음본을 `recording-script.md` 타임코드대로 얹는다.

```bash
python3 tools/fetch.py            # media.json의 클립 내려받기 (assets/clips)
python3 tools/synth_audio.py assets/audio   # 배경음악·효과음 합성 (외부 음원 없음)
python3 build.py                  # 장면 52개 → segments/ (HyperFrames 프로젝트), plan.json
tools/render.sh 3                 # 장면 렌더링 → renders/
python3 tools/assemble.py         # 이어 붙이기 + 믹스 → out/
```

- 문장·순위·크레딧은 `build.py`의 `scenes()`, `WINNERS`, `CREDITS`에서 고친다. 고친 장면의 `renders/<장면>.mp4`를 지우고 다시 렌더링한다.
- 순위는 단아쌤 1차 채점 초안이다. 확인 후 확정한다.
- 권위 카드 문구(경희대 교수 · 기업 대표)는 아직 본인 확인 전이다.
