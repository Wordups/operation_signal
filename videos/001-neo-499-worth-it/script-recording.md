# VIDEO #001 — RECORDING SCRIPT (Brian's voice)

Teleprompter cut of `script-debut-7min.md` — spoken words only, no stage directions. Same HUMAN_PASS-approved text the edge-tts debut used.

## How to record

- **One file per section** (5 sections + optional intro line). Flub a line → pause two seconds, restart that sentence or just redo the section; they're all under two minutes.
- **Mic:** whatever you have, 6–8 inches away, slightly off to the side. Small room with soft stuff in it (closet full of clothes is a pro booth). Kill fans/HVAC.
- **Format:** WAV or highest-quality voice memo; 48kHz if the app asks. Don't worry about levels — the prep script normalizes.
- **Pace:** conversational, ~160 wpm. Reference durations from the TTS version are listed per section, but they're only a sanity check — the assembler re-times all visuals to *your* audio automatically. Do not rush to match them.
- **Tone:** you're on team robot. Smile on the cold open and the verdict; the fine-print sections can flatten a little. Short sentences at section turns are retention resets — let them punch, don't smooth them.
- Read numbers exactly as written ("four ninety-nine," "twenty twenty-eight").

## After recording

Drop raw files in `narration-raw/` named by section number (any of wav/m4a/mp3, e.g. `01.wav`, `02.m4a`), then:

```
python tts/prep_human_narration.py videos/001-neo-499-worth-it   # normalize + trim -> narration-human/
python videos/001-neo-499-worth-it/assemble_debut.py             # auto-prefers narration-human/
```

C-1 note: with your voice, narration is no longer synthetic but the visuals still are — keep the Studio toggle ON, and swap the description line to: "Some visuals in this video are AI-generated, disclosed per YouTube policy."

---

## 00 — INTRO LINE (optional, ~8s — replaces the synthetic VO in the 12s branded open)

Welcome to The Robot Desk. On today's episode: NEO — the four ninety-nine a month home robot.

*(Save as `intro-vo.wav` → goes in `G:\dev\operation-signal\intro\vo-human.wav`, then re-run `python intro/make_intro.py` and the assembler.)*

---

## 01 — COLD OPEN (TTS reference: 0:35)

I have wanted a robot in my house since I was about eight years old. And this year, for the first time ever, that's an actual product: five hundred dollars a month, and a five-foot-six humanoid robot is yours. I'm fully on team robot. But I read the spec sheets, the demos, and the fine print — and there are three things in there that completely change the math. One of them: nobody who ordered this robot actually has one yet. Another involves a person, in an office somewhere, who can see through its eyes. By the end of this video you'll know whether the smart move is buy, subscribe — or wait for a date I'll put on screen.

---

## 02 — THE MACHINE AND THE WAITLIST (TTS reference: 1:28)

The robot is called NEO, made by 1X — a Norwegian-American company backed early by OpenAI money. Two ways in: twenty thousand dollars outright, or four ninety-nine a month, with a reported six-month minimum. Either way you put down a refundable two-hundred-dollar deposit, and here's fine-print item number one: you're not buying a robot today. Despite all the videos and headlines, there have been zero customer deliveries as I record this. What you're buying is a place in line — the first ten thousand units sold out in five days, and deliveries start late this year.

And the machine itself? Genuinely beautiful engineering. Five foot six, sixty-six pounds, tendon-driven so it moves soft and quiet — twenty-two decibels, quieter than your fridge — with about four hours of battery. It wears an actual knit suit, which sounds like a gimmick until you realize it's padding, because this thing is designed to live where you live. Real thought went into this machine, and I love that it exists. Now, what does it do today? The most honest picture is the Wall Street Journal's demo, where NEO took about five minutes to load three things into a dishwasher — with a human operator controlling every move. And before anyone laughs: a robot loading a dishwasher at ALL was science fiction five years ago. The first cars lost races to horses. That's not an insult — that's just where we are on the curve. But "a human operator controlling every move" is fine-print item number two, and it's the most interesting thing in this video.

---

## 03 — THE PERSON INSIDE (TTS reference: 1:19)

When NEO hits a task its AI can't handle, a trained 1X operator in a VR headset sees through its cameras and takes over its hands. 1X calls it Expert Mode. The product in the ad is an autonomous robot. The product in your house is, some of the time, a human presence wearing a robot body.

The facts are better than the internet rumor version: nothing connects without you. You schedule and approve every session, you can block rooms entirely, faces are blurred by default, and the operators are background-checked and don't know whose home they're in. It's disclosed. It's actually a clever way to ship a robot before the AI is finished.

I work in cybersecurity, and it's changed how I look at every new device. Most people ask what chores this robot does. I ask: who has access to the cameras? What data leaves the home? Those aren't fear questions — history just shows convenience always arrives before the security conversation catches up.

And Expert Mode tells you what this product really is: you're not buying a robot — you're buying a seat in the training fleet. Every task an operator performs becomes training data teaching version three to do it alone. Early buyers aren't just customers. They're the teachers. Which is noble — it's how self-driving cars got trained. Just know whether you're paying to be the teacher, or waiting to hire the graduate.

---

## 04 — THE HONEST MATH (TTS reference: 1:41)

So — none of that makes NEO a bad product. It makes it an early one. The question was never robot or no robot; you're getting a robot eventually. The question is which generation you buy into, and that's just math. Five hundred a month is six thousand a year. For that, today, you could run the boring stack: a flagship robot vacuum — a thousand dollars on sale — plus a human cleaner twice a month. Call it forty-six hundred to five thousand for the first year, and it cleans bathrooms, which NEO can't do yet. Buying NEO outright? That's twenty thousand on version-one hardware right as prices start collapsing — and the collapse is the exciting part. Unitree's G1 has already dropped from sixteen thousand to thirteen and a half. Their R1 is under five grand. Goldman Sachs watched build costs fall forty percent in a single year, and Bank of America sees them halving by twenty thirty. One wrinkle: a bill in Congress — the GUARD Act — would restrict Chinese-built robots from the US market, so that price war may reach American living rooms late. Changes the date, not the direction.

Here's the beautiful part of waiting: wait until twenty twenty-eight, and you've spent zero — while other people's subscriptions literally train your future robot, for free, from your point of view. That's the best deal in tech right now.

Two honest exceptions. If you have mobility or accessibility needs, the comparison isn't a cleaner — it's assisted living at seventy-five thousand a year, and the math genuinely changes. And if you're a builder, or you just want to be early and can truly afford it — subscribe, don't buy. Five hundred a month you can walk away from is a fair front-row ticket. Twenty grand locked into gen one, sight unseen, is not.

---

## 05 — THE VERDICT (TTS reference: 1:08)

The whole video in four sentences. Saving money on chores? Not yet — the boring stack wins today. Accessibility needs, or building on robotics? Genuinely worth a serious look, and the subscription means you're renting a capability that improves every single month. Want the future early and can afford it? Subscribe — five hundred a month you can walk away from is a fair ticket to the front row. Everyone else: your robot is coming, and here's your exact buy signal so you know the moment it arrives. The day a humanoid can clean a bathroom unattended AND costs under ten grand — it's go time. My honest guess is twenty twenty-eight. I'll be in line with you.

I'm fascinated by robotics, and I think it's too important to cover like another gadget launch. My goal here is to separate marketing from reality and tell you when these products are truly ready for your home. I'll be tracking every price drop and every real test on this channel — so when your moment comes, you'll know it. Links to everything, including the robot help you can actually buy today, are in the description. Subscribe for a front-row seat to the robot decade — without paying front-row prices.
