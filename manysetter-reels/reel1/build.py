#!/usr/bin/env python3
"""Reel 1 "The challenge": word timing → captions, bleeps and scene cues → index.html + cues.json.

Every cue in the picture and in the sound comes from the aligned voice (../vo/reel1/timing.json),
so a new take re-times the whole reel. Usage: python3 reel1/build.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TIMING = json.loads((HERE.parent / "vo/reel1/timing.json").read_text())
W = TIMING["words"]
TAIL = 1.6  # end hold after the last word (CTA, loop)
TOTAL = round(W[-1]["end"] + TAIL, 2)


def t(i):
    return W[i]["t"]


def e(i):
    return W[i]["end"]


ICONS = ["arrow-down", "hand", "moon", "message-circle", "arrow-up", "book-open", "file-text", "calendar-check", "calendar-days"]

# swear words: bleeped in the mix, censor bar on Setty's mouth and over the caption
BLEEPS = [1, 5, 79]

# caption chunks: (first word, last word, options). Words appear one by one on their own cue.
#   accent: orange words · display: replaced text · hide: words shown by a prop instead · hero: big
CHUNKS = [
    (0, 0, {}),
    (1, 1, {"hide": True}),  # the hook is a close-up: the censor bar on Setty's mouth is the caption
    (2, 4, {}),
    (5, 5, {}),
    (6, 7, {"accent": [6], "hero": True}),
    (8, 10, {"accent": [10]}),
    (11, 12, {"accent": [12]}),
    (13, 16, {}),
    (17, 18, {}),
    (19, 21, {"accent": [19], "display": {19: "400", 20: ""}, "hero": True, "count": [19]}),
    (22, 25, {"display": {25: "like…"}}),
    (26, 26, {"hide": True}),
    (27, 30, {"display": {30: "them…"}}),
    (31, 32, {"accent": [32], "hero": True}),
    (33, 34, {"accent": [34]}),
    (35, 36, {"accent": [36]}),
    (37, 40, {}),
    (41, 44, {"accent": [43, 44]}),
    (45, 48, {"accent": [48], "display": {48: "Manychat."}}),
    (49, 52, {"accent": [52]}),
    (53, 56, {"accent": [56]}),
    (57, 59, {}),
    (60, 63, {"display": {60: "“I’ll", 63: "it”…"}}),
    (64, 68, {"accent": [68]}),
    (69, 71, {"accent": [71]}),
    (72, 72, {"accent": [72], "hero": True}),
    (73, 75, {"accent": [75]}),
    (76, 78, {}),
    (79, 79, {}),
    (80, 81, {"accent": [81]}),
    (82, 86, {"accent": [86], "hold": 0.3}),
]


def chunks():
    out = []
    for k, (a, b, o) in enumerate(CHUNKS):
        nxt = t(CHUNKS[k + 1][0]) if k + 1 < len(CHUNKS) else TOTAL
        toks = []
        for i in range(a, b + 1):
            txt = o.get("display", {}).get(i, W[i]["w"])
            if txt == "":
                continue
            toks.append({"i": i, "text": txt.replace('"', ""), "t": t(i), "accent": i in o.get("accent", []),
                         "bleep": i in BLEEPS, "count": i in o.get("count", [])})
        out.append({"id": k, "start": t(a), "end": min(nxt, e(b) + o.get("hold", 0.9)), "next": nxt, "hide": o.get("hide", False),
                    "hero": o.get("hero", False), "tokens": toks})
    return out


# scene cues, in seconds (shared with the sound design)
CUES = {
    "total": TOTAL,
    "hey": t(0), "bleep1": t(1), "youdid": t(2), "bleep2": t(5), "challenge": t(6), "right": t(7),
    "five": t(8), "days": t(9), "live": t(10), "voice": t(11), "dead": t(12), "ring": t(13), "stillon": t(15),
    "andnow": t(17), "four": t(19), "people": t(21), "dms": t(24), "like": t(25), "info": t(26), "info_end": e(26),
    "answer": t(27), "byhand": t(31), "hand": t(32), "midnight": t(34), "inbed": t(35), "bed": t(36),
    "business": t(37), "business_end": e(40), "hostage_line": t(41), "hostage": t(43), "situation": t(44),
    "situation_end": e(44),
    "plug": t(45), "manychat": t(48), "manychat_end": e(48),
    "learn": t(49), "offer": t(52), "talk": t(53), "likeyou": t(56), "handle": t(57), "illthink": t(60),
    "thinkend": e(63), "andbook": t(64), "call": t(68), "inyour": t(69), "calendar": t(71), "calendar_end": e(71),
    "you": t(72), "gosleep": t(73), "sleep": t(75), "youlook": t(76), "bleep3": t(79),
    "comment": t(80), "setty": t(81), "slide": t(83), "dms_end": e(86), "end": e(86),
}


def main():
    lucide = json.loads((HERE.parent / "assets/ui/lucide.json").read_text())
    lucide.setdefault("arrow-down", '<path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>')  # Lucide arrow-down
    icons = {k: lucide[k] for k in ICONS}
    data = {"words": [{k: w[k] for k in ("w", "t", "end")} for w in W], "chunks": chunks(), "cues": CUES,
            "bleeps": [{"i": i, "t": t(i), "end": e(i)} for i in BLEEPS], "icons": icons}
    (HERE / "cues.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    src = (HERE / "src/template.html").read_text()
    html = src.replace("/*DATA*/", "const DATA = " + json.dumps(data, ensure_ascii=False) + ";")
    html = html.replace("{{TOTAL}}", f"{TOTAL:.2f}")
    (HERE / "index.html").write_text(html)
    print(f"reel1: {TOTAL:.2f}s, {len(data['chunks'])} caption chunks → index.html, cues.json")


if __name__ == "__main__":
    main()
