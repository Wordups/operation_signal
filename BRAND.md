# Robot Desk — BRAND.md

**v0.1 — 2026-07-09.** Only rules that shipped work has proven. One video = a few earned lines. Do not add speculative rules; the long-term structure lives in `BRAND-OS-VISION.md` and graduates here only after a published video validates it.

## Identity
- Channel: **Robot Desk** — humanoid robots, consumer BUYER lane (worth-it / vs / price analysis). Never the enthusiast-news lane.
- Stance: "Dark door, warm room" (`TITLE-MECHANICS.md`) — title sells from the sharp tier, body is on-team-robot honest math.
- The differentiator paragraph (Brian, HUMAN-PASS-NOTES.md): fascinated by robotics, covering it like it's too important to treat as a gadget launch; cybersecurity lens (who has camera access, what data leaves, how are sessions authenticated).

## Editorial standards (proven in #001)
- Every claim: primary source > press > social. Named institutions only ("Goldman Sachs watched…"), never "analysts say."
- Hedge what isn't primary-sourced ("a reported six-month minimum"). Rather hedge than overstate.
- Facts get dated: verify within ~2 weeks of upload; prices/specs in this niche rot in weeks.
- Never claim owner reviews/experiences that don't exist. Say what a demo actually was (e.g., "100% teleoperated").
- `HUMAN_PASS` gate on every script (C-2). Brian's pass arrives as prose notes — transcribe his words verbatim into the script; never ghost-write his take.

## Voice
- **Channel voice (LOCKED 2026-07-10): edge-tts `brian` (en-US-BrianMultilingualNeural), rate +4%, pitch -4Hz** — "The Insider": approachable, sincere, slightly deepened. Brian's pick after 7-voice + 4-pitch A/B. (Andrew -8% deprecated — read as slow/low-confidence at documentary length.)
- Effective pace ≈ 180 wpm at these settings → 7 min ≈ 1,250 words; 20 min ≈ 3,600.
- Known ceiling: edge-tts still reads as AI to attentive ears (C-1 disclosed). Upgrade path when ready: ElevenLabs / recorded own voice.
- Short sentences at section turns = retention resets; don't smooth them.
- Numbers written as words in narration text ("twenty thousand," "four ninety-nine").

## Visual system (v1 — synced from Claude Design, 2026-07-09)
- Source of truth: `Design/the-robot-desk-video-graphics.pptx` (Claude Design export) + share link in project.
- Tokens: BG `#111114`, card `#1C1F24`, card-alt `#2C2F36`, FG `#F0F0EE`, dim `#96989E`; **accent orange `#F2703C`** (one accent per composition); amber `#E3A94A` (mid-tier), green `#50C878`, red `#EB5A5A`.
- Type: **Instrument Sans** (variable, weights 400/600/700) for headings/body; **IBM Plex Mono** for eyebrow labels, numbering, and source dates. Fonts vendored in `fonts/` (OFL).
- Slide anatomy: 6px orange top bar → mono eyebrow "THE ROBOT DESK" → Instrument Sans 700 title; rounded-24 cards; numbered sources with mono dates + credo footer "Every claim primary-sourced or hedged."
- **Evidence frames** (all third-party footage/screenshots — Bloomberg Primer grammar, see `kb/formats/bloomberg-primer.md`): inset ~72% on brand canvas with faint dot grid, registration crosshairs, mono SOURCE chip bottom-left, orange "THE ROBOT DESK" mark bottom-right. Never show third-party material full-bleed. Implemented in `prep_broll.py`.
- **Poster theme (v1.1):** slides composite over the four cinematic set-piece backgrounds (`graphics/posters/`: doorway, pedestals, bands, desk — from `Design/the-robot-desk-video-graphics-poster-theme.pptx`) with a black legibility scrim (~130–165 alpha, tuned per poster). Poster-to-content mapping: doorway → product/spec/buy-signal; pedestals → money/market; bands → verdict; desk → analysis/sources/title-adjacent. Title cards use the doorway's left negative space, eyebrow + Instrument Sans 96 two-line title.
- **Motion:** nothing static — slides drift at 3.5% push-in, b-roll at 10%, generated per-segment in the assembler. Slow, elegant, never flashy.
- Wider direction (Claude Design brief): light-premium for web/thumbnails (#FFFFFF/#F7F7F5/#111111); video graphics use this dark variant.
- B-roll prompt style block (see `videos/001-*/broll-prompts.md`): cinematic documentary, photorealistic, shallow DOF, warm muted palette + dark teal shadows, slow deliberate camera, 35mm grain; robot movement slow and careful, never menacing; no text/logos.
- Stills get slow Ken Burns push-ins (assembler does this automatically).

## Skeleton log (C-3 — no consecutive reuse)
| # | Video | Skeleton |
|---|---|---|
| 001 | NEO $499 worth it | cold-open question → teardown → math → verdict |
| 002 | (planned) | MUST differ — candidates: timeline, investigation, day-in-the-life |

## Pipeline (per video)
```
python tts/make_narration.py videos/<id>/script-final.md     # sections -> txt + mp3
python videos/<id>/graphics/make_slides.py                   # slide deck
python videos/<id>/assemble_preview.py                       # broll/ + slides + narration -> mp4
```
- TTS gotcha: edge-tts occasionally truncates a section silently — check each MP3's duration against words/155wpm and regenerate outliers.

## Compliance quick list
- C-1: "altered or synthetic content" toggle ON every upload; disclosure line in every description.
- C-2: HUMAN_PASS before voicing; drafts saved unchanged as evidence.
- C-3: skeleton logged per video (table above), never repeated consecutively.
