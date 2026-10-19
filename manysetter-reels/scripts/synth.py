"""Small synthesis toolkit for the film's original score and sound design (48 kHz, numpy)."""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
rng = np.random.default_rng(20261003)


def t_(sec: float) -> np.ndarray:
    return np.arange(int(sec * SR)) / SR


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono or stereo signal into a stereo buffer at time `at` (equal-power pan)."""
    i = int(round(at * SR))
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], axis=1)
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
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
IR_SHORT = reverb_ir(0.9, 5000)


def verb(x, wet=0.3, ir=None):
    ir = IR if ir is None else ir
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    x = np.concatenate([x, np.zeros((len(ir) // 2, 2))])
    w = np.stack([fftconvolve(x[:, 0], ir[:, 0])[: len(x)], fftconvolve(x[:, 1], ir[:, 1])[: len(x)]], axis=1)
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


def epiano(f, dur=1.2):
    """FM electric piano (the cheesy lounge colour)."""
    t = t_(dur)
    mod = np.sin(2 * np.pi * f * t) * 1.4 * np.exp(-t * 5)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 5.5 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.4) * trem * env_adsr(len(t), 0.003, 0.05, 1, 0.15)


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
    """Filtered-noise whoosh/riser with a sweeping band."""
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


def whoosh(dur=0.45, f0=500, f1=3500):
    return noise_swell(dur, f0, f1, up=False)


def swish(dur=0.7):
    return hp(noise_swell(dur, 2500, 7000, up=False), 1800)


def sub_hit(f=52, dur=0.7):
    t = t_(dur)
    ff = f + 40 * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 5)
    trans = hp(rng.standard_normal(len(t)) * np.exp(-t * 300), 2000) * 0.3
    return body + trans


def impact(f=48):
    """Slam: sub thump + clap crack + short room."""
    s = sub_hit(f, 0.8)
    c = np.pad(clap(0.2), (0, len(s) - int(0.2 * SR)))
    return verb(s + 0.5 * c, 0.2, IR_SHORT)[: len(s) + int(0.4 * SR)]


def tick_soft():
    n = int(0.025 * SR)
    x = bp(rng.standard_normal(n), 2500, 9000) * np.exp(-np.arange(n) / SR * 380)
    return x


def thump(f=110):
    t = t_(0.18)
    ff = f + 60 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 26)


def blip(kind="send"):
    if kind == "send":
        t = t_(0.16)
        f = 640 + 520 * (1 - np.exp(-t * 40))
    else:
        t = t_(0.2)
        f = np.where(t < 0.06, 880, 1320)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 22) * env_adsr(len(t), 0.002, 0.02, 1, 0.03)


def ping(f=1568):
    """Notification ping (two quick sine partials)."""
    t = t_(0.35)
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)
    return s * np.exp(-t * 14) * env_adsr(len(t), 0.002, 0.02, 1, 0.05)


def scribble(dur=0.6):
    """Felt pen on paper: band-passed noise with a stroke-like amplitude flutter."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 1800, 6500)
    am = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 7.5 * t + 1.3 * np.sin(2 * np.pi * 2.1 * t)))
    return x * am * np.sin(np.linspace(0, np.pi, n)) ** 0.7


def scratch():
    """Record scratch: a pitched noise grain swept down then up."""
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    rate = np.concatenate([np.linspace(2.2, 0.3, n // 2), np.linspace(0.3, 1.8, n - n // 2)])
    ph = np.cumsum(rate) / SR
    tone = np.sin(2 * np.pi * 220 * ph * 3) * 0.5 + bp(rng.standard_normal(n), 600, 3800) * 0.8
    return tone * np.sin(np.linspace(0, np.pi, n)) ** 0.6 * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t))


def tape_stop(x, dur):
    """Slow a stereo snippet down to a halt (pitch dives)."""
    n = int(dur * SR)
    rate = np.linspace(1.0, 0.0, n) ** 1.6
    pos = np.cumsum(rate)
    pos = np.clip(pos, 0, len(x) - 2)
    i = pos.astype(int)
    fr = (pos - i)[:, None]
    return x[i] * (1 - fr) + x[i + 1] * fr


def woodblock(f=520):
    t = t_(0.18)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t * 38)


def sparkle(dur=0.8, lo=86, hi=104):
    out = np.zeros(int(dur * SR))
    for k in range(9):
        f = midi(rng.integers(lo, hi))
        o = int(rng.uniform(0, dur * 0.7) * SR)
        b = bell(f, 0.5, 1.0, 2.0)[: len(out) - o]
        out[o : o + len(b)] += b * 0.3
    return out


def click():
    n = int(0.03 * SR)
    return bp(rng.standard_normal(n), 1200, 7000) * np.exp(-np.arange(n) / SR * 260) + thump(180)[:n] * 0.5


def impact_word(f=50):
    """Slam under a spoken word: sub thump and a soft click, no mid-range crack to mask the consonant."""
    s = sub_hit(f, 0.7)
    s[: int(0.004 * SR)] += hp(rng.standard_normal(int(0.004 * SR)), 5000) * 0.2
    return lp(s, 1200)
