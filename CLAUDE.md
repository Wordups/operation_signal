# Operation SIGNAL — The Robot Desk

Faceless YouTube channel, humanoid-robot **buyer** lane. `BLUEPRINT.md` (repo root) is the governing doc — read it before doing anything substantive. Non-negotiables: HUMAN_PASS gate on every script (Brian rewrites by hand, never automate), C-1 disclosure toggle on every upload, warm "on team robot" tone (never a hit piece).

## Where the project lives

- **Canonical working copy:** iCloud Drive → `operation signal` (Mac: `~/Library/Mobile Documents/com~apple~CloudDocs/operation signal`). Work there so outputs sync.
- **Git remote:** https://github.com/Wordups/operation_signal — the `.git` is inside the iCloud folder. Commit+push before switching machines, pull after. Rendered videos (`debut-*.mp4`, `draft-preview.mp4`) and `Narration/files.zip` are gitignored — they exist only in iCloud.

## CURRENT TASK — finish the voice clone (handed off from the PC 2026-07-13)

Goal: video #1 debut cut narrated in Brian's **cloned** voice (supersedes both the edge-tts voice and the human takes in `narration-human/`).

State: `tts/clone_narration.py` is ready (Chatterbox; auto-uses MPS on Apple Silicon, else CPU). `videos/001-neo-499-worth-it/voice-ref.wav` is the reference (20s cut at 90s offset from `Narration/files/TheRobotDesk_Voice_Training_Master.wav`; the old 14s ref is `voice-ref-v1.wav`). `narration-clone/` is **empty** — nothing generated yet.

Steps:

1. Setup (once): `python3 -m venv .venv && source .venv/bin/activate && pip install chatterbox-tts`. Also `brew install ffmpeg` if missing (needed for assembly).
2. Generate section 01 first and have Brian listen before burning time on all five:
   `python tts/clone_narration.py videos/001-neo-499-worth-it 01`
3. If the voice passes, generate the rest: `python tts/clone_narration.py videos/001-neo-499-worth-it 02 03 04 05`
   Output lands in `videos/001-neo-499-worth-it/narration-clone/<section>.wav`. Text comes from `script-recording.txt` (5 sections, ~1246 words).
4. Rebuild the debut: `python videos/001-neo-499-worth-it/assemble_debut.py`. `pick_narration()` now prefers `narration-clone/` over `narration-human/` over TTS once all 5 sections exist. Intro VO stays Brian's human take (`intro/vo-human.wav`).
5. Re-measure the chapter timestamps in `videos/001-neo-499-worth-it/upload-package.md` (narration durations will have shifted; chapters are butt-joined after the 12s intro).
6. Brian watches/listens before anything ships — then: register channel, affiliate links, upload per `upload-package.md`.

Tuning knobs if the clone sounds off: `exaggeration=0.45, cfg_weight=0.5` in `clone_narration.py`; or re-cut `voice-ref.wav` from a different offset in the training master (Chatterbox only conditions on roughly the first 10s of the ref).
