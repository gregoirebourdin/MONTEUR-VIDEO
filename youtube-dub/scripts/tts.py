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


def generate(p, out_dir: pathlib.Path, n: int, voice: str, key: str):
    """Network-bound: one take, kept on disk as pNN_tryN.wav (reused if it already exists)."""
    path = out_dir / f"p{p['id']:02d}_try{n}.wav"
    if path.exists():
        return path
    try:
        pcm, rate = tts_gemini.synthesize_interactions(p["text"], STYLE, voice, tts_gemini.DEFAULT_MODEL, key)
    except RuntimeError as e:
        print(f"p{p['id']:02d} try{n} TTS error: {e}", flush=True)
        return None
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--tries", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    plan = json.loads(pathlib.Path(a.plan).read_text())
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    only = {int(x) for x in a.only.split(",") if x}
    todo = [p for p in plan["paragraphs"] if (not only or p["id"] in only) and not (out / f"p{p['id']:02d}.wav").exists()]
    key = tts_gemini.load_key()
    rp = out / "qa.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    # Generation is network-bound (parallel); whisper QA is CPU-bound (one at a time, all cores).
    for n in range(1, a.tries + 1):
        if not todo:
            break
        with cf.ThreadPoolExecutor(a.workers) as ex:
            paths = list(ex.map(lambda p: (p, generate(p, out, n, a.voice, key)), todo))
        failed = []
        for p, path in paths:
            if path is None:
                failed.append(p)
                continue
            ok, diffs, _ = qa(str(path), p["text"])
            report.setdefault(str(p["id"]), {"log": []})["log"].append(f"try{n}: {'PASS' if ok else 'FAIL'} {diffs}")
            report[str(p["id"])]["ok"] = ok
            print(f"p{p['id']:02d} try{n} {'PASS' if ok else 'FAIL'} {diffs}", flush=True)
            if ok:
                (out / f"p{p['id']:02d}.wav").write_bytes(path.read_bytes())
            else:
                failed.append(p)
            rp.write_text(json.dumps(report, indent=1))
        todo = failed
    print("failed paragraphs:", [p["id"] for p in todo] or "none")


if __name__ == "__main__":
    main()
