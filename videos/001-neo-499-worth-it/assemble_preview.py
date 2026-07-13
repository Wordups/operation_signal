"""Video #001 — assemble the cut: narration + b-roll + slide builds + music -> mp4.

- B-roll: drop into broll/ named S1..S8 (.mp4/.mov clips, or .png/.jpg stills —
  stills get a slow Ken Burns push-in). Missing assets are skipped.
- Slide builds: each TIMELINE slide stem expands to its build frames
  (graphics/<stem>-b1.png ... <stem>.png) played in order.
- Music: drop music.mp3 / music.wav / music.m4a next to this script — it loops
  under the narration at low volume with fade in/out.

    python assemble_preview.py            # -> draft-preview.mp4
"""

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
NARR = HERE / "narration"
GFX = HERE / "graphics"
BROLL = HERE / "broll"
OUT = HERE / "draft-preview.mp4"

STILL_SECS = 6.0   # Ken Burns duration per b-roll still
CLIP_MAX = 8.0     # cap per b-roll video clip
MUSIC_VOL = 0.12   # music level under narration
FPS = 30

# section audio -> (broll slots shown first, slide stems filling the rest)
TIMELINE = [
    ("01-cold-open.mp3", ["S1"], ["00-title"]),
    ("02-what-youre-actually-buying.mp3", ["S2", "S3"], ["06-spec-card", "02-does-vs-doesnt"]),
    ("03-the-person-inside-the-robot.mp3", ["S4", "S5"], ["07-expert-mode"]),
    ("04-the-honest-math.mp3", ["S7"], ["01-subscription-math", "03-three-options"]),
    ("05-the-wait-math.mp3", ["S6"], ["08-cost-curve", "09-guard-act"]),
    ("06-the-verdict.mp3", ["S8"], ["04-verdict", "05-buy-signal"]),
    ("07-outro.mp3", [], ["10-sources"]),
]

VCODEC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
          "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", "-f", "mpegts"]
FIT = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
       "pad=1920:1080:(ow-iw)/2:(oh-ih)/2")


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


def render_still_kb(img: Path, secs: float, out: Path) -> None:
    render_ken_burns(img, secs, out, zoom=0.10)   # b-roll: noticeable push


def render_slide(img: Path, secs: float, out: Path) -> None:
    render_ken_burns(img, secs, out, zoom=0.035)  # slides: barely-alive drift


def render_clip(clip: Path, secs: float, out: Path) -> None:
    run(["-i", str(clip), "-t", f"{secs:.3f}",
         "-vf", f"{FIT},fps={FPS}", *VCODEC, str(out)])


def main() -> None:
    BROLL.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="assemble_"))
    segments: list[Path] = []
    audio_files: list[Path] = []
    total = 0.0
    n = 0

    for i, (mp3, slots, slide_stems) in enumerate(TIMELINE):
        audio = NARR / mp3
        if not audio.exists():
            sys.exit(f"missing narration: {audio}")
        d = ffprobe_dur(audio)
        total += d
        audio_files.append(audio)

        slide_frames = [f for stem in slide_stems for f in expand_slides(stem)]

        pieces = []  # (kind, path, secs)
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
        per_frame = remaining / len(slide_frames)
        for f in slide_frames:
            pieces.append(("slide", f, per_frame))
        if i == len(TIMELINE) - 1:  # tail buffer so -shortest trims video, not audio
            kind, path, secs = pieces[-1]
            pieces[-1] = (kind, path, secs + 1.5)

        for kind, path, secs in pieces:
            n += 1
            seg = tmp / f"seg{n:03d}.ts"
            {"still": render_still_kb, "slide": render_slide, "clip": render_clip}[kind](path, secs, seg)
            segments.append(seg)
            print(f"  [{mp3[:2]}] {kind:5s} {path.name:36s} {secs:5.1f}s")

    concat_v = tmp / "video.txt"
    concat_v.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    concat_a = tmp / "audio.txt"
    concat_a.write_text("".join(f"file '{a.as_posix()}'\n" for a in audio_files), encoding="utf-8")

    music = find_music()
    print(f"Muxing {len(segments)} segments, {total / 60:.2f} min narration"
          + (f", music: {music.name}" if music else ", no music") + "...")
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


if __name__ == "__main__":
    main()
