#!/usr/bin/env python3
"""Frame-accurate word cues: CTC forced alignment of the script on the edited VO track.

whisper's word starts drift by up to ~0.4 s, which is visible when every spoken word is written
on screen. This re-times the words in timing.json (written by edit_vo.py) with a wav2vec2
character model (torchaudio WAV2VEC2_ASR_BASE_960H), one line at a time.

Usage: python3 scripts/align_words.py film2/timing.json film2/assets/audio/vo.wav
"""
import json
import pathlib
import re
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio
from scipy.signal import resample_poly

# How each script token is pronounced, when its spelling differs from its sound.
SPOKEN = {
    "126": "a hundred and twenty six",
    "9": "nine",
    "p.m.": "p m",
    "dms": "dee ems",
    "dm": "dee em",
    "ai": "ay eye",
    "ten-x": "ten x",
    "manysetter": "many setter",
    "manychat": "many chat",
    "uh": "uh",
}


def spoken(token: str) -> list[str]:
    t = token.lower().strip("\"'“”‘’.,!?…:;")
    t = t.replace("’", "'")
    if t in SPOKEN:
        return SPOKEN[t].split()
    if token.lower().strip("\"“”!?,") in SPOKEN:
        return SPOKEN[token.lower().strip("\"“”!?,")].split()
    t = re.sub(r"[^a-z' ]", " ", t.replace("-", " "))
    return t.split()


def main() -> None:
    timing_path, wav_path = pathlib.Path(sys.argv[1]), sys.argv[2]
    timing = json.loads(timing_path.read_text())
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().eval()
    labels = bundle.get_labels()  # ('-', '|', 'E', 'T', ...)
    idx = {c: i for i, c in enumerate(labels)}
    a16 = resample_poly(audio, bundle.sample_rate, sr).astype(np.float32)

    for ln in timing["lines"]:
        t0 = max(0.0, ln["start"] - 0.15)
        t1 = ln["end"] + 0.15
        seg = torch.from_numpy(a16[int(t0 * 16000) : int(t1 * 16000)])[None]
        with torch.inference_mode():
            emis, _ = model(seg)
            emis = torch.log_softmax(emis, dim=-1)
        sec_per_frame = seg.shape[1] / 16000 / emis.shape[1]

        # Flatten the line into characters, remembering which script token owns each spoken word.
        chars, owner = [], []
        for wi, w in enumerate(ln["words"]):
            for sw in spoken(w["w"]):
                for c in sw.upper():
                    if c in idx:
                        chars.append(idx[c])
                        owner.append(wi)
                chars.append(idx["|"])
                owner.append(-1)
        chars, owner = chars[:-1], owner[:-1]
        targets = torch.tensor([chars], dtype=torch.int32)
        ali, scores = torchaudio.functional.forced_align(emis, targets, blank=0)
        spans = torchaudio.functional.merge_tokens(ali[0], scores[0].exp())
        if len(spans) != len(chars):
            raise SystemExit(f"{ln['id']}: alignment produced {len(spans)} spans for {len(chars)} chars")

        first = {}
        last = {}
        for sp, o in zip(spans, owner):
            if o < 0:
                continue
            first.setdefault(o, sp.start)
            last[o] = sp.end
        for wi, w in enumerate(ln["words"]):
            old = w["t"]
            w["t"] = round(t0 + first[wi] * sec_per_frame, 3)
            w["end"] = round(t0 + last[wi] * sec_per_frame, 3)
            w["dt"] = round(w["t"] - old, 3)
        print(ln["id"], " ".join(f"{w['w']}@{w['t']:.2f}" for w in ln["words"]))
        for w in ln["words"]:
            w.pop("dt", None)
    timing_path.write_text(json.dumps(timing, indent=1))
    print("aligned →", timing_path)


if __name__ == "__main__":
    main()
