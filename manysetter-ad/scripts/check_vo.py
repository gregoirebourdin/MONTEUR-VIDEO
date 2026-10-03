#!/usr/bin/env python3
"""QA a voice-over take: transcribe it with whisper.cpp and diff the words against the script.

Exit code 0 = every word of the script is spoken, nothing extra. 1 = mismatch.

Usage: python3 scripts/check_vo.py vo/take.wav vo/script.txt [--lang en]
"""
import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

WHISPER = "whisper-cli"
MODELS = {"en": "/opt/whisper.cpp/models/ggml-small.en.bin", "fr": "/opt/whisper.cpp/models/ggml-small.bin"}

# Spellings whisper uses for the brand names, mapped back to the script's spelling.
ALIASES = {
    "minichat": "manychat",
    "manychats": "manychat",
    "manysetters": "manysetter",
    "real": "reel",
}


def words(text: str) -> list[str]:
    text = text.lower().replace("many chat", "manychat").replace("many setter", "manysetter")
    text = text.replace("dot com", "dotcom").replace(".com", " dotcom")
    out = re.findall(r"[a-z0-9àâäéèêëïîôöùûüç$]+", text)
    return [ALIASES.get(w, w) for w in out]


def transcribe(wav: str, lang: str) -> tuple[str, list[dict]]:
    with tempfile.TemporaryDirectory() as tmp:
        wav16 = f"{tmp}/in.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ar", "16000", "-ac", "1", wav16], check=True)
        base = f"{tmp}/out"
        subprocess.run(
            [WHISPER, "-m", MODELS[lang], "-l", lang, "-f", wav16, "-ojf", "-of", base, "-np", "-ml", "1", "-sow"],
            check=True,
            capture_output=True,
        )
        data = json.loads(pathlib.Path(base + ".json").read_text())
    segs = data.get("transcription", [])
    text = " ".join(s["text"].strip() for s in segs)
    return text, segs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("script")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()

    script = pathlib.Path(a.script).read_text()
    heard, _ = transcribe(a.wav, a.lang)
    want, got = words(script), words(heard)
    sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    problems = [op for op in sm.get_opcodes() if op[0] != "equal"]
    print(f"heard: {heard.strip()}")
    if not problems:
        print("OK: every word matches the script")
        sys.exit(0)
    for tag, i1, i2, j1, j2 in problems:
        print(f"{tag.upper():8} script={' '.join(want[i1:i2])!r} heard={' '.join(got[j1:j2])!r}")
    sys.exit(1)


if __name__ == "__main__":
    main()
