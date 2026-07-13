#!/usr/bin/env python3
"""Operation SIGNAL — placeholder ambient underscore generator.

Slow two-chord synth pad, documentary-neutral, meant to sit at ~-18 dB under
narration. Swap for a licensed track before upload if you want a real score.

    python make_music.py out.wav [minutes]
"""

import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100


def pad(freqs: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Detuned-sine pad with gentle per-voice movement."""
    sig = np.zeros_like(t)
    for i, f in enumerate(freqs):
        for det in (-1.5, 0.0, 1.5):  # cents-ish detune -> slow chorus
            fd = f * (1 + det / 1200)
            lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.031 + 0.017 * i) * t + i * 1.7)
            sig += lfo * np.sin(2 * np.pi * fd * t + i)
    return sig / (len(freqs) * 3)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("music.wav")
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
    n = int(SR * 60 * minutes)
    t = np.arange(n) / SR

    chord_a = np.array([110.00, 164.81, 220.00, 329.63])   # A2 E3 A3 E4
    chord_b = np.array([146.83, 220.00, 293.66, 369.99])   # D3 A3 D4 F#4
    xfade = 0.5 + 0.5 * np.sin(2 * np.pi * t / 40.0)        # 40 s chord cycle
    sig = xfade * pad(chord_a, t) + (1 - xfade) * pad(chord_b, t)

    # soft top-end shimmer, very quiet
    sig += 0.04 * np.sin(2 * np.pi * 659.26 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.011 * t))

    # gentle fades and safe level
    fade = int(SR * 4)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    sig = np.tanh(sig * 1.2) * env * 0.5

    data = (sig * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"Done: {out} ({minutes:.1f} min)")


if __name__ == "__main__":
    main()
