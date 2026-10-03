# ManySetter promo ad

Brief: [`brief/PROMPT.md`](brief/PROMPT.md)

## Toolchain

| Tool | Role | Install |
|---|---|---|
| HyperFrames 0.8.114 (HeyGen, open source) | HTML + GSAP compositions rendered to MP4 by headless Chrome | `npm i` then `npx hyperframes browser ensure` |
| Node.js 22, FFmpeg 6 | runtime, encoding, loudness, QA filters | preinstalled |
| Gemini TTS `gemini-3.8-flash-tts` | voice-over | key in `GEMINI_API_KEY` or `~/.config/manysetter/gemini.env` (never in the repo) |
| whisper.cpp + `ggml-small.en` | word-level QA and timings of every VO take | build from github.com/ggml-org/whisper.cpp |
| Python 3.11 + numpy, scipy, soundfile, pyloudnorm | original music and SFX made in code, LUFS checks | `pip install numpy scipy soundfile pyloudnorm` |

## Scripts

- `scripts/tts_gemini.py --voice Kore --text-file vo/script.txt --style "..." --out vo/take.wav`
  generates a take. On 3.8 models the style is sent as `speech_metadata`, so it is never read aloud.
- `scripts/check_vo.py vo/take.wav vo/script.txt` transcribes the take and diffs it word by word
  against the script (exit code 1 on any missing, extra or wrong word).

## Layout

```
assets_in/   brand logo, fonts (Nohemi from manysetter.com, Inter OFL), kit SFX
brief/       PROMPT.md
research/    site copy and scroll captures used as the visual reference
vo/          scripts and voice takes (auditions/ = casting)
scripts/     TTS, VO QA
```
