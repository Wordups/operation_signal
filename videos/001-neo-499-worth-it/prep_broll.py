"""Prep raw screenshots into broll/S*.png as Robot Desk "evidence frames" —
Bloomberg Primer-style: inset on the brand canvas with registration crosshairs,
a mono source chip, and the channel mark. Attribution as design.

Mapping is per-video: edit SOURCES and rerun.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
IMAGES = HERE.parent.parent / "images"
FONTS = HERE.parent.parent / "fonts"
BROLL = HERE / "broll"
W, H = 1920, 1080

BG = (17, 17, 20)
DIM = (150, 152, 158)
GRID = (38, 39, 44)
ACCENT = (242, 112, 60)
CHIP = (28, 31, 36)

# slot -> (source file, top crop, bottom crop, source label)
SOURCES = {
    "S1": ("2026-07-09 20_55_32-.png", 0, 0, "SOURCE: 1X — NEO PROMO FILM"),
    "S2": ("man robot.png", 0, 0, "SOURCE: 1X.TECH — ORDER PAGE"),
    "S3": ("neor.png", 0, 0, "SOURCE: 1X.TECH — PRODUCT IMAGERY"),
    "S4": ("2026-07-09 20_54_40-.png", 42, 0, "SOURCE: 1X — NEO PROMO FILM"),
}


def mono(size):
    return ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), size)


def crosshair(d, x, y, r=14, w=3):
    d.line([x - r, y, x + r, y], fill=GRID, width=w)
    d.line([x, y - r, x, y + r], fill=GRID, width=w)


def evidence_frame(img: Image.Image, label: str) -> Image.Image:
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)

    # faint dot grid
    for gx in range(60, W, 120):
        for gy in range(60, H, 120):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=GRID)

    # inset the footage at ~72% height, centered slightly above middle
    target_h = int(H * 0.72)
    scale = min((W * 0.78) / img.width, target_h / img.height)
    fg = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x0, y0 = (W - fg.width) // 2, int(H * 0.10)
    canvas.paste(fg, (x0, y0))
    d = ImageDraw.Draw(canvas)
    d.rectangle([x0 - 1, y0 - 1, x0 + fg.width, y0 + fg.height], outline=GRID, width=2)

    # registration crosshairs in the margins
    for cx, cy in [(x0 - 60, y0 + 40), (x0 - 60, y0 + fg.height - 40),
                   (x0 + fg.width + 60, y0 + 40), (x0 + fg.width + 60, y0 + fg.height - 40),
                   (x0 + 40, y0 + fg.height + 60), (x0 + fg.width - 40, y0 + fg.height + 60)]:
        if 20 < cx < W - 20 and 20 < cy < H - 20:
            crosshair(d, cx, cy)

    # source chip, bottom-left under the inset
    f = mono(26)
    pad = 18
    tw = d.textlength(label, font=f)
    cy0 = y0 + fg.height + 36
    d.rounded_rectangle([x0, cy0, x0 + tw + pad * 2, cy0 + 52], 10, fill=CHIP)
    d.text((x0 + pad, cy0 + 11), label, font=f, fill=DIM)

    # channel mark, bottom-right
    f2 = mono(26)
    mark = "THE ROBOT DESK"
    mw = d.textlength(mark, font=f2)
    d.text((x0 + fg.width - mw, cy0 + 11), mark, font=f2, fill=ACCENT)
    return canvas


BROLL.mkdir(exist_ok=True)
for slot, (name, top, bottom, label) in SOURCES.items():
    src = IMAGES / name
    img = Image.open(src).convert("RGB")
    img = img.crop((0, top, img.width, img.height - bottom))
    evidence_frame(img, label).save(BROLL / f"{slot}.png")
    print(f"{slot}.png <- {name}  [{label}]")
print("open slots: " + ", ".join(s for s in ["S1","S2","S3","S4","S5","S6","S7","S8"] if s not in SOURCES))
