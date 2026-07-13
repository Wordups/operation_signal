#!/usr/bin/env python3
"""Operation SIGNAL — TTS machine.

Turns a plain-text script into narration MP3 using Microsoft neural voices.
No character limit, no cost. Usage:

    python speak.py script.txt                        # -> script.mp3, default voice
    python speak.py script.txt -v brian               # different voice
    python speak.py script.txt -r -8 -o narration.mp3 # 8% slower, custom output
    python speak.py --voices                          # list narration voices
"""

import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

import edge_tts

# Curated narration voices (male/female, US). Keys are shorthand.
VOICES = {
    "andrew": "en-US-AndrewMultilingualNeural",  # natural, warm — default
    "brian": "en-US-BrianMultilingualNeural",    # calm, conversational
    "christopher": "en-US-ChristopherNeural",    # deeper, authoritative
    "guy": "en-US-GuyNeural",                    # classic narrator
    "ava": "en-US-AvaMultilingualNeural",        # natural female
    "aria": "en-US-AriaNeural",                  # bright female
    "emma": "en-US-EmmaMultilingualNeural",      # warm female
}

# ElevenLabs shorthand -> voice ID. Fill in after picking from `--engine eleven --voices`.
ELEVEN_VOICES = {
    # "robotdesk": "PASTE_VOICE_ID",   # channel voice, once chosen/cloned
}
ELEVEN_MODEL = "eleven_multilingual_v2"


def eleven_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        sys.exit("set ELEVENLABS_API_KEY environment variable first "
                 "(ElevenLabs -> Profile -> API keys)")
    return key


def eleven_list_voices() -> None:
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": eleven_key()})
    data = json.load(urllib.request.urlopen(req))
    for v in data.get("voices", []):
        labels = ", ".join(f"{k}:{x}" for k, x in (v.get("labels") or {}).items())
        print(f"  {v['voice_id']}  {v['name']:<22} {labels}")


def synth_eleven(text: str, voice: str, out: Path) -> None:
    voice_id = ELEVEN_VOICES.get(voice.lower(), voice)
    body = json.dumps({
        "text": text,
        "model_id": ELEVEN_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=body, method="POST",
        headers={"xi-api-key": eleven_key(),
                 "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req) as r, open(out, "wb") as f:
        f.write(r.read())


async def synth(text: str, voice: str, rate: int, pitch: int, out: Path) -> None:
    rate_s = f"{rate:+d}%"
    pitch_s = f"{pitch:+d}Hz"
    communicate = edge_tts.Communicate(text, voice, rate=rate_s, pitch=pitch_s)
    with open(out, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


def main() -> None:
    p = argparse.ArgumentParser(description="Text file -> narration MP3")
    p.add_argument("script", nargs="?", help="path to plain-text script")
    p.add_argument("-v", "--voice", default="andrew",
                   help="voice shorthand (see --voices) or full Azure voice name")
    p.add_argument("-r", "--rate", type=int, default=0, help="speed adjust in %% (e.g. -8 slower, 10 faster)")
    p.add_argument("-p", "--pitch", type=int, default=0, help="pitch adjust in Hz (e.g. -5)")
    p.add_argument("-o", "--out", help="output mp3 path (default: script name .mp3)")
    p.add_argument("--voices", action="store_true", help="list curated voices and exit")
    args = p.parse_args()

    if args.voices:
        for k, v in VOICES.items():
            print(f"  {k:<12} {v}")
        return

    if not args.script:
        p.error("give me a text file (or --voices)")

    src = Path(args.script)
    if not src.exists():
        sys.exit(f"file not found: {src}")

    text = src.read_text(encoding="utf-8-sig").strip()
    if not text:
        sys.exit("script file is empty")

    voice = VOICES.get(args.voice.lower(), args.voice)
    out = Path(args.out) if args.out else src.with_suffix(".mp3")

    words = len(text.split())
    print(f"Script: {src.name} — {len(text):,} chars, {words:,} words (~{words / 145:.1f} min)")
    print(f"Voice:  {voice}  rate {args.rate:+d}%  pitch {args.pitch:+d}Hz")

    asyncio.run(synth(text, voice, args.rate, args.pitch, out))

    size_kb = out.stat().st_size / 1024
    print(f"Done:   {out}  ({size_kb:,.0f} KB)")


if __name__ == "__main__":
    main()
