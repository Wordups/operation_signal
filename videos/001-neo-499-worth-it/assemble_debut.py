"""Video #001 DEBUT CUT (~7 min) — narration-debut/ + b-roll + slide builds + music -> debut-preview.mp4.

Same engine as assemble_preview.py with the debut timeline.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
NARR = HERE / "narration-debut"
NARR_HUMAN = HERE / "narration-human"
GFX = HERE / "graphics"
BROLL = HERE / "broll"
OUT = HERE / "debut-preview.mp4"

STILL_SECS = 6.0
CLIP_MAX = 8.0
MUSIC_VOL = 0.12
FPS = 30

TIMELINE = [
    ("01-cold-open.mp3", ["S1"], ["00-title"]),
    ("02-the-machine-and-the-waitlist.mp3", ["S2", "S3"], ["06-spec-card", "02-does-vs-doesnt"]),
    ("03-the-person-inside.mp3", ["S4", "S5"], ["07-expert-mode"]),
    ("04-the-honest-math.mp3", ["S7"], ["01-subscription-math", "03-three-options", "08-cost-curve"]),
    ("05-the-verdict.mp3", ["S8"], ["04-verdict", "05-buy-signal", "10-sources"]),
]

VCODEC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
          "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", "-f", "mpegts"]

# source labels for video-clip evidence frames (stills are pre-framed by prep_broll)
SLOT_LABELS = {
    "S1": "SOURCE: 1X — NEO PROMO FILM",
    "S2": "SOURCE: 1X.TECH",
    "S3": "SOURCE: 1X.TECH",
    "S4": "SOURCE: 1X — NEO PROMO FILM",
    "S5": "SOURCE: 1X — NEO APP",
    "S6": "SOURCE: 1X — FACTORY FILM",
    "S7": "SOURCE: 1X — NEO PROMO FILM",
    "S8": "SOURCE: 1X — NEO PROMO FILM",
}


AUDIO_EXTS = (".wav", ".mp3", ".m4a")


def find_audio(narr_dir: Path, name: str) -> Path | None:
    stem = Path(name).stem
    for ext in AUDIO_EXTS:
        p = narr_dir / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def pick_narration() -> Path:
    """Brian's recordings win over TTS once all sections are present."""
    if all(find_audio(NARR_HUMAN, mp3) for mp3, _, _ in TIMELINE):
        return NARR_HUMAN
    return NARR


def ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def find_broll(slot: str) -> Path | None:
    for ext in (".mp4", ".mov", ".png", ".jpg", ".jpeg"):
        p = BROLL / f"{slot}{ext}"
        if p.exists():
            return p
    return None


def find_music() -> Path | None:
    for ext in (".mp3", ".wav", ".m4a"):
        p = HERE / f"music{ext}"
        if p.exists():
            return p
    return None


def expand_slides(stem: str) -> list[Path]:
    frames = sorted(GFX.glob(f"{stem}*.png"))
    if not frames:
        sys.exit(f"no slide frames match graphics/{stem}*.png")
    return frames


def run(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def render_ken_burns(img: Path, secs: float, out: Path, zoom: float) -> None:
    frames = int(secs * FPS)
    zp = (f"scale=2880:1620:force_original_aspect_ratio=increase,"
          f"crop=2880:1620,"
          f"zoompan=z='1+{zoom}*on/{frames}':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={FPS}")
    run(["-loop", "1", "-t", f"{secs:.3f}", "-i", str(img),
         "-vf", zp, "-t", f"{secs:.3f}", *VCODEC, str(out)])


def evidence_canvas(label: str, tmp: Path) -> Path:
    """Empty evidence-frame canvas (dot grid, crosshairs, chip, mark) for clip overlay."""
    from PIL import Image, ImageDraw, ImageFont
    fonts = HERE.parent.parent / "fonts"
    W2, H2 = 1920, 1080
    BGc, GRID, DIMc, CHIP, ACC = (17, 17, 20), (38, 39, 44), (150, 152, 158), (28, 31, 36), (242, 112, 60)
    img = Image.new("RGB", (W2, H2), BGc)
    d = ImageDraw.Draw(img)
    for gx in range(60, W2, 120):
        for gy in range(60, H2, 120):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=GRID)
    x0, y0, fw, fh = 264, 108, 1392, 778   # inset window (16:9)
    d.rectangle([x0 - 1, y0 - 1, x0 + fw, y0 + fh], outline=GRID, width=2)
    for cx, cy in [(x0 - 60, y0 + 40), (x0 - 60, y0 + fh - 40),
                   (x0 + fw + 60, y0 + 40), (x0 + fw + 60, y0 + fh - 40)]:
        d.line([cx - 14, cy, cx + 14, cy], fill=GRID, width=3)
        d.line([cx, cy - 14, cx, cy + 14], fill=GRID, width=3)
    f = ImageFont.truetype(str(fonts / "IBMPlexMono-Medium.ttf"), 26)
    cy0 = y0 + fh + 36
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([x0, cy0, x0 + tw + 36, cy0 + 52], 10, fill=CHIP)
    d.text((x0 + 18, cy0 + 11), label, font=f, fill=DIMc)
    mark = "THE ROBOT DESK"
    mw = d.textlength(mark, font=f)
    d.text((x0 + fw - mw, cy0 + 11), mark, font=f, fill=ACC)
    p = tmp / f"canvas-{abs(hash(label))}.png"
    img.save(p)
    return p


def render_clip(clip: Path, secs: float, out: Path, label: str, tmp: Path) -> None:
    """Video clip composited into the evidence frame."""
    canvas = evidence_canvas(label, tmp)
    run(["-loop", "1", "-i", str(canvas), "-i", str(clip),
         "-filter_complex",
         f"[1:v]scale=1392:778:force_original_aspect_ratio=decrease,"
         f"pad=1392:778:(ow-iw)/2:(oh-ih)/2,fps={FPS}[c];"
         f"[0:v][c]overlay=264:108:shortest=0,fps={FPS}",
         "-t", f"{secs:.3f}", *VCODEC, str(out)])


def main() -> None:
    BROLL.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="debut_"))
    segments, audio_files = [], []
    total, n = 0.0, 0

    narr_dir = pick_narration()
    print(f"Narration: {narr_dir.name}"
          + (" (Brian's voice)" if narr_dir is NARR_HUMAN else " (TTS)"))
    for i, (mp3, slots, slide_stems) in enumerate(TIMELINE):
        audio = find_audio(narr_dir, mp3)
        if audio is None:
            sys.exit(f"missing narration: {narr_dir / mp3}")
        d = ffprobe_dur(audio)
        total += d
        audio_files.append(audio)
        slide_frames = [f for stem in slide_stems for f in expand_slides(stem)]

        pieces = []
        remaining = d
        for slot in slots:
            asset = find_broll(slot)
            if asset is None:
                continue
            if asset.suffix.lower() in (".mp4", ".mov"):
                secs = min(ffprobe_dur(asset), CLIP_MAX, remaining - 3 * len(slide_frames))
                kind = "clip"
            else:
                secs = min(STILL_SECS, remaining - 3 * len(slide_frames))
                kind = "still"
            if secs >= 2.0:
                pieces.append((kind, asset, secs))
                remaining -= secs
        per = remaining / len(slide_frames)
        pieces += [("slide", f, per) for f in slide_frames]
        if i == len(TIMELINE) - 1:
            kind, path, secs = pieces[-1]
            pieces[-1] = (kind, path, secs + 1.5)

        for kind, path, secs in pieces:
            n += 1
            seg = tmp / f"seg{n:03d}.ts"
            if kind == "clip":
                render_clip(path, secs, seg, SLOT_LABELS.get(path.stem, "SOURCE: ARCHIVE"), tmp)
            else:
                render_ken_burns(path, secs, seg, zoom=0.10 if kind == "still" else 0.035)
            segments.append(seg)
            print(f"  [{mp3[:2]}] {kind:5s} {path.name:36s} {secs:5.1f}s")

    concat_v = tmp / "video.txt"
    concat_v.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    concat_a = tmp / "audio.txt"
    concat_a.write_text("".join(f"file '{a.as_posix()}'\n" for a in audio_files), encoding="utf-8")

    music = find_music()
    print(f"Muxing {len(segments)} segments, {total / 60:.2f} min narration"
          + (f", music: {music.name}" if music else "") + "...")
    if music:
        fade_out = max(total - 4.0, 0)
        run(["-f", "concat", "-safe", "0", "-i", str(concat_v),
             "-f", "concat", "-safe", "0", "-i", str(concat_a),
             "-stream_loop", "-1", "-i", str(music),
             "-filter_complex",
             f"[2:a]volume={MUSIC_VOL},afade=t=in:d=3,"
             f"afade=t=out:st={fade_out:.2f}:d=4[m];"
             f"[1:a][m]amix=inputs=2:duration=first:dropout_transition=3,"
             f"alimiter=limit=0.95[a]",
             "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(OUT)])
    else:
        run(["-f", "concat", "-safe", "0", "-i", str(concat_v),
             "-f", "concat", "-safe", "0", "-i", str(concat_a),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(OUT)])

    for s in tmp.iterdir():
        s.unlink()
    tmp.rmdir()
    print(f"Done: {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {total / 60:.2f} min)")

    intro = HERE.parent.parent / "intro" / "intro.mp4"
    if intro.exists():
        final = HERE / "debut-final.mp4"
        run(["-i", str(intro), "-i", str(OUT),
             "-filter_complex",
             "[0:v]fps=30,scale=1920:1080[v0];[1:v]fps=30,scale=1920:1080[v1];"
             "[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];"
             "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
             "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", str(final)])
        print(f"With intro: {final} ({final.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
