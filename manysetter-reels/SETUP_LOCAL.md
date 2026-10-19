# Run the Setty reel studio on your computer

Everything below is free except the Charon voice (a few cents per reel on your Gemini key).
A machine with a graphics card renders the 3D several times faster than the cloud session.

## 1. Get the project

```bash
git clone https://github.com/gregoirebourdin/monteur-video.git
cd monteur-video
git checkout claude/manysetter-promo-video-qe55in   # or main, once merged
```

## 2. Tools

| Tool | Mac (Homebrew) | Why |
|---|---|---|
| Node.js 22+ | `brew install node` | HyperFrames (renders the reels) |
| FFmpeg 6+ | `brew install ffmpeg` | audio processing, loudness, final files |
| Python 3.11+ | `brew install python@3.12` | voice editing, music, SFX |
| whisper.cpp | `brew install whisper-cpp` | checks every spoken word |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | the reel expert |

On Windows, use WSL (Ubuntu) and the same tools with `apt`.

Python packages:

```bash
python3 -m pip install numpy scipy soundfile torch torchaudio num2words requests
```

The first voice alignment downloads the wav2vec2 model (~360 MB) once.

Whisper model:

```bash
mkdir -p ~/whisper-models
curl -L -o ~/whisper-models/ggml-small.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin
echo 'export WHISPER_MODELS_DIR="$HOME/whisper-models"' >> ~/.zshrc
# if the binary is not called whisper-cli on your system:
# echo 'export WHISPER_CLI=whisper-cpp' >> ~/.zshrc
```

HyperFrames and its headless browser:

```bash
cd manysetter-reels
npx --yes hyperframes@0.8.114 browser ensure
npx --yes hyperframes@0.8.114 skills update   # HyperFrames skills for Claude Code
```

## 3. Your Gemini key (never in the project)

```bash
mkdir -p ~/.config/manysetter
printf 'GEMINI_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/manysetter/gemini.env
chmod 600 ~/.config/manysetter/gemini.env
```

Create a fresh key in Google AI Studio (API keys) and delete the old one.

## 4. Check that everything works

```bash
cd manysetter-reels
python3 reel1/build.py && python3 reel1/audio.py
npx --yes hyperframes@0.8.114 snapshot reel1 --at 0.3,15 --no-end --describe false --timeout 30000
```

You should see two PNGs in `reel1/snapshots/`. Then start Claude in this folder:

```bash
claude
```

and paste the prompt from `PROMPT_LOCAL.md`.
