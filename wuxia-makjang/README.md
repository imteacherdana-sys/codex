# 혈풍혼례(血風婚禮) — 60초 무협 막장 드라마 제작 키트

> 힉스필드(Higgsfield) × **Kling 4.0** · 9:16 세로 · 실사 사극 · 자막 + 한국어 TTS

| 항목 | 설정 |
|---|---|
| 모델 | Kling 4.0 (`kling4_0`) — `reference-to-video` 모드 |
| 비율 / 해상도 | 9:16 / 1080p |
| 구성 | 15초 × 4클립 = 60초 |
| 예상 비용 | 클립당 48.75 크레딧 → 4클립 약 195 크레딧 (재생성 여유분 포함 300~400) |
| 오디오 | 영상 원본 소리는 쓰지 않고, 자막 + 한국어 TTS + BGM으로 후반 작업 |

---

## 1. 캐릭터 시트 (완성)

`character-sheets/` 폴더에 원본 PNG가 있고, 힉스필드 계정의 생성 기록(History)에도 같은 이미지가 남아 있습니다.

| # | 인물 | 역할 | 파일 | 힉스필드 Job ID |
|---|---|---|---|---|
| 1 | **설화** | 무림맹주의 딸, 신부 (진홍 혼례복) | `01_seolhwa_bride.png` | `49d66bed-a87e-402c-9ec1-fea0327fdadb` |
| 2 | **설련** | 죽은 줄 알았던 쌍둥이 언니 (흰 소복, 오른뺨 흉터) | `02_seolryeon_twin.png` | `4a6f0e6d-d250-4725-af3e-8fa23f4b99f8` |
| 3 | **무진** | 신랑 검객 (흑·적 혼례복, 장검) | `03_mujin_groom.png` | `f58a852f-209e-40ce-8b80-97cef42b1792` |
| 4 | **맹주** | 설화·설련의 아버지 (청금 호랑이 장포) | `04_maengju_father.png` | `5b42f3d6-ac8f-420b-bbdf-7460f4bf588c` |
| 5 | **무진 모친** | 흑풍마교의 안주인 (흑자색 뱀 자수, 은 손톱) | `05_mujin_mother.png` | `c2546c27-f19b-4914-9c2e-73f2811a7eef` |

> 설련 시트는 설화 시트를 레퍼런스로 넣어서 생성했습니다. 그래서 두 사람의 얼굴이 같고, 쌍둥이 설정이 화면에서도 성립합니다.

---

## 2. 대본 · 자막 · TTS

| 클립 | 시간 | 화자 | 대사 (자막 = TTS 원고) |
|---|---|---|---|
| C1 | 0:00–0:05 | 내레이션 | 무림맹 혼례식 날… 하늘이 핏빛으로 물들었다. |
| C1 | 0:08–0:14 | 설련 | 그 남자는… 원래 내 정혼자였다! |
| C2 | 0:15–0:19 | 설화 | 언니…? 언니는 3년 전에 죽었잖아! |
| C2 | 0:21–0:29 | 맹주 | 무진, 너는… 내 원수, 흑풍마교 교주의 아들이다! |
| C3 | 0:30–0:35 | 무진 | 아버님… 그게 무슨…! |
| C3 | 0:37–0:44 | 무진 모친 | 내 아들 앞길, 감히 누가 막느냐! |
| C4 | 0:45–0:50 | 설련 | 어머님… 아니, 마교 교주님. 약속과 다르잖아요. |
| C4 | 0:52–0:58 | 설화 | 기억을 잃은 척했던 건… 나였어. |
| C4 | 0:58–1:00 | 화면 텍스트 | **다음 화에 계속** |

**TTS 보이스 제안**
- 설화: 차분하고 낮은 20대 여성 → 마지막 대사는 속삭이듯
- 설련: 같은 연령대 여성, 조금 더 거칠고 날카로운 톤 (쌍둥이 구분용)
- 무진: 낮은 20대 후반 남성
- 맹주: 굵고 무거운 50대 남성
- 무진 모친: 냉소적인 50대 여성
- 내레이션: 사극 해설 톤

---

## 3. Kling 4.0 프롬프트 (클립별)

**공통 설정:** Mode `Reference to Video` · Aspect `9:16` · Duration `15s` · Resolution `1080p`
**레퍼런스 이미지:** 각 클립 표의 `레퍼런스` 칸에 적힌 시트만 넣으세요. 등장하지 않는 인물의 시트까지 넣으면 그 인물이 엉뚱하게 화면에 끼어들 수 있습니다.

### C1 (0–15초) 혼례식 · 쌍둥이 언니의 등장
레퍼런스: 설화, 무진, 설련

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, moody crimson and gold color grade, 35mm film grain.
Setting: a grand ancient martial-alliance hall decorated for a wedding, red silk banners, hundreds of red candles, petals falling, guests in robes on both sides.
0-5s: slow dolly-in on the bride (the woman in the crimson phoenix wedding robe from the reference) and the groom (the swordsman in the black and crimson robe from the reference) bowing to each other at the altar, candle flames flicker.
5-8s: a sudden gust of wind blows the huge wooden doors open with a bang, all candles bend, guests turn in shock, the bride's veil ornaments swing.
8-15s: in the doorway stands the woman in the white torn mourning robe with long loose black hair and a scar on her right cheek (reference), backlit by grey daylight, white ribbons fluttering; slow push-in to her cold face as she speaks a line with intense anger; quick cut to the bride's shocked close-up — same face as the woman in white.
Realistic skin texture, natural motion, dramatic K-drama acting, no text, no subtitles.
```

### C2 (15–30초) 출생의 비밀
레퍼런스: 설화, 맹주, 무진

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, crimson and gold candlelit hall, film grain.
0-6s: close-up of the bride in the crimson phoenix wedding robe (reference), trembling lips, tears forming, she speaks in disbelief toward the doorway.
6-10s: the martial-alliance leader (grey-bearded man in royal blue and gold tiger robe with fur mantle, reference) slowly stands from his throne, face darkening with rage, draws a gleaming sword with a metallic ring.
10-15s: he points the sword tip straight at the groom's throat (swordsman in black and crimson robe, reference) and shouts a line; extreme close-up of the groom's eyes widening, his sword slips from his hand and falls in slow motion, clanging on the stone floor.
Dramatic K-drama acting, realistic skin texture, no text, no subtitles.
```

### C3 (30–45초) 시어머니 등판
레퍼런스: 무진, 무진 모친, 설련

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, candlelit wedding hall, ominous purple smoke, film grain.
0-5s: the groom (black and crimson swordsman robe, reference) staggers back, speaking in a broken voice, sweat on his face.
5-9s: black-purple smoke swirls at the entrance; the cold older woman in the black and purple serpent-embroidered robe with silver nail guards and dagger hairpins (reference) glides in with slow menacing steps, guests part in fear.
9-15s: she swiftly strikes the woman in the white mourning robe (reference) across the face with a black lacquered sword scabbard, a whip-fast slap with fluttering white sleeves, slow-motion hair whip; she then turns and speaks a sharp line to camera.
Stylized wuxia choreography, no blood, no gore, dramatic K-drama acting, no text, no subtitles.
```

### C4 (45–60초) 최종 반전 · 다음 화에 계속
레퍼런스: 설련, 설화, 무진 모친

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, candles guttering, red petals falling slowly, film grain.
0-6s: the woman in the white mourning robe (reference) holds her cheek, looks at the older woman in black and purple (reference) with betrayal and whispers a line.
6-12s: slow push-in to the bride in the crimson phoenix wedding robe (reference) standing alone at the altar; her red veil ornaments swing; her expression changes from fragile tears to a cold, chilling half-smile as she speaks quietly.
12-15s: extreme close-up of her eyes, a single red petal crosses frame, then a hard freeze-frame with a slight desaturation.
Dramatic K-drama acting, realistic skin texture, no text, no subtitles.
```

---

## 4. 🎥 화면녹화 가이드: 힉스필드에서 Kling 4.0 열고 생성 시작하기

> 튜토리얼 영상(단아쌤TV 등)에 넣을 녹화 구간입니다. **메뉴 이름이나 버튼 위치는 힉스필드 업데이트에 따라 조금 다를 수 있으니**, 녹화 전에 한 번 리허설해 보세요.

### 4-1. 녹화 준비 (녹화 버튼 누르기 전에)
1. **녹화 도구**
   - Windows: `Win + Alt + R` (Xbox Game Bar), 또는 OBS Studio
   - Mac: `Cmd + Shift + 5` → "선택 부분 기록"
2. **브라우저 정리**: 불필요한 탭과 북마크바를 숨기고, 확대 비율을 110~125%로 맞추면 글씨가 잘 보입니다.
3. **미리 로그인**: higgsfield.ai에 로그인한 상태로 시작하세요. 계정 이메일이나 크레딧 숫자가 보이는 게 싫다면 그 영역은 편집 때 블러 처리합니다.
4. **준비물**: 캐릭터 시트 5장(`character-sheets/`)과 이 문서의 C1 프롬프트를 메모장에 열어 둡니다.

### 4-2. 녹화 시퀀스 (클릭 순서 + 멘트)

| 순서 | 화면 동작 | 녹화 멘트 예시 |
|---|---|---|
| ① | 녹화 시작 → 힉스필드 메인 화면 | "오늘은 힉스필드에서 클링 4.0으로 60초짜리 무협 막장 드라마를 만들어 볼게요." |
| ② | 상단 메뉴에서 **Video**(영상 생성) 클릭 | "영상 생성 메뉴로 들어갑니다." |
| ③ | 모델 선택 드롭다운 → **Kling 4.0** 선택 | "모델 목록에서 클링 4.0을 고를게요. 최대 30초, 레퍼런스 이미지도 넣을 수 있는 모델이에요." |
| ④ | 모드 → **Reference to Video** 선택 | "인물 얼굴을 고정하려고 레퍼런스 모드를 씁니다." |
| ⑤ | 레퍼런스 영역에 설화·무진·설련 시트 업로드 (또는 History/Assets에서 선택) | "미리 만들어 둔 캐릭터 시트 세 장을 넣어 줄게요." |
| ⑥ | 프롬프트 창에 C1 프롬프트 붙여넣기 | "첫 번째 장면, 혼례식에 죽은 언니가 나타나는 장면 프롬프트예요." |
| ⑦ | 설정: **9:16 / 15s / 1080p** | "쇼츠용 세로 9:16, 15초, 1080p로 맞춥니다." |
| ⑧ | 하단 예상 크레딧 확인 (약 49) | "15초 한 컷에 49크레딧 정도 드네요." |
| ⑨ | **Generate** 클릭 → 진행률 표시 | "자, 생성 시작! 몇 분 기다리면…" |
| ⑩ | (편집 때 컷) 완성 영상 재생 | "짜잔! 쌍둥이 언니 등장 장면 완성입니다." |

> 팁: ⑨에서 ⑩까지 기다리는 시간은 편집할 때 잘라내거나 "몇 분 후" 자막으로 넘기세요. C2~C4도 같은 방법으로 반복하되, 레퍼런스만 각 클립 표에 맞게 바꾸면 됩니다.

---

## 5. 후반 작업 (조립)

1. C1~C4 클립을 순서대로 이어 붙입니다 (힉스필드 `video-montage` 또는 프리미어/캡컷).
2. 2장의 대사표 타임코드에 맞춰 TTS 음성을 배치합니다.
3. 자막은 하단 1/3 지점, 흰 글씨 + 검은 외곽선 (사극체 폰트 추천).
4. BGM은 국악 현악 + 북으로 긴장감을 쌓고, 반전 순간에 "쾅" 효과음을 넣습니다.
5. 마지막 2초는 정지 화면 + **「다음 화에 계속」**.
6. 업로드할 때 **AI 생성 콘텐츠 표시**를 켜세요 (유튜브: "변경되거나 합성된 콘텐츠").
