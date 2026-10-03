#!/usr/bin/env python3
"""Cut a verified VO take into script lines and lay them out on the film timeline.

The picture is re-timed to the voice: this script is the single source of timing.
Swap the voice -> re-run this script -> re-run film/scripts/build_film.py.

Inputs
  --take   vo/takes/<take>.wav                (any sample rate, mono)
  --lines  vo/hero_lines.json                 [{"id": "L1", "text": "...", "gap": 0.6, "anchor": 0.6}, ...]
Outputs
  --out-wav     film/assets/audio/vo.wav       48 kHz mono, lines placed on the film timeline
  --out-timing  film/timing.json               line + word times in film seconds
"""
import argparse
import json
import pathlib
import re
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
WHISPER_MODEL = "/opt/whisper.cpp/models/ggml-small.en.bin"


def norm(w: str) -> str:
    w = w.lower().replace("many chat", "manychat").replace("many setter", "manysetter")
    return re.sub(r"[^a-z0-9]", "", w)


def transcribe(wav: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        w16 = f"{tmp}/a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ar", "16000", "-ac", "1", w16], check=True)
        subprocess.run(
            ["whisper-cli", "-m", WHISPER_MODEL, "-l", "en", "-f", w16, "-ojf", "-of", f"{tmp}/o", "-np", "-ml", "1", "-sow"],
            check=True,
            capture_output=True,
        )
        segs = json.loads(pathlib.Path(f"{tmp}/o.json").read_text())["transcription"]
    out = []
    for s in segs:
        t = s["text"].strip()
        if t:
            out.append({"w": t, "start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000})
    return out


def silences(wav: str, db: float = -42, dur: float = 0.18) -> list[tuple[float, float]]:
    r = subprocess.run(
        ["ffmpeg", "-i", wav, "-af", f"silencedetect=noise={db}dB:d={dur}", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", required=True)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--out-wav", required=True)
    ap.add_argument("--out-timing", required=True)
    ap.add_argument("--fade", type=float, default=0.012)
    a = ap.parse_args()

    lines = json.loads(pathlib.Path(a.lines).read_text())
    words = transcribe(a.take)
    sil = silences(a.take)
    audio, sr = sf.read(a.take, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    total = len(audio) / sr

    # Align whisper words to script lines in order (word counts after normalisation).
    wi = 0
    for ln in lines:
        target = [norm(w) for w in ln["text"].replace("...", " ").replace("dot com", "dotcom").split() if norm(w)]
        got = []
        while wi < len(words) and len(got) < len(target):
            n = norm(words[wi]["w"]).replace("manysettercom", "manysetter dotcom")
            for piece in n.split():
                got.append((piece, words[wi]))
            wi += 1
        ln["_words"] = [w for _, w in got]
        if len(got) < len(target):
            raise SystemExit(f"{ln['id']}: ran out of words ({len(got)}/{len(target)})")

    # Line boundaries: snap to the surrounding silences.
    for i, ln in enumerate(lines):
        first, last = ln["_words"][0], ln["_words"][-1]
        # whisper word starts drift early or late by a few hundred ms: bound each line by the
        # silence that actually precedes its first word and the one that follows its last word
        before = [s for s in sil if s[1] is not None and s[0] <= first["start"] + 0.1]
        src_in = before[-1][1] if before else 0.0
        after = [s for s in sil if (s[1] if s[1] is not None else total) > last["start"] + 0.15]
        src_out = after[0][0] if after else total
        ln["src_in"] = max(0.0, src_in - 0.04)
        ln["src_out"] = min(total, src_out + 0.06)

    # Lay out on the film timeline: start = max(anchor, previous end + gap).
    t = 0.0
    for ln in lines:
        start = max(ln.get("anchor", 0.0), t + ln.get("gap", 0.5))
        ln["start"] = round(start, 3)
        ln["end"] = round(start + (ln["src_out"] - ln["src_in"]), 3)
        t = ln["end"]

    # Render the edited VO at 48 kHz.
    up = resample_poly(audio, SR, sr).astype(np.float32)
    out = np.zeros(int((lines[-1]["end"] + 1.0) * SR), dtype=np.float32)
    f = int(a.fade * SR)
    ramp = np.linspace(0, 1, f, dtype=np.float32)
    for ln in lines:
        seg = up[int(ln["src_in"] * SR) : int(ln["src_out"] * SR)].copy()
        seg[:f] *= ramp
        seg[-f:] *= ramp[::-1]
        s0 = int(ln["start"] * SR)
        out[s0 : s0 + len(seg)] += seg
    pathlib.Path(a.out_wav).parent.mkdir(parents=True, exist_ok=True)
    sf.write(a.out_wav, out, SR, subtype="PCM_24")

    # Word cues: whisper's word starts drift by up to ~0.4 s. Snap each one to the nearest
    # energy onset (a rise out of a local dip) of the edited track, inside its own line.
    hop = int(0.01 * SR)
    env = np.sqrt(np.convolve(out**2, np.ones(hop * 2) / (hop * 2), mode="same")[::hop] + 1e-12)
    db = 20 * np.log10(env + 1e-9)
    rise = np.zeros_like(db)
    rise[3:] = db[3:] - np.minimum.reduce([db[2:-1], db[1:-2], db[:-3]])
    onsets = [i * 0.01 for i in range(3, len(db) - 1) if rise[i] > 9 and rise[i] >= rise[i - 1] and rise[i] >= rise[i + 1] and db[i] > -45]

    def snap(t: float, lo: float, hi: float) -> float:
        cands = [o for o in onsets if lo <= o <= hi and abs(o - t) <= 0.35]
        return min(cands, key=lambda o: abs(o - t)) if cands else min(max(t, lo), hi)

    timing = {"take": a.take, "duration": round(len(out) / SR, 3), "lines": []}
    for ln in lines:
        off = ln["start"] - ln["src_in"]
        cues, prev = [], ln["start"] - 0.01
        for k, w in enumerate(ln["_words"]):
            t = ln["start"] + 0.04 if k == 0 else snap(w["start"] + off, prev + 0.08, ln["end"] - 0.1)
            t = max(t, prev + 0.06)
            cues.append({"w": w["w"], "t": round(t, 3)})
            prev = t
        timing["lines"].append({"id": ln["id"], "text": ln["text"], "start": ln["start"], "end": ln["end"], "words": cues})
    pathlib.Path(a.out_timing).write_text(json.dumps(timing, indent=1))
    for ln in timing["lines"]:
        print(f"{ln['id']}  {ln['start']:6.2f} → {ln['end']:6.2f}  {ln['text']}")
    print(f"VO track: {timing['duration']:.2f}s → {a.out_wav}")


if __name__ == "__main__":
    main()
