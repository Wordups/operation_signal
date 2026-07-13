"""Video #001 thumbnail v2 — doorway poster + brand type (design system v1.1).

Template ("locked thumbnail template" per BLUEPRINT week 1):
poster right, text stack in left negative space —
mono eyebrow / giant orange hook number / white subject / sharp-tier kicker.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONTS = OUT.parent.parent.parent / "fonts"
W, H = 1280, 720

ACCENT = "#F2703C"
FG = "#F0F0EE"
DIM = "#96989E"


def sans(size, weight=700):
    f = ImageFont.truetype(str(FONTS / "InstrumentSans.ttf"), size)
    f.set_variation_by_axes([100, weight])
    return f


def mono(size, medium=True):
    name = "IBMPlexMono-Medium.ttf" if medium else "IBMPlexMono-Regular.ttf"
    return ImageFont.truetype(str(FONTS / name), size)


poster = Image.open(OUT / "posters" / "doorway.png").convert("RGB")
img = poster.resize((W, round(poster.height * W / poster.width)))
img = img.crop((0, (img.height - H) // 2, W, (img.height - H) // 2 + H))
d = ImageDraw.Draw(img, "RGBA")

# legibility scrim over the left text column only
for x in range(760):
    a = int(200 * (1 - x / 760) ** 1.5)
    d.line([(x, 0), (x, H)], fill=(10, 10, 12, a))

d.text((64, 96), "THE ROBOT DESK", font=mono(30), fill=ACCENT)
d.text((58, 150), "$499/MO", font=sans(168, 700), fill=ACCENT)
d.text((62, 348), "HOME ROBOT", font=sans(92, 700), fill=FG)

kicker = "READ THE FINE PRINT"
kf = sans(52, 600)
kw = d.textlength(kicker, font=kf)
d.rounded_rectangle([56, 512, 56 + kw + 64, 604], 14, fill=(17, 17, 20, 235), outline=ACCENT, width=3)
d.text((88, 530), kicker, font=kf, fill=FG)

img.save(OUT / "thumb-v2-doorway.png")
print("thumb-v2-doorway.png written")
