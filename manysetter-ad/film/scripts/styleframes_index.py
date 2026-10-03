#!/usr/bin/env python3
"""Write a style-frame review index.html: each frame shown for 1 s, in order."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
frames = sys.argv[1:]
clips = []
for i, f in enumerate(frames):
    fid = "f" + f[:2]
    clips.append(f'    <div id="{fid}" class="clip" data-composition-id="{fid}" data-composition-src="compositions/frames/{f}.html" data-start="{i}" data-duration="1" data-track-index="0" data-width="1920" data-height="1080"></div>')
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
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{len(frames)}" data-width="1920" data-height="1080">
{chr(10).join(clips)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
(ROOT / "index.html").write_text(html)
print("index with", len(frames), "frames")
