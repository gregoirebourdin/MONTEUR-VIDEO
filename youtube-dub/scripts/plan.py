#!/usr/bin/env python3
"""Dubbing plan from a translated SRT: rebuild sentences, estimate when each word is spoken,
split into placement chunks (a chunk never spans a pause) and TTS paragraphs.

Subtitle cues cut sentences anywhere and some cues stretch over long silent screen demos, so cue
times are not word times. Heuristic:
  - normal cue: words are spread over the cue in proportion to their characters;
  - long cue (much longer than its text needs): the words up to the last sentence break are spoken
    at the cue start, the words after it (the start of the next sentence) right before the cue end.

Usage: python3 scripts/plan.py source/<file>.srt plan.json
"""
import json
import re
import sys

CPS = 15.0  # characters per second of the original speech (French, ~15 cps)

# Manual cleanups of the translation, applied before planning (listed in the report).
EDITS = [
    # a false start the speaker repeats right after
    (r"Once that's done, you can… Once that's done, you can see", "Once that's done, you can see"),
    # a false start while typing
    (r"ask, for example, I want… And type here: I want a better tone with emoji face\.", "ask, for example, by typing here: I want a better tone, with emojis."),
    (r"\bMany Chat\b", "ManyChat"),
    (r"\bMany Setter\b", "ManySetter"),
]


def ts(s: str) -> float:
    h, m, rest = s.strip().split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + float(ms) / 1000


def parse_srt(path):
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8-sig").read().strip())
    cues = []
    for b in blocks:
        lines = [l for l in b.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        a, z = lines[1].split("-->")
        cues.append({"i": int(lines[0]), "start": ts(a), "end": ts(z), "text": " ".join(lines[2:]).strip()})
    return cues


SENT_END = re.compile(r"[.?!…]$")


def main():
    src, out = sys.argv[1], sys.argv[2]
    cues = parse_srt(src)

    # word stream with the cue each word comes from
    words = []
    for c in cues:
        for w in c["text"].split():
            words.append({"w": w, "cue": c["i"]})
    full = " ".join(w["w"] for w in words)
    edited = full
    applied = []
    for pat, rep in EDITS:
        new = re.sub(pat, rep, edited)
        if new != edited:
            applied.append((pat, rep))
        edited = new

    # Re-attach edited words to cues: diff the token streams and give inserted words the cue of the
    # nearest kept neighbour.
    import difflib

    a = [w["w"] for w in words]
    b = edited.split()
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    new_words = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            new_words += [dict(words[i1 + k]) for k in range(i2 - i1)]
        elif tag in ("replace", "insert"):
            cue = words[i1]["cue"] if i1 < len(words) else words[-1]["cue"]
            if tag == "replace" and i2 > i1:
                cue = words[i2 - 1]["cue"] if b[j2 - 1] == a[i2 - 1] else words[i1]["cue"]
            new_words += [{"w": b[j], "cue": cue} for j in range(j1, j2)]
    words = new_words
    by_cue = {c["i"]: c for c in cues}

    # estimated time of each word
    for ci, c in by_cue.items():
        ws = [w for w in words if w["cue"] == ci]
        if not ws:
            continue
        text = " ".join(w["w"] for w in ws)
        dur = c["end"] - c["start"]
        need = len(text) / CPS
        long_cue = dur > need * 1.5 + 1.5
        c["long"] = long_cue
        if not long_cue:
            pos = 0
            for w in ws:
                w["t"] = c["start"] + dur * pos / max(1, len(text))
                pos += len(w["w"]) + 1
            continue
        # split point: last sentence end or colon inside the cue (not on the last word)
        split = None
        for k in range(len(ws) - 1):
            if re.search(r"[.?!…:]$", ws[k]["w"]):
                split = k
        head = ws if split is None else ws[: split + 1]
        tail = [] if split is None else ws[split + 1 :]
        pos = 0
        for w in head:
            w["t"] = c["start"] + pos / CPS
            pos += len(w["w"]) + 1
        tail_len = sum(len(w["w"]) + 1 for w in tail)
        pos = 0
        for w in tail:
            w["t"] = c["end"] - tail_len / CPS + pos / CPS
            pos += len(w["w"]) + 1

    # sentences
    sentences, cur = [], []
    for k, w in enumerate(words):
        cur.append(k)
        nxt = words[k + 1]["w"] if k + 1 < len(words) else ""
        if SENT_END.search(w["w"]) and (not nxt or nxt[0].isupper() or nxt[0].isdigit()):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)

    # chunks: split a sentence where the speaker pauses
    chunks = []
    for si, s in enumerate(sentences):
        cur = [s[0]]
        for a_, b_ in zip(s, s[1:]):
            natural = (len(words[a_]["w"]) + 1) / CPS
            if words[b_]["t"] - words[a_]["t"] > natural + 1.0:
                chunks.append({"sent": si, "words": cur})
                cur = []
            cur.append(b_)
        chunks.append({"sent": si, "words": cur})
    for k, ch in enumerate(chunks):
        ws = ch["words"]
        ch["id"] = k
        ch["text"] = " ".join(words[i]["w"] for i in ws)
        ch["t"] = round(words[ws[0]]["t"], 3)
        last = words[ws[-1]]
        ch["fr_end"] = round(last["t"] + (len(last["w"]) + 1) / CPS, 3)
    for k, ch in enumerate(chunks):
        ch["next_t"] = chunks[k + 1]["t"] if k + 1 < len(chunks) else ch["fr_end"] + 3.0

    # TTS paragraphs: consecutive sentences, broken at long pauses or ~650 characters
    paras, cur, chars = [], [], 0
    for si, s in enumerate(sentences):
        t0 = words[s[0]]["t"]
        if cur:
            prev_end = words[sentences[cur[-1]][-1]]["t"]
            if t0 - prev_end > 5.0 or chars > 650:
                paras.append(cur)
                cur, chars = [], 0
        cur.append(si)
        chars += sum(len(words[i]["w"]) + 1 for i in s)
    if cur:
        paras.append(cur)

    plan = {
        "source": src,
        "duration": max(c["end"] for c in cues),
        "edits": [{"from": p, "to": r} for p, r in applied],
        "words": words,
        "sentences": [{"id": i, "words": s, "text": " ".join(words[k]["w"] for k in s)} for i, s in enumerate(sentences)],
        "chunks": chunks,
        "paragraphs": [{"id": i, "sentences": p, "text": " ".join(" ".join(words[k]["w"] for k in sentences[si]) for si in p)} for i, p in enumerate(paras)],
    }
    json.dump(plan, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(cues)} cues → {len(sentences)} sentences, {len(chunks)} chunks, {len(paras)} TTS paragraphs; {len(applied)} edits")
    print("long cues:", sum(1 for c in cues if c.get("long")))


if __name__ == "__main__":
    main()
