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

    # Align script words to whisper words at character level (robust to "2am" vs "two a.m.",
    # "$1,500" vs "fifteen hundred dollar", "many chats" vs "Manychat"...).
    import difflib

    def clean(txt: str) -> str:
        return re.sub(r"<[^>]+>", " ", txt).replace("...", " ")

    s_words, s_line = [], []
    for li, ln in enumerate(lines):
        for w in clean(ln["text"]).split():
            if norm(w):
                s_words.append(w)
                s_line.append(li)
    s_stream, s_pos = "", []
    for w in s_words:
        s_pos.append(len(s_stream))
        s_stream += norm(w)
    w_stream, w_owner = "", []
    for k, w in enumerate(words):
        nw = norm(w["w"])
        w_stream += nw
        w_owner += [k] * len(nw)
    sm = difflib.SequenceMatcher(a=s_stream, b=w_stream, autojunk=False)
    s2w = [None] * len(s_stream)
    for blk in sm.get_matching_blocks():
        for i in range(blk.size):
            s2w[blk.a + i] = blk.b + i

    def whisper_time(ci: int) -> float:
        # nearest mapped char at or after ci, else before
        for j in list(range(ci, len(s2w))) + list(range(ci - 1, -1, -1)):
            if s2w[j] is not None:
                k = w_owner[s2w[j]]
                w = words[k]
                start_c = w_owner.index(k)
                n_c = w_owner.count(k)
                nxt = words[k + 1]["start"] if k + 1 < len(words) else w["end"]
                frac = (s2w[j] - start_c) / max(1, n_c)
                return w["start"] + frac * max(0.0, nxt - w["start"])
        return 0.0

    for ln in lines:
        ln["_words"] = []
    for i, w in enumerate(s_words):
        t0 = whisper_time(s_pos[i])
        lines[s_line[i]]["_words"].append({"w": w, "start": t0})
    for ln in lines:
        if not ln["_words"]:
            raise SystemExit(f"{ln['id']}: no words aligned")

    # Line boundaries: each boundary is ONE silence shared by the two lines (no overlap possible).
    # Pick the longest silence between the end of line i and the start of line i+1.
    sil_c = [(st, en if en is not None else total) for st, en in sil]
    lines[0]["src_in"] = max(0.0, (max([e for s_, e in sil_c if s_ <= lines[0]["_words"][0]["start"] + 0.1] or [0.0])) - 0.04)
    for i in range(len(lines) - 1):
        t_a = lines[i]["_words"][-1]["start"]
        t_b = lines[i + 1]["_words"][0]["start"]
        cands = [x for x in sil_c if x[1] > t_a + 0.12 and x[0] < t_b + 0.5]
        if not cands:
            mid = (t_a + t_b) / 2
            cands = [min(sil_c, key=lambda x: abs((x[0] + x[1]) / 2 - mid))]
        best = max(cands, key=lambda x: x[1] - x[0])
        lines[i]["src_out"] = min(total, best[0] + 0.06)
        lines[i + 1]["src_in"] = max(0.0, best[1] - 0.04)
    after = [x for x in sil_c if x[1] > lines[-1]["_words"][-1]["start"] + 0.15]
    lines[-1]["src_out"] = min(total, (after[0][0] if after else total) + 0.06)

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
