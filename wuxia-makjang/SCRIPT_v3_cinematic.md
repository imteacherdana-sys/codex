# 죽림밀애 1화 v3 — 시네마틱 리메이크 (21:9 · 30초 × 2)

> **바뀐 점 (v2 대비)**
> - **영상:** Kling 4.0만 사용. 21:9 시네마틱, 1080p, **한 클립 30초 × 2개** (Kling 3.0의 최대 15초 대비 2배라는 브리프 핵심 포인트를 그대로 시연)
> - **룩:** 흰 배경 캐릭터 시트만으로는 영상이 화사하고 납작하게 나와서 "촌스러운" 느낌이 났습니다. 그래서 시네마틱 **장소 레퍼런스 3장**을 추가하고, 프롬프트에 촬영 언어(ARRI Alexa 65, 아나모픽 렌즈, 볼류메트릭 헤이즈, 필름 그레인, 탈채도 그레이딩)를 명시했습니다.
> - **연기:** 밀회를 훔쳐보는 설화가 웃던 문제를 고쳤습니다. 눈물이 차오르고, 입술이 떨리고, 비녀를 부러뜨리는 연기로 바꿨고, 미소는 다음 날 아침 마지막 대사에서 한 번만 나오게 했습니다.
> - **반전 연출:** v2에는 설화가 진홍 옷을 입은 채로 흰 옷 여인이 들어오는 모순이 있었습니다. v3에서는 **설화가 그 자리에서 머리를 풀고, 흰 소복을 두르고, 붓으로 흉터를 그려 넣어** 쌍둥이와 똑같아지는 장면으로 바꿨습니다.
> - **더빙:** ElevenLabs(Eleven v4) 11줄. 감정 태그(whispers, crying, nervous, angry, gasping)를 썼습니다.
> - **입모양:** 한국어 대사를 Kling 프롬프트에 그대로 적어서 Kling이 그 대사를 말하는 입모양을 만들게 했습니다. 그다음 Kling 원본 소리에서 말하는 구간을 찾아, 그 위치에 ElevenLabs 대사를 맞춰 넣었습니다.
> - **자막 없음.**

## 레퍼런스 (Omni Reference)

| 종류 | 이미지 | Job ID |
|---|---|---|
| 인물 | 설화 / 설련 / 무진 / 시어머니 시트 | `character-sheets/` 참고 |
| 장소 1 | 달빛 대나무숲 (안개, 21:9) | `5686b88f-7ab1-497a-9a30-b3b150f41608` |
| 장소 2 | 아침 정자 (창호지 빛, 청자 다기) | `34637a9b-29f2-438a-b4a4-eea8d357e7de` |
| 장소 3 | 해 질 녘 촛불 정자 | `437c3f18-f5a3-4dc6-93aa-fcc46aacd09b` |

- 클립 A 레퍼런스: 무진 · 설련 · 설화 · 장소 1 · 장소 2
- 클립 B 레퍼런스: 시어머니 · 설화 · 무진 · 설련 · 장소 3

## 대본 · 더빙 (ElevenLabs Eleven v4)

| # | 클립 | 샷 | 화자 (보이스) | 대사 (감정 태그) |
|---|---|---|---|---|
| A1 | A | 2 · 대나무숲 공터 | 흰 옷 여인 = 변장한 설화 (Tallulah) | [whispers] 늦으셨네요. |
| A2 | A | 2 | 무진 (Julian) | 부인이 잠들 때까지 기다렸소. |
| A3 | A | 3 · 숨어서 지켜봄 | 설화 (Tallulah) | [crying] …그렇단 말이지. |
| A4 | A | 4 · 아침 찻상 | 설화 (Tallulah) | 서방님, 어젯밤엔 어디 계셨어요? |
| A5 | A | 4 | 무진 (Julian) | [nervous] 수, 수련 중이었소. |
| A6 | A | 4 | 설화 (Tallulah) | 그럼 이 차 드시고 힘내세요. |
| B1 | B | 1 · 장풍 | 시어머니 (Vesper) | [angry] 사내가 한눈 좀 판 걸로 집안을 흔들 셈이냐! |
| B2 | B | 2 | 설화 (Tallulah) | 어머님은… 누가 누군지도 모르시잖아요. |
| B3 | B | 3 · 각혈, 실패한 장풍 | 무진 (Julian) | [gasping] 내 내공이…! |
| B4 | B | 4 · 흉터를 그려 넣음 | 설화 (Tallulah) | 어젯밤 대나무숲의 그 여인… 나였어요. |
| B5 | B | 6 · 어둠 속 귓속말 | 진짜 설련 (Maya) | [whispers] 이제 우리 차례예요. |

> 🎭 A1을 설련(Maya)이 아니라 **설화(Tallulah)의 속삭임**으로 녹음한 게 떡밥입니다. B5에서 진짜 설련(Maya)의 목소리가 처음 나오면서 "목소리가 달랐네!"가 됩니다.

## Kling 4.0 프롬프트

공통 설정: Mode `Reference to Video` · Aspect `21:9` · Duration `30s` · Resolution `1080p` (클립 1개 225크레딧)

### 클립 A (0–30초): 밀회 → 목격 → 독이 든 차

```
A 30-second scene from a prestige Korean historical wuxia film. Photorealistic, shot on ARRI Alexa 65 with anamorphic lenses, 2.39:1, natural motivated lighting, deep shadows, volumetric haze, shallow depth of field, muted desaturated color grade, subtle halation, fine 35mm film grain. Restrained, naturalistic acting with real emotion; no glossy beauty lighting, no oversaturated colors. Characters, costumes and faces exactly as in the character references; the moonlit bamboo forest and the wooden pavilion exactly as in the location references.

SHOT 1 (0-6s): Wide tracking shot at night. The swordsman in the black and crimson robe with a silver hair crown runs and leaps lightly across the swaying tops of tall bamboo under the full moon, wuxia qinggong wire-work style, robes billowing, bamboo bending under each step, leaves scattering, camera tracking alongside him. He drops softly into the misty clearing.

SHOT 2 (6-13s): Medium two-shot in the misty clearing. The woman in the white torn mourning robe with long loose hair and a scar on her right cheek stands with her back half-turned. He embraces her from behind. She says quietly in Korean: "늦으셨네요." He answers in a low voice in Korean: "부인이 잠들 때까지 기다렸소." Clear, natural lip movement.

SHOT 3 (13-19s): Slow push-in through dark bamboo stalks in the foreground: the woman in the crimson phoenix wedding-style robe with the gold phoenix hairpin hides in the shadows, watching them. She is devastated: eyes brimming with tears, lips trembling, breath shaking, jaw clenched, a single tear falls. No smile at all. Extreme close-up: her fist tightens around the gold phoenix hairpin until it snaps. She whispers in Korean through her tears: "…그렇단 말이지."

SHOT 4 (19-30s): Hard cut to the pavilion the next morning in soft grey window light. The same woman in crimson, eyes still red and swollen, face composed and cold, pours tea from the celadon teapot for the swordsman sitting across the low table. Without looking up she says in Korean: "서방님, 어젯밤엔 어디 계셨어요?" He freezes, avoids her eyes, sweat on his temple, and stammers in Korean: "수, 수련 중이었소." She slides the cup toward him and says softly in Korean: "그럼 이 차 드시고 힘내세요." Only now a faint, chilling half-smile. Slow push-in on him lifting the steaming cup and drinking.

No text, no subtitles, no logos.
```

### 클립 B (30–60초): 장풍 → 산공독 → 흉터 반전 → 귓속말

```
A 30-second scene from a prestige Korean historical wuxia film. Photorealistic, shot on ARRI Alexa 65 with anamorphic lenses, 2.39:1, candlelit interior at dusk, warm amber flames against deep blue twilight, heavy shadows, volumetric haze, shallow depth of field, muted cinematic color grade, subtle halation, fine 35mm film grain. Restrained, naturalistic acting with real tension; no glossy beauty lighting. Characters, costumes and faces exactly as in the character references; the candlelit pavilion exactly as in the location reference.

SHOT 1 (0-8s): The doors burst open. The cold older woman in the black and purple serpent-embroidered robe with silver nail guards and dagger hairpins strides in. She thrusts her palm forward: a translucent wave of inner energy ripples out in slow motion, the low tea table and celadon cups fly back and shatter, curtains whip, candle flames bend. The young woman in the crimson phoenix robe is pushed back two steps but stays standing. The older woman says sharply in Korean: "사내가 한눈 좀 판 걸로 집안을 흔들 셈이냐!" Clear lip movement.

SHOT 2 (8-13s): Close-up of the young woman in crimson, perfectly calm, eyes cold. She says slowly in Korean: "어머님은… 누가 누군지도 모르시잖아요."

SHOT 3 (13-18s): The swordsman in the black and crimson robe suddenly coughs, a thin line of dark blood at the corner of his mouth, and drops to one knee. He gasps in Korean: "내 내공이…!" and pushes his palm out with all his strength, but only a weak wisp of grey smoke drifts from his hand. Nothing happens. Despair on his face.

SHOT 4 (18-25s): Slow push-in on the young woman in crimson. She lets her hair down, drapes a white mourning veil over her shoulders, and with a fine brush paints a thin red scar onto her right cheek — suddenly she looks exactly like the woman in the white mourning robe. She looks down at him and says quietly in Korean: "어젯밤 대나무숲의 그 여인… 나였어요."

SHOT 5 (25-28s): With one flick of her wide sleeve, a gust blows out every candle at once in slow motion. Darkness.

SHOT 6 (28-30s): In the last moonlight from the window, behind the older woman, the real twin in the white torn mourning robe with a real scar leans in and whispers into her ear with a sly smile, in Korean: "이제 우리 차례예요." Cut to black.

Stylized, minimal blood, no gore. No text, no subtitles, no logos.
```
