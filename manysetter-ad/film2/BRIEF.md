# ManySetter, film v2 (script v7)

16:9, 1920×1080 at 60 fps, about 90 s. Charon voice (Gemini 3.8 Flash TTS), first person: a coach's inner monologue, problem first (PASTOR).

## Rules for the picture

- **Every spoken word is written on screen, on its own cue.** The kinetic type layer is generated from `scripts/spec.py`, and `build.py` refuses to build if the words on screen differ from the voice.
- **One idea per beat.** Each beat shows one phrase and at most one UI element.
- **The UI is the app's own.** It is rebuilt from the app's CSS: tokens, Nohemi and Inter, shadows, bubbles, chips and the AI summary.
- **The light tells the story:**
  - night for the problem (P1–P3);
  - the logo's light trace blooms into day at "ManySetter?" (P4);
  - a sunrise on "Next morning" (P7).

## Shot list

| Scene | Voice | On screen |
|---|---|---|
| s1 | I posted a Reel… 126 DMs! … It's 9 p.m.! | Reel card, double-tap heart, Manychat sends the link ×3, the 126 count with a flood of DM notifications |
| s2 | If I reply too late… for nothing? | DM at 9:04 PM, a reply the next day, the lead fades away, "nothing?" loses its strength |
| s3 | Quick, I need to hire a setter… Uh… no. | Job post card (train them, pay commission), then the cringe DM typed word by word and struck out |
| s4 | Wait… what's this? ManySetter? … like me? | Spark that traces the M, bloom into day, lockup, then Manychat ⇄ ManySetter plugged together, "Your tone. Your words." |
| s5 | Okay, let's try… Wait… seriously? | Playbook (sales page dropped in, about 2 min, learned), then a live DM thread: price, objection, Qualified, Call booked |
| s6 | It's sneaky… calls booked. | Reply delay set to Human-like with a typing indicator, AI summary card, Results for the sales team |
| s7 | Next morning… sounds like me. | Sunrise, coffee, then a calendar filling with three calls; "No setter. No commission." |
| s8 | Got a Reel coming up?… the whole year. | The real "Build my setter free" button clicked, "No card.", then $1,500 vs $119/mo × 12 |
| s9 | ManySetter. Your DMs on autopilot… manysetter.com | Lockup, tagline, URL pill, legal line |

The Results tile values (126 / 41 / 17) are illustrative demo values inside the UI, not claims.

## Rebuild

```bash
python3 ../scripts/edit_vo.py --take ../vo/takes_v3/charon_v7_try3.wav --lines ../vo/hero_v7_lines.json --out-wav assets/audio/vo.wav --out-timing timing.json
python3 ../scripts/align_words.py timing.json assets/audio/vo.wav    # frame-accurate word cues
python3 scripts/build.py                                            # kinetic layer + scenes + index.html
python3 scripts/make_audio.py                                       # score + SFX
npx hyperframes check && npx hyperframes render . --fps 60 -o renders/manysetter_v2_raw.mp4
python3 scripts/finalize.py renders/manysetter_v2_raw.mp4 renders/manysetter_v2_1080p60.mp4
```
