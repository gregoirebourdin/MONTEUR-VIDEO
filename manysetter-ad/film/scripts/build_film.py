#!/usr/bin/env python3
"""Assemble the film: scene windows from the VO timing, cue substitution, index.html.

Everything is derived from timing.json (written by ../scripts/edit_vo.py), so a new voice
take re-times the whole film by re-running both scripts.

Cue placeholders inside src/frames/*.html (seconds, relative to the scene's own start):
  {{cue:L4.voice}}    first word "voice" of line L4
  {{cue:L4.voice#2}}  second occurrence
  {{cue:L4.start}}    line start / {{cue:L4.end}} line end
  {{dur}}             scene duration
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_frames  # noqa: E402

T = json.loads((ROOT / "timing.json").read_text())
LINES = {l["id"]: l for l in T["lines"]}


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def cue_abs(key: str) -> float:
    line_id, word = key.split(".", 1)
    ln = LINES[line_id]
    if word == "start":
        return ln["start"]
    if word == "end":
        return ln["end"]
    occ = 1
    if "#" in word:
        word, n = word.split("#")
        occ = int(n)
    hits = [w["t"] for w in ln["words"] if norm(w["w"]).startswith(norm(word))]
    if len(hits) < occ:
        raise SystemExit(f"cue not found: {key}")
    return hits[occ - 1]


L = lambda i: LINES[f"L{i}"]  # noqa: E731

# Scene windows (film seconds). Overlap = how long the scene keeps playing under the next one.
S = []


def scene(name: str, cid: str, start: float, end: float, overlap: float = 0.0) -> None:
    S.append({"name": name, "id": cid, "start": round(start, 3), "end": round(end, 3), "overlap": overlap})


scene("01-thread", "f01", 0.0, L(2)["start"] - 0.15)
scene("03-quiet", "f03", L(2)["start"] - 0.15, L(2)["end"] + 0.55)
scene("04-logo", "f04", S[-1]["end"], L(4)["start"] - 0.25, overlap=0.45)
scene("05-learns", "f05", L(4)["start"] - 0.25, L(5)["start"] - 0.15, overlap=0.35)
scene("06-qualifies", "f06", L(5)["start"] - 0.15, L(6)["start"] - 0.3, overlap=0.3)
scene("07-booked", "f07", L(6)["start"] - 0.3, L(7)["start"] - 0.15, overlap=0.3)
scene("08-control", "f08", L(7)["start"] - 0.15, L(8)["start"] - 0.2, overlap=0.3)
scene("09-cta", "f09", L(8)["start"] - 0.2, L(8)["end"] + 1.6, overlap=0.5)
scene("10-endcard", "f10", S[-1]["end"], S[-1]["end"] + 3.8)
TOTAL = round(S[-1]["end"], 3)


def build_scene(sc: dict) -> None:
    src = ROOT / "src/frames" / f"{sc['name']}.html"
    if not src.exists():
        return
    text = src.read_text()
    dur = sc["end"] - sc["start"] + sc["overlap"]

    def rep(m: re.Match) -> str:
        return f"{cue_abs(m.group(1)) - sc['start']:.3f}"

    text = re.sub(r"\{\{cue:([A-Za-z0-9#.]+)\}\}", rep, text)
    text = text.replace("{{dur}}", f"{dur:.3f}").replace("{{hold}}", f"{sc['end'] - sc['start']:.3f}")
    tmp = ROOT / ".hyperframes" / "src" / src.name
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text)
    build_frames.build(tmp)


def write_index() -> None:
    hosts = []
    for i, sc in enumerate(S):
        if not (ROOT / "src/frames" / f"{sc['name']}.html").exists():
            continue
        dur = sc["end"] - sc["start"] + sc["overlap"]
        hosts.append(
            f'      <div id="{sc["id"]}" class="clip" data-composition-id="{sc["id"]}" '
            f'data-composition-src="compositions/frames/{sc["name"]}.html" data-start="{sc["start"]:.3f}" '
            f'data-duration="{dur:.3f}" data-track-index="{i % 2}" data-width="1920" data-height="1080" '
            f'style="z-index: {i + 1}"></div>'
        )
    audio = []
    for a in AUDIO:
        if (ROOT / a["src"]).exists():
            audio.append(
                f'      <audio id="{a["id"]}" src="{a["src"]}" data-start="{a.get("start", 0)}" '
                f'data-duration="{a.get("duration", TOTAL)}" data-track-index="{a["track"]}" data-volume="{a.get("volume", 1)}"></audio>'
            )
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <link rel="stylesheet" href="assets/ms.css" />
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #0d0c0a; }}
      #root {{ position: relative; width: 100%; height: 100%; background: #0d0c0a; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-fps="60" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
{chr(10).join(audio)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(html)


AUDIO = [
    {"id": "vo", "src": "assets/audio/vo.wav", "track": 10, "volume": 1},
    {"id": "music", "src": "assets/audio/music.wav", "track": 11, "volume": 0.75},
    {"id": "sfx", "src": "assets/audio/sfx.wav", "track": 12, "volume": 0.8},
]

if __name__ == "__main__":
    for sc in S:
        build_scene(sc)
    write_index()
    (ROOT / "scenes.json").write_text(json.dumps({"total": TOTAL, "scenes": S}, indent=1))
    for sc in S:
        print(f"{sc['id']} {sc['name']:<14} {sc['start']:6.2f} → {sc['end']:6.2f}  (+{sc['overlap']})")
    print("total", TOTAL)
