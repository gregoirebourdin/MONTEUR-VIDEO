#!/usr/bin/env python3
"""Edit a Charon take for a reel: tight pauses, word-accurate timing.

  1. wav2vec2 CTC forced alignment of the whole script on the take → every word's start and end
  2. every pause is shortened to a target (tight inside a sentence, a beat after punctuation, longer
     only on the comedic beats listed in BEATS); the pause audio is kept, just cut in the middle
  3. optional small speed-up without pitch change (ffmpeg atempo)
  4. writes vo.wav (48 kHz) and timing.json: words with t/end, the segment (line) each belongs to

Usage: python3 scripts/voice.py vo/reel1_segments.json vo/takes/reel1_try3.wav out_dir [--rate 1.05]
"""
import argparse
import json
import pathlib
import re
import subprocess
import tempfile

import numpy as np
import soundfile as sf
import torch
import torchaudio
from scipy.signal import resample_poly

SR = 48000
SPOKEN = {"dms": "dee ems", "manychat": "many chat", "manysetter": "many setter", "400": "four hundred", "ai": "ay eye"}
IN_SENTENCE, AFTER_PUNCT = 0.12, 0.22
# pauses held longer for comedic timing: (word the pause comes after) → seconds
BEATS = {"like...": 0.34, "them...": 0.3, "dead.": 0.26, "business.": 0.3, "it\"...": 0.22, "you?": 0.3, "bed?": 0.34,
         "situation.": 0.36, "calendar.": 0.32, "shit.": 0.34}


def spoken(token):
    t = token.lower().strip("\"'“”‘’.,!?…:;")
    if t in SPOKEN:
        return SPOKEN[t].split()
    return re.sub(r"[^a-z' ]", " ", t.replace("-", " ")).split()


def align(audio, words):
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().eval()
    idx = {c: i for i, c in enumerate(bundle.get_labels())}
    a16 = torch.from_numpy(resample_poly(audio, 16000, SR).astype(np.float32))[None]
    with torch.inference_mode():
        emis, _ = model(a16)
        emis = torch.log_softmax(emis, dim=-1)
    spf = a16.shape[1] / 16000 / emis.shape[1]
    chars, owner = [], []
    for wi, w in enumerate(words):
        for sw in spoken(w):
            for c in sw.upper():
                if c in idx:
                    chars.append(idx[c])
                    owner.append(wi)
            chars.append(idx["|"])
            owner.append(-1)
    chars, owner = chars[:-1], owner[:-1]
    ali, scores = torchaudio.functional.forced_align(emis, torch.tensor([chars], dtype=torch.int32), blank=0)
    spans = torchaudio.functional.merge_tokens(ali[0], scores[0].exp())
    assert len(spans) == len(chars), (len(spans), len(chars))
    first, last, score = {}, {}, {}
    for sp, o in zip(spans, owner):
        if o < 0:
            continue
        first.setdefault(o, sp.start)
        last[o] = sp.end
        score.setdefault(o, []).append(float(sp.score))
    return [(first[i] * spf, last[i] * spf, float(np.mean(score[i]))) for i in range(len(words))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("take")
    ap.add_argument("out")
    ap.add_argument("--rate", type=float, default=1.0)
    a = ap.parse_args()
    segs = json.loads(pathlib.Path(a.segments).read_text())
    words, line_of = [], []
    for li, s in enumerate(segs):
        for w in s["text"].split():
            words.append(w)
            line_of.append(li)

    x, sr = sf.read(a.take, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = resample_poly(x, SR, sr).astype(np.float32)
    times = align(x, words)

    # rebuild the track: words untouched, pauses shortened (cut in the middle with a short crossfade)
    out, new_times = [], []
    pos = 0.0
    lead = 0.06
    start0 = max(0.0, times[0][0] - lead)
    cursor = start0
    fade = int(0.012 * SR)
    for i, (t, e, sc) in enumerate(times):
        nxt = times[i + 1][0] if i + 1 < len(times) else min(len(x) / SR, e + 0.35)
        w = words[i]
        target = BEATS.get(w.lower(), AFTER_PUNCT if re.search(r"[.,!?…]\"?$", w) else IN_SENTENCE)
        if i + 1 < len(words) and words[i + 1].startswith('"'):
            target = max(target, 0.2)  # a breath before a quoted phrase
        if i + 1 == len(times):
            target = 0.35
        gap = max(0.0, nxt - e)
        # the word itself (from the cursor, which sits just before the word)
        seg = x[int(cursor * SR) : int(e * SR)]
        new_times.append((pos + (t - cursor), pos + (e - cursor), sc))
        chunk = [seg]
        if gap <= target:
            chunk.append(x[int(e * SR) : int(nxt * SR)])
        else:
            # keep more audio before the next word: aligned onsets can be a little late
            h2 = max(0.09, target * 0.6)
            h1 = max(0.03, target - h2)
            a1 = x[int(e * SR) : int((e + h1) * SR) + fade]
            a2 = x[int((nxt - h2) * SR) - fade : int(nxt * SR)]
            ramp = np.linspace(0, 1, fade, dtype=np.float32)
            joined = np.concatenate([a1[:-fade], a1[-fade:] * (1 - ramp) + a2[:fade] * ramp, a2[fade:]])
            chunk.append(joined)
        piece = np.concatenate(chunk)
        out.append(piece)
        pos += len(piece) / SR
        cursor = nxt
    y = np.concatenate(out)
    y[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    y[-int(0.05 * SR) :] *= np.linspace(1, 0, int(0.05 * SR))

    outdir = pathlib.Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    vo = outdir / "vo.wav"
    if abs(a.rate - 1.0) > 1e-3:
        with tempfile.TemporaryDirectory() as td:
            raw = pathlib.Path(td) / "raw.wav"
            sf.write(raw, y, SR, subtype="FLOAT")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"atempo={a.rate}", "-ar", str(SR),
                            "-c:a", "pcm_s24le", str(vo)], check=True)
        new_times = [(t / a.rate, e / a.rate, sc) for t, e, sc in new_times]
    else:
        sf.write(vo, y, SR, subtype="PCM_24")

    dur = sf.info(vo).duration
    timing = {
        "take": a.take, "rate": a.rate, "duration": round(dur, 3),
        "lines": [{"id": li, "text": s["text"]} for li, s in enumerate(segs)],
        "words": [{"i": i, "w": w, "line": line_of[i], "t": round(t, 3), "end": round(e, 3), "score": round(sc, 2)}
                  for i, (w, (t, e, sc)) in enumerate(zip(words, new_times))],
    }
    (outdir / "timing.json").write_text(json.dumps(timing, indent=1))
    weak = [f"{w['w']}({w['score']})" for w in timing["words"] if w["score"] < 0.35]
    print(f"{vo}: {dur:.2f}s, {len(words)} words; weak alignments: {weak or 'none'}")


if __name__ == "__main__":
    main()
