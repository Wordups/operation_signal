"""Prep Brian's raw voice takes for the assembler.

Usage: python tts/prep_human_narration.py videos/001-neo-499-worth-it

Reads narration-raw/ (files named by section number: 01.wav, 02.m4a, ...),
trims leading/trailing silence, loudness-normalizes to -16 LUFS (YouTube voice
standard), writes narration-human/<full-section-name>.wav ready for
assemble_debut.py. Also handles intro-vo.* -> ../../intro/vo-human.wav.
"""

import subprocess
import sys
from pathlib import Path

SECTIONS = {
    "01": "01-cold-open",
    "02": "02-the-machine-and-the-waitlist",
    "03": "03-the-person-inside",
    "04": "04-the-honest-math",
    "05": "05-the-verdict",
}
EXTS = (".wav", ".m4a", ".mp3", ".aac", ".flac", ".ogg")

FILTERS = (
    "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.3,"
    "areverse,"
    "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.4,"
    "areverse,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)


def find_take(raw: Path, key: str) -> Path | None:
    for p in sorted(raw.iterdir()):
        if p.suffix.lower() in EXTS and p.stem.split("-")[0].split("_")[0] == key:
            return p
    return None


def convert(src: Path, dst: Path) -> float:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-af", FILTERS, "-ar", "48000", "-ac", "1", str(dst)],
        check=True,
    )
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(dst)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    video = Path(sys.argv[1]).resolve()
    raw = video / "narration-raw"
    if not raw.is_dir():
        sys.exit(f"create {raw} and drop takes in it (01.wav, 02.m4a, ...)")
    out = video / "narration-human"
    out.mkdir(exist_ok=True)

    done, missing = [], []
    for key, name in SECTIONS.items():
        take = find_take(raw, key)
        if take is None:
            missing.append(f"{key} ({name})")
            continue
        secs = convert(take, out / f"{name}.wav")
        done.append(name)
        print(f"  {take.name:20s} -> {name}.wav  {secs:6.1f}s")

    intro_take = next((p for p in sorted(raw.iterdir())
                       if p.stem.lower().startswith("intro") and p.suffix.lower() in EXTS), None)
    if intro_take:
        dst = video.parent.parent / "intro" / "vo-human.wav"
        secs = convert(intro_take, dst)
        print(f"  {intro_take.name:20s} -> intro/vo-human.wav  {secs:6.1f}s  (re-run intro/make_intro.py)")

    if missing:
        print(f"\nStill missing: {', '.join(missing)}")
        print("Assembler keeps using narration-debut/ (TTS) until all 5 are present.")
    else:
        print(f"\nAll 5 sections ready in {out.name}/ — re-run assemble_debut.py.")


if __name__ == "__main__":
    main()
