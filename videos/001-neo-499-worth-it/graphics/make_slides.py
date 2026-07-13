"""Video #001 graphics — Robot Desk design system v1.1 "poster theme".

Slides composite over the cinematic poster backgrounds (Design/
the-robot-desk-video-graphics-poster-theme.pptx) with a legibility scrim.
Progressive build variants: NN-name-b1.png ... NN-name.png (builds sort
before the full slide, so the assembler's glob plays the reveal).
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
POSTERS = OUT / "posters"
FONTS = OUT.parent.parent.parent / "fonts"
W, H = 1920, 1080

BG = (17, 17, 20)
CARD = (28, 31, 36)
FG = (240, 240, 238)
DIM = (170, 172, 178)
ACCENT = (242, 112, 60)
AMBER = (227, 169, 74)
GREEN = (80, 200, 120)
RED = (235, 90, 90)


def sans(size, weight=400):
    f = ImageFont.truetype(str(FONTS / "InstrumentSans.ttf"), size)
    f.set_variation_by_axes([100, weight])
    return f


def mono(size, medium=False):
    name = "IBMPlexMono-Medium.ttf" if medium else "IBMPlexMono-Regular.ttf"
    return ImageFont.truetype(str(FONTS / name), size)


TITLE = sans(72, 700)
BIG = sans(120, 700)
HEAD = sans(56, 600)
BODY = sans(46)
SMALL = sans(36)
EYEBROW = mono(28, medium=True)

_poster_cache = {}


def poster_bg(name: str, scrim: int) -> Image.Image:
    """Poster background, cover-fit to 1920x1080, darkened by scrim alpha (0-255)."""
    key = (name, scrim)
    if key not in _poster_cache:
        img = Image.open(POSTERS / f"{name}.png").convert("RGB")
        scale = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        img = img.crop(((img.width - W) // 2, (img.height - H) // 2,
                        (img.width - W) // 2 + W, (img.height - H) // 2 + H))
        img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0),
                  Image.new("L", (W, H), scrim))
        _poster_cache[key] = img
    return _poster_cache[key].copy()


def new_slide(poster=None, scrim=150):
    img = poster_bg(poster, scrim) if poster else Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def card(d, box, radius=24, fill=CARD):
    d.rounded_rectangle(box, radius, fill=fill)


def center(d, y, text, fnt, fill=FG):
    w = d.textlength(text, font=fnt)
    d.text(((W - w) / 2, y), text, font=fnt, fill=fill)


def title_bar(d, text):
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    center(d, 48, "THE ROBOT DESK", EYEBROW, DIM)
    center(d, 96, text, TITLE, FG)


def emit(name, draw_fn, n_states):
    for r in range(1, n_states + 1):
        img, d = draw_fn(r)
        suffix = "" if r == n_states else f"-b{r}"
        img.save(OUT / f"{name}{suffix}.png")


# ---- 00: title card (cold open) — doorway poster, left negative space ----
def s00(r):
    img, d = new_slide("doorway", 40)
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    d.text((114, 400), "The $499/Month", font=sans(96, 700), fill=FG)
    d.text((114, 510), "Home Robot", font=sans(96, 700), fill=FG)
    d.text((114, 650), "What they don't tell you.", font=sans(52, 600), fill=DIM)
    return img, d

emit("00-title", s00, 1)


# ---- 01: subscription math — pedestals poster ----
def s01(r):
    img, d = new_slide("pedestals", 140)
    title_bar(d, "THE SUBSCRIPTION MATH")
    steps = [("$499", "per month"), ("$6,000", "per year"), ("$42,000", "over 7 years")]
    x = 180
    for i, (num, lab) in enumerate(steps[: min(r, 3)]):
        card(d, [x, 340, x + 440, 620])
        w = d.textlength(num, font=BIG)
        d.text((x + (440 - w) / 2, 390), num, font=BIG, fill=FG)
        w = d.textlength(lab, font=BODY)
        d.text((x + (440 - w) / 2, 530), lab, font=BODY, fill=DIM)
        if i < min(r, 3) - 1:
            d.text((x + 460, 440), "→", font=BIG, fill=ACCENT)
        x += 560
    if r >= 4:
        card(d, [360, 730, 1560, 930], radius=28)
        center(d, 755, "Buying it outright: $20,000", HEAD, DIM)
        center(d, 840, "You could buy the robot twice.", HEAD, ACCENT)
    return img, d

emit("01-subscription-math", s01, 4)


# ---- 02: does vs doesn't — doorway poster ----
def s02(r):
    img, d = new_slide("doorway", 165)
    title_bar(d, "WHAT $499/MONTH ACTUALLY BUYS")
    does = ["Opens doors", "Tidies rooms", "Loads laundry", "Waters plants", "Fetches things"]
    doesnt = ["Cook", "Clean bathrooms", "Beat a $300 robot vacuum", "Move fast"]
    card(d, [120, 240, 920, 960])
    d.text((170, 280), "DOES  (slowly)", font=HEAD, fill=GREEN)
    for i, t in enumerate(does):
        y = 410 + i * 100
        d.ellipse([176, y + 22, 204, y + 50], fill=GREEN)
        d.text((240, y), t, font=BODY, fill=FG)
    if r >= 2:
        card(d, [1000, 240, 1800, 960])
        d.text((1050, 280), "DOESN'T", font=HEAD, fill=RED)
        for i, t in enumerate(doesnt):
            y = 410 + i * 100
            d.ellipse([1056, y + 22, 1084, y + 50], fill=RED)
            d.text((1120, y), t, font=BODY, fill=FG)
    return img, d

emit("02-does-vs-doesnt", s02, 2)


# ---- 03: three options — desk poster ----
def s03(r):
    img, d = new_slide("desk", 150)
    title_bar(d, "THE HONEST MATH — THREE OPTIONS")
    opts = [
        ("OPTION 1 — THE BORING STACK", "$4,600–5,000", "Vacuum + cleaner 2×/mo. Works today.", GREEN),
        ("OPTION 2 — NEO SUBSCRIPTION", "$6,000 / yr", "Still need the vacuum + cleaner.", AMBER),
        ("OPTION 3 — BUY NEO OUTRIGHT", "$20,000", "Gen-1 hardware. Prices falling fast.", RED),
    ]
    y = 250
    for head, num, sub, col in opts[:r]:
        card(d, [140, y, 1780, y + 220])
        d.rectangle([140, y, 156, y + 220], fill=col)
        d.text((220, y + 30), head, font=HEAD, fill=col)
        d.text((220, y + 115), sub, font=BODY, fill=DIM)
        w = d.textlength(num, font=sans(84, 700))
        d.text((1700 - w, y + 60), num, font=sans(84, 700), fill=FG)
        y += 260
    return img, d

emit("03-three-options", s03, 3)


# ---- 04: verdict tree — bands poster (rows echo the light bands) ----
def s04(r):
    img, d = new_slide("bands", 150)
    title_bar(d, "THE VERDICT")
    rows = [
        ("Trying to save money on chores?", "DON'T BUY", RED),
        ("Mobility or accessibility needs?", "WORTH A SERIOUS LOOK", GREEN),
        ("Want to be early — and can afford it?", "SUBSCRIBE, DON'T BUY", AMBER),
        ("Everyone else", "WAIT", ACCENT),
    ]
    y = 260
    for q, a, col in rows[:r]:
        card(d, [140, y, 1780, y + 160])
        d.rectangle([140, y, 156, y + 160], fill=col)
        d.text((220, y + 50), q, font=BODY, fill=DIM)
        w = d.textlength(a, font=HEAD)
        d.text((1700 - w, y + 48), a, font=HEAD, fill=col)
        y += 200
    return img, d

emit("04-verdict", s04, 4)


# ---- 05: buy signal — doorway poster ----
def s05(r):
    img, d = new_slide("doorway", 130)
    title_bar(d, "YOUR BUY SIGNAL")
    card(d, [260, 300, 1660, 800], radius=32)
    d.rounded_rectangle([260, 300, 1660, 800], 32, outline=ACCENT, width=4)
    center(d, 380, "Cleans a bathroom unattended", HEAD)
    center(d, 490, "+", BIG, ACCENT)
    center(d, 640, "Costs under $10,000", HEAD)
    if r >= 2:
        center(d, 880, "Best guess: 2028", TITLE, ACCENT)
    return img, d

emit("05-buy-signal", s05, 2)


# ---- 06: spec card — doorway poster ----
def s06(r):
    img, d = new_slide("doorway", 150)
    title_bar(d, "NEO — THE MACHINE")
    specs = [
        ("5'6\"", "tall"), ("66 lbs", "light enough to share a house"),
        ("22 dB", "quieter than your fridge"), ("~4 hrs", "runtime per charge"),
        ("Tendon-driven", "soft, quiet motion"), ("Knit nylon suit", "padding, not fashion"),
    ]
    positions = [(140, 260), (960, 260), (140, 500), (960, 500), (140, 740), (960, 740)]
    for (num, lab), (x, y) in list(zip(specs, positions))[: r * 2]:
        card(d, [x, y, x + 820, y + 200])
        d.text((x + 50, y + 30), num, font=sans(64, 700), fill=FG)
        d.text((x + 50, y + 120), lab, font=SMALL, fill=DIM)
    return img, d

emit("06-spec-card", s06, 3)


# ---- 07: Expert Mode controls — desk poster ----
def s07(r):
    img, d = new_slide("desk", 160)
    title_bar(d, "EXPERT MODE — WHAT'S ACTUALLY IN PLACE")
    controls = [
        "You schedule and approve every operator session",
        "No-go zones — rooms blocked even during teleoperation",
        "Faces blurred for the operator, on by default",
        "Audio masking + data-sharing opt-out",
        "Operators background-checked, don't know whose home",
    ]
    counts = {1: 2, 2: 4, 3: 5}
    y = 270
    for t in controls[: counts[r]]:
        card(d, [160, y, 1760, y + 120])
        d.ellipse([210, y + 42, 246, y + 78], fill=GREEN)
        d.text((300, y + 32), t, font=BODY, fill=FG)
        y += 150
    return img, d

emit("07-expert-mode", s07, 3)


# ---- 08: cost curve — pedestals poster ----
def s08(r):
    img, d = new_slide("pedestals", 140)
    title_bar(d, "THE COST CURVE IS REAL")
    rows = [
        ("Unitree G1", "$16,000 → $13,500", "since launch"),
        ("Unitree R1", "$4,900", "launched 2025"),
        ("Noetix Bumi", "$1,400", "a toy — but it exists"),
    ]
    y = 250
    for name, num, sub in rows[: min(r, 3)]:
        card(d, [140, y, 1780, y + 170])
        d.text((220, y + 40), name, font=HEAD, fill=FG)
        w = d.textlength(num, font=sans(72, 700))
        d.text((1400 - w, y + 40), num, font=sans(72, 700), fill=ACCENT)
        d.text((1440, y + 62), sub, font=SMALL, fill=DIM)
        y += 210
    if r >= 4:
        card(d, [200, 870, 1720, 960], radius=20)
        center(d, 885, "Goldman: build costs fell ~40% in one year   •   BofA: halved by 2030", HEAD, GREEN)
    return img, d

emit("08-cost-curve", s08, 4)


# ---- 09: GUARD Act — desk poster ----
def s09(r):
    img, d = new_slide("desk", 150)
    title_bar(d, "THE WRINKLE — THE GUARD ACT")
    card(d, [200, 270, 1720, 640], radius=32)
    d.rounded_rectangle([200, 270, 1720, 640], 32, outline=RED, width=4)
    center(d, 340, "Bill in Congress: restrict Chinese-built humanoids", HEAD)
    center(d, 450, "pending national-security review", HEAD)
    if r >= 2:
        card(d, [280, 700, 1640, 900], radius=24)
        center(d, 720, "The overseas price war may take longer to reach the US", BODY, DIM)
        center(d, 810, "Doesn't change the direction. Changes the date.", HEAD, ACCENT)
    return img, d

emit("09-guard-act", s09, 2)


# ---- 10: sources — desk poster (the literal robot desk) ----
def s10(r):
    img, d = new_slide("desk", 165)
    title_bar(d, "SOURCES — CHECK THEM YOURSELF")
    sources = [
        ("1x.tech/order + 1x.tech/neo — pricing, specs, Expert Mode", "2026-07-09"),
        ("Wall Street Journal — NEO demo (teleoperated)", "2025-10"),
        ("Fortune — subscription terms", "2026-02-26"),
        ("Goldman Sachs / BofA Institute — cost forecasts", "2026-03"),
        ("CareScout 2025 Cost of Care Survey — assisted living", "2026-03-02"),
        ("shop.unitree.com — G1 / R1 pricing", "2026-07-09"),
        ("chinaselectcommittee.house.gov — the GUARD Act", "2026-06"),
    ]
    y = 250
    for i, (t, date) in enumerate(sources, 1):
        d.text((200, y + 6), f"{i:02d}", font=mono(34, medium=True), fill=ACCENT)
        d.text((300, y), t, font=BODY, fill=FG)
        w = d.textlength(date, font=mono(30))
        d.text((1720 - w, y + 10), date, font=mono(30), fill=DIM)
        y += 100
    center(d, y + 20, "Every claim primary-sourced or hedged.", SMALL, DIM)
    return img, d

emit("10-sources", s10, 1)

n = len(list(OUT.glob("[0-9]*.png")))
print(f"{n} slide frames written (Robot Desk v1.1 poster theme)")
