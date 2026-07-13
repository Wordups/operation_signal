"""The Robot Desk — 12s branded channel intro. SportsCenter energy, brand-book restraint.

Phases: orange glyph rain + type-on (0-3s) -> desk-poster brand reveal (3-7s)
-> three fast evidence flashes (7-9s) -> episode card (9-12s).
Custom synth sting (riser/boom/pulse/hit) + Brian VO, muxed with ffmpeg.

    python make_intro.py "NEO" "The $499/Month Home Robot"
Writes intro.mp4 next to this script; copy/point episodes at it.
"""

import random
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE = Path(__file__).parent
REPO = HERE.parent
FONTS = REPO / "fonts"
POSTERS = REPO / "videos" / "001-neo-499-worth-it" / "graphics" / "posters"
FLASHES = [REPO / "videos" / "001-neo-499-worth-it" / "broll" / n for n in ("S1.png", "S4.png", "S2.png")]

W, H, FPS, SECS = 1920, 1080, 30, 12
N = FPS * SECS
BG = (17, 17, 20)
FG = (240, 240, 238)
DIM = (150, 152, 158)
ACCENT = (242, 112, 60)

EP_TITLE = sys.argv[1] if len(sys.argv) > 1 else "NEO"
EP_SUB = sys.argv[2] if len(sys.argv) > 2 else "The $499/Month Home Robot"


def sans(size, weight=700):
    f = ImageFont.truetype(str(FONTS / "InstrumentSans.ttf"), size)
    f.set_variation_by_axes([100, weight])
    return f


def mono(size):
    return ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), size)


def cover(img, w=W, h=H):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    return img.crop(((img.width - w) // 2, (img.height - h) // 2,
                     (img.width - w) // 2 + w, (img.height - h) // 2 + h))


def scrim(img, alpha):
    img.paste(Image.new("RGB", img.size, (0, 0, 0)), (0, 0), Image.new("L", img.size, alpha))
    return img


GLYPHS = "01<>[]{}#$%&*+=?ABCDEFXYZ"
random.seed(7)
COLS = [{"x": x, "y": random.randint(-H, 0), "v": random.randint(9, 22),
         "s": [random.choice(GLYPHS) for _ in range(40)]} for x in range(30, W, 64)]
GLYPH_FONT = mono(30)

desk = scrim(cover(Image.open(POSTERS / "desk.png").convert("RGB")), 90)
doorway = scrim(cover(Image.open(POSTERS / "doorway.png").convert("RGB")), 60)
flashes = [cover(Image.open(p).convert("RGB")) for p in FLASHES if p.exists()]

BRAND = "THE ROBOT DESK"


def frame(i: int) -> Image.Image:
    t = i / FPS
    if t < 3.0:                                     # A: glyph rain + type-on
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        fade = min(1.0, t / 0.5) * (1.0 if t < 2.5 else max(0.0, (3.0 - t) / 0.5))
        for c in COLS:
            y = (c["y"] + i * c["v"]) % (H + 400) - 200
            for k in range(14):
                gy = y - k * 34
                if -30 < gy < H:
                    a = max(0, 1 - k / 14) * fade
                    col = (int(ACCENT[0] * a * 0.55), int(ACCENT[1] * a * 0.55), int(ACCENT[2] * a * 0.55))
                    d.text((c["x"], gy), c["s"][(k + i // 3) % 40], font=GLYPH_FONT, fill=col)
        shown = BRAND[: int(len(BRAND) * min(1.0, t / 2.0))]
        cursor = "▌" if (i // 8) % 2 == 0 else " "
        f = mono(72)
        tw = d.textlength(shown + cursor, font=f)
        d.text(((W - tw) / 2, H / 2 - 50), shown + cursor, font=f, fill=FG)
        return img
    if t < 7.0:                                     # B: brand reveal on desk poster
        p = (t - 3.0) / 4.0
        z = 1.15 - 0.15 * min(1.0, p * 1.6)
        zw, zh = int(W * z), int(H * z)
        img = desk.resize((zw, zh), Image.BILINEAR).crop(
            ((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
        if t < 3.2:                                 # white impact flash
            img = ImageEnhance.Brightness(img).enhance(1 + (3.2 - t) * 6)
        d = ImageDraw.Draw(img)
        bar_w = int(W * min(1.0, p * 3))
        d.rectangle([0, 0, bar_w, 6], fill=ACCENT)
        if p > 0.08:
            a = min(1.0, (p - 0.08) / 0.15)
            d.text((W / 2 - d.textlength("WELCOME TO", font=mono(34)) / 2, 340),
                   "WELCOME TO", font=mono(34),
                   fill=tuple(int(c * a) for c in ACCENT))
        if p > 0.15:
            a = min(1.0, (p - 0.15) / 0.2)
            f = sans(140, 700)
            tw = d.textlength(BRAND, font=f)
            rise = int(30 * (1 - a))
            d.text(((W - tw) / 2, 420 + rise), BRAND, font=f,
                   fill=tuple(int(c * a) for c in FG))
        if p > 0.45:
            a = min(1.0, (p - 0.45) / 0.2)
            s = "HONEST MATH FOR THE ROBOT DECADE"
            d.text((W / 2 - d.textlength(s, font=mono(30)) / 2, 620), s,
                   font=mono(30), fill=tuple(int(c * a) for c in DIM))
        return img
    if t < 9.0 and flashes:                         # C: fast evidence flashes
        k = min(int((t - 7.0) / (2.0 / len(flashes))), len(flashes) - 1)
        img = flashes[k].copy()
        lt = ((t - 7.0) % (2.0 / len(flashes))) / (2.0 / len(flashes))
        if lt < 0.12:
            img = ImageEnhance.Brightness(img).enhance(1 + (0.12 - lt) * 10)
        return img
    # D: episode card on doorway poster
    p = min(1.0, (t - 9.0) / 0.8)
    img = doorway.copy()
    if t < 9.15:
        img = ImageEnhance.Brightness(img).enhance(1 + (9.15 - t) * 8)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    d.text((120, 330), "ON TODAY'S EPISODE", font=mono(36), fill=ACCENT)
    f = sans(min(230, int(230 * (0.6 + 0.4 * p))), 700)
    d.text((110, 400), EP_TITLE, font=f, fill=FG)
    if p >= 1.0:
        d.text((120, 680), EP_SUB, font=sans(54, 600), fill=DIM)
    return img


def build_sting(out: Path, vo: Path | None) -> None:
    sr = 44100
    n = sr * SECS
    t = np.arange(n) / sr
    audio = np.zeros(n)
    rng = np.random.default_rng(7)

    rise = rng.standard_normal(3 * sr) * np.linspace(0.02, 0.30, 3 * sr) ** 2  # noise riser 0-3s
    rise = np.convolve(rise, np.ones(24) / 24, mode="same")
    audio[: 3 * sr] += rise

    def boom(at, f0=62, dur=1.2, amp=0.8):
        i0 = int(at * sr)
        tt = np.arange(int(dur * sr)) / sr
        sig = np.sin(2 * np.pi * (f0 * (1 - 0.35 * tt / dur)) * tt) * np.exp(-3.2 * tt) * amp
        audio[i0:i0 + len(sig)] += sig[: max(0, n - i0)]

    boom(3.0)                                        # brand impact
    for k in range(8):                               # low pulse under phases B/C
        boom(3.75 + k * 0.75, f0=48, dur=0.35, amp=0.16)
    boom(9.0, f0=58, amp=0.9)                        # episode-card hit
    shimmer = np.sin(2 * np.pi * 660 * t) * 0.03 * np.exp(-np.maximum(0, t - 9.0)) * (t > 9.0)
    audio += shimmer
    audio = np.tanh(audio * 1.3)
    audio *= np.concatenate([np.ones(n - sr), np.linspace(1, 0.6, sr)])

    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((audio * 32767 * 0.7).astype(np.int16).tobytes())


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="intro_"))
    for i in range(N):
        frame(i).save(tmp / f"f{i:04d}.png")
    print(f"{N} frames rendered")

    sting = tmp / "sting.wav"
    build_sting(sting, None)

    human_vo = HERE / "vo-human.wav"
    if human_vo.exists():
        vo = human_vo
        dur = float(subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(vo)], capture_output=True, text=True, check=True).stdout)
        delay_ms = max(0, min(3400, int((N / FPS - dur - 0.4) * 1000)))
        print(f"VO: vo-human.wav (Brian's voice, {dur:.1f}s, delay {delay_ms}ms) + sting done")
    else:
        vo = tmp / "vo.mp3"
        vo_text = (f"Welcome to The Robot Desk. On today's episode: {EP_TITLE} — "
                   f"{EP_SUB.lower().replace('$499/month', 'four-ninety-nine-a-month')}.")
        import asyncio
        sys.path.insert(0, str(REPO / "tts"))
        import speak as sp
        asyncio.run(sp.synth(vo_text, sp.VOICES["brian"], 4, -4, vo))
        delay_ms = 3400
        print("VO + sting done")

    out = HERE / "intro.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
         "-i", str(sting), "-i", str(vo),
         "-filter_complex",
         f"[1:a]volume=0.9[s];[2:a]adelay={delay_ms}|{delay_ms},volume=1.0[v];"
         "[s][v]amix=inputs=2:duration=first:dropout_transition=3,"
         "alimiter=limit=0.95,aresample=48000[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)])
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    print(f"Done: {out} ({out.stat().st_size / 1e6:.1f} MB, {SECS}s)")


if __name__ == "__main__":
    main()
