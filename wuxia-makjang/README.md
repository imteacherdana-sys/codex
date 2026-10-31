# 죽림밀애(竹林密愛) — 60초 무협 불륜 막장 드라마 제작 키트

> 힉스필드(Higgsfield) × **Kling 4.0** · 9:16 세로 · 실사 사극 · 자막 + 한국어 TTS · 경공·장풍 액션

| 항목 | 설정 |
|---|---|
| 모델 | Kling 4.0 (`kling4_0`) — `reference-to-video` 모드 (C1 경공 컷은 키프레임 `image-to-video` 대안 포함) |
| 비율 / 해상도 | 9:16 / 1080p |
| 구성 | 15초 × 4클립 = 60초 |
| 예상 비용 | 클립당 48.75 크레딧 → 4클립 약 195 크레딧 (재생성 여유분 포함 300~400) |
| 오디오 | 영상 원본 소리는 쓰지 않고, 자막 + 한국어 TTS + BGM·효과음으로 후반 작업 |

> 이전 초안 「혈풍혼례」는 `ALT_hyeolpung-honrye.md`에 보관해 두었습니다.

---

## 0. 로그라인

혼인 3년 차, 무림맹 후계자 **무진**은 매일 밤 경공으로 대나무숲에 날아가 아내 **설화**의 쌍둥이 언니 **설련**을 만난다. 시어머니는 알면서도 덮어 준다.
그런데 어젯밤 대나무숲의 그 여인은 **변장한 아내**였고, 아침 찻잔에는 무공을 흩어 버리는 **산공독**이 들어 있었다.
마지막 순간, 진짜 설련은 시어머니 곁에서 웃는다.

- **1차 반전:** 남편이 만난 여인은 언니가 아니라 변장한 아내였다.
- **2차 반전:** 진짜 설련과 시어머니가 한편이다.

---

## 1. 캐릭터 시트 (완성)

`character-sheets/` 폴더에 원본 PNG가 있고, 힉스필드 계정의 생성 기록(History)에도 같은 이미지가 남아 있습니다.

| # | 인물 | 이번 역할 | 파일 | 힉스필드 Job ID |
|---|---|---|---|---|
| 1 | **설화** | 아내. 숨은 고수. C4에서는 흰 옷으로 변장한 모습으로 등장 | `01_seolhwa_bride.png` | `49d66bed-a87e-402c-9ec1-fea0327fdadb` |
| 2 | **설련** | 쌍둥이 언니, 불륜 상대이자 흑막 (오른뺨 흉터) | `02_seolryeon_twin.png` | `4a6f0e6d-d250-4725-af3e-8fa23f4b99f8` |
| 3 | **무진** | 바람난 남편, 경공의 달인 | `03_mujin_groom.png` | `f58a852f-209e-40ce-8b80-97cef42b1792` |
| 4 | **맹주** | 이번 편에는 나오지 않음 (2화 복수극 때 등장) | `04_maengju_father.png` | `5b42f3d6-ac8f-420b-bbdf-7460f4bf588c` |
| 5 | **무진 모친** | 묵인하는 시어머니, 장풍을 쓰는 흑막 | `05_mujin_mother.png` | `c2546c27-f19b-4914-9c2e-73f2811a7eef` |

> 설련 시트는 설화 시트를 레퍼런스로 넣어서 생성했습니다. 그래서 두 사람의 얼굴이 같고, "변장한 아내" 반전이 화면에서도 성립합니다.

---

## 2. 대본 · 자막 · TTS

> 🎬 **빠른 템포 확정 대본(32줄, 0.1초 단위 타임코드), 캐스팅, 편집 규칙은 [`SCRIPT_fast.md`](SCRIPT_fast.md)를 기준으로 합니다.** 아래 표는 장면 흐름을 한눈에 보기 위한 요약본입니다.

| 클립 | 시간 | 화자 | 대사 (자막 = TTS 원고) |
|---|---|---|---|
| C1 | 0:00–0:05 | 내레이션 | 혼인 3년… 무림맹 후계자에겐 숨겨 둔 밤이 있었다. |
| C1 | 0:08–0:11 | 무진 | 설화에겐… 절대 들켜선 안 되오. |
| C1 | 0:11–0:14 | 흰 옷 여인 | 같은 얼굴인데, 왜 나는 밤에만 만나야 하죠? |
| C2 | 0:20–0:24 | 설화 | 서방님… 어젯밤엔 어디 계셨어요? |
| C2 | 0:24–0:26 | 무진 | 수, 수련 중이었소. |
| C2 | 0:26–0:29 | 설화 | 그래요? 그럼 이 차 드시고 힘내세요. |
| C3 | 0:35–0:39 | 시어머니 | 사내가 한눈 좀 판 걸로 집안을 흔들 셈이냐! |
| C3 | 0:41–0:44 | 시어머니 | 어차피 같은 얼굴 아니더냐? |
| C4 | 0:48–0:52 | 설화 | 어젯밤 대나무숲의 그 여인… 나였어요. |
| C4 | 0:52–0:55 | 설화 | 그 찻잔엔 산공독이 들어 있었죠. |
| C4 | 0:56–0:58 | 설련 | (속삭이며) 어머님, 이제 우리 차례예요. |
| C4 | 0:58–1:00 | 화면 텍스트 | **다음 화에 계속** |

> C1의 "흰 옷 여인"은 시청자에게 설련으로 보이게 연출하지만, 목소리는 **설화(Tallulah)의 속삭임**으로 녹음합니다. C4의 반전 뒤에 다시 보면 알아챌 수 있는 떡밥입니다.

**TTS 보이스 (확정):** 내레이션 Gideon · 무진 Julian · 설화 Tallulah · 설련 Maya · 시어머니 Vesper (근거와 Voice ID는 `SCRIPT_fast.md` 참고)

**효과음 큐**
| 시간 | 효과음 |
|---|---|
| 0:03 | 경공 도약 "휙", 댓잎 흩날리는 소리 |
| 0:16 | 비녀가 부러지는 "딱" |
| 0:33 | 장풍 "쿠웅" 기 폭발 + 찻상과 찻잔이 깨지는 소리 |
| 0:47 | 실패한 장풍 "픽" (헛웃음이 나오는 타이밍) |
| 0:55 | 촛불이 한꺼번에 꺼지는 "후욱" → 암전 |

---

## 3. Kling 4.0 프롬프트 (클립별)

**공통 설정:** Mode `Reference to Video` · Aspect `9:16` · Duration `15s` · Resolution `1080p`
**레퍼런스 이미지:** 각 클립 표의 `레퍼런스` 칸에 적힌 시트만 넣으세요. 등장하지 않는 인물의 시트까지 넣으면 그 인물이 엉뚱하게 화면에 끼어들 수 있습니다.

**액션 안정화 요령**
- 액션 컷에는 `slow motion`을 넣습니다.
- 한 컷에 동작은 하나만 넣습니다 (도약 → 착지처럼 짧게).
- 장풍은 기운 자체보다 주변이 날아가는 반응으로 표현합니다.

### C1 (0–15초) 달밤의 밀회 · 경공
레퍼런스: 무진, 설련

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, cold blue moonlight with silver highlights, 35mm film grain.
Setting: a vast bamboo forest at night under a huge full moon, mist drifting between the stalks.
0-7s: the swordsman (long black hair, topknot with silver crown, black and crimson robe, sword at hip, from the reference) leaps lightly across the tops of swaying bamboo stalks, wuxia qinggong wire-work style, robes billowing, slow motion, bamboo bending under each step, leaves scattering in the moonlight; he lands softly in a clearing.
7-15s: waiting in the clearing is the woman in the white torn mourning robe with long loose black hair and a scar on her right cheek (reference); they embrace tenderly, close two-shot, he whispers to her with a guilty look, she answers with a sad, longing expression; bamboo leaves drift past.
Romantic but non-explicit, fully clothed, dramatic K-drama acting, realistic skin texture, no text, no subtitles.
```

**🔑 키프레임 대안 (협찬 영상 '키프레임' 챕터 시연용):** 경공 부분(0–7초)만 따로 만들 때 씁니다.
- Mode `Image to Video`, Duration `7s`
- `start_image`: 땅에 선 무진 (C1 결과의 첫 프레임 캡처, 또는 시트로 따로 생성)
- `end_image`: 대나무 꼭대기에 선 무진
- 프롬프트: `the swordsman springs upward and runs along the bamboo tops in slow motion, qinggong, robes flowing, leaves scattering`

### C2 (15–30초) 아내의 눈 · 독이 든 차
레퍼런스: 설화, 무진

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, film grain.
0-5s: night, bamboo forest: the woman in the crimson phoenix robe with gold phoenix hairpin (reference) hides behind thick bamboo, watching something off-screen, tears in her eyes; extreme close-up of her hand gripping the gold phoenix hairpin until it snaps in two.
5-15s: hard cut to soft morning light in an elegant wooden pavilion: the same woman, now calm and smiling sweetly, kneels and pours tea from a celadon teapot into a cup for the swordsman in the black and crimson robe (reference); she asks him something gently, he stammers nervously and avoids her eyes, sweat on his temple; she slides the teacup toward him with a too-perfect smile; slow push-in on the steaming cup.
Dramatic K-drama acting, realistic skin texture, no text, no subtitles.
```

### C3 (30–45초) 시어머니 등판 · 장풍
레퍼런스: 무진 모친, 설화

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, morning pavilion, ominous purple tint creeping in, film grain.
0-4s: the doors slam open; the cold older woman in the black and purple serpent-embroidered robe with silver nail guards and dagger hairpins (reference) strides in.
4-9s: she thrusts her palm forward, a translucent purple shockwave of inner energy bursts out, slow motion, the tea table and celadon cups fly backward and shatter, curtains and candle flames blown violently; the woman in the crimson phoenix robe (reference) is pushed back several steps, sleeves whipping, but stays standing.
9-15s: the older woman points a long silver nail guard at her and speaks a harsh line with contempt; the younger woman lowers her eyes, but a faint cold smile appears for a split second.
Stylized wuxia energy effects, no blood, no gore, dramatic K-drama acting, no text, no subtitles.
```

### C4 (45–60초) 이중 반전 · 실패한 장풍
레퍼런스: 무진, 설련, 무진 모친
(변장한 설화는 설련 시트와 같은 얼굴이므로 설련 시트로 연출합니다)

```
Vertical 9:16 cinematic Korean historical wuxia drama, photorealistic, candlelit pavilion at dusk, film grain.
0-4s: the swordsman in the black and crimson robe (reference) suddenly coughs, a thin trickle of dark blood at the corner of his mouth, drops to one knee; he pushes his palm out with all his strength but only a weak wisp of grey smoke drifts from his hand, nothing happens, his face turns to despair.
4-10s: the woman in the white mourning robe with a scar on her right cheek (reference) walks in slowly; she wipes her cheek with her fingertips and the scar smears away like paint, revealing smooth skin; she looks down at him with a cold calm stare and speaks quietly.
10-13s: with one flick of her wide sleeve, a gust of wind blows out every candle in the room at once, slow motion.
13-15s: in the last fading light, behind the older woman in black and purple (reference), a second identical woman in white with a real scar leans in and whispers into her ear with a sly smile; hard cut to black.
Stylized, minimal blood, dramatic K-drama acting, realistic skin texture, no text, no subtitles.
```

> ⚠️ C4는 같은 얼굴 두 명(변장한 설화 + 진짜 설련)이 한 화면에 나와야 해서 가장 어려운 컷입니다. 한 번에 잘 안 나오면 10–15초를 별도 5초 클립으로 나눠 생성하는 걸 추천합니다.

---

## 4. 🎥 화면녹화 가이드: 힉스필드에서 Kling 4.0 열고 생성 시작하기

> 튜토리얼 영상(단아쌤TV 등)에 넣을 녹화 구간입니다. **메뉴 이름이나 버튼 위치는 힉스필드 업데이트에 따라 조금 다를 수 있으니**, 녹화 전에 한 번 리허설해 보세요.

### 4-1. 녹화 준비 (녹화 버튼 누르기 전에)
1. **녹화 도구**
   - Windows: `Win + Alt + R` (Xbox Game Bar), 또는 OBS Studio
   - Mac: `Cmd + Shift + 5` → "선택 부분 기록"
2. **브라우저 정리**: 불필요한 탭과 북마크바를 숨기고, 확대 비율을 110~125%로 맞추면 글씨가 잘 보입니다.
3. **미리 로그인**: higgsfield.ai에 로그인한 상태로 시작하세요. 계정 이메일이나 크레딧 숫자가 보이는 게 싫다면 그 영역은 편집 때 블러 처리합니다.
4. **준비물**: 캐릭터 시트(`character-sheets/`)와 이 문서의 C1 프롬프트를 메모장에 열어 둡니다.

### 4-2. 녹화 시퀀스 (클릭 순서 + 멘트)

| 순서 | 화면 동작 | 녹화 멘트 예시 |
|---|---|---|
| ① | 녹화 시작 → 힉스필드 메인 화면 | "오늘은 힉스필드에서 클링 4.0으로 60초짜리 무협 불륜 막장 드라마를 만들어 보겠습니다." |
| ② | 상단 메뉴에서 **Video**(영상 생성) 클릭 | "영상 생성 메뉴로 한번 들어가 보겠습니다." |
| ③ | 모델 선택 드롭다운 → **Kling 4.0** 선택 | "모델 목록에서 클링 4.0을 고르겠습니다. 최대 30초까지, 레퍼런스 이미지도 여러 장 넣을 수가 있는 모델입니다." |
| ④ | 모드 → **Reference to Video** 선택 | "인물 얼굴을 고정하기 위해서 레퍼런스 모드를 쓰겠습니다." |
| ⑤ | 레퍼런스 영역에 **무진·설련** 시트 업로드 (또는 History/Assets에서 선택) | "미리 만들어 둔 남편과 쌍둥이 언니 캐릭터 시트를 넣어 주겠습니다." |
| ⑥ | 프롬프트 창에 C1 프롬프트 붙여넣기 | "첫 장면은 남편이 경공으로 대나무 위를 날아서 밀회를 가는 장면입니다." |
| ⑦ | 설정: **9:16 / 15s / 1080p** | "쇼츠용 세로 9:16, 15초, 1080p로 맞추겠습니다." |
| ⑧ | 하단 예상 크레딧 확인 (약 49) | "15초 한 컷에 49크레딧 정도 드는 걸 확인할 수가 있습니다." |
| ⑨ | **Generate** 클릭 → 진행률 표시 | "자, 생성을 시작해 보겠습니다." |
| ⑩ | (편집 때 컷) 완성 영상 재생 | "경공 장면이 이렇게 완성됐습니다." |
| ⑪ | (선택) 모드 → **Image to Video**, 시작·끝 프레임 업로드 | "이번에는 키프레임 기능으로 경공 궤적을 직접 지정해 보겠습니다." |

> 팁: ⑨에서 ⑩까지 기다리는 시간은 편집할 때 잘라내거나 "몇 분 후" 자막으로 넘기세요. C2~C4도 같은 방법으로 반복하되, 레퍼런스만 각 클립 표에 맞게 바꾸면 됩니다.

---

## 5. 후반 작업 (조립)

1. C1~C4 클립을 순서대로 이어 붙입니다 (힉스필드 `video-montage` 또는 프리미어/캡컷).
2. 2장의 대사표 타임코드에 맞춰 TTS 음성과 효과음을 배치합니다.
3. 자막은 하단 1/3 지점, 흰 글씨 + 검은 외곽선 (사극체 폰트 추천).
4. BGM은 C1에 애절한 해금, C3~C4에 북과 현악으로 긴장감을 쌓고, 반전 순간에 "쾅" 효과음을 넣습니다.
5. 마지막 2초는 암전 + **「다음 화에 계속」**.
6. 업로드할 때 **AI 생성 콘텐츠 표시**를 켜세요 (유튜브: "변경되거나 합성된 콘텐츠").

> 수위 메모: 포옹·눈빛까지만 보여 주고 노출이나 성적 묘사는 넣지 않았습니다. 피는 얇은 핏줄기 수준으로 맞췄습니다. 협찬 영상이라 플랫폼 정책과 광고주 브랜드 안전을 고려한 선택입니다.
