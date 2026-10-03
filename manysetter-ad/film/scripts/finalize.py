#!/usr/bin/env python3
"""Master the audio of a rendered film and run the delivery QA.

  python3 scripts/finalize.py renders/in.mp4 renders/out.mp4 [--expect-fps 60] [--size 1920x1080]

1. Two-pass EBU R128 loudnorm to -14 LUFS integrated / -1 dBTP (linear mode), video copied.
2. QA: resolution, frame rate, duration, A/V stream lengths, black frames, frozen frames,
   final loudness and true peak. Exit code 1 on any failure.
"""
import argparse
import json
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def loudnorm_json(path, extra=""):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"loudnorm=I=-14:TP=-1:LRA=11:print_format=json{extra}", "-f", "null", "-"])
    m = re.search(r"\{[\s\S]*?\}", r.stderr[r.stderr.rfind("[Parsed_loudnorm") :])
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--expect-fps", type=float, default=60)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--allow-black", default="")  # "start-end,start-end" windows where black is intended
    a = ap.parse_args()

    m1 = loudnorm_json(a.src)
    af = (
        f"loudnorm=I=-14:TP=-1:LRA=11:linear=true:measured_I={m1['input_i']}:measured_TP={m1['input_tp']}"
        f":measured_LRA={m1['input_lra']}:measured_thresh={m1['input_thresh']}:offset={m1['target_offset']},aresample=48000"
    )
    r = run(["ffmpeg", "-hide_banner", "-y", "-i", a.src, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", a.dst])
    if r.returncode:
        print(r.stderr[-2000:])
        sys.exit(1)

    problems = []
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", a.dst]).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    au = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    size = f"{v['width']}x{v['height']}"
    dur = float(pr["format"]["duration"])
    print(f"video   {size} @ {fps:g} fps, {v['codec_name']} {v.get('pix_fmt')}, {dur:.2f}s")
    if size != a.size:
        problems.append(f"size {size} != {a.size}")
    if abs(fps - a.expect_fps) > 0.01:
        problems.append(f"fps {fps} != {a.expect_fps}")
    if au is None:
        problems.append("no audio stream")
    else:
        ad = float(au.get("duration", dur))
        print(f"audio   {au['codec_name']} {au['sample_rate']} Hz {au['channels']} ch, {ad:.2f}s")
        if abs(ad - float(v.get("duration", dur))) > 0.1:
            problems.append(f"A/V length mismatch {ad:.2f} vs {v.get('duration')}")

    bd = run(["ffmpeg", "-hide_banner", "-i", a.dst, "-vf", "blackdetect=d=0.12:pic_th=0.985:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
    allowed = [tuple(map(float, w.split("-"))) for w in a.allow_black.split(",") if w]
    for s, e in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", bd):
        s, e = float(s), float(e)
        ok = any(s >= lo - 0.05 and e <= hi + 0.05 for lo, hi in allowed)
        print(f"black   {s:.2f}-{e:.2f} {'(intended)' if ok else 'UNEXPECTED'}")
        if not ok:
            problems.append(f"black frames {s:.2f}-{e:.2f}")
    fz = run(["ffmpeg", "-hide_banner", "-i", a.dst, "-vf", "freezedetect=n=0.0008:d=1.5", "-an", "-f", "null", "-"]).stderr
    for s, d in re.findall(r"freeze_start: ([0-9.]+)[\s\S]*?freeze_duration: ([0-9.]+)", fz):
        print(f"freeze  {float(s):.2f}s for {float(d):.2f}s")
        problems.append(f"frozen picture at {float(s):.2f}s ({float(d):.2f}s)")

    m2 = loudnorm_json(a.dst)
    print(f"loudness {m2['input_i']} LUFS, true peak {m2['input_tp']} dBTP, LRA {m2['input_lra']}")
    if abs(float(m2["input_i"]) + 14) > 0.6:
        problems.append(f"loudness {m2['input_i']} LUFS")
    if float(m2["input_tp"]) > -0.9:
        problems.append(f"true peak {m2['input_tp']} dBTP")

    if problems:
        print("QA FAILED:\n  - " + "\n  - ".join(problems))
        sys.exit(1)
    print("QA PASSED")


if __name__ == "__main__":
    main()
