#!/usr/bin/env python3
"""Reel 1 sound: Charon voice with bleeps, an original trap beat, and an SFX on every motion.

  cues.json (build.py) + ../vo/<reel>/vo.wav  →  audio/mix.wav          (voice + music + SFX, -14 LUFS, ≤ -1 dBTP)
                                              audio/mix_nomusic.wav  (same without music, for trending sounds)
Every sound is placed from the same cues as the picture. Usage: python3 reelN/audio.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from synth import *  # noqa: E402,F403

D = json.loads((HERE / "cues.json").read_text())
C, WORDS = D["cues"], D["words"]
TOTAL = C["total"]
N = int(TOTAL * SR) + SR // 2
OUT = HERE / "audio"


def buf():
    return np.zeros((N, 2))


# ---------------- voice + bleeps ----------------
vo, sr = sf.read(HERE.parent / f"vo/{HERE.name}/vo.wav", dtype="float64")
assert sr == SR
vo = vo if vo.ndim == 1 else vo.mean(axis=1)
voice = np.zeros(N)
voice[: len(vo)] = vo
bleep_track = np.zeros(N)
peak = np.percentile(np.abs(vo), 99.5)
for b in D["bleeps"]:
    # let the first consonant through ("b—", "f—", "sh—"), then the classic 1 kHz bleep;
    # never into the next word ("…ing challenge")
    nxt = WORDS[b["i"] + 1]["t"] if b["i"] + 1 < len(WORDS) else TOTAL
    a, z = b["t"] + 0.07, min(b["end"] + 0.04, nxt - 0.015)
    i, j = int(a * SR), int(z * SR)
    f = int(0.006 * SR)
    voice[i - f : i] *= np.linspace(1, 0, f)
    voice[i:j] = 0
    tt = np.arange(j - i) / SR
    tone = np.sin(2 * np.pi * 1000 * tt) * env_adsr(j - i, 0.004, 0.01, 1, 0.01) * peak * 0.55
    bleep_track[i:j] += tone

# reel dialogue chain: a little less box, a little more presence, gentle glue
with tempfile.TemporaryDirectory() as td:
    src, dst = pathlib.Path(td) / "v.wav", pathlib.Path(td) / "o.wav"
    sf.write(src, voice.astype(np.float32), SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    "highpass=f=80:poles=2,equalizer=f=260:t=q:w=1:g=-3,equalizer=f=3000:t=q:w=1:g=3,"
                    "highshelf=f=8000:g=2,deesser=i=0.3:m=0.5:f=0.5,"
                    "acompressor=threshold=-20dB:ratio=3:attack=6:release=120:knee=6",
                    "-c:a", "pcm_f32le", str(dst)], check=True)
    voice, _ = sf.read(dst, dtype="float64")
voice = voice[:N] + bleep_track[:N]
VOX = np.stack([voice, voice], axis=1)

# ---------------- music: half-time trap at 150 BPM ----------------
BPM = 150
BEAT = 60 / BPM
music = buf()


def b808(f, dur, glide_to=None):
    t = t_(dur)
    ff = f if glide_to is None else f * (glide_to / f) ** np.clip((t - dur * 0.6) / (dur * 0.4), 0, 1)
    s = np.sin(2 * np.pi * np.cumsum(ff) / SR)
    s = np.tanh(2.2 * s) * 0.8
    return s * env_adsr(len(t), 0.004, 0.2, 0.75, 0.12)


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.6
    return body + clap(0.3)[:n]


def bell_note(f, dur=0.5):
    return bell(f, dur, 1.4, 3.0) * 0.5


# sections: (start, end, level) — "full" beat, "lite" (no hats), silences on the comedic stops
SECTIONS = [
    (0.0, C["dead"] + 0.02, "full"),
    (C["ring"] - 0.02, C["business"] - 0.2, "full"),
    (C["plug"] - 0.12, C["you"] - 0.15, "full"),
    (C["you"] - 0.15, C["comment"] - 0.12, "lite"),
    (C["comment"] - 0.12, C["end"] + 0.25, "full"),
]
BASS = [midi(n) for n in (30, 30, 26, 28)]  # F#1, F#1, D1, E1 per bar
MELO = [78, 81, 78, 76, 73, 76, 78, 73]      # F#5 pentatonic motif


def in_section(t):
    for a, z, kind in SECTIONS:
        if a <= t < z:
            return kind
    return None


nb = int(TOTAL / BEAT) + 2
for k in range(nb):
    t = k * BEAT
    kind = in_section(t)
    if not kind:
        continue
    bar, pos = divmod(k, 4)
    if pos == 0:
        place(music, kick(0.45), t, 0.9)
        place(music, b808(BASS[bar % 4], BEAT * 3.6, BASS[(bar + 1) % 4] if bar % 2 else None), t, 0.55)
    if pos == 2 and kind == "full":
        place(music, kick(0.4, 0.6), t + BEAT * 0.75, 0.55)
    if pos == 2:
        place(music, snare(), t, 0.55)
    if kind == "full":
        # hats on 8ths, a 32nd roll at the end of every other bar
        for h in range(2):
            place(music, hat(0.05), t + h * BEAT / 2, 0.16 + 0.06 * (h == 0), pan=0.25)
        if pos == 3 and bar % 2 == 1:
            for r in range(6):
                place(music, hat(0.03), t + BEAT / 2 + r * BEAT / 12, 0.1 + 0.02 * r, pan=-0.2)
        # the cheeky bell motif, once every 2 bars
        if pos in (0, 1, 2, 3) and bar % 2 == 0:
            n = MELO[(bar // 2 * 4 + pos) % len(MELO)]
            place(music, bell_note(midi(n), 0.45), t + BEAT * 0.5, 0.11, pan=0.3)

# the hostage drop: a low drone under the silence
drone_t = C["business"] - 0.2
dr = t_(C["plug"] - 0.12 - drone_t)
drone = (np.sin(2 * np.pi * 41.2 * dr) + 0.3 * np.sin(2 * np.pi * 82.4 * dr)) * np.minimum(1, dr * 3) * 0.35
place(music, lp(drone, 300), drone_t, 1.0)

# duck the music under the voice (look-ahead envelope)
env = np.sqrt(np.convolve(voice**2, np.ones(int(0.03 * SR)) / int(0.03 * SR), "same"))
env = env / (env.max() + 1e-9)
la = int(0.06 * SR)
env = np.concatenate([env[la:], np.zeros(la)])
sm = np.convolve(env, np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
duck = 1 - 0.64 * np.clip(sm * 3, 0, 1)
music *= duck[:, None]

# ---------------- SFX ----------------
sfx = buf()


def boing(f0=180, f1=520, dur=0.35):
    t = t_(dur)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 18)) + 40 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def zap(dur=0.35):
    t = t_(dur)
    buzz = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.3 + bp(rng.standard_normal(len(t)), 2000, 9000) * 0.7
    return buzz * np.exp(-t * 12) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))


def hum(dur=0.9):
    t = t_(dur)
    s = sum(np.sin(2 * np.pi * 60 * k * t) / k for k in (1, 2, 3, 5))
    return lp(s, 900) * np.minimum(1, t * 8) * np.exp(-t * 2.5) * 0.4


def beep(f=880, dur=0.1):
    t = t_(dur)
    return np.sin(2 * np.pi * f * t) * env_adsr(len(t), 0.003, 0.01, 1, 0.01)


def key_click():
    n = int(0.04 * SR)
    return bp(rng.standard_normal(n), 2500, 8000) * np.exp(-np.arange(n) / SR * 220) * 0.7 + thump(260)[:n] * 0.3


def riser(dur):
    return noise_swell(dur, 300, 6000, up=True)


def pop():
    b, th = blip("recv"), thump(320)
    out = np.zeros(max(len(b), len(th)))
    out[: len(b)] += b * 0.6
    out[: len(th)] += th * 0.4
    return out


# word ticks: a soft tick under every caption word, a pop on the big ones
for w in WORDS:
    place(sfx, tick_soft(), w["t"] - 0.07, 0.1, pan=((len(w["w"]) * 3) % 7 - 3) / 6)

H = lambda key: C[key]  # noqa: E731
place(sfx, impact(44), 0.0, 0.5)
place(sfx, whoosh(0.5, 400, 2600), 0.0, 0.35)
for k in ("bleep1", "bleep2", "bleep3"):
    place(sfx, thump(140), H(k) - 0.02, 0.6)
    place(sfx, click(), H(k) - 0.02, 0.4)
place(sfx, whoosh(0.35, 700, 4200), H("youdid") - 0.1, 0.4, pan=-0.3)
place(sfx, impact_word(46), H("challenge") - 0.03, 0.7)
place(sfx, swish(0.6), H("challenge") - 0.05, 0.3)
place(sfx, pop(), H("five") - 0.03, 0.4)
for d in range(4):
    place(sfx, woodblock(700 + d * 60), H("days") + d * ((H("live") + 0.15 - H("days")) / 3.2), 0.25)
# heart monitor: three beats while the line draws, then the flatline
span = H("dead") - H("voice") + 0.1
for x in (120, 360, 600):
    place(sfx, beep(880, 0.09), H("voice") - 0.05 + span * (x + 35) / 1000, 0.2)
place(sfx, beep(880, 0.55), H("dead"), 0.22)
place(sfx, hum(1.0), H("ring") - 0.04, 0.5)
place(sfx, thump(90), H("ring") - 0.04, 0.6)
for k in range(4):
    place(sfx, click(), H("ring") + 0.24 + k * 0.04, 0.12)
place(sfx, thump(70), H("andnow") - 0.12, 0.4)
# 40 notifications, the rain
t0, t1 = H("four") - 0.15, H("info") - 0.25
for k in range(40):
    at = t0 + (k / 40) ** 0.75 * (t1 - t0)
    place(sfx, ping(midi(84 + (k * 5) % 9)), at, 0.12 + 0.002 * k, pan=((k * 37) % 11 - 5) / 6)
place(sfx, impact(52), H("info") - 0.06, 0.55)
place(sfx, whoosh(0.4, 900, 3000), H("info") - 0.12, 0.3)
place(sfx, whoosh(0.7, 2500, 300), H("answer") - 0.1, 0.35)
hand_end = WORDS[32]["end"]
place(sfx, pop(), H("byhand") - 0.1, 0.35)
for k in range(5):
    place(sfx, woodblock(900), hand_end + 0.03 + k * 0.08, 0.14)
for k, f in enumerate((1200, 900, 1200)):
    place(sfx, woodblock(f), H("midnight") - 0.22 + k * 0.3, 0.22)
place(sfx, boing(150, 420), H("inbed") - 0.08, 0.35)
place(sfx, scratch(), H("business") - 0.32, 0.45)
place(sfx, whoosh(0.3, 3000, 600), H("hostage") - 0.12, 0.35, pan=-0.4)
place(sfx, impact(48), H("hostage") - 0.02, 0.6)
place(sfx, whoosh(0.3, 600, 3000), H("situation") - 0.12, 0.35, pan=0.4)
place(sfx, impact(40), H("situation") - 0.02, 0.85)
place(sfx, riser(0.55), H("plug") - 0.67, 0.3)
place(sfx, impact(46), H("plug") - 0.12, 0.6)
place(sfx, whoosh(0.4, 400, 3000), H("plug") - 0.15, 0.3)
place(sfx, key_click(), H("manychat") - 0.01, 0.6)
place(sfx, zap(0.35), H("manychat"), 0.35)
place(sfx, blip("recv"), H("manychat") + 0.06, 0.35)
place(sfx, whoosh(0.45, 300, 2500), H("learn") - 0.2, 0.35)
scan = t_(H("offer") - H("learn") + 0.15)
place(sfx, np.sin(2 * np.pi * np.cumsum(500 + 900 * scan / scan[-1]) / SR) * 0.15 * np.sin(np.linspace(0, np.pi, len(scan))), H("learn"), 0.5)
place(sfx, sparkle(0.6), H("offer") + 0.12, 0.35)
place(sfx, whoosh(0.35, 3000, 900), H("talk") - 0.14, 0.3)
place(sfx, blip("recv"), H("talk") - 0.12, 0.3)
for k in range(3):
    place(sfx, key_click(), H("talk") + 0.25 + k * 0.08, 0.2)
place(sfx, blip("send"), H("likeyou") - 0.2, 0.4)
place(sfx, blip("recv"), H("illthink") - 0.32, 0.3)
for k in range(3):
    place(sfx, key_click(), H("illthink") + 0.42 + k * 0.1, 0.2)
place(sfx, blip("send"), H("thinkend") + 0.02, 0.4)
place(sfx, pop(), H("andbook"), 0.35)
place(sfx, impact_word(52), H("call") - 0.05, 0.55)
place(sfx, sparkle(1.0, 90, 108), H("call"), 0.5)
place(sfx, hp(rng.standard_normal(int(0.25 * SR)) * np.exp(-t_(0.25) * 18), 1500), H("call"), 0.35)
place(sfx, whoosh(0.4, 500, 2600), H("inyour") - 0.12, 0.3)
place(sfx, thump(200), H("calendar"), 0.5)
for k in range(3):
    place(sfx, pop(), H("calendar") + 0.22 + k * 0.1, 0.25)
place(sfx, whoosh(0.4, 2600, 500), H("you") - 0.2, 0.35)
place(sfx, sparkle(0.9, 80, 96), H("gosleep"), 0.25)
place(sfx, whoosh(0.4, 400, 2400), H("comment") - 0.12, 0.35)
for k in range(5):
    place(sfx, key_click(), H("setty") - 0.02 + k * 0.065, 0.45)
place(sfx, blip("send"), H("setty") + 0.38, 0.45)
place(sfx, whoosh(0.5, 500, 5000), H("slide") - 0.05, 0.6, pan=0.6)
place(sfx, whoosh(0.5, 5000, 700), H("slide") + 0.5, 0.45, pan=-0.6)
place(sfx, ping(1318), H("dms_end") + 0.05, 0.35)
place(sfx, ping(1760), H("dms_end") + 0.2, 0.3)
place(sfx, pop(), H("end") + 0.32, 0.45)
place(sfx, sparkle(0.8), H("end") + 0.34, 0.3)

# SFX also step back a little while Setty talks
sfx *= (1 - 0.3 * np.clip(sm * 3, 0, 1))[:, None]

# ---------------- mix + loudness ----------------
def master(stem, path):
    with tempfile.TemporaryDirectory() as td:
        raw = pathlib.Path(td) / "raw.wav"
        sf.write(raw, stem.astype(np.float32), SR, subtype="FLOAT")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True)
        I = float(r.stderr.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0])
        gain = -14.0 - I
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                        f"volume={gain:.2f}dB,alimiter=limit=-1.5dB:attack=2:release=60:level=disabled:latency=1",
                        "-c:a", "pcm_s16le", str(path)], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    summ = r.stderr.split("Summary:")[1]
    I2 = summ.split("I:")[1].split("LUFS")[0].strip()
    P2 = summ.split("Peak:")[1].split("dBFS")[0].strip()
    print(f"{path.name}: {I2} LUFS, true peak {P2} dBTP")


OUT.mkdir(exist_ok=True)
mix = VOX * 1.0 + music * 0.42 + sfx * 0.5
master(mix, OUT / "mix.wav")
master(VOX * 1.0 + sfx * 0.5, OUT / "mix_nomusic.wav")
