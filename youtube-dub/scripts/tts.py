#!/usr/bin/env python3
"""Charon takes for every TTS paragraph of the plan, each checked word by word with whisper.

A paragraph is retried (up to --tries) until whisper hears every word: no dropped or invented words,
at most two single-word spelling differences (numbers, brand names).
Usage: python3 scripts/tts.py plan.json takes/ [--voice Charon] [--only 3,7]
"""
import argparse
import concurrent.futures as cf
import difflib
import json
import pathlib
import sys
import wave

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent.parent / "manysetter-ad/scripts"))
import check_vo  # noqa: E402
import tts_gemini  # noqa: E402
from common import norm_words  # noqa: E402

STYLE = (
    "A friendly, upbeat YouTube tutorial host talking to his viewers while sharing his screen. "
    "Natural and conversational, energetic but relaxed, a little enthusiastic, medium-fast pace, clear diction."
)


def qa(wav: str, text: str):
    heard, _ = check_vo.transcribe(wav, "en")
    want, got = norm_words(text), norm_words(heard)
    ops = [o for o in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_opcodes() if o[0] != "equal"]
    diffs = [(o[0], " ".join(want[o[1] : o[2]]), " ".join(got[o[3] : o[4]])) for o in ops]
    minor = all(o[0] == "replace" and o[2] - o[1] <= 1 and o[4] - o[3] <= 2 for o in ops) and len(ops) <= 2
    return (not ops or minor), diffs, heard


def make(p, out_dir: pathlib.Path, voice: str, tries: int, key: str):
    log = []
    for n in range(1, tries + 1):
        path = out_dir / f"p{p['id']:02d}_try{n}.wav"
        try:
            pcm, rate = tts_gemini.synthesize_interactions(p["text"], STYLE, voice, tts_gemini.DEFAULT_MODEL, key)
        except RuntimeError as e:
            log.append(f"try{n}: {e}")
            continue
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm)
        ok, diffs, heard = qa(str(path), p["text"])
        log.append(f"try{n}: {'PASS' if ok else 'FAIL'} {diffs}")
        if ok:
            final = out_dir / f"p{p['id']:02d}.wav"
            final.write_bytes(path.read_bytes())
            return p["id"], True, log
    return p["id"], False, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--tries", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    plan = json.loads(pathlib.Path(a.plan).read_text())
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    only = {int(x) for x in a.only.split(",") if x}
    todo = [p for p in plan["paragraphs"] if (not only or p["id"] in only) and not (out / f"p{p['id']:02d}.wav").exists()]
    key = tts_gemini.load_key()
    report = {}
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for pid, ok, log in ex.map(lambda p: make(p, out, a.voice, a.tries, key), todo):
            report[pid] = {"ok": ok, "log": log}
            print(f"p{pid:02d} {'OK ' if ok else 'BAD'} " + " | ".join(log), flush=True)
    rp = out / "qa.json"
    old = json.loads(rp.read_text()) if rp.exists() else {}
    old.update({str(k): v for k, v in report.items()})
    rp.write_text(json.dumps(old, indent=1))
    bad = [k for k, v in report.items() if not v["ok"]]
    print("failed paragraphs:", bad or "none")


if __name__ == "__main__":
    main()
