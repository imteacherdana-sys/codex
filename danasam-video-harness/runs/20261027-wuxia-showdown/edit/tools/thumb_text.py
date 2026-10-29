"""썸네일 배경 이미지에 제목 글자를 얹는다 (흰 글자 + 노란 강조, 굵은 검은 테두리).

사용: python3 tools/thumb_text.py 배경.png 결과.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = str(ROOT / "assets/fonts/Pretendard-Black.ttf")
W, H = 1280, 720


def draw_parts(img, parts, size, cy, stroke):
    """[(글자, 색)]을 한 줄로 가운데 정렬해 그린다. 그림자 → 테두리 → 글자 순서."""
    font = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(img)
    widths = [d.textlength(t, font=font) for t, _ in parts]
    x = (W - sum(widths)) / 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    xs = x
    for (t, _), w in zip(parts, widths):
        sd.text((xs + 6, cy + 8), t, font=font, fill=(0, 0, 0, 170), anchor="lm", stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        xs += w
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    for (t, col), w in zip(parts, widths):
        d.text((x, cy), t, font=font, fill=col, anchor="lm", stroke_width=stroke, stroke_fill=(10, 10, 10))
        x += w


def main(src, dst):
    img = Image.open(src).convert("RGBA").resize((W, H), Image.LANCZOS)
    # 아래쪽을 살짝 어둡게 해서 글자가 잘 읽히게
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(150 * max(0, (y - H * 0.55) / (H * 0.45))))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    shade.putalpha(grad.resize((W, H)))
    img.alpha_composite(shade)
    white, yellow = (255, 255, 255), (255, 222, 0)
    draw_parts(img, [("웰컴투 ", white), ("AI무협월드", yellow)], 112, 560, 9)
    draw_parts(img, [("Seedance2.5 ", white), ("VS", yellow), (" Kling4", white)], 64, 664, 7)
    img.convert("RGB").save(dst, quality=92)
    print("saved", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
