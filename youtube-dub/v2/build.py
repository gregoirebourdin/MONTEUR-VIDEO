#!/usr/bin/env python3
"""From the original French SRT + segments.py:
  out/YOUTUBE_VIDEO_FR_corrige.srt   corrected French, original timings
  out/YOUTUBE_VIDEO_EN-US.srt        American English, same timings
  plan.json                          dub plan for ../scripts/tts.py and ../scripts/place.py

Each phrase keeps the timing of the cues it covers. Its words are spread over those cues in
proportion to each cue's duration, cut at word boundaries, so the subtitles follow the speaker.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))
from plan import parse_srt  # noqa: E402
from segments import NOTES, SEGMENTS  # noqa: E402

MAX_LINE = 42


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def wrap(text):
    if len(text) <= MAX_LINE:
        return text
    mid = len(text) // 2
    spaces = [i for i, c in enumerate(text) if c == " "]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut] + "\n" + text[cut + 1 :]


def distribute(words, cues):
    """Split a phrase's words over its cues in proportion to their durations (≥1 word per cue)."""
    if len(cues) == 1 or len(words) <= 1:
        return [(cues[0]["start"], cues[-1]["end"], " ".join(words))]
    if len(words) < len(cues):
        out = [(c["start"], c["end"], w) for c, w in zip(cues, words)]
        s, _, w = out[-1]
        out[-1] = (s, cues[-1]["end"], w)
        return out
    durs = [c["end"] - c["start"] for c in cues]
    total = sum(durs)
    chars = [len(w) + 1 for w in words]
    ctot = sum(chars)
    bounds, acc, k = [], 0.0, 0
    for d in durs[:-1]:
        acc += d / total
        # first word index whose cumulative character share passes the cue boundary
        run = 0
        idx = 0
        for i, c in enumerate(chars):
            if run + c / 2 >= acc * ctot:
                idx = i
                break
            run += c
        else:
            idx = len(words) - 1
        bounds.append(idx)
    # enforce strictly increasing cut points, at least one word per cue
    cuts, prev = [], 0
    for i, b in enumerate(bounds):
        b = max(b, prev + 1)
        b = min(b, len(words) - (len(bounds) - i))
        cuts.append(b)
        prev = b
    edges = [0] + cuts + [len(words)]
    return [(cues[i]["start"], cues[i]["end"], " ".join(words[edges[i] : edges[i + 1]])) for i in range(len(cues))]


def write_srt(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for n, (a, b, text) in enumerate(rows, 1):
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{wrap(text)}\n\n")


def main():
    cues = {c["i"]: c for c in parse_srt(HERE / "source/YOUTUBE_VIDEO_FR.srt")}
    # coverage check: every cue exactly once, in order, except the dropped ones
    covered = [i for a, b, *_ in SEGMENTS for i in range(a, b + 1)]
    dropped = sorted(set(cues) - set(covered))
    assert covered == sorted(covered) and len(covered) == len(set(covered)), "segments overlap or are out of order"
    print("dropped cues:", dropped)

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    fr_rows, en_rows = [], []
    words, sentences, chunks, segs = [], [], [], []
    for sid, (a, b, fr, en) in enumerate(SEGMENTS):
        cs = [cues[i] for i in range(a, b + 1)]
        fr_rows += distribute(fr.split(), cs)
        en_rows += distribute(en.split(), cs)
        t0, t1 = cs[0]["start"], cs[-1]["end"]
        wids = []
        for w in en.split():
            wids.append(len(words))
            words.append({"w": w, "cue": a, "t": t0})
        sentences.append({"id": sid, "words": wids, "text": en})
        chunks.append({"id": sid, "sent": sid, "words": wids, "text": en, "t": round(t0, 3), "fr_end": round(t1, 3)})
        segs.append({"id": sid, "cues": [a, b], "start": t0, "end": t1, "fr": fr, "en": en})
    for k, ch in enumerate(chunks):
        ch["next_t"] = chunks[k + 1]["t"] if k + 1 < len(chunks) else ch["fr_end"] + 3.0

    # TTS paragraphs: consecutive phrases close in time, up to ~600 characters (one natural take each)
    paras, cur, chars = [], [], 0
    for s in segs:
        if cur and (s["start"] - segs[cur[-1]]["end"] > 3.0 or chars > 600):
            paras.append(cur)
            cur, chars = [], 0
        cur.append(s["id"])
        chars += len(s["en"]) + 1
    paras.append(cur)

    write_srt(out / "YOUTUBE_VIDEO_FR_corrige.srt", fr_rows)
    write_srt(out / "YOUTUBE_VIDEO_EN-US.srt", en_rows)
    plan = {
        "source": "v2/source/YOUTUBE_VIDEO_FR.srt",
        "duration": max(c["end"] for c in cues.values()),
        "notes": NOTES,
        "words": words,
        "sentences": sentences,
        "chunks": chunks,
        "segments": segs,
        "paragraphs": [{"id": i, "sentences": p, "text": " ".join(segs[s]["en"] for s in p)} for i, p in enumerate(paras)],
    }
    (HERE / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"{len(SEGMENTS)} phrases, {len(fr_rows)} subtitles, {len(paras)} TTS paragraphs, video {plan['duration'] / 60:.2f} min")


if __name__ == "__main__":
    main()
