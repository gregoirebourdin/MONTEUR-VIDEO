#!/usr/bin/env python3
"""Build the v7 film: kinetic VO type + scene templates + index.html, all timed from timing.json.

  timing.json (edit_vo.py + align_words.py)  →  word cues in film seconds
  scripts/spec.py                            →  what is written on screen, beat by beat
  src/scenes/sN.html                         →  scene UI (cue placeholders, see below)
  src/bg/*.html                              →  long background layers (night, day)

Placeholders in src/**/*.html (times are seconds relative to the composition's own start):
  {{cue:P5.sales}}  {{cue:P5.sales#2}}  word start      {{end:P5.sales}}  word end
  {{cue:P5.start}}  {{cue:P5.end}}      line bounds
  {{bin:3}}  {{bout:3}}                 beat 3 of this scene: first word / exit time
  {{abs:s6}}                            absolute start of scene s6 (for background layers)
  {{dur}}  {{hold}}                     composition duration / time before the outgoing hand-off
  {{kt}}  {{kt_js}}                     the generated kinetic type layer and its tweens
  {{fonts}}  {{i:icon[:cls]}}  {{b:brand[:cls]}}
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from spec import SCENES  # noqa: E402

T = json.loads((ROOT / "timing.json").read_text())
LINES = {l["id"]: l for l in T["lines"]}
LUCIDE = json.loads((ROOT / "assets/lucide.json").read_text())
FONTS = """@font-face { font-family: "Nohemi"; src: url("assets/fonts/Nohemi-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
@font-face { font-family: "Nohemi"; src: url("assets/fonts/Nohemi-600.woff2") format("woff2"); font-weight: 600; font-display: block; }
@font-face { font-family: "Inter"; src: url("assets/fonts/Inter-var.woff2") format("woff2"); font-weight: 100 900; font-display: block; }"""

OVAL = "M166 5C130 3 70 3 26 5.5C11 6.5 3 19 3 32C3 46 9.9 58 26 59.5C70 61.5 130 61.5 174 59C190.1 58 197 45 197 30.5C197 17 189 7 170 6C150 5 120 6 96 8"
UNDER = "M3 14.5C46 8.2 118 6.1 197 9.8"
END_CARD = 4.2  # seconds of end card after the last word
FLAGS = ("slam", "pop", "soft", "count", "rise", "sink")


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


# ----------------------------------------------------------------------------- scene windows

def part(sc):
    return LINES[sc["part"]]


for k, sc in enumerate(SCENES):
    if k == 0:
        sc["start"] = 0.0
    else:
        prev = part(SCENES[k - 1])
        sc["start"] = round((prev["end"] + part(sc)["start"]) / 2, 3)
for k, sc in enumerate(SCENES):
    sc["end"] = SCENES[k + 1]["start"] if k + 1 < len(SCENES) else round(part(sc)["end"] + END_CARD, 3)
    sc["overlap"] = 0.3 if k + 1 < len(SCENES) else 0.0  # the outgoing scene finishes its exits under the next one
TOTAL = SCENES[-1]["end"]
SC = {sc["id"]: sc for sc in SCENES}


def cue_abs(key: str, field: str = "t") -> float:
    line_id, word = key.split(".", 1)
    ln = LINES[line_id]
    if word in ("start", "end"):
        return ln[word]
    occ = 1
    if "#" in word:
        word, n = word.split("#")
        occ = int(n)
    hits = [w for w in ln["words"] if norm(w["w"]) == norm(word)] or [w for w in ln["words"] if norm(w["w"]).startswith(norm(word))]
    if len(hits) < occ:
        raise SystemExit(f"cue not found: {key}")
    return hits[occ - 1][field]


# ----------------------------------------------------------------------------- beat parsing

def parse(text: str):
    """→ list of lines; each line a list of items {disp, spoken, acc, soft, fx, group, mark}."""
    shown = {}

    def stash(m):
        k = f"\x00{len(shown)}"
        shown[k] = (m.group(1), m.group(2).split())
        return k

    text = re.sub(r"\[\[(.+?)\|\|(.+?)\]\]", stash, text)
    lines, cur, group, gid = [], [], None, 0
    for tok in text.split():
        if tok == "|":
            lines.append(cur)
            cur = []
            continue
        it = {"acc": False, "soft": False, "fx": None, "group": None, "mark": None}
        if tok.startswith("{"):
            gid += 1
            group = gid
            tok = tok[1:]
        m = re.search(r"\}~([ou])$", tok)
        close = None
        if m:
            close = m.group(1)
            tok = tok[: m.start()]
        m = re.search(r"!(" + "|".join(FLAGS) + r")$", tok)
        if m:
            it["fx"] = m.group(1)
            tok = tok[: m.start()]
        if tok.startswith("*"):
            it["acc"], tok = True, tok[1:]
        elif tok.startswith("_"):
            it["soft"], tok = True, tok[1:]
        if tok in shown:
            it["disp"], it["spoken"] = shown[tok]
        else:
            it["disp"], it["spoken"] = tok, [tok]
        it["group"] = group
        if close:
            it["mark"] = close
            group = None
        cur.append(it)
    lines.append(cur)
    return lines


_FONT = None


def text_width(s: str, size: float) -> float:
    """Advance width of a line in Nohemi 600 with the film's tracking (kerning ignored, ~3%)."""
    global _FONT
    if _FONT is None:
        from fontTools.ttLib import TTFont

        f = TTFont(str(ROOT / "assets/fonts/Nohemi-600.woff2"))
        _FONT = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    cmap, hmtx, upm = _FONT
    return sum(hmtx[cmap.get(ord(c)) or cmap[ord("o")]][0] / upm * size - 0.045 * size for c in s)


MAX_W = {"left": 900, "center": 1680, "top": 1680, "bottom": 1680}


def check_widths():
    bad = 0
    for sc in SCENES:
        for b in sc["beats"]:
            if b.get("ui"):
                continue
            for ln in b["lines"]:
                w = text_width(" ".join(it["disp"] for it in ln), b.get("size", 120))
                if w > MAX_W[b.get("pos", "center")]:
                    bad += 1
                    print(f"  ! {sc['id']} line too wide ({w:.0f}px > {MAX_W[b.get('pos', 'center')]}): {' '.join(it['disp'] for it in ln)}")
    return bad


def resolve():
    """Attach word times to every beat item and check the words against the voice."""
    for sc in SCENES:
        words = part(sc)["words"]
        ptr = 0
        for b in sc["beats"]:
            b["lines"] = parse(b["t"])
            for ln in b["lines"]:
                for it in ln:
                    ts = []
                    for sp in it["spoken"]:
                        if ptr >= len(words) or norm(words[ptr]["w"]) != norm(sp):
                            got = words[ptr]["w"] if ptr < len(words) else "<end>"
                            raise SystemExit(f"{sc['id']}: beat word {sp!r} ≠ voice word {got!r} (beat: {b['t']})")
                        ts.append(words[ptr])
                        ptr += 1
                    it["t"], it["end"] = ts[0]["t"], ts[-1].get("end", ts[-1]["t"] + 0.3)
            items = [it for ln in b["lines"] for it in ln]
            b["t_in"], b["t_last"], b["t_end"] = items[0]["t"], items[-1]["t"], items[-1]["end"]
        if ptr != len(words):
            raise SystemExit(f"{sc['id']}: {len(words) - ptr} voice words not on screen: {[w['w'] for w in words[ptr:]]}")
        text_beats = [b for b in sc["beats"] if not b.get("ui")]
        for i, b in enumerate(text_beats):
            nxt = text_beats[i + 1] if i + 1 < len(text_beats) else None
            if "out" in b:
                if b["out"] == "hold":
                    b["t_out"] = None if sc is SCENES[-1] else sc["end"] - 0.26
                else:
                    b["t_out"] = b["out"]
            elif nxt:
                b["t_out"] = nxt["t_in"] - 0.2
            else:
                b["t_out"] = sc["end"] - 0.1  # finishes under the next scene (scenes overlap)


# ----------------------------------------------------------------------------- kinetic layer

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kinetic(sc: dict):
    sid, t0 = sc["id"], sc["start"]
    html, js, events = [], [], []
    rel = lambda t: round(t - t0, 3)  # noqa: E731
    wn = 0
    for bi, b in enumerate(sc["beats"]):
        if b.get("ui"):
            continue
        theme = b.get("theme", sc["theme"])
        fx_default = b.get("fx", "rise")
        bid = f"{sid}-b{bi}"
        out_lines = []
        shakes = []
        for ln in b["lines"]:
            parts, open_group = [], None
            for it in ln:
                wn += 1
                wid = f"{sid}-w{wn}"
                fx = it["fx"] or fx_default
                cls = "kt-w" + (" kt-acc" if it["acc"] else "") + (" kt-soft" if it["soft"] else "")
                if fx == "count":
                    inner = f'<span class="kt-count"><span class="kt-sizer">{esc(it["disp"])}</span><span class="kt-num" id="{wid}-n">0</span></span>'
                else:
                    inner = esc(it["disp"])
                wrap = "kt-clip" if fx in ("rise", "sink") else "kt-noclip"
                word = f'<span class="{cls}" data-layout-allow-overflow><span class="{wrap}"><span class="kt-wi" id="{wid}">{inner}</span></span></span>'
                if it["group"] and open_group != it["group"]:
                    parts.append(f'<span class="kt-grp" id="{sid}-g{it["group"]}-{bi}">')
                    open_group = it["group"]
                parts.append(word)
                if it["mark"]:
                    kind = "oval" if it["mark"] == "o" else "under"
                    vb = "0 0 200 64" if kind == "oval" else "0 0 200 20"
                    d = OVAL if kind == "oval" else UNDER
                    mid = f"{sid}-m{it['group']}-{bi}"
                    parts.append(f'<svg class="kt-mark {kind}" viewBox="{vb}" preserveAspectRatio="none"><path id="{mid}" pathLength="1" stroke-dasharray="1 2" stroke-dashoffset="1" d="{d}" /></svg></span>')
                    open_group = None
                    first = next(x for x in ln if x["group"] == it["group"])
                    tm = first["t"] + 0.1
                    js.append(f'tl.fromTo("#{mid}", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.72, ease: "power2.inOut" }}, {rel(tm)});')
                    events.append({"t": round(tm, 3), "kind": "mark", "scene": sid})
                # entrance
                t = it["t"]
                if fx == "sink":  # rises in, then loses its strength
                    js.append(f'tl.fromTo("#{wid}", {{ yPercent: 140, rotation: 5 }}, {{ yPercent: 0, rotation: 0, duration: 0.62, ease: "expo.out" }}, {rel(t - 0.05)});')
                    js.append(f'tl.to("#{wid}", {{ opacity: 0.32, y: 10, filter: "blur(1.5px)", duration: 1.1, ease: "power1.inOut" }}, {rel(it["end"] + 0.1)});')
                elif fx == "rise":
                    js.append(f'tl.fromTo("#{wid}", {{ yPercent: 140, rotation: 5 }}, {{ yPercent: 0, rotation: 0, duration: 0.62, ease: "expo.out" }}, {rel(t - 0.05)});')
                elif fx == "slam":
                    js.append(f'tl.fromTo("#{wid}", {{ opacity: 0, scale: 1.85, filter: "blur(16px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.34, ease: "power4.out" }}, {rel(t - 0.03)});')
                    shakes.append(t)
                elif fx == "pop":
                    js.append(f'tl.fromTo("#{wid}", {{ opacity: 0, scale: 0.3 }}, {{ opacity: 1, scale: 1, duration: 0.55, ease: "back.out(2.4)" }}, {rel(t - 0.04)});')
                elif fx == "soft":
                    js.append(f'tl.fromTo("#{wid}", {{ opacity: 0, y: 14, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.55, ease: "power2.out" }}, {rel(t - 0.06)});')
                elif fx == "count":
                    js.append(f'tl.fromTo("#{wid}", {{ opacity: 0, scale: 0.6, filter: "blur(12px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }}, {rel(t - 0.04)});')
                    target = int(norm(it["disp"]))
                    js.append(
                        f'(() => {{ const el = document.getElementById("{wid}-n"); const c = {{ v: 0 }}; '
                        f'tl.fromTo(c, {{ v: 0 }}, {{ v: {target}, duration: {round(max(0.3, it["end"] - t), 3)}, ease: "power2.out", immediateRender: false, '
                        f'onUpdate: () => {{ el.textContent = String(Math.round(c.v)); }} }}, {rel(t)}); }})();'
                    )
                events.append({"t": round(t, 3), "kind": fx, "scene": sid, "acc": it["acc"], "w": it["disp"]})
            out_lines.append(f'<span class="kt-line">{" ".join(parts)}</span>')
        cls = f'kt-beat kt-{b.get("pos", "center")} kt-{theme} {b.get("cls", "")}'.strip()
        html.append(
            f'<div class="{cls}" id="{bid}" style="font-size: {b.get("size", 120)}px; {b.get("style", "")}"><div class="kt-drift" id="{bid}-d">'
            f'<div class="kt-in" id="{bid}-in">{"".join(out_lines)}</div></div></div>'
        )
        # shakes on slams, never overlapping
        for k, ts in enumerate(shakes):
            nxt = shakes[k + 1] if k + 1 < len(shakes) else ts + 1
            d = round(min(0.26, nxt - ts - 0.02), 3)
            if d > 0.08:
                js.append(
                    f'tl.fromTo("#{bid}-in", {{ x: 0, y: 0 }}, {{ keyframes: {{ x: [0, -10, 8, -4, 2, 0], y: [0, 5, -4, 2, -1, 0] }}, duration: {d}, ease: "none", immediateRender: false }}, {rel(ts + 0.01)});'
                )
        t_end = b["t_out"] + 0.24 if b["t_out"] is not None else sc["end"]
        life = t_end - (b["t_in"] - 0.1)
        js.append(f'tl.fromTo("#{bid}-d", {{ scale: 1 }}, {{ scale: {1.035 if life < 5 else 1.05}, duration: {round(life, 3)}, ease: "none" }}, {rel(b["t_in"] - 0.1)});')
        if b["t_out"] is not None:
            js.append(f'tl.to("#{bid}", {{ opacity: 0, y: -34, filter: "blur(10px)", duration: 0.24, ease: "power2.in" }}, {rel(b["t_out"])});')
            events.append({"t": round(b["t_out"], 3), "kind": "exit", "scene": sid})
    return (
        '<div class="kt-layer">\n' + "\n".join(html) + "\n</div>",
        "\n".join(js),
        events,
    )


# ----------------------------------------------------------------------------- templating

def icon(m):
    name, extra = m.group(1), (m.group(2) or "").strip(":")
    if name not in LUCIDE:
        sys.exit(f"unknown lucide icon: {name}")
    cls = ("ms-ico " + extra.replace(".", " ")).strip()
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{LUCIDE[name]}</svg>'


def brand(m):
    name, extra = m.group(1), (m.group(2) or "").strip(":")
    svg = (ROOT / f"assets/icons/{name}.svg").read_text().strip()
    cls = ("ms-brand " + extra.replace(".", " ")).strip()
    return svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" ', 1)


def glow(m):
    """Gaussian-falloff radial gradient (no banding rings), for soft lights and mesh blobs."""
    r, g, b, a = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4))
    import math
    stops = [f"rgba({r},{g},{b},{a * math.exp(-8 * (x / 10) ** 2):.4f}) {x * 10}%" for x in range(10)]
    return f"radial-gradient(closest-side, {', '.join(stops)}, rgba({r},{g},{b},0) 100%)"


_LOGO_N = [0]


def logo_svg() -> str:
    """The ManySetter app icon (tile + M), self-contained with its own gradient id."""
    _LOGO_N[0] += 1
    g = f"lg{_LOGO_N[0]}"
    return (
        f'<svg class="ms-logo" viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#ff884d" /><stop offset="1" stop-color="#e64b15" /></linearGradient></defs>'
        f'<rect width="64" height="64" rx="15" fill="url(#{g})" />'
        '<g transform="translate(12.16 12.16) scale(1.6533)" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M5.5 17.5V7.25c0-.62.75-.93 1.19-.49L12 12.06l5.31-5.3c.44-.44 1.19-.13 1.19.49V17.5" /></g></svg>'
    )


def render(text: str, t0: float, dur: float, hold: float, sc: dict | None, kt=("", "")) -> str:
    text = re.sub(r"\{\{cue:([A-Za-z0-9#.']+)\}\}", lambda m: f"{cue_abs(m.group(1)) - t0:.3f}", text)
    text = re.sub(r"\{\{end:([A-Za-z0-9#.']+)\}\}", lambda m: f"{cue_abs(m.group(1), 'end') - t0:.3f}", text)
    text = re.sub(r"\{\{abs:([a-z0-9]+)\}\}", lambda m: f"{SC[m.group(1)]['start'] - t0:.3f}", text)
    if sc:
        text = re.sub(r"\{\{bin:(\d+)\}\}", lambda m: f"{sc['beats'][int(m.group(1))]['t_in'] - t0:.3f}", text)
        text = re.sub(r"\{\{bout:(\d+)\}\}", lambda m: f"{sc['beats'][int(m.group(1))]['t_out'] - t0:.3f}", text)
    text = text.replace("{{dur}}", f"{dur:.3f}").replace("{{hold}}", f"{hold:.3f}")
    text = re.sub(r"\{\{glow:(\d+),(\d+),(\d+),([0-9.]+)\}\}", glow, text)
    if "{{motionblur}}" in text:
        mb = (ROOT / "compositions/components/motion-blur.html").read_text().splitlines()
        start = next(i for i, l in enumerate(mb) if l.strip() == "<script>")
        stop = next(i for i, l in enumerate(mb) if l.strip() == "</script>")
        text = text.replace("{{motionblur}}", "\n".join(mb[start : stop + 1]))
    text = text.replace("{{heart}}", LUCIDE["heart"])
    text = re.sub(r"\{\{lucide:([a-z0-9-]+)\}\}", lambda m: LUCIDE[m.group(1)], text)
    text = text.replace("{{sun}}", LUCIDE["sun"]).replace("{{coffee}}", LUCIDE["coffee"])
    text = re.sub(r"\{\{logo\}\}", lambda m: logo_svg(), text)
    text = text.replace("{{kt}}", kt[0]).replace("{{kt_js}}", kt[1]).replace("{{fonts}}", FONTS)
    text = re.sub(r"\{\{i:([a-z0-9-]+)(:[a-z0-9.-]+)?\}\}", icon, text)
    text = re.sub(r"\{\{b:([a-z0-9-]+)(:[a-z0-9.-]+)?\}\}", brand, text)
    if "{{" in text:
        i = text.index("{{")
        sys.exit(f"unresolved placeholder: {text[i:i + 40]}")
    return text


# Long background layers under the scenes: (id, file, start, end)
def bg_layers():
    s4 = SC["s4"]
    bloom = cue_abs("P4.manysetter")
    return [
        {"id": "bgn", "src": "night", "start": 0.0, "end": round(bloom + 1.4, 3)},
        {"id": "bgd", "src": "day", "start": round(s4["start"], 3), "end": TOTAL},
    ]


AUDIO = [
    {"id": "vo", "src": "assets/audio/vo.wav", "track": 20, "volume": 1},
    {"id": "music", "src": "assets/audio/music.wav", "track": 21, "volume": 0.8},
    {"id": "sfx", "src": "assets/audio/sfx.wav", "track": 22, "volume": 0.85},
]


def main():
    resolve()
    check_widths()
    hosts, events = [], []
    z = 1
    for bg in bg_layers():
        src = ROOT / "src/bg" / f"{bg['src']}.html"
        if not src.exists():
            continue
        dur = bg["end"] - bg["start"]
        out = ROOT / "compositions/bg" / f"{bg['src']}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(src.read_text(), bg["start"], dur, dur, None))
        hosts.append(
            f'      <div id="{bg["id"]}" class="clip" data-composition-id="{bg["id"]}" data-composition-src="compositions/bg/{bg["src"]}.html" '
            f'data-start="{bg["start"]:.3f}" data-duration="{dur:.3f}" data-track-index="{z}" data-width="1920" data-height="1080" style="z-index: {z}"></div>'
        )
        z += 1
    for sc in SCENES:
        src = ROOT / "src/scenes" / f"{sc['id']}.html"
        dur = sc["end"] - sc["start"] + sc.get("overlap", 0.0)
        kt_html, kt_js, ev = kinetic(sc)
        events += ev
        if not src.exists():
            continue
        out = ROOT / "compositions/scenes" / f"{sc['id']}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(src.read_text(), sc["start"], dur, sc["end"] - sc["start"], sc, (kt_html, kt_js)))
        hosts.append(
            f'      <div id="{sc["id"]}" class="clip" data-composition-id="{sc["id"]}" data-composition-src="compositions/scenes/{sc["id"]}.html" '
            f'data-start="{sc["start"]:.3f}" data-duration="{dur:.3f}" data-track-index="{z}" data-width="1920" data-height="1080" style="z-index: {z + 10}"></div>'
        )
        z += 1
    audio = []
    for a in AUDIO:
        if (ROOT / a["src"]).exists():
            import soundfile

            adur = min(TOTAL, soundfile.info(str(ROOT / a["src"])).duration)
            audio.append(
                f'      <audio id="{a["id"]}" src="{a["src"]}" data-start="0" data-duration="{adur:.3f}" '
                f'data-track-index="{a["track"]}" data-volume="{a["volume"]}"></audio>'
            )
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #0d0c0a; }}
      #root {{ position: relative; width: 100%; height: 100%; background: #0d0c0a; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-fps="60" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(html)
    meta = {
        "total": TOTAL,
        "scenes": [{k: sc[k] for k in ("id", "part", "start", "end")} for sc in SCENES],
        "beats": [
            {"scene": sc["id"], "i": i, "t": b["t"], "in": b["t_in"], "out": b.get("t_out"), "ui": bool(b.get("ui"))}
            for sc in SCENES
            for i, b in enumerate(sc["beats"])
        ],
        "events": sorted(events, key=lambda e: e["t"]),
    }
    (ROOT / "film.json").write_text(json.dumps(meta, indent=1))
    for sc in SCENES:
        print(f"{sc['id']} {sc['part']} {sc['start']:6.2f} → {sc['end']:6.2f}")
    print("total", TOTAL)


if __name__ == "__main__":
    main()
