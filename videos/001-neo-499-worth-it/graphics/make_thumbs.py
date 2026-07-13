"""Video #001 thumbnails — 1280x720, text-led, two variants."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
W, H = 1280, 720
F = "C:/Windows/Fonts/"

def font(size, weight="bold"):
    files = {"regular": "segoeui.ttf", "bold": "segoeuib.ttf", "black": "seguibl.ttf"}
    try:
        return ImageFont.truetype(F + files[weight], size)
    except OSError:
        return ImageFont.truetype(F + "segoeuib.ttf", size)


def robot_head(d, cx, cy, s, body, accent):
    """Simple geometric robot head, s = half-width."""
    d.rounded_rectangle([cx - s, cy - s, cx + s, cy + s], int(s * 0.25), fill=body)
    eye = int(s * 0.22)
    for ex in (cx - int(s * 0.45), cx + int(s * 0.45)):
        d.ellipse([ex - eye, cy - int(s * 0.35) - eye, ex + eye, cy - int(s * 0.35) + eye], fill=accent)
    d.rounded_rectangle([cx - int(s * 0.5), cy + int(s * 0.35), cx + int(s * 0.5), cy + int(s * 0.55)], 8, fill=accent)
    d.rectangle([cx - 6, cy - s - int(s * 0.3), cx + 6, cy - s], fill=body)
    d.ellipse([cx - 16, cy - s - int(s * 0.55), cx + 16, cy - s - int(s * 0.25)], fill=accent)


# ---- Variant A: $499/MO? ----
img = Image.new("RGB", (W, H), (12, 14, 18))
d = ImageDraw.Draw(img)
for i in range(H):  # subtle vertical gradient
    v = int(12 + 18 * i / H)
    d.line([(0, i), (W, i)], fill=(v, v + 2, v + 8))
robot_head(d, 1075, 470, 150, (52, 58, 70), (255, 200, 60))
d.text((70, 90), "$499/MO", font=font(150, "black"), fill=(255, 200, 60))
d.text((70, 290), "HOME ROBOT", font=font(90), fill=(240, 240, 238))
d.rounded_rectangle([64, 490, 850, 610], 16, fill=(200, 40, 40))
d.text((92, 505), "READ THE FINE PRINT", font=font(62), fill=(255, 255, 255))
img.save(OUT / "thumb-A-499.png")

# ---- Variant B: WORTH IT? ----
img = Image.new("RGB", (W, H), (12, 14, 18))
d = ImageDraw.Draw(img)
for i in range(H):
    v = int(10 + 22 * i / H)
    d.line([(0, i), (W, i)], fill=(v + 6, v, v))
robot_head(d, 270, 330, 200, (52, 58, 70), (235, 90, 90))
d.text((560, 90), "$20,000", font=font(160, "black"), fill=(240, 240, 238))
d.text((560, 290), "ROBOT", font=font(120, "black"), fill=(240, 240, 238))
d.text((560, 470), "WORTH IT?", font=font(120, "black"), fill=(255, 200, 60))
img.save(OUT / "thumb-B-worthit.png")

print("2 thumbnails written")
