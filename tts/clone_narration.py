"""Generate narration in Brian's cloned voice with Chatterbox (local, CPU).

Usage:
  python tts/clone_narration.py videos/001-neo-499-worth-it [section ...]

Reads section text from script-recording.txt (spoken words only), clones from
voice-ref.wav (12s of Brian), writes narration-clone/<section>.wav.
Sections default to all five. CPU generation is slow — expect several
minutes per finished minute of audio.
"""

import re
import sys
from pathlib import Path

SECTIONS = {
    "01": "01-cold-open",
    "02": "02-the-machine-and-the-waitlist",
    "03": "03-the-person-inside",
    "04": "04-the-honest-math",
    "05": "05-the-verdict",
}
PAUSE_SENT = 0.25   # extra silence between sentences
PAUSE_PARA = 0.6    # extra silence between paragraphs


def load_sections(txt: Path) -> dict[str, list[str]]:
    """Parse script-recording.txt -> {key: [paragraph, ...]}."""
    raw = txt.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^(\d\d) — .*?\n=+\n(.*?)(?=\n=+\n|\Z)", raw, re.S | re.M):
        key, body = m.group(1), m.group(2)
        if key not in SECTIONS:
            continue
        paras = [re.sub(r"\s+", " ", p).strip()
                 for p in body.split("\n\n") if p.strip() and not p.strip().startswith("(")]
        out[key] = paras
    return out


def sentences(para: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", para)
    # merge tiny fragments into the previous sentence
    merged = []
    for p in parts:
        if merged and len(p) < 25:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged


def main() -> None:
    import numpy as np
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    video = Path(sys.argv[1]).resolve()
    only = set(sys.argv[2:]) or set(SECTIONS)
    ref = video / "voice-ref.wav"
    if not ref.exists():
        sys.exit(f"missing reference clip: {ref}")
    script = load_sections(video / "script-recording.txt")
    missing = [k for k in only if k not in script]
    if missing:
        sys.exit(f"sections not found in script-recording.txt: {missing}")

    out_dir = video / "narration-clone"
    out_dir.mkdir(exist_ok=True)

    model = ChatterboxTTS.from_pretrained(device="cpu")
    sr = model.sr

    for key in sorted(only):
        chunks = []
        paras = script[key]
        n_sent = sum(len(sentences(p)) for p in paras)
        done = 0
        for pi, para in enumerate(paras):
            for sent in sentences(para):
                wav = model.generate(sent, audio_prompt_path=str(ref),
                                     exaggeration=0.45, cfg_weight=0.5)
                chunks.append(wav.squeeze(0))
                chunks.append(torch.zeros(int(sr * PAUSE_SENT)))
                done += 1
                print(f"  [{key}] {done}/{n_sent}: {sent[:60]}", flush=True)
            if pi < len(paras) - 1:
                chunks.append(torch.zeros(int(sr * PAUSE_PARA)))
        audio = torch.cat(chunks).unsqueeze(0)
        dst = out_dir / f"{SECTIONS[key]}.wav"
        torchaudio.save(str(dst), audio, sr)
        print(f"{dst.name}: {audio.shape[1] / sr:.1f}s", flush=True)


if __name__ == "__main__":
    main()
