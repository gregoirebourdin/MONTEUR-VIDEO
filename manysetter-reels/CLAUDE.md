# ManySetter Reels with Setty: the expert guide

You make vertical reels (Instagram Reels and YouTube Shorts) for **ManySetter**, starring **Setty**, its mascot.
This file is everything learned while making reel 1. Read it fully before touching a reel. The step-by-step
workflow is the `/setty-reel` skill (`.claude/skills/setty-reel/SKILL.md`).

**Grégoire** (founder) speaks French: answer him in French, short and direct. The reels themselves are in
**American English**. He decides; when he gives a direction, write it into `BRIEF.md` the same day.

## 1. The product (only true claims)

ManySetter is an AI appointment setter plugged into **Manychat** (Instagram DMs). Allowed facts:

- It learns your offer from your sales page in about 2 minutes (the Playbook).
- It replies in your tone and your words, with a human-like reply delay.
- It qualifies leads, handles objections ("I'll think about it"), and books calls into your calendar
  (Calendly, Cal.com, iClosed).
- AI summary of each conversation; results for the sales team.
- Price: $119/month. Free to start, no card. A human setter: around $1,500/month plus commission.
- Never invent numbers, testimonials, or client results. Numbers in UI cards are demo values.

## 2. Audience and tone (Grégoire's direction, keep it)

Coaches and infopreneurs who run **webinars, 5-day challenges, VSLs, lives**, then drown in Instagram DMs
they have no time to answer, or pay a setter.

Setty is **ultra insolent, hardcore, a bit vulgar, and talks like a real human**. He goes straight into the
pain in the first second. Grégoire's words: « faut que tu sois hard, hardcore, que tu rentres cash dans le
truc », « un poil vulgaire », « que tu parles vraiment comme un humain ». He threw out soft, generic hooks
(« t'attends des DM alors qu'il est 11 h, on s'en bat les couilles ») and polite marketing pitches.

- **Signature hook, every reel:** `Hey [bleep]. You did your [bleep]ing <challenge|webinar|VSL>, right?`
- **Three bleeps per reel at most**: two in the hook, one in the punchline. More becomes noise.
- A bleep lets the first consonant through ("b—", "f—", "sh—"), then a 1 kHz tone; a censor bar covers
  Setty's mouth (`pose.censor`) and the caption word (`.tok.bleep`).
- **CTA, every reel:** `Comment SETTY. I'll slide into your DMs.` (the keyword SETTY exists in Manychat,
  so Setty really answers: the CTA proves the product).
- Funny > clever. Roast the viewer like a best friend, never punch down.

Series hooks ready to use:

- Hey [bleep]. You did your [bleep]ing webinar, right? Two hours. Twelve people stayed.
- Hey [bleep]. You shot your [bleep]ing VSL, right? Forty takes. Your mom watched it.
- Hey [bleep]. You went live. Again. For the [bleep]ing algorithm, right?

## 3. Setty, the character

- A living DM bubble: puffy squircle, the logo gradient (#ffa066 → #e64b15), glossy, a tail at the bottom
  left pointing down and **out** (Grégoire caught it pointing the wrong way once), hovering above its shadow.
- Big glossy eyes with real lids and lash lines, arched brows, a drawn mouth (smile, smirk, open, "O",
  tongue), blush, stubby arms. The three typing dots above his head are his mood ("!" when shocked).
- Voice: **Charon** (Gemini 3.8 Flash TTS). A cute bubble with a deep, confident voice is part of the joke.
- Code: `assets/setty/setty.js` (Three.js, procedural, no model file). `createSetty()` → `{ root, apply(pose) }`.
  A pose is a flat object of numbers (GSAP-tweenable). Presets: `happy, smug (signature), sideEye, shocked,
  laughing, unimpressed, wink, excuseMe, proud`; `pose(name, extra)`. Useful fields: `lookX/lookY, lidL/lidR,
  lowL/lowR, happyL/happyR (^ eyes), slantL/R, browLy/Ry/Lr/Rr, curve, smirk, mouthOpen, mouthRound,
  tongue, teeth, blush, censor, armLr/Rr (raise), armLf/Rf (forward), dots, dotsBounce, alert, x, y, turn,
  tilt, lean, squash`.
- Character sheet and personality clip: `deliverables/setty/`. Lab compositions: `lab/sheet`, `lab/hello`.

## 4. Reel format

- 1080×1920, **25–30 s**, about **85–90 spoken words** (Charon speaks ~3.3 words/s once the pauses are tight).
- **Frame 0 is the thumbnail**: Setty in close-up with his smug face, never a black frame.
- Something changes on screen every ~0.5–0.8 s: a word, a prop, a camera move, a cut.
- Every spoken word is on screen (captions), except a word shown by a prop (the giant "info?" bubble).
- The last frame loops into the first (Setty centered, smug or winking; frame 0 is the close-up).
- Safe zones: captions live in y 1185–1465 (centred, ≤ 920 px wide). Nothing important below y 1440,
  right of x ~950 between y 900–1700 (IG buttons), or in the top 150 px (IG header), except decoration.
- Deliver two files: with music, and without music (voice + SFX) for a trending sound added in-app.

## 5. Script recipe

1. Hook (0–3 s): the signature hook, naming the coach's exact format.
2. Pain, made physical (3–12 s): 3–4 short, concrete images (live for five days, voice dead, ring light
   still on, 400 people writing "info?", answering by hand at midnight in bed).
3. The turn (12–15 s): a dead-serious one-liner on black ("That's not a business. That's a hostage situation.").
4. Setty's flex (15–22 s): "Plug me into Manychat." then 3 product facts shown in the real UI.
5. Punchline (22–24 s): a roast with the third bleep ("Go to sleep. You look like [bleep].").
6. CTA (24–28 s): "Comment SETTY. I'll slide into your DMs."

Write each line as a segment with its own delivery direction (`vo/<reel>_segments.json`), e.g.
`"Deadpan and mocking, short punchy beats"`, `"Suddenly dead serious, low and dramatic"`,
`"Fast, confident and rhythmic, like listing flexes"`, `"Smooth, smug, a little flirty sign-off"`.

## 6. Pipeline (commands, from `manysetter-reels/`)

| Step | Command | Time |
|---|---|---|
| New reel from the reference | `scripts/new_reel.sh reel2` | instant |
| 3 voice takes in parallel | `for i in 1 2 3; do python3 ../manysetter-ad/scripts/tts_gemini.py --voice Charon --segments vo/reel2_segments.json --out vo/takes/reel2_try$i.wav --no-fallback & done; wait` | ~25 s |
| Pick the take (whisper diff) | `python3 ../manysetter-ad/scripts/check_vo.py vo/takes/reel2_tryN.wav vo/reel2_script.txt` (script = all segment texts joined) | ~20 s each |
| Tight pauses + word timing | `python3 scripts/voice.py vo/reel2_segments.json vo/takes/reel2_tryN.wav vo/reel2` → `vo.wav`, `timing.json`; re-run check_vo on it | ~30 s |
| Captions, bleeps, cues | edit `CHUNKS`, `BLEEPS`, `CUES` in `reel2/build.py`; `python3 reel2/build.py` | instant |
| Picture | edit `reel2/src/template.html` (scenes = Setty keyframes `K(...)` + DOM timeline `tl`) | the work |
| Iterate | `npx --yes hyperframes@0.8.114 snapshot reel2 --at 0.3,2.4,5.0 --no-end --describe false --timeout 30000` then read `reel2/snapshots/contact-sheet*.jpg` | ~30–60 s |
| Sound | edit SFX cues in `reel2/audio.py`; `python3 reel2/audio.py` → `audio/mix.wav`, `mix_nomusic.wav` | ~7 s |
| Voice QA on the mix | `python3 ../manysetter-ad/scripts/check_vo.py reel2/audio/mix.wav vo/reel2_script.txt` | ~20 s |
| Check | `npx --yes hyperframes@0.8.114 check reel2` | ~1 min |
| Render | `npx --yes hyperframes@0.8.114 render reel2 --fps 30 -o renders/reel2_v1.mp4` (preview), `--fps 60` for the final | GPU: minutes; CPU only: ~16 min per 30 s at 30 fps |
| Deliver | `scripts/deliver.sh reel2 renders/reel2_v1.mp4` | seconds |

Run long renders in the background and keep working. Never re-render for the no-music version.

## 7. The reel kit (all in `reel1/`, reuse it)

- `build.py`: `CHUNKS` = caption groups by word index with `accent`, `display` (e.g. "400"), `hide`, `hero`,
  `count`, `hold`; `BLEEPS` = word indices; `CUES` = named times from words (`t(i)`, `e(i)`). Everything is
  timed from the voice, so a new take re-times the whole reel. Icons are inlined from `assets/ui/lucide.json`.
- `src/template.html` (single composition, `{{ID}}`/`{{TOTAL}}`/`/*DATA*/` filled by build.py):
  - Setty performance: `K(t, dur, {pose fields, cam: {...}, light: {...}}, ease)`, `face(name, extra)`, `shake(t, amp)`.
    Camera presets: hook close-up `z 8.4–9.2, ly 1.85`; `MID z 14, ly 0.25` (Setty centred at y≈576);
    `TOP z 19, ly −1.2` (Setty in y 74–645, UI cards in 660–1150); end `z 14, ly 1.05`.
  - Captions engine (pop per word, orange accents, black stroke, bleep bars), flash frames.
  - Props: `5-DAY CHALLENGE` marquee, LIVE pill + day counter, ECG → flatline, ring light (follows Setty via
    `--sx/--sy/--su`), DM rain (matter.js, precomputed at 60 fps), giant "info?" bubble, hand badge, 00:00
    clock, bed, hostage tapes on black with a red spot, Manychat pill + cable from Setty's tail + spark,
    real-UI cards (Playbook learning, DM thread with typing, Qualified chip, Call booked + confetti, week
    calendar), moon "zzz", IG comment bar typing SETTY, DM notification, end CTA pill.
- `audio.py`: Charon + bleeps + dialogue chain; original half-time trap at 150 BPM (kick, snare, hats with
  rolls, 808 with glides, a bell motif) with sections that stop on comedic beats; SFX library (impact,
  whoosh, swish, ping storm, ECG beeps, hum, scratch, zap, boing, key clicks, sparkle, pops); ducking;
  constant-gain master to −14 LUFS + limiter.
- Brand UI: `assets/ui/ms.css` (app tokens and components: `.ms-window`, `.ms-bubble.lead/.setter`,
  `.ms-typing`, `.ms-chip.green/.orange`, `.ms-avatar`), fonts Nohemi + Inter in `assets/fonts/`.

## 8. Hard-won rules (each one cost a render)

Picture
- Tweens read right after `seek()` (Setty pose, camera, lights) must be `lazy: false`, or jumps show stale poses.
- `fromTo` on an element that is reused (`#flash`) or hidden by CSS (confetti, sparks) needs
  `immediateRender: false`, or it shows at t=0 (we got a grey veil and a white square).
- One root HTML with `data-composition-id` per reel folder: the template lives in `src/`.
- No `fetch()` and no randomness at render: inline data in `DATA`, use the seeded `rnd()`.
- CSS `zoom` on a positioned element also scales its `top/left`: zoom an inner element inside an unzoomed wrapper.
- Caption stroke = `-webkit-text-stroke` + `paint-order: stroke fill` + a hard drop shadow: readable on anything.
- In a close-up, Setty's mouth sits in the caption zone: hide the caption of a bleeped word there (the mouth
  bar is the caption), or you get two bars.
- Physics: Setty is a static rounded body from his projected silhouette; no side walls (bubbles bridge the
  gap and make a ceiling); remove the floor and raise gravity to drain the pile.
- Setty's pupils and glints must stay inside the lid radius (1.07 × eye radius) or they poke through closed
  lids; closed eyes need the `^`/`u` arcs (`happyL/R`, lid > 0.9).
- Mark intentional off-canvas props with `data-layout-ignore` (tapes, marquee, rain, notification).

Sound
- Never put an SFX on a word onset: it eats the consonant ("by hand" → "buy ham", "I'll" → "oh"). Word ticks
  go 0.07 s before the word; message blips 0.1–0.3 s before; taps after the word ends.
- The bleep ends before the next word starts ("…ing challenge" lost its "ch" once).
- Duck the music by ~0.64 under the voice with a 60 ms look-ahead; duck SFX by 0.3.
- Master with a constant gain to −14 LUFS + `alimiter` at −1.5 dB. Never ffmpeg loudnorm in dynamic mode.
- Never time-stretch the voice slower (it blurs); `atempo` ≤ 1.1 only if a take is too long.
- Whisper QA on the final mix; "four hundred" → "400" and "SETTY" → "SETI" are spelling, not errors.

Speed
- Generate takes in parallel; iterate with snapshots (8 frames ≈ 30 s), never with full renders.
- Preview at 30 fps; final at 60 fps once Grégoire approves.
- Commit and push after each validated step (the repo is the memory between sessions).

## 9. Security

- The Gemini key lives only in `~/.config/manysetter/gemini.env` (`GEMINI_API_KEY=...`) or the environment.
  Never write it in the repo, a log, or a commit.
- Dashboard sessions or app captures with client data never go into the repo.
