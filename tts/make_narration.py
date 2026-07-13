#!/usr/bin/env python3
"""Operation SIGNAL — script-to-narration pipeline.

Reads a production-master script markdown, extracts the narration text
per section (dropping B-ROLL/GRAPHIC cues, ad-break markers, headers),
writes numbered .txt files and voices each one with edge-tts.

    python make_narration.py <script-final.md> [-v andrew] [-r -8] [-o narration_dir]

Narration lands next to the script in narration/NN-section-name.{txt,mp3}.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from speak import VOICES, synth  # noqa: E402


def slugify(heading: str) -> str:
    name = heading.split("(")[0]
    name = re.sub(r"SECTION \d+\s*[—-]\s*", "", name)
    name = re.sub(r"[^A-Za-z0-9 ]", "", name).strip().lower()
    return re.sub(r"\s+", "-", name)


def extract_sections(md: str) -> list[tuple[str, str]]:
    """Return [(slug, narration_text)] from the SCRIPT block of a master doc."""
    m = re.search(r"^# SCRIPT\s*$(.*?)^# DESCRIPTION", md, re.M | re.S)
    if not m:
        sys.exit("could not find '# SCRIPT' ... '# DESCRIPTION' block")
    block = m.group(1)

    sections: list[tuple[str, list[str]]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            sections.append((slugify(stripped[4:]), []))
            continue
        if not sections:
            continue
        # drop cues, ad markers, dividers, empty lines
        if not stripped or stripped == "---":
            sections[-1][1].append("")
            continue
        if re.match(r"^\**\[(B-ROLL|GRAPHIC|AD BREAK)", stripped, re.I):
            continue
        sections[-1][1].append(stripped)

    out = []
    for slug, lines in sections:
        text = "\n".join(lines)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # unbold
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            out.append((slug, text))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Master script -> per-section narration MP3s")
    p.add_argument("script", help="path to production master markdown")
    p.add_argument("-v", "--voice", default="andrew")
    p.add_argument("-r", "--rate", type=int, default=-8)
    p.add_argument("-p", "--pitch", type=int, default=0)
    p.add_argument("-o", "--outdir", help="output dir (default: <script dir>/narration)")
    p.add_argument("--dry-run", action="store_true", help="write .txt files only, skip TTS")
    args = p.parse_args()

    src = Path(args.script)
    if not src.exists():
        sys.exit(f"file not found: {src}")
    outdir = Path(args.outdir) if args.outdir else src.parent / "narration"
    outdir.mkdir(exist_ok=True)

    voice = VOICES.get(args.voice.lower(), args.voice)
    sections = extract_sections(src.read_text(encoding="utf-8-sig"))
    total_words = 0

    for i, (slug, text) in enumerate(sections, 1):
        stem = f"{i:02d}-{slug}"
        txt = outdir / f"{stem}.txt"
        txt.write_text(text + "\n", encoding="utf-8")
        words = len(text.split())
        total_words += words
        print(f"{stem}: {words:,} words (~{words / 145:.1f} min)")
        if not args.dry_run:
            mp3 = outdir / f"{stem}.mp3"
            asyncio.run(synth(text, voice, args.rate, args.pitch, mp3))
            print(f"  -> {mp3.name} ({mp3.stat().st_size / 1024:,.0f} KB)")

    print(f"\nTotal: {total_words:,} words (~{total_words / 145:.1f} min @145wpm, longer at rate {args.rate:+d}%)")


if __name__ == "__main__":
    main()
