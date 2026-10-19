---
name: setty-reel
description: Make a ManySetter reel starring Setty (9:16, 25–30 s, insolent, Charon voice) from an idea or a hook, using the reel1 engine. Use for any new reel, a series variant (webinar, VSL, live…), or edits to an existing reel.
---

# /setty-reel — from an idea to two MP4s

Read `CLAUDE.md` first (product facts, tone, Setty, format, kit, hard-won rules). Work in `manysetter-reels/`.
Talk to Grégoire in French, short. Validate with him at the two gates marked ✋; between them, work on your own.

## 1. Script ✋

- Write the script in the recipe of CLAUDE.md § 5: signature hook naming his format, physical pain images,
  the dead-serious turn on black, "Plug me into Manychat" + 3 true product facts, the bleeped punchline,
  "Comment SETTY. I'll slide into your DMs."
- 85–90 words, ≤ 3 bleeps, only facts from § 1. Show it as a table: line (EN) / gist (FR) / on screen.
- Save it in `writing/<reel>_<name>.md`. Wait for his go (or his edits) before spending on the voice.

## 2. Voice

- `scripts/new_reel.sh <reel>` (copies reel1's engine), then write `vo/<reel>_segments.json`: one segment per
  line, each with a delivery direction, and `vo/<reel>_script.txt` (all texts joined by spaces).
- Three Charon takes in parallel, whisper-check each, keep the best (all words right, best energy).
- `scripts/voice.py` → `vo/<reel>/vo.wav` + `timing.json`; whisper-check again. Aim for 26–29 s. If a quoted
  phrase or a key word gets swallowed, give that pause more room in `BEATS` / the quote rule.

## 3. Build the picture

- In `<reel>/build.py`: set `CHUNKS` (2–5 words each, a new chunk at each punctuation or idea; `hero` for the
  big words, `display` for numbers, `hide` when a prop says the word), `BLEEPS`, and `CUES` named after
  the words that trigger scenes.
- In `<reel>/src/template.html`: keep the engine (Setty, camera, captions, flash, physics, render loop) and
  rewrite the scenes. For each line: Setty's face (`K` with a preset), a camera move, one prop or one UI
  card, a flash on hard cuts. Reuse reel1 props before inventing new ones. Real ManySetter UI only.
- `python3 <reel>/build.py`, a silent placeholder `audio/mix.wav` if needed, then snapshot 8 key moments,
  read the contact sheet, fix, repeat. Check: framing, captions readable and inside the safe zone, nothing
  important under IG buttons, no stray elements at t=0, every scene lands on its word.

## 4. Sound

- In `<reel>/audio.py`: keep the voice chain, bleeps, beat and master; re-place the SFX list on the new cues,
  stop the beat on the comedic beats, and keep SFX off word onsets.
- `python3 <reel>/audio.py`, then whisper-check `audio/mix.wav` against the script.

## 5. Render ✋

- `npx --yes hyperframes@0.8.114 check <reel>` (fix errors; layout warnings on intentional off-canvas props
  get `data-layout-ignore`), then render a 30 fps preview in the background.
- Extract 6–8 frames from the MP4 to verify, then `scripts/deliver.sh <reel> renders/<file>.mp4`.
- Send both files to Grégoire. After his notes: fix, then render the final at 60 fps.
- Commit and push the sources and `deliverables/<reel>/` (not `renders/`, snapshots or takes logs).
