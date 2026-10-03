#!/usr/bin/env python3
"""Generate voice-over takes with Gemini TTS.

Reads GEMINI_API_KEY from the environment (or from ~/.config/manysetter/gemini.env).
The key is never written into the project folder.

Usage:
  python3 scripts/tts_gemini.py --voice Kore --text-file vo/script.txt --out vo/kore.wav
  python3 scripts/tts_gemini.py --voice Kore --text "Hello" --style "Warm and confident" --out vo/test.wav
"""
import argparse
import base64
import json
import os
import pathlib
import re
import sys
import time
import wave

import requests

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
INTERACTIONS_API = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.8-flash-tts"
FALLBACK_MODELS = ["gemini-3.1-flash-tts-preview"]


def load_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env_file = pathlib.Path.home() / ".config/manysetter/gemini.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("GEMINI_API_KEY is not set")


def _post(url: str, body: dict, key: str) -> dict:
    for attempt in range(4):
        r = requests.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            data=json.dumps(body),
            timeout=180,
        )
        if r.status_code in (429, 500, 503) and attempt < 3:
            time.sleep(20 if r.status_code == 429 else 2 ** (attempt + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1500]}")
        return r.json()
    raise RuntimeError("retries exhausted")


def synthesize_interactions(text: str, style: str, voice: str, model: str, key: str) -> tuple[bytes, int]:
    """Gemini 3.8 TTS: text is a verbatim transcript, style goes in speech_metadata."""
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    body = {
        "model": model,
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    data = _post(INTERACTIONS_API, body, key)
    audio = [
        c
        for step in data.get("steps", [])
        if step.get("type") == "model_output"
        for c in step.get("content", [])
        if c.get("type") == "audio"
    ]
    if not audio:
        raise RuntimeError(f"no audio in response: {json.dumps(data)[:600]}")
    raw = base64.b64decode(audio[-1]["data"])
    if raw[:4] == b"RIFF":
        import io

        with wave.open(io.BytesIO(raw)) as w:
            return w.readframes(w.getnframes()), w.getframerate()
    return raw, 24000


def synthesize_legacy(text: str, style: str, voice: str, model: str, key: str) -> tuple[bytes, int]:
    """Older TTS models (generateContent): the style note is part of the prompt."""
    prompt = f"{style}: {text}" if style else text
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    data = _post(API.format(model=model), body, key)
    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
    return base64.b64decode(part["data"]), int(m.group(1)) if m else 24000


def synthesize(text: str, style: str, voice: str, model: str, key: str) -> tuple[bytes, int]:
    if model.startswith("gemini-3.8"):
        return synthesize_interactions(text, style, voice, model, key)
    return synthesize_legacy(text, style, voice, model, key)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--style", default="", help="Delivery direction (sent as metadata, never read aloud)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-fallback", action="store_true", help="Fail instead of falling back to an older model")
    a = ap.parse_args()

    script = a.text if a.text else pathlib.Path(a.text_file).read_text().strip()
    key = load_key()

    last_err = None
    models = [a.model] if a.no_fallback else [a.model, *[m for m in FALLBACK_MODELS if m != a.model]]
    for model in models:
        try:
            pcm, rate = synthesize(script, a.style.strip(), a.voice, model, key)
            break
        except RuntimeError as e:
            last_err = e
            print(f"warn: {e}", file=sys.stderr)
    else:
        sys.exit(f"all models failed: {last_err}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    print(f"{out}  {len(pcm) / 2 / rate:.2f}s  {rate} Hz  model={model}  voice={a.voice}")


if __name__ == "__main__":
    main()
