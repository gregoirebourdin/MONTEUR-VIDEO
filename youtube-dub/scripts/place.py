#!/usr/bin/env python3
"""Cut the Charon takes into chunks and lay them on the original video timeline.

  1. forced alignment (wav2vec2 CTC) of each paragraph take → every word's start/end in the take
  2. each chunk (a phrase between two pauses of the speaker) is cut at quiet points
  3. the chunk's first word lands on the moment the speaker starts that phrase in the original video;
     when the English runs longer than the French, it may start up to 0.3 s early into silence, then is
     sped up without pitch change (rubberband, at most ×1.22); anything left over delays the next phrase
  4. the track is normalised to -16 LUFS / -1.5 dBTP (dialogue) and a timing report + SRT are written

Usage: python3 scripts/place.py plan.json takes/ out/
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
import torch
import torchaudio
from scipy.signal import resample_poly

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from common import spoken  # noqa: E402

SR = 48000
MAX_RATE = 1.2
MIN_RATE = 1.0  # never slow the voice down: time-stretching blurs speech
EARLY = 0.3
GAP = 0.12
VOICE_EQ = (
    "highpass=f=75:poles=2,"
    "equalizer=f=250:t=q:w=0.9:g=-4.5,"
    "equalizer=f=480:t=q:w=1.2:g=-2,"
    "equalizer=f=3200:t=q:w=0.9:g=4.5,"
    "highshelf=f=7000:g=3,"
    "deesser=i=0.35:m=0.5:f=0.5,"
    "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=150:knee=6"
)


def load_take(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    return resample_poly(x, SR, sr).astype(np.float32)


BUNDLE = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
MODEL = None


def align(audio48: np.ndarray, words: list[str]):
    """→ [(start, end)] in seconds for every word."""
    global MODEL
    if MODEL is None:
        MODEL = BUNDLE.get_model().eval()
    labels = BUNDLE.get_labels()
    idx = {c: i for i, c in enumerate(labels)}
    a16 = resample_poly(audio48, 16000, SR).astype(np.float32)
    with torch.inference_mode():
        emis, _ = MODEL(torch.from_numpy(a16)[None])
        emis = torch.log_softmax(emis, dim=-1)
    spf = len(a16) / 16000 / emis.shape[1]
    chars, owner = [], []
    for wi, w in enumerate(words):
        for sw in spoken(w).upper().replace("'", "'").split():
            for c in sw:
                if c in idx:
                    chars.append(idx[c])
                    owner.append(wi)
            chars.append(idx["|"])
            owner.append(-1)
    chars, owner = chars[:-1], owner[:-1]
    ali, scores = torchaudio.functional.forced_align(emis, torch.tensor([chars], dtype=torch.int32), blank=0)
    spans = torchaudio.functional.merge_tokens(ali[0], scores[0].exp())
    first, last = {}, {}
    for sp, o in zip(spans, owner):
        if o >= 0:
            first.setdefault(o, sp.start)
            last[o] = sp.end
    out = []
    for wi in range(len(words)):
        if wi in first:
            out.append((first[wi] * spf, last[wi] * spf))
        else:  # word with no alignable letters (should not happen): borrow the neighbour's time
            out.append(out[-1] if out else (0.0, 0.0))
    return out


def quiet_point(x, t, lo, hi):
    """Lowest-energy 10 ms frame between lo and hi (seconds), nearest to t on ties."""
    a, b = max(0, int(lo * SR)), min(len(x), int(hi * SR))
    if b - a < 480:
        return t
    hop = 240
    e = np.array([np.sum(x[i : i + hop] ** 2) for i in range(a, b - hop, hop)])
    if not len(e):
        return t
    k = int(np.argmin(e + 1e-9 * np.abs(np.arange(len(e)) * hop / SR + lo - t)))
    return (a + k * hop + hop // 2) / SR


def stretch(x: np.ndarray, rate: float) -> np.ndarray:
    """Speed up speech without changing pitch (ffmpeg atempo: clean on voice for small ratios)."""
    if abs(rate - 1) < 0.01:
        return x
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/i.wav", x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/i.wav", "-af", f"atempo={rate:.4f}", f"{d}/o.wav"], check=True)
        y, _ = sf.read(f"{d}/o.wav", dtype="float32")
    return y


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    plan_path, takes, out = map(pathlib.Path, sys.argv[1:4])
    length = float(sys.argv[4]) if len(sys.argv) > 4 else None  # exact video length in seconds
    out.mkdir(parents=True, exist_ok=True)
    plan = json.loads(plan_path.read_text())
    words = plan["words"]
    sent_par = {si: p["id"] for p in plan["paragraphs"] for si in p["sentences"]}

    # 1. word times inside each take
    word_take = {}
    audio = {}
    for p in plan["paragraphs"]:
        x = load_take(takes / f"p{p['id']:02d}.wav")
        audio[p["id"]] = x
        wids = [wi for si in p["sentences"] for wi in plan["sentences"][si]["words"]]
        for wi, se in zip(wids, align(x, [words[w]["w"] for w in wids])):
            word_take[wi] = se
        print(f"aligned p{p['id']:02d} ({len(x) / SR:.1f}s)", flush=True)

    # 2. units: a chunk is split again at every cue start that follows a punctuation mark, so the dub
    #    re-syncs with the speaker every few seconds at natural pause points
    units = []
    for ch in plan["chunks"]:
        cur = [ch["words"][0]]
        for a_, b_ in zip(ch["words"], ch["words"][1:]):
            if words[b_]["cue"] != words[a_]["cue"] and words[a_]["w"][-1] in ",.?!:;…":
                units.append({"sent": ch["sent"], "words": cur})
                cur = []
            cur.append(b_)
        units.append({"sent": ch["sent"], "words": cur, "fr_end": ch["fr_end"]})
    for k, u in enumerate(units):
        u["id"] = k
        u["t"] = round(words[u["words"][0]]["t"], 3)
        u["text"] = " ".join(words[i]["w"] for i in u["words"])
    for k, u in enumerate(units):
        if "fr_end" not in u:
            u["fr_end"] = units[k + 1]["t"]
    chunks = units
    for k, ch in enumerate(chunks):
        pid = sent_par[ch["sent"]]
        x = audio[pid]
        s0 = word_take[ch["words"][0]][0]
        s1 = word_take[ch["words"][-1]][1]
        prev_end = word_take[ch["words"][0] - 1][1] if ch["words"][0] - 1 in word_take and sent_par.get(chunks[k - 1]["sent"]) == pid and k > 0 else 0.0
        nxt = ch["words"][-1] + 1
        next_start = word_take[nxt][0] if nxt in word_take and k + 1 < len(chunks) and sent_par[chunks[k + 1]["sent"]] == pid else len(x) / SR
        a = quiet_point(x, s0 - 0.04, max(prev_end, s0 - 0.12), s0 - 0.005)
        b = quiet_point(x, s1 + 0.1, s1 + 0.02, min(next_start, s1 + 0.3))
        clip = x[int(a * SR) : int(b * SR)].copy()
        f = int(0.008 * SR)
        clip[:f] *= np.linspace(0, 1, f)
        clip[-f:] *= np.linspace(1, 0, f)
        ch["clip"] = clip
        ch["lead"] = s0 - a  # silence before the first word inside the clip

    print(f"{len(units)} units")
    # 3. place on the timeline
    total = length if length else plan["duration"] + 2.0
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    cursor = 0.0
    rows = []
    for k, ch in enumerate(chunks):
        clip, lead = ch["clip"], ch["lead"]
        target = ch["t"]
        next_t = chunks[k + 1]["t"] if k + 1 < len(chunks) else (total - 0.05 if length else target + len(clip) / SR + 1)
        onset = max(target, cursor + GAP)
        speech = len(clip) / SR - lead
        avail = next_t - onset - GAP
        fr_span = max(0.3, min(ch["fr_end"], next_t) - onset - 0.1)
        # follow the speaker's pace: slow down a little when English is shorter, speed up when longer
        rate = min(MAX_RATE, max(MIN_RATE, speech / fr_span))
        if speech / rate > avail:
            early = min(EARLY, max(0.0, onset - (cursor + GAP)))
            onset -= early
            avail += early
            rate = min(MAX_RATE, max(rate, speech / max(avail, 0.05)))
        if abs(rate - 1) > 0.01:
            clip = stretch(clip, rate)
            lead /= rate
        at = onset - lead
        i = int(at * SR)
        track[i : i + len(clip)] += clip
        cursor = at + len(clip) / SR
        rows.append({"id": ch["id"], "text": ch["text"], "target": target, "fr_end": round(ch["fr_end"], 3), "onset": round(onset, 3), "end": round(cursor, 3), "rate": round(rate, 3), "late": round(onset - target, 3)})

    track = track[: int(total * SR)]
    raw = out / "dub_raw.wav"
    sf.write(raw, track, SR, subtype="PCM_24")

    # 4. loudness: one constant gain to -16 LUFS, then a look-ahead limiter on the rare peaks above
    #    -1.5 dBTP. (loudnorm switches to dynamic mode on a track like this and pumps.)
    # dialogue EQ: Charon's TTS piles up 150-600 Hz and lacks presence (boxy, "resonant" on its own)
    eq = out / "dub_eq.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", VOICE_EQ, "-c:a", "pcm_f32le", str(eq)], check=True)
    raw = eq
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    import re as _re

    integrated = float(_re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    gain = -16.0 - integrated
    final = out / "dub_en_charon.wav"
    af = f"volume={gain:.2f}dB,alimiter=limit={10 ** (-1.5 / 20):.4f}:attack=2:release=50:level=disabled:latency=1"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", str(final)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-ac", "1", "-c:a", "libmp3lame", "-b:a", "160k", str(out / "dub_en_charon.mp3")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-sample_fmt", "s16", "-c:a", "flac", str(out / "dub_en_charon.flac")], check=True)
    print(f"loudness: {integrated:.1f} LUFS raw, gain {gain:+.1f} dB")

    # report + SRT of the dub as placed
    (out / "dub_timing.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    with open(out / "dub_en_charon.srt", "w") as f:
        for n, r in enumerate(rows, 1):
            f.write(f"{n}\n{srt_time(r['onset'])} --> {srt_time(r['end'])}\n{r['text']}\n\n")
    late = np.array([r["late"] for r in rows])
    rates = np.array([r["rate"] for r in rows])
    print(f"chunks {len(rows)} | on time (≤0.25 s late) {np.mean(late <= 0.25) * 100:.0f}% | mean late {late.mean():.2f}s | max late {late.max():.2f}s")
    print(f"sped up {np.sum(rates > 1.01)} units (max ×{rates.max():.2f}, {np.sum(rates >= MAX_RATE - 0.001)} at the cap), slowed {np.sum(rates < 0.99)}")
    ends = np.array([r["end"] - r["fr_end"] for r in rows])
    print(f"dub ends vs speaker: median {np.median(ends):+.2f}s, 90% within {np.percentile(np.abs(ends), 90):.2f}s")
    print("→", final)


if __name__ == "__main__":
    main()
