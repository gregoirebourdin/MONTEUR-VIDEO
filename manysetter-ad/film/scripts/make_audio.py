#!/usr/bin/env python3
"""Original score + sound design for the ManySetter film, generated in code.

Everything is placed from the same cues as the picture (timing.json via build_film), so a new
voice take re-times the music and the SFX too. Outputs 48 kHz stereo stems:
  assets/audio/music.wav   ducked under the voice-over (sidechain from vo.wav)
  assets/audio/sfx.wav
"""
import pathlib
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_film as BF  # noqa: E402

SR = 48000
TOTAL = BF.TOTAL
N = int(TOTAL * SR) + SR
SC = {s["id"]: s for s in BF.S}
rng = np.random.default_rng(20261003)


def cue(key: str) -> float:
    return BF.cue_abs(key)


def t_(sec: float) -> np.ndarray:
    return np.arange(int(sec * SR)) / SR


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono or stereo signal into a stereo buffer at time `at` (equal-power pan)."""
    i = int(at * SR)
    if i >= len(buf):
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], axis=1)
    n = min(len(sig), len(buf) - i)
    if i < 0:
        sig, n, i = sig[-i:], n + i, 0
    buf[i : i + n] += sig[:n] * gain


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.3, hold=None):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    h_n = max(0, n - a_n - d_n - r_n) if hold is None else int(hold * SR)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False), np.full(h_n, s), np.linspace(s, 0, r_n)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def additive(f, dur, partials=10, tilt=1.0, detune_cents=0.0):
    t = t_(dur)
    out = np.zeros_like(t)
    fd = f * 2 ** (detune_cents / 1200)
    for k in range(1, partials + 1):
        if fd * k > 16000:
            break
        out += np.sin(2 * np.pi * fd * k * t + k * 0.7) / (k**tilt)
    return out


def reverb_ir(seconds=2.4, damp=3000):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.0 / seconds)[:, None]
    ir = lp(ir, damp)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir**2).sum(axis=0, keepdims=True))


IR = reverb_ir()


def verb(x, wet=0.3):
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    w = np.stack([fftconvolve(x[:, 0], IR[:, 0])[: len(x)], fftconvolve(x[:, 1], IR[:, 1])[: len(x)]], axis=1)
    return x * (1 - wet) + w * wet * 3.0


# ----------------------------------------------------------------------------- instruments


def pad_chord(notes, dur, bright=1.0, att=0.9, rel=1.2):
    n = int(dur * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for m in notes:
        f = midi(m)
        L += additive(f, dur, 12, 1.35, -6)[:n]
        R += additive(f, dur, 12, 1.35, +6)[:n]
    e = env_adsr(n, att, 0.4, 0.85, rel)
    st = np.stack([L * e, R * e], axis=1) / max(1, len(notes))
    return lp(st, 900 + 2600 * bright)


def bell(f, dur=2.5, index=2.2, ratio=3.5):
    t = t_(dur)
    mod = np.sin(2 * np.pi * f * ratio * t) * index * np.exp(-t * 2.2)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.6) * env_adsr(len(t), 0.004, 0.05, 1, 0.2)


def pluck(f, dur=0.6):
    t = t_(dur)
    s = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) + 0.18 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t * 7.5) * env_adsr(len(t), 0.003, 0.05, 1, 0.08)


def bass_note(f, dur=0.45):
    t = t_(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return np.tanh(1.6 * s * env_adsr(len(t), 0.006, 0.08, 0.75, 0.12)) * 0.8


def kick(dur=0.45, soft=1.0):
    t = t_(dur)
    f = 44 + 90 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.25 * soft
    return body + lp(click, 4000)


def clap(dur=0.25):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    e = np.zeros(n)
    for k, o in enumerate([0, 0.011, 0.022]):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(n - i) / SR * (60 if k < 2 else 16))
    return bp(noise * e, 900, 3500) * 0.9


def hat(dur=0.06):
    n = int(dur * SR)
    return hp(rng.standard_normal(n), 7000) * np.exp(-np.arange(n) / SR * 70)


def noise_swell(dur, f0, f1, up=True):
    """Filtered-noise whoosh/riser with a sweeping band (STFT-free: block-wise filter)."""
    n = int(dur * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    blocks = 48
    edges = np.linspace(0, n, blocks + 1).astype(int)
    for b in range(blocks):
        u = b / (blocks - 1)
        fc = f0 * (f1 / f0) ** u
        seg = x[max(0, edges[b] - 2048) : edges[b + 1]]
        y = bp(seg, max(40, fc * 0.6), min(20000, fc * 1.6))
        out[edges[b] : edges[b + 1]] = y[-(edges[b + 1] - edges[b]) :]
    shape = np.linspace(0, 1, n) ** 2 if up else np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return out * shape


# ----------------------------------------------------------------------------- music

music = np.zeros((N, 2))

# Act I — the silence: B minor 9 drone, heartbeat, clock
q_end = cue("L2.quiet") + 0.42
drone_len = q_end + 0.2
dr = pad_chord([35, 42, 50, 57, 61], drone_len, bright=0.25, att=1.8, rel=0.05)
lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * t_(drone_len))[:, None]
fade = np.ones(len(dr))
fade[-int(0.03 * SR) :] = np.linspace(1, 0, int(0.03 * SR))
place(music, dr * lfo * fade[:, None], 0.0, 0.55)
for k, tb in enumerate(np.arange(1.2, q_end - 0.3, 60 / 68)):
    place(music, lp(kick(0.5, 0.2), 180) * (0.35 + 0.05 * k), tb, 0.55)
tick_t = 0.5
while tick_t < cue("L1.nothing") + 0.05:
    tk = hp(rng.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / SR * 500), 3000)
    place(music, tk, tick_t, 0.10, pan=0.35 if int(tick_t * 2) % 2 else -0.35)
    tick_t += 0.5 if tick_t < cue("L1.and") - 0.2 else 0.18  # time speeds up while the counter rolls
place(music, noise_swell(1.4, 2000, 300, up=False) * 0.35, cue("L1.nothing") - 0.4, 0.5)

# the silence, then the light trace
T_SPARK = SC["f04"]["start"] + 0.32
MEET = cue("L3.meet")
sh_len = MEET - T_SPARK + 0.1
sh = np.zeros(int(sh_len * SR))
for m in (86, 93, 98, 105):
    sh += additive(midi(m), sh_len, 3, 1.5)[: len(sh)] * 0.25
sh *= np.linspace(0, 1, len(sh)) ** 2.2
place(music, verb(sh, 0.5), T_SPARK, 0.35)
place(music, noise_swell(sh_len, 400, 6000, up=True) * 0.25, T_SPARK, 0.5)

# the sting on "Meet": D add9 bells + sub + pad bloom
for m, g in ((74, 1.0), (78, 0.8), (81, 0.8), (88, 0.55), (62, 0.6)):
    place(music, verb(bell(midi(m), 3.0), 0.45), MEET - 0.02, 0.22 * g)
sub = np.sin(2 * np.pi * midi(26) * t_(2.5)) * np.exp(-t_(2.5) * 1.6)
place(music, sub, MEET - 0.02, 0.5)

# Act III groove — the grid lands MEET and the CTA on downbeats
CTA = SC["f09"]["start"]
BAR = (CTA - MEET) / 9
BEAT = BAR / 4
prog = [  # (root midi for bass, chord voicing)
    (38, [62, 66, 69, 76]),  # D add9
    (35, [59, 62, 66, 73]),  # Bm add9
    (31, [55, 59, 62, 69]),  # G add9
    (33, [57, 61, 64, 71]),  # A add9
]
bars = [prog[i % 4] for i in range(9)] + [prog[0], prog[2]]
dark = (SC["f07"]["start"], SC["f07"]["end"])
for b, (root, chord) in enumerate(bars):
    t0 = MEET + b * BAR
    in_dark = dark[0] - 0.3 <= t0 < dark[1] - 0.5
    place(music, verb(pad_chord(chord, BAR + 1.2, bright=0.45 if in_dark else 0.8, att=0.5, rel=1.0), 0.35), t0, 0.40)
    if b >= 1:
        for k, o in enumerate((0, 1.5, 2, 3.5)):
            place(music, bass_note(midi(root), BEAT * 0.9), t0 + o * BEAT, 0.42 if k % 2 == 0 else 0.3)
    if t0 >= SC["f05"]["start"] - 0.3:
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[3] + 12, chord[2] + 12, chord[1] + 12, chord[3] + 12, chord[2] + 12]
        for k in range(8):
            p = pluck(midi(arp[k]), 0.7)
            place(music, p, t0 + k * BEAT / 2, 0.07, pan=-0.3 if k % 2 else 0.3)
            place(music, lp(p, 3000), t0 + k * BEAT / 2 + BEAT * 0.75, 0.025, pan=0.6 if k % 2 else -0.6)
    if b >= 2:
        for o in (0, 2):
            place(music, kick(), t0 + o * BEAT, 0.5)
    if b >= 3 and not in_dark:
        for k in range(8):
            place(music, hat(), t0 + k * BEAT / 2, 0.06 if k % 2 else 0.035, pan=0.25)
    if b >= 4:
        for o in (1, 3):
            place(music, verb(clap(), 0.25), t0 + o * BEAT, 0.16)

# lift into the CTA
place(music, noise_swell(2.2, 300, 9000, up=True) * 0.5, CTA - 2.2, 0.5)
place(music, kick(0.6), CTA, 0.7)
place(music, sub, CTA, 0.45)
for m in (74, 81, 86):
    place(music, verb(bell(midi(m), 2.5), 0.4), CTA, 0.12)

# the groove fades out as the end card arrives, then the last chord rings under it
END = SC["f10"]["start"]
g0, g1 = int((END - 0.3) * SR), int(END * SR)
music[g0:g1] *= np.linspace(1, 0, g1 - g0)[:, None]
music[g1:] = 0
ring = verb(pad_chord([50, 57, 62, 66, 69, 76], TOTAL - END + 0.5, bright=0.7, att=0.4, rel=2.5), 0.45)
place(music, ring, END - 0.25, 0.55)
for m in (74, 78, 81, 88):
    place(music, verb(bell(midi(m), 3.5), 0.5), END + 0.2, 0.14)
fade_out = np.ones(N)
fo0, fo1 = int((TOTAL - 1.1) * SR), int(TOTAL * SR)
fade_out[fo0:fo1] = np.linspace(1, 0, fo1 - fo0)
fade_out[fo1:] = 0
music *= fade_out[:, None]

# sidechain: duck the bed under every spoken word
vo, vsr = sf.read(ROOT / "assets/audio/vo.wav", dtype="float64")
if vo.ndim > 1:
    vo = vo.mean(axis=1)
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
hop = 240
env = np.sqrt(np.convolve(vo**2, np.ones(hop * 4) / (hop * 4), mode="same"))
active = (env > 0.01).astype(float)
att, rel = 0.02, 0.35
sm = np.zeros(N)
a_c, r_c = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
lvl = 0.0
for i in range(0, N, hop):
    target = active[i]
    c = a_c if target > lvl else r_c
    lvl = target + (lvl - target) * c**hop
    sm[i : i + hop] = lvl
duck_db = -15.0
music *= (10 ** (duck_db * sm / 20))[:, None]

# ----------------------------------------------------------------------------- sound design

sfx = np.zeros((N, 2))


def kit(name):
    x, sr = sf.read(ROOT.parent / "assets_in/sfx-kit" / f"{name}.wav", dtype="float64")
    return x


def blip(kind="send"):
    if kind == "send":
        t = t_(0.16)
        f = 640 + 520 * (1 - np.exp(-t * 40))
    else:
        t = t_(0.2)
        f = np.where(t < 0.06, 880, 1320)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 22) * env_adsr(len(t), 0.002, 0.02, 1, 0.03)


def tap():
    n = int(0.03 * SR)
    return bp(rng.standard_normal(n), 1500, 6000) * np.exp(-np.arange(n) / SR * 260)


def whoosh(dur=0.45, f0=500, f1=3500):
    return noise_swell(dur, f0, f1, up=False)


def sub_hit(f=52):
    t = t_(0.7)
    ff = f + 40 * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 5)
    trans = hp(rng.standard_normal(len(t)) * np.exp(-t * 300), 2000) * 0.3
    return body + trans


def swish(dur=0.7):
    return hp(noise_swell(dur, 2500, 7000, up=False), 1800)


def sparkle(dur=0.8):
    out = np.zeros(int(dur * SR))
    for k in range(9):
        f = midi(rng.integers(86, 104))
        o = int(rng.uniform(0, dur * 0.7) * SR)
        b = bell(f, 0.5, 1.0, 2.0)[: len(out) - o]
        out[o : o + len(b)] += b * 0.3
    return out


S_ = lambda cid, off=0.0: SC[cid]["start"] + off  # noqa: E731

# Act I
place(sfx, kit("pop") * 0.5, S_("f01", 0.18), 0.25)
place(sfx, kit("pop"), S_("f01", 0.42), 0.32)
place(sfx, blip("send"), cue("L1.manychat") - 0.1, 0.22, pan=0.3)
place(sfx, kit("tick"), cue("L1.link") - 0.18, 0.18, pan=0.3)
for k in range(5):
    place(sfx, tap(), cue("L1.the") - 0.1 + k * 0.11, 0.12, pan=-0.3)
place(sfx, blip("recv"), cue("L1.lead") - 0.05, 0.2, pan=-0.3)
for k, o in enumerate((0.05, 0.3, 0.55)):
    place(sfx, kit("tick") * (0.6 - 0.15 * k), cue("L1.then") + o, 0.12, pan=0.3)
place(sfx, kit("counter"), cue("L1.and") - 0.15, 0.10, pan=0.4)
place(sfx, sub_hit(42) * 0.6, cue("L1.nothing") - 0.05, 0.3)
# Act I — slams
for i, w in enumerate(("good", "leads", "go", "quiet")):
    place(sfx, sub_hit(50 - i * 3), cue(f"L2.{w}") - 0.06, 0.28 + 0.04 * i)
    place(sfx, lp(clap(), 2500) * 0.5, cue(f"L2.{w}") - 0.06, 0.12)
for k in range(4):
    place(sfx, kit("tick") * 0.5, cue("L2.quiet") + 0.4 + k * 0.12, 0.05 * (1 - k * 0.2))
# Act II — the light
place(sfx, sparkle(0.9), T_SPARK, 0.18)
place(sfx, whoosh(1.0, 300, 5000), MEET - 0.1, 0.35)
place(sfx, swish(0.6), cue("L3.manysetter") - 0.1, 0.12)
place(sfx, kit("pop"), cue("L3.the") - 0.15, 0.2)
# S5 learns
place(sfx, whoosh(0.6, 400, 2500), S_("f05", 0.12), 0.25, pan=0.4)
for k, o in enumerate((-0.35, -0.25, -0.15, -0.05)):
    place(sfx, whoosh(0.4, 700, 4000), cue("L4.offer") + o, 0.2, pan=-0.6 + 0.1 * k)
    place(sfx, kit("snap"), cue("L4.offer") + o + 0.45, 0.12)
place(sfx, whoosh(0.5, 3000, 600), cue("L4.voice") - 0.25, 0.18, pan=0.3)
place(sfx, kit("success") * 0.6, cue("L4.voice") + 0.2, 0.14, pan=0.5)
for k in range(7):
    place(sfx, kit("tick") * 0.6, cue("L4.voice") + 0.25 + k * 0.24, 0.07, pan=0.3)
place(sfx, swish(0.8), cue("L4.sounds") - 0.05, 0.14)
place(sfx, kit("pop"), cue("L4.you") - 0.1, 0.2, pan=-0.4)
place(sfx, whoosh(0.5, 500, 3000), cue("L4.even") - 0.3, 0.2, pan=0.3)
place(sfx, kit("switch"), cue("L4.voice#2") - 0.1, 0.18, pan=0.3)
# S6 qualifies
place(sfx, whoosh(0.6, 400, 3000), cue("L5.qualifies") - 0.35, 0.22, pan=-0.6)
place(sfx, whoosh(0.6, 400, 3000), cue("L5.qualifies") - 0.25, 0.22, pan=0.6)
place(sfx, blip("recv"), cue("L5.lead") - 0.1, 0.16, pan=-0.5)
place(sfx, blip("recv"), cue("L5.with"), 0.16, pan=0.5)
place(sfx, kit("pop"), cue("L5.rules") - 0.25, 0.25)
place(sfx, kit("fill") * 0.5, cue("L5.rules") + 0.1, 0.08)
place(sfx, kit("success"), cue("L5.only") - 0.05, 0.2, pan=-0.5)
place(sfx, blip("send"), cue("L5.only") + 0.35, 0.14, pan=-0.5)
place(sfx, blip("send"), cue("L5.right") - 0.15, 0.14, pan=0.5)
place(sfx, kit("pop") * 0.7, cue("L5.right") + 0.2, 0.15, pan=0.5)
place(sfx, swish(0.8), cue("L5.right") + 0.15, 0.12)
place(sfx, kit("pop"), cue("L5.calendar") - 0.15, 0.18, pan=-0.5)
# S7 booked
place(sfx, whoosh(0.5, 2000, 300), S_("f07"), 0.2)
place(sfx, kit("pop"), S_("f07", 0.2), 0.2, pan=0.4)
for k in range(3):
    place(sfx, kit("tick"), S_("f07", 0.6 + k * 0.1), 0.1, pan=-0.5)
place(sfx, blip("send"), cue("L6.books") - 0.25, 0.18, pan=0.4)
place(sfx, blip("recv"), cue("L6.call") + 0.25, 0.18, pan=0.4)
place(sfx, whoosh(0.6, 600, 4000), cue("L6.call") + 0.65, 0.25, pan=0.4)
place(sfx, kit("chime"), cue("L6.right") - 0.05, 0.3, pan=0.3)
place(sfx, verb(bell(midi(86), 1.6), 0.4), cue("L6.right") - 0.04, 0.10, pan=0.3)
for k in range(3):
    place(sfx, kit("tick"), cue("L6.right") + 0.25 + k * 0.16, 0.12, pan=0.3)
place(sfx, swish(0.8), cue("L6.dm") - 0.15, 0.12, pan=-0.4)
# S8 control
place(sfx, whoosh(0.5, 300, 2500), S_("f08"), 0.2)
place(sfx, kit("pop"), cue("L7.manychat") - 0.15, 0.18, pan=-0.5)
place(sfx, kit("pop"), cue("L7.manychat") + 0.15, 0.18, pan=-0.4)
place(sfx, kit("snap"), cue("L7.flows") - 0.05, 0.3, pan=-0.2)
place(sfx, sub_hit(70) * 0.4, cue("L7.flows") - 0.05, 0.15)
place(sfx, swish(0.7), cue("L7.flows") + 0.25, 0.1, pan=-0.4)
for k in range(3):
    place(sfx, kit("tick"), cue("L7.flows") + 0.3 + k * 0.08, 0.08, pan=-0.5)
place(sfx, kit("switch"), cue("L7.over") - 0.05, 0.3, pan=0.5)
place(sfx, kit("success") * 0.7, cue("L7.over") + 0.2, 0.14, pan=0.5)
# S9 CTA
place(sfx, kit("pop"), cue("L8.setter") - 0.15, 0.22)
place(sfx, kit("switch"), cue("L8.free") + 0.12, 0.32, pan=0.2)
for k in range(3):
    place(sfx, kit("tick"), cue("L8.free") + 0.3 + k * 0.14, 0.1, pan=-0.3 + 0.3 * k)
place(sfx, kit("pop") * 0.6, cue("L8.manysettercom") - 0.2, 0.14)
# S10
place(sfx, whoosh(0.8, 3000, 400), END, 0.15)
place(sfx, swish(0.8), END + 1.1, 0.1)
sfx *= fade_out[:, None]

# ----------------------------------------------------------------------------- write stems


def finish(x, peak_db):
    x = x[: int(TOTAL * SR)]
    pk = np.max(np.abs(x)) + 1e-9
    return x * (10 ** (peak_db / 20) / pk)


out = ROOT / "assets/audio"
sf.write(out / "music.wav", finish(music, -4.0), SR, subtype="PCM_24")
sf.write(out / "sfx.wav", finish(sfx, -3.0), SR, subtype="PCM_24")
print("music.wav / sfx.wav written", round(TOTAL, 2), "s")
