#!/usr/bin/env python3
"""Original score + sound design for the v7 film, generated in code from the same cues as the picture.

  timing.json / film.json (build.py)  →  assets/audio/music.wav  (ducked under the voice)
                                          assets/audio/sfx.wav    (every word and every motion)
Arc: night tension → the 126 flood → doubt → scramble → cringe → silence → the reveal → groove → morning → lift → end.
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build as B  # noqa: E402
from synth import *  # noqa: E402,F403

FILM = json.loads((ROOT / "film.json").read_text())
TOTAL = FILM["total"]
N = int(TOTAL * SR) + SR
SC = {s["id"]: s for s in FILM["scenes"]}
cue = B.cue_abs


def end(key):
    return B.cue_abs(key, "end")


music = np.zeros((N, 2))
sfx = np.zeros((N, 2))


def cut(buf, at, fade=0.04):
    """Hard stop of a stem at `at` (short fade)."""
    i, f = int(at * SR), int(fade * SR)
    buf[i : i + f] *= np.linspace(1, 0, f)[:, None]
    buf[i + f :] = 0


# ============================================================================ MUSIC

# ---------------------------------------------------------------- A. the Reel (0 → "and I got…")
A = np.zeros((N, 2))
BOOM = cue("P1.boom")
GOT = cue("P1.and")
BPM_A = 120
beat_a = 60 / BPM_A
grid0 = BOOM - 4 * beat_a  # the pulse lands "Boom" on a downbeat
drone = pad_chord([38, 45, 53, 57], GOT + 0.5, bright=0.35, att=0.6, rel=0.1)
place(A, drone, 0.0, 0.32)
k = 0
t = grid0
while t < GOT - 0.05:
    if t >= 0.1:
        place(A, lp(kick(0.4, 0.3), 220) * (0.5 if t < BOOM else 1.0), t, 0.42)
        ost = [62, 65, 69, 65, 62, 67, 65, 60]
        p = pluck(midi(ost[k % 8] + 12), 0.4)
        place(A, lp(p, 2600 if t < BOOM else 5000), t, 0.05 if t < BOOM else 0.08, pan=-0.25)
        place(A, lp(pluck(midi(ost[(k + 3) % 8] + 12), 0.35), 3000), t + beat_a / 2, 0.035, pan=0.3)
        if t >= BOOM:
            place(A, hat(), t + beat_a / 2, 0.05, pan=0.2)
            if k % 2 == 1:
                place(A, verb(clap(), 0.2), t, 0.12)
            place(A, bass_note(midi(38), beat_a * 0.8), t, 0.3)
    t += beat_a
    k += 1
place(A, noise_swell(GOT - cue("P1.manychat") + 0.2, 400, 7000, up=True), cue("P1.manychat") - 0.1, 0.22)
cut(A, GOT - 0.06)
# the hold: one eerie note while he looks at his phone
eerie = additive(midi(81), 1.4, 3, 1.6) * env_adsr(int(1.4 * SR), 0.3, 0.2, 0.8, 0.5)
place(A, verb(eerie, 0.5), GOT + 0.05, 0.05)
music += A

# ---------------------------------------------------------------- B. 126 DMs → 9 p.m.
Bm = np.zeros((N, 2))
FLOOD = cue("P1.126")
PM9 = cue("P1.9")
P1_END = B.LINES["P1"]["end"]
beat_b = 60 / 126
t, k = FLOOD, 0
while t < P1_END - 0.05:
    u = (t - FLOOD) / (P1_END - FLOOD)
    place(Bm, lp(bass_note(midi(38 if (k // 8) % 2 == 0 else 36), beat_b * 0.45), 600 + 2600 * u), t, 0.3)
    place(Bm, lp(bass_note(midi(38 if (k // 8) % 2 == 0 else 36), beat_b * 0.45), 600 + 2600 * u), t + beat_b / 2, 0.22)
    if k % 2 == 0:
        place(Bm, kick(0.4), t, 0.5)
    place(Bm, hat(0.04), t + beat_b / 2, 0.035 + 0.04 * u, pan=0.25)
    t += beat_b
    k += 1
place(Bm, verb(pad_chord([50, 53, 57, 62, 64], P1_END - FLOOD + 0.4, bright=0.6, att=0.3, rel=0.3), 0.3), FLOOD, 0.22)
# the three slams of "It's 9 p.m.!"
for w, f in (("P1.its", 46), ("P1.9", 43), ("P1.pm", 38)):
    place(Bm, verb(pad_chord([50, 57, 62, 65], 0.5, bright=1.0, att=0.005, rel=0.3), 0.25), cue(w) - 0.01, 0.35)
cut(Bm, P1_END + 0.15, 0.25)
music += Bm

# ---------------------------------------------------------------- C. P2: doubt, then "for nothing?"
C = np.zeros((N, 2))
P2s, P2e = B.LINES["P2"]["start"], B.LINES["P2"]["end"]
NOTHING = cue("P2.nothing")
dark = verb(pad_chord([38, 45, 48, 53, 57], NOTHING - P2s + 0.9, bright=0.3, att=0.5, rel=0.2), 0.4)
place(C, dark, P2s - 0.25, 0.32)
for k, tt in enumerate(np.arange(P2s - 0.1, NOTHING, 0.5)):
    tk = hp(rng.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / SR * 500), 3000)
    place(C, tk, tt, 0.07, pan=0.35 if k % 2 else -0.35)
# the energy drains out on "nothing?"
seg = C[int((NOTHING - 0.2) * SR) : int((NOTHING + 1.2) * SR)].copy()
C[int((NOTHING - 0.2) * SR) :] = 0
place(C, tape_stop(seg, 1.1), NOTHING - 0.2, 1.0)
place(C, sub_hit(36, 1.2), NOTHING - 0.02, 0.35)
music += C

# ---------------------------------------------------------------- D. P3: the scramble, then the cringe
D = np.zeros((N, 2))
QUICK = cue("P3.quick")
HEY = cue("P3.hey")
beat_d = 60 / 132
t, k = QUICK, 0
while t < HEY - 0.3:
    if k % 2 == 0:
        place(D, kick(0.35), t, 0.45)
    place(D, hat(0.035), t + beat_d / 2, 0.06, pan=0.2)
    place(D, hat(0.03), t + beat_d * 0.25, 0.025, pan=-0.2)
    place(D, lp(bass_note(midi([40, 40, 43, 40, 45, 43, 40, 38][k % 8]), beat_d * 0.4), 1600), t, 0.28)
    place(D, lp(bass_note(midi([40, 40, 43, 40, 45, 43, 40, 38][k % 8] + 12), beat_d * 0.3), 2400), t + beat_d / 2, 0.14)
    if k % 4 == 2:
        place(D, verb(clap(), 0.2), t, 0.1)
    t += beat_d
    k += 1
place(D, verb(pad_chord([52, 55, 59, 62], HEY - QUICK, bright=0.5, att=0.2, rel=0.3), 0.3), QUICK, 0.12)
cut(D, HEY - 0.28, 0.1)
# lounge cheese under "Hey babe! Ready to 10x your life?"
UH = cue("P3.uh")
vamp = [(HEY - 0.05, [60, 64, 67, 71, 74]), (cue("P3.ready") - 0.05, [57, 60, 64, 67, 71]), (cue("P3.tenx") - 0.05, [62, 65, 69, 72, 76])]
for tt, ch in vamp:
    for m in ch:
        place(D, verb(epiano(midi(m), 1.3), 0.35), tt, 0.06, pan=0.2 * ((m % 3) - 1))
place(D, verb(sparkle(0.9, 88, 108), 0.4), HEY - 0.02, 0.08)
place(D, lp(bass_note(midi(36), 0.5), 900), HEY - 0.05, 0.3)
place(D, lp(bass_note(midi(33), 0.5), 900), cue("P3.ready") - 0.05, 0.3)
place(D, lp(bass_note(midi(38), 0.5), 900), cue("P3.tenx") - 0.05, 0.3)
cut(D, UH - 0.12, 0.05)
music += D

# ---------------------------------------------------------------- E. P4: silence, the spark, the reveal
E = np.zeros((N, 2))
WAIT = cue("P4.wait")
MEET = cue("P4.manysetter")
T_SPARK = WAIT + 0.25
sh_len = MEET - T_SPARK + 0.1
sh = np.zeros(int(sh_len * SR))
for m in (86, 93, 98, 105):
    sh += additive(midi(m), sh_len, 3, 1.5)[: len(sh)] * 0.25
sh *= np.linspace(0, 1, len(sh)) ** 2.2
place(E, verb(sh, 0.5), T_SPARK, 0.3)
place(E, noise_swell(sh_len, 400, 6000, up=True) * 0.25, T_SPARK, 0.45)
for m, g in ((74, 1.0), (78, 0.8), (81, 0.8), (88, 0.55), (62, 0.6)):
    place(E, verb(bell(midi(m), 3.0), 0.45), MEET - 0.02, 0.2 * g)
place(E, sub_hit(26, 2.5), MEET - 0.02, 0.45)
music += E

# ---------------------------------------------------------------- F. the groove: reveal → morning → offer
ANCHOR = MEET
CTA = cue("P9.manysetter")
NBARS = 23
BAR = (CTA - ANCHOR) / NBARS
BEAT = BAR / 4
F = np.zeros((N, 2))
prog = [(38, [62, 66, 69, 76]), (35, [59, 62, 66, 73]), (31, [55, 59, 62, 69]), (33, [57, 61, 64, 71])]
STOP0, STOP1 = cue("P5.wait") - 0.1, cue("P5.seriously") - 0.02  # stop-time on "Wait… seriously?"
MORNING = cue("P7.next")
for b in range(NBARS):
    t0 = ANCHOR + b * BAR
    root, chord = prog[b % 4]
    morning = MORNING - 0.3 <= t0 < cue("P7.and") - 0.3
    bright = 0.55 if b < 3 else (1.0 if morning else 0.8)
    pad = pad_chord([m + (12 if morning else 0) for m in chord[1:]] + [chord[0]], BAR + 1.0, bright=bright, att=0.4, rel=0.9)
    place(F, verb(pad, 0.35), t0, 0.32 if not morning else 0.4)
    arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[3] + 12, chord[2] + 12, chord[1] + 12, chord[3] + 12, chord[2] + 12]
    for k in range(8):
        p = pluck(midi(arp[k] + (12 if morning else 0)), 0.6)
        place(F, p, t0 + k * BEAT / 2, 0.055, pan=-0.3 if k % 2 else 0.3)
        place(F, lp(p, 3000), t0 + k * BEAT / 2 + BEAT * 0.75, 0.02, pan=0.6 if k % 2 else -0.6)
    if b >= 2 and not morning:
        for k, o in enumerate((0, 1.5, 2, 3.5)):
            place(F, bass_note(midi(root), BEAT * 0.9), t0 + o * BEAT, 0.4 if k % 2 == 0 else 0.28)
    if b >= 3 and not morning:
        for o in (0, 1, 2, 3):
            place(F, kick(), t0 + o * BEAT, 0.42 if o % 2 == 0 else 0.3)
        for k in range(8):
            place(F, hat(), t0 + k * BEAT / 2, 0.05 if k % 2 else 0.028, pan=0.25)
    if b >= 4 and not morning:
        for o in (1, 3):
            place(F, verb(clap(), 0.25), t0 + o * BEAT, 0.14)
    if morning:
        for k, m in enumerate((81, 86, 88, 93)):
            place(F, verb(bell(midi(m), 2.2), 0.45), t0 + k * BEAT, 0.07)
# stop-time: everything drops for "Wait…", comes back on "seriously?"
i0, i1 = int(STOP0 * SR), int(STOP1 * SR)
F[i0:i1] *= np.linspace(1, 0.0, i1 - i0)[:, None] ** 6
place(F, noise_swell(STOP1 - end("P5.wait") - 0.05, 600, 8000, up=True), end("P5.wait") + 0.05, 0.12)
place(F, sub_hit(40, 1.0), STOP1, 0.4)
place(F, verb(hp(rng.standard_normal(int(1.6 * SR)) * np.exp(-t_(1.6) * 3.2), 3500), 0.3), STOP1, 0.06)
# lift into the end
place(F, noise_swell(CTA - cue("P8.one"), 300, 9000, up=True), cue("P8.one"), 0.32)
END_CARD = cue("P9.com") + 0.4
g0, g1 = int((END_CARD - 0.6) * SR), int(END_CARD * SR)
F[g0:g1] *= np.linspace(1, 0, g1 - g0)[:, None]
F[g1:] = 0
music += F
# final: the logo hit and the last chord under the end card
place(music, kick(0.6), CTA, 0.55)
place(music, sub_hit(30, 2.0), CTA, 0.4)
for m in (74, 81, 86, 90):
    place(music, verb(bell(midi(m), 3.0), 0.45), CTA, 0.11)
ring = verb(pad_chord([50, 57, 62, 66, 69, 76], TOTAL - END_CARD + 1.2, bright=0.75, att=0.5, rel=2.5), 0.45)
place(music, ring, END_CARD - 0.5, 0.42)
for m in (74, 78, 81, 88):
    place(music, verb(bell(midi(m), 3.5), 0.5), END_CARD, 0.1)
fade_out = np.ones(N)
fo0, fo1 = int((TOTAL - 1.4) * SR), int(TOTAL * SR)
fade_out[fo0:fo1] = np.linspace(1, 0, fo1 - fo0) ** 1.5
fade_out[fo1:] = 0
music *= fade_out[:, None]

# sidechain: duck the bed under every spoken word
vo, vsr = sf.read(ROOT / "assets/audio/vo.wav", dtype="float64")
if vo.ndim > 1:
    vo = vo.mean(axis=1)
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
hop = 240
envv = np.sqrt(np.convolve(vo**2, np.ones(hop * 4) / (hop * 4), mode="same"))
active = (envv > 0.004).astype(float)
look = int(0.08 * SR)  # look-ahead: the bed is already down when a word starts
active = np.maximum(active, np.concatenate([active[look:], np.zeros(look)]))
a_c, r_c = np.exp(-1 / (0.02 * SR)), np.exp(-1 / (0.3 * SR))
sm = np.zeros(N)
lvl = 0.0
for i in range(0, N, hop):
    target = active[i]
    c = a_c if target > lvl else r_c
    lvl = target + (lvl - target) * c**hop
    sm[i : i + hop] = lvl
music *= (10 ** (-15.0 * sm / 20))[:, None]

# ============================================================================ SOUND DESIGN


def kit(name):
    x, _ = sf.read(ROOT.parent / "assets_in/sfx-kit" / f"{name}.wav", dtype="float64")
    return x


# every word that lands on screen
for ev in FILM["events"]:
    t, kind = ev["t"], ev["kind"]
    if kind == "rise":
        place(sfx, tick_soft(), t - 0.1, 0.035 if not ev.get("acc") else 0.05)  # just before the consonant
        if ev.get("acc"):
            place(sfx, thump(120), t - 0.02, 0.12)
    elif kind == "sink":
        place(sfx, tick_soft(), t - 0.1, 0.035)
    elif kind == "slam":
        place(sfx, impact_word(50), t - 0.05, 0.3)
    elif kind == "pop":
        place(sfx, kit("pop"), t - 0.03, 0.2)
    elif kind == "soft":
        place(sfx, swish(0.35), t - 0.3, 0.02)
    elif kind == "count":
        pass  # the 126 roll is designed below
    elif kind == "mark":
        place(sfx, scribble(0.62), t, 0.075)
    elif kind == "exit":
        place(sfx, whoosh(0.22, 2500, 900), t - 0.06, 0.02)

S = lambda sid: SC[sid]["start"]  # noqa: E731

# ---- s1: the Reel
place(sfx, whoosh(0.7, 400, 3000), 0.25, 0.12, pan=0.5)
place(sfx, impact(44), BOOM - 0.02, 0.3, pan=0.4)
place(sfx, verb(kit("pop"), 0.3), BOOM, 0.25, pan=0.4)
for k in range(6):
    place(sfx, kit("pop") * 0.6, cue("P1.blew") + k * 0.09, 0.1, pan=0.5)
place(sfx, kit("counter"), cue("P1.blew") - 0.05, 0.08, pan=0.5)
for k in range(3):
    place(sfx, blip("send"), cue("P1.manychat") + 0.04 + k * 0.3, 0.13, pan=0.45)
# ---- the 126 flood: a quiet roll under the words, the storm of pings in the gap after "DMs!"
ct0, ct1 = FLOOD, end("P1.126")
for k in range(24):
    place(sfx, tick_soft(), ct0 + (ct1 - ct0) * (k / 23) ** 0.8, 0.035)
st0, st1 = end("P1.dms") + 0.05, cue("P1.how") - 0.08
n_ping = 30
for k in range(n_ping):
    u = k / (n_ping - 1)
    tt = st0 + (st1 - st0) * (u**1.35)
    place(sfx, ping(midi(84 + (k * 5) % 9)), tt, 0.075 * (1 - 0.5 * u), pan=((k * 37) % 13 - 6) / 7)
tt = cue("P1.how") + 0.1
k = 0
while tt < P1_END:
    place(sfx, ping(midi(84 + (k * 7) % 12)), tt, 0.018, pan=((k * 29) % 11 - 5) / 6)
    tt += 0.3 + 0.12 * ((k * 13) % 5) / 4
    k += 1
place(sfx, whoosh(0.9, 3000, 300), FLOOD - 0.15, 0.12)
# ---- s2: the late reply
place(sfx, whoosh(0.6, 500, 3000), S("s2") + 0.05, 0.1, pan=0.5)
place(sfx, blip("recv"), cue("P2.reply") - 0.1, 0.14, pan=0.5)
place(sfx, kit("tick"), cue("P2.late") - 0.08, 0.12, pan=0.5)
place(sfx, blip("send"), end("P2.me") + 0.05, 0.08, pan=0.5)
place(sfx, whoosh(1.0, 2000, 300), cue("P2.forget") + 0.1, 0.07, pan=0.5)
place(sfx, whoosh(0.7, 2500, 400), B.LINES["P2"]["start"] + 2.0, 0.08, pan=0.5)
# ---- s3: hiring, the cringe
place(sfx, whoosh(0.6, 500, 3000), cue("P3.need") - 0.15, 0.1, pan=0.5)
place(sfx, kit("snap"), cue("P3.train") - 0.08, 0.14, pan=0.5)
place(sfx, kit("snap"), cue("P3.commission") - 0.08, 0.14, pan=0.5)
place(sfx, whoosh(0.6, 500, 3000), cue("P3.what") - 0.2, 0.1, pan=0.5)
place(sfx, blip("recv"), cue("P3.reply") - 0.1, 0.13, pan=0.4)
for k in range(3):
    place(sfx, tick_soft(), cue("P3.total") + 0.1 + k * 0.5, 0.04, pan=0.5)
for w in ("P3.hey", "P3.babe", "P3.ready", "P3.to#3", "P3.tenx", "P3.your", "P3.life"):
    place(sfx, kit("star") * 0.8, cue(w) - 0.04, 0.06, pan=0.45)
place(sfx, scratch(), UH - 0.5, 0.22)
place(sfx, woodblock(420), cue("P3.no") - 0.01, 0.2)
place(sfx, scribble(0.3), cue("P3.no"), 0.12, pan=0.5)
place(sfx, whoosh(0.5, 2000, 300), S("s4") - 0.55, 0.1, pan=0.5)
# ---- s4: the spark, the bloom, the plug
for k in range(10):
    place(sfx, hp(rng.standard_normal(int(0.01 * SR)) * np.exp(-t_(0.01) * 400), 4000), T_SPARK + k * (MEET - T_SPARK) / 10, 0.05)
place(sfx, verb(swish(0.8), 0.4), MEET - 0.7, 0.1)
place(sfx, sparkle(1.0), end("P4.manysetter") + 0.02, 0.08)
place(sfx, kit("pop"), end("P4.manysetter") + 0.05, 0.12)  # the "?"
place(sfx, whoosh(0.5, 3000, 500), cue("P4.an") - 0.32, 0.08)
place(sfx, whoosh(0.6, 500, 3000), cue("P4.ai") - 0.05, 0.1, pan=0.5)
place(sfx, whoosh(0.6, 500, 3000), cue("P4.plugs") - 0.05, 0.1, pan=0.5)
place(sfx, noise_swell(0.75, 800, 5000, up=True), cue("P4.into") - 0.2, 0.07, pan=0.5)
place(sfx, kit("snap"), cue("P4.manychat") - 0.02, 0.22, pan=0.5)
place(sfx, sub_hit(70, 0.4), cue("P4.manychat") - 0.02, 0.12)
place(sfx, kit("switch"), cue("P4.manychat") + 0.18, 0.16, pan=0.5)
place(sfx, kit("pop"), cue("P4.talks") - 0.05, 0.14, pan=0.5)
# ---- s5: playbook → chat → booked
place(sfx, whoosh(0.7, 500, 3500), cue("P5.i") - 0.25, 0.1, pan=0.5)
place(sfx, whoosh(0.6, 3500, 700), cue("P5.sales") - 0.12, 0.12, pan=0.3)
place(sfx, kit("snap"), cue("P5.sales") + 0.45, 0.16, pan=0.5)
place(sfx, kit("fill"), cue("P5.two") - 0.05, 0.1, pan=0.5)
for k in range(4):
    place(sfx, kit("tick"), cue("P5.knows") + k * 0.17 + 0.12, 0.12, pan=0.5)
place(sfx, kit("success"), cue("P5.heart") - 0.05, 0.14, pan=0.5)
place(sfx, whoosh(0.7, 500, 3500), cue("P5.it#3") - 0.2, 0.1, pan=0.5)
place(sfx, blip("recv"), cue("P5.answers") - 0.1, 0.13, pan=0.4)
place(sfx, blip("send"), cue("P5.dm") - 0.05, 0.13, pan=0.6)
place(sfx, blip("recv"), cue("P5.need") - 0.1, 0.13, pan=0.4)
place(sfx, blip("send"), cue("P5.and") - 0.12, 0.13, pan=0.6)
place(sfx, kit("pop"), cue("P5.fit") - 0.04, 0.16, pan=0.6)
place(sfx, kit("chime"), cue("P5.call") - 0.05, 0.2, pan=0.5)
place(sfx, verb(bell(midi(86), 1.6), 0.4), cue("P5.call") - 0.04, 0.08, pan=0.5)
place(sfx, kit("success") * 0.7, cue("P5.call") + 0.3, 0.12, pan=0.5)
# ---- s6: delay, summary, stats
place(sfx, whoosh(0.7, 500, 3500), cue("P6.it") - 0.25, 0.1, pan=0.5)
place(sfx, kit("switch"), cue("P6.waits"), 0.18, pan=0.5)
for k in range(3):
    place(sfx, tick_soft(), cue("P6.before") + 0.15 + k * 0.45, 0.035, pan=0.5)
place(sfx, blip("send"), cue("P6.would") - 0.12, 0.13, pan=0.6)
place(sfx, whoosh(0.7, 500, 3500), cue("P6.every") - 0.2, 0.1, pan=0.5)
place(sfx, sparkle(0.7), end("P6.summary") + 0.02, 0.04, pan=0.5)
for k in range(4):
    place(sfx, tick_soft(), cue("P6.summary") + k * 0.16, 0.04, pan=0.5)
place(sfx, scribble(0.4), cue("P6.exactly") - 0.05, 0.06, pan=0.5)
place(sfx, scribble(0.4), cue("P6.calling") - 0.1, 0.06, pan=0.5)
place(sfx, whoosh(0.7, 500, 3500), cue("P6.and#2") - 0.15, 0.1, pan=0.5)
place(sfx, kit("pop"), cue("P6.team") - 0.08, 0.15, pan=0.6)
for w in ("P6.conversations", "P6.qualified", "P6.calls"):
    place(sfx, kit("counter"), cue(w) - 0.04, 0.07, pan=0.5)
    place(sfx, kit("snap"), cue(w) - 0.06, 0.12, pan=0.5)
# ---- s7: morning
place(sfx, verb(sparkle(1.2, 88, 100), 0.5), cue("P7.next") - 0.3, 0.08)
place(sfx, kit("pop"), cue("P7.coffee") - 0.12, 0.14)
place(sfx, noise_swell(1.0, 1500, 300, up=False), cue("P7.coffee") + 0.15, 0.04)
place(sfx, whoosh(0.7, 500, 3500), cue("P7.and") - 0.2, 0.1, pan=0.5)
for w in ("P7.calls", "P7.already", "P7.calendar"):
    place(sfx, kit("pop"), cue(w) - 0.02, 0.15, pan=0.5)
    place(sfx, kit("chime") * 0.5, cue(w) + 0.05, 0.06, pan=0.5)
# ---- s8: the button, the maths
place(sfx, whoosh(0.6, 500, 3000), cue("P8.build") - 0.1, 0.1)
place(sfx, whoosh(0.5, 2500, 800), cue("P8.free") - 0.85, 0.05, pan=0.4)
place(sfx, click(), cue("P8.free") - 0.06, 0.3)
place(sfx, kit("success"), cue("P8.free") + 0.02, 0.15)
place(sfx, whoosh(0.7, 500, 3500), cue("P8.if") - 0.1, 0.1, pan=0.5)
place(sfx, kit("counter"), cue("P8.fifteen") - 0.05, 0.08, pan=0.5)
place(sfx, kit("snap"), cue("P8.pays") - 0.1, 0.12, pan=0.5)
place(sfx, kit("success"), cue("P8.year") - 0.08, 0.16, pan=0.5)
# ---- s9: the logo, the address
place(sfx, verb(swish(0.9), 0.4), cue("P9.manysetter") - 0.12, 0.12)
place(sfx, sparkle(1.0), cue("P9.manysetter") + 0.05, 0.08)
place(sfx, kit("pop"), cue("P9.manysetter#2") - 0.15, 0.15)
for w in ("P9.manysetter#2", "P9.dot", "P9.com"):
    place(sfx, kit("tick"), cue(w) - 0.04, 0.1)
place(sfx, kit("switch"), cue("P9.com") + 0.15, 0.14)
sfx *= fade_out[:, None]

# ============================================================================ write stems


def finish(x, peak_db):
    x = x[: int(TOTAL * SR)]
    pk = np.max(np.abs(x)) + 1e-9
    return x * (10 ** (peak_db / 20) / pk)


out = ROOT / "assets/audio"
sf.write(out / "music.wav", finish(music, -4.0), SR, subtype="PCM_24")
sf.write(out / "sfx.wav", finish(sfx, -3.0), SR, subtype="PCM_24")
print("music.wav / sfx.wav written", round(TOTAL, 2), "s")
