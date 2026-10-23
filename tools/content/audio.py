#!/usr/bin/env python3
"""Burn Rate's sounds and music, synthesized (no samples): the 18 common sound
slots and 5 menu sounds by the events the engine plays them for
(docs/INTERFACE_SLOTS.md §8-9), the attack swing, and eight chiptune tracks
for the engine's music names. Returns 16-bit mono WAV bytes."""
import struct
import numpy as np

RATE = 22050

def wav(samples, rate=RATE):
    x = np.clip(np.asarray(samples, float), -1, 1)
    data = (x * 32000).astype("<i2").tobytes()
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate * 2, 2, 16)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(data)) + data
    return b"RIFF" + struct.pack("<I", len(body)) + body

def t(seconds): return np.arange(int(seconds * RATE)) / RATE
def env(n, attack=0.004, decay=6.0):
    x = np.arange(n) / RATE
    return np.minimum(1, x / attack) * np.exp(-decay * x)
def noise(n, seed): return np.random.default_rng(seed).uniform(-1, 1, n)
def lowpass(x, alpha):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += alpha * (v - acc); y[i] = acc
    return y
def sweep(f0, f1, seconds, shape=np.sin):
    tt = t(seconds); f = np.linspace(f0, f1, len(tt)); return shape(2 * np.pi * np.cumsum(f) / RATE)
def square(phase): return np.sign(np.sin(phase))

def thud(seconds=0.16, pitch=110, crack=0.4, seed=1):
    n = int(seconds * RATE); body = sweep(pitch * 1.8, pitch * 0.6, seconds) * env(n, decay=18)
    snap = lowpass(noise(n, seed), 0.35) * env(n, decay=45) * crack
    return 0.9 * body + snap

def clank(seconds=0.22, freq=1400, seed=2):
    n = int(seconds * RATE); tt = t(seconds)
    ring = (np.sin(2 * np.pi * freq * tt) + 0.6 * np.sin(2 * np.pi * freq * 1.51 * tt)) * env(n, decay=16)
    return 0.5 * ring + 0.4 * noise(n, seed) * env(n, decay=60)

def whoosh(seconds=0.18, seed=3, up=True):
    n = int(seconds * RATE); x = noise(n, seed)
    a = np.linspace(0.05, 0.4, n) if up else np.linspace(0.4, 0.05, n)
    y = np.empty(n); acc = 0.0
    for i in range(n): acc += a[i] * (x[i] - acc); y[i] = acc
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return 1.6 * y * shape

def zap(seconds=0.2, f0=1800, f1=200):
    n = int(seconds * RATE); return 0.45 * square(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / RATE) * env(n, decay=10)

def blip(freqs, step=0.06, duty=0.25, decay=14):
    out = []
    for f in freqs:
        n = int(step * RATE); ph = (np.arange(n) * f / RATE) % 1
        out.append(np.where(ph < duty, 0.35, -0.35) * env(n, decay=decay))
    return np.concatenate(out)

def mix(*parts):
    out = np.zeros(max(len(p) for p in parts))
    for p in parts: out[:len(p)] += p
    return out

def common_sounds():
    """Slots 0-17 by the events they play for."""
    s = [None] * 18
    s[0] = thud(0.14, 120, 0.5, 10)                       # hit
    s[1] = clank(0.2, 1500, 11)                            # blocked
    s[2] = mix(thud(0.3, 80, 0.9, 12), 0.3 * zap(0.15, 600, 90))  # knockdown hit
    s[6] = thud(0.25, 60, 0.3, 13)                         # body hits the ground
    s[7] = whoosh(0.2, 14)                                 # dash
    s[11] = zap(0.18, 2200, 400)                           # effect hit
    s[12] = zap(0.32, 1600, 120)                           # effect knockdown
    s[13] = thud(0.12, 220, 1.0, 15)                       # object strike
    s[14] = sweep(2400, 3200, 0.3) * env(int(0.3 * RATE), decay=6) * 0.3   # freeze
    s[15] = clank(0.35, 2600, 16) + 0.3 * noise(int(0.35 * RATE), 17) * env(int(0.35 * RATE), decay=12)  # ice breaks
    s[16] = whoosh(0.4, 18, up=False) + 0.2 * noise(int(0.4 * RATE), 19) * env(int(0.4 * RATE), decay=5)  # catch fire
    s[17] = clank(0.24, 700, 20)                           # armoured block
    for i in (3, 4, 5, 8, 9, 10): s[i] = blip([660 + 40 * i], 0.05)   # no engine caller; valid WAVs
    return [wav(x) for x in s]

def menu_sounds():
    return [wav(blip([523, 784], 0.05)),                  # join / pick
            wav(blip([880], 0.05)),                       # ok
            wav(blip([523, 330], 0.06)),                  # cancel
            wav(blip([523, 659, 784, 1047], 0.08)),       # pass / champion
            wav(blip([784, 659, 523, 392], 0.12, decay=6))]  # round over

def swing():
    return wav(whoosh(0.13, 21))

# --- music --------------------------------------------------------------------
NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)
PROGRESSIONS = [[0, -4, 3, -2], [0, 5, -4, -2], [0, -2, -4, -5], [0, 3, -2, 5]]   # i VI III VII etc. (semitones from root)
MINOR = [0, 2, 3, 5, 7, 8, 10]

def track(seed, bpm, root=57, bars=16):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm; step = beat / 4; steps = bars * 16
    n = int(steps * step * RATE) + RATE; out = np.zeros(n)
    prog = PROGRESSIONS[seed % len(PROGRESSIONS)]
    def add(start, sig, gain):
        i = int(start * RATE); j = min(n, i + len(sig)); out[i:j] += gain * sig[:j - i]
    def tone(freq, seconds, kind, decay=4.0):
        m = int(seconds * RATE); ph = np.arange(m) * freq / RATE % 1
        if kind == "tri": w = 4 * np.abs(ph - 0.5) - 1
        elif kind == "pulse": w = np.where(ph < 0.25, 1.0, -1.0)
        else: w = np.where(ph < 0.125, 1.0, -1.0)
        return w * env(m, 0.003, decay)
    # A melody motif per track (two bars), varied each repeat.
    motif = []
    for k in range(32):
        if rng.random() < 0.55: motif.append(None)
        else: motif.append(int(rng.integers(0, 7)) + 7 * int(rng.integers(0, 2)))
    for s in range(steps):
        bar, pos = divmod(s, 16); chord = root + prog[(bar // 2) % 4]; at = s * step
        if pos % 4 == 0: add(at, sweep(150, 40, 0.12) * env(int(0.12 * RATE), decay=20), 0.55)          # kick
        if pos in (4, 12): add(at, lowpass(noise(int(0.12 * RATE), s), 0.6) * env(int(0.12 * RATE), decay=25), 0.3)  # snare
        if pos % 2 == 1: add(at, noise(int(0.03 * RATE), s + 7) * env(int(0.03 * RATE), decay=80), 0.08)  # hat
        if pos % 2 == 0: add(at, tone(NOTE(chord - 12), step * 1.8, "tri", 6), 0.32)                     # bass
        arp = [0, 3, 7, 12][pos % 4]; add(at, tone(NOTE(chord + arp + 12), step * 0.9, "thin", 18), 0.07)  # arpeggio
        degree = motif[(s % 32)]
        if degree is not None and bar % 8 < 7:
            d = degree + (2 if (bar // 4) % 2 and rng.random() < 0.2 else 0)
            octave, idx = divmod(d, 7)
            add(at, tone(NOTE(chord + 12 + MINOR[idx] + 12 * octave), step * 1.7, "pulse", 7), 0.12)    # lead
    out = out[:int(steps * step * RATE)]
    return out / max(1e-6, np.abs(out).max()) * 0.8

MUSIC = [("main", 1, 128), ("stage1", 2, 150), ("stage2", 3, 156), ("stage3", 4, 144), ("stage4", 5, 160),
         ("stage5", 6, 152), ("boss1", 7, 170), ("boss2", 8, 176)]

def music():
    """(name, wav bytes, frames) for the engine's eight music names."""
    out = []
    for name, seed, bpm in MUSIC:
        x = track(seed, bpm, root=[57, 52, 55, 50, 53, 57, 45, 48][seed - 1])
        out.append((name, wav(x), len(x)))
    return out
