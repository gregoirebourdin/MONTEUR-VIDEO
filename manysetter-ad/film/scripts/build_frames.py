#!/usr/bin/env python3
"""Build scene sub-compositions from src/frames/*.html.

Placeholders:
  {{fonts}}            @font-face block (root-relative paths, as HyperFrames serves from the project root)
  {{i:name}}           inline Lucide icon (from assets/lucide.json), class "ms-ico"
  {{i:name:extra}}     same, with extra classes
  {{b:file}}           inline brand SVG from assets/icons/<file>.svg, class "ms-brand"
  {{b:file:extra}}     same, with extra classes
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LUCIDE = json.loads((ROOT / "assets/lucide.json").read_text())

FONTS = """@font-face { font-family: "Nohemi"; src: url("assets/fonts/Nohemi-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
@font-face { font-family: "Nohemi"; src: url("assets/fonts/Nohemi-600.woff2") format("woff2"); font-weight: 600; font-display: block; }
@font-face { font-family: "Inter"; src: url("assets/fonts/Inter-var.woff2") format("woff2"); font-weight: 100 900; font-display: block; }"""


def icon(m: re.Match) -> str:
    name, extra = m.group(1), (m.group(2) or "").strip(":")
    if name not in LUCIDE:
        sys.exit(f"unknown lucide icon: {name}")
    cls = ("ms-ico " + extra.replace(".", " ")).strip()
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{LUCIDE[name]}</svg>'


def brand(m: re.Match) -> str:
    name, extra = m.group(1), (m.group(2) or "").strip(":")
    svg = (ROOT / f"assets/icons/{name}.svg").read_text().strip()
    cls = ("ms-brand " + extra.replace(".", " ")).strip()
    return svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" ', 1)


def build(src: pathlib.Path) -> pathlib.Path:
    text = src.read_text()
    text = text.replace("{{fonts}}", FONTS)
    text = re.sub(r"\{\{i:([a-z0-9-]+)(:[a-z0-9.-]+)?\}\}", icon, text)
    text = re.sub(r"\{\{b:([a-z0-9-]+)(:[a-z0-9.-]+)?\}\}", brand, text)
    if "{{" in text:
        sys.exit(f"unresolved placeholder in {src.name}: {text[text.index('{{'):text.index('{{') + 40]}")
    out = ROOT / "compositions/frames" / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


if __name__ == "__main__":
    files = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((ROOT / "src/frames").glob("*.html"))
    for f in files:
        print("built", build(f).relative_to(ROOT))
