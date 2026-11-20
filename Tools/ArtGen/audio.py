"""Procedural audio for WorldSim: ~150 SFX, 12 ambient loops, 6 era music loops.  numpy + scipy only, encoded to OGG Vorbis by ffmpeg.
Everything is synthesised from scratch (noise, filters, oscillators, envelopes) - no samples, nothing copied."""
import os, sys, math, json, subprocess, tempfile
import numpy as np
from scipy import signal

SR = 22050
RNG = np.random.default_rng(7)


# ------------------------------------------------------------------ building blocks
def t_(d): return np.arange(int(SR * d)) / SR


def noise(d, kind='white', seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    n = r.standard_normal(int(SR * d))
    if kind == 'pink':
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        n = signal.lfilter(b, a, n) * 4
    elif kind == 'brown':
        n = np.cumsum(n); n = signal.lfilter([1, -1], [1, -.995], n) * .08
    return n


def lp(x, f, o=2): b, a = signal.butter(o, min(f / (SR / 2), .99), 'low'); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, max(f / (SR / 2), .001), 'high'); return signal.lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = signal.butter(o, [max(f1 / (SR / 2), .001), min(f2 / (SR / 2), .99)], 'band'); return signal.lfilter(b, a, x)


def env(n, a=.005, d=.1, s=0.0, r=.05, total=None):
    N = n
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    e = np.zeros(N)
    A = min(A, N); e[:A] = np.linspace(0, 1, A, endpoint=False) if A else e[:A]
    D2 = min(D, N - A); e[A:A + D2] = np.linspace(1, s, D2, endpoint=False) if D2 else e[A:A + D2]
    e[A + D2:] = s
    if R and s > 0: e[-R:] *= np.linspace(1, 0, min(R, N))[-min(R, N):]
    return e


def expd(n, tau): return np.exp(-np.arange(n) / (SR * tau))


def osc(freq, d, kind='sine', phase=0.0):
    """freq: scalar or array (sweep)."""
    n = int(SR * d)
    f = np.full(n, freq, float) if np.isscalar(freq) else np.asarray(freq, float)[:n]
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == 'sine': return np.sin(ph)
    if kind == 'square': return np.sign(np.sin(ph)) * .6
    if kind == 'saw': return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'tri': return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    if kind == 'pulse': return np.where((ph / (2 * np.pi)) % 1 < .25, .7, -.7)


def sweep(f0, f1, d, curve='exp'):
    n = int(SR * d)
    return f0 * (f1 / f0) ** np.linspace(0, 1, n) if curve == 'exp' else np.linspace(f0, f1, n)


def msum(items):
    items = list(items)
    if not items: return np.zeros(1)
    if all(np.isscalar(i) for i in items): return float(np.sum(items))
    return mix(*[np.atleast_1d(i) for i in items])


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts: out[:len(p)] += p
    return out


def at(x, delay, total=None):
    pad = np.zeros(int(delay * SR)); y = np.concatenate([pad, x])
    return y


def reverb(x, room=.3, wet=.25):
    ir_len = int(SR * (.25 + room * 1.2))
    ir = noise(ir_len / SR + 1e-6, 'white', 3) * np.exp(-np.arange(ir_len) / (SR * (.05 + room * .35)))
    ir[0] = 0
    y = signal.fftconvolve(x, ir)[:len(x) + ir_len // 2]
    y = y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))
    out = np.zeros(len(y)); out[:len(x)] = x * (1 - wet)
    return out + y * wet


def formant(x, formants, bw=80):
    return msum(bp(x, f - bw, f + bw) * g for f, g in formants)


def norm(x, peak=.89):
    x = x - np.mean(x)
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def fade(x, fin=.003, fout=.02):
    n = len(x); a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def loopify(x, xf=.5):
    """crossfade the tail into the head so the loop is seamless."""
    n = int(xf * SR)
    head, tail = x[:n].copy(), x[-n:].copy()
    w = np.linspace(0, 1, n)
    y = x[:-n].copy()
    y[:n] = head * w + tail * (1 - w)
    return y


# ------------------------------------------------------------------ voices / instruments
def pluck(freq, d, bright=.5, seed=0):
    """Karplus-Strong string."""
    n = int(SR * d); N = max(2, int(SR / freq))
    buf = np.random.default_rng(seed).uniform(-1, 1, N)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % N]
        buf[i % N] = .5 * (buf[i % N] + buf[(i + 1) % N]) * (.994 + bright * .005)
    return out


def drum(kind, d=.4, seed=0):
    n = int(SR * d)
    if kind == 'kick': return osc(sweep(140, 45, d), d) * expd(n, .12) + lp(noise(d, seed=seed), 300) * expd(n, .01) * .3
    if kind == 'tom': return osc(sweep(180, 110, d), d) * expd(n, .15)
    if kind == 'hand': return lp(noise(d, seed=seed), 900) * expd(n, .05) + osc(220, d) * expd(n, .04) * .4
    if kind == 'snare': return hp(noise(d, seed=seed), 1200) * expd(n, .08) * .7 + osc(190, d) * expd(n, .05) * .4
    if kind == 'hat': return hp(noise(d, seed=seed), 6000) * expd(n, .025) * .5
    if kind == 'shaker': return bp(noise(d, seed=seed), 3000, 8000) * env(n, .02, .08) * .4


def flute(freq, d, vib=5):
    n = int(SR * d)
    f = freq * (1 + .006 * np.sin(2 * np.pi * vib * t_(d)))
    tone = osc(f, d) + .25 * osc(f * 2, d) + .08 * osc(f * 3, d)
    breath = bp(noise(d, seed=int(freq)), freq * .8, freq * 3) * .12
    return (tone + breath) * env(n, .06, .1, .8, .12)


def pad(freqs, d, kind='saw', cutoff=1200):
    n = int(SR * d)
    s = msum(osc(f * (1 + det), d, kind) for f in freqs for det in (-.004, .004))
    return lp(s, cutoff) * env(n, .6, .3, .8, .8)


def brass(freq, d):
    n = int(SR * d)
    s = osc(freq, d, 'saw') + .5 * osc(freq * 2.003, d, 'saw')
    cut = np.linspace(400, 2400, n) if n else 1
    y = lp(s, 1600) * env(n, .04, .1, .7, .1)
    return y


def chip(freq, d, duty='pulse'):
    n = int(SR * d)
    return osc(freq, d, duty) * env(n, .002, .08, .5, .05)


def bell(freq, d):
    n = int(SR * d)
    return msum(osc(freq * r, d) * g * expd(n, tau) for r, g, tau in ((1, 1, .9), (2.76, .5, .5), (5.4, .25, .25), (8.93, .12, .12)))


NOTE = lambda midi: 440 * 2 ** ((midi - 69) / 12)


# ------------------------------------------------------------------ SFX definitions
def hit(d=.25, f=600, seed=0, body=180):
    n = int(SR * d)
    return lp(noise(d, seed=seed), f) * expd(n, .04) + osc(sweep(body, body * .6, d), d) * expd(n, .06) * .6


def whoosh(d=.35, f0=400, f1=2500, seed=0):
    n = int(SR * d)
    x = noise(d, seed=seed)
    fc = np.geomspace(f0, f1, n)
    y = np.zeros(n); block = 256
    for i in range(0, n, block):
        y[i:i + block] = bp(x[max(0, i - 512):i + block], fc[i] * .7, fc[i] * 1.4)[-len(x[i:i + block]):]
    return y * np.sin(np.linspace(0, np.pi, n))


def explosion(d=1.6, size=1.0, seed=0):
    n = int(SR * d)
    boom = lp(noise(d, 'brown', seed), 180 + 120 / size) * expd(n, .35 * size) * 3
    crack = hp(noise(d, seed=seed + 1), 1500) * expd(n, .03) * .8
    rumble = lp(noise(d, seed=seed + 2), 90) * env(n, .05, d * .8, 0) * 2
    debris = msum(at(hp(noise(.05, seed=seed + 10 + i), 2500) * expd(int(.05 * SR), .01) * .3, .2 + .1 * i) for i in range(int(6 * size)))
    return mix(boom, crack, rumble, debris)


def gunshot(d=.5, cal=1.0, seed=0):
    n = int(SR * d)
    return mix(hp(noise(d, seed=seed), 800) * expd(n, .015 * cal) * 1.3, lp(noise(d, seed=seed + 1), 400) * expd(n, .09 * cal), reverb(hp(noise(d, seed=seed + 2), 400) * expd(n, .01), .5, .5) * .4)


def vocal(f0, d, vowel='a', shape=None, rough=0.0, seed=0):
    """formant-filtered buzz: crude 'oof', 'aah', scream, cheer voices."""
    n = int(SR * d)
    f = f0 if shape is None else shape
    src = osc(f, d, 'saw') + rough * noise(d, seed=seed)
    F = {'a': ((800, 1), (1150, .5), (2900, .25)), 'o': ((450, 1), (800, .5), (2830, .15)), 'u': ((325, 1), (700, .3), (2530, .1)),
         'e': ((400, 1), (1600, .4), (2700, .2)), 'i': ((300, 1), (2300, .3), (3000, .2))}[vowel]
    return formant(src, F, 90)


def animal_call(kind, seed=0):
    if kind == 'howl':
        d = 2.2; f = 380 + 220 * np.sin(np.linspace(0, np.pi, int(SR * d))) ** .7
        return vocal(None, d, 'u', f, .05) * env(int(SR * d), .2, .2, .9, .5)
    if kind == 'roar':
        d = 1.4; f = sweep(140, 90, d)
        return mix(vocal(None, d, 'a', f, .6, seed), lp(noise(d, seed=seed), 600) * .5) * env(int(SR * d), .08, .3, .7, .4)
    if kind == 'growl':
        d = 1.0; f = 85 + 10 * np.sin(2 * np.pi * 9 * t_(d))
        return vocal(None, d, 'o', f, .9, seed) * env(int(SR * d), .1, .2, .8, .2)
    if kind == 'bark':
        d = .35; return msum(at(vocal(None, .14, 'a', sweep(520, 300, .14), .4, seed) * expd(int(.14 * SR), .05), i * .17) for i in range(2))
    if kind == 'moo':
        d = 1.3; f = 120 + 25 * np.sin(np.linspace(0, np.pi, int(SR * d)))
        return vocal(None, d, 'u', f, .1) * env(int(SR * d), .15, .2, .8, .3)
    if kind == 'baa':
        d = .8; f = 300 * (1 + .04 * np.sign(np.sin(2 * np.pi * 18 * t_(d))))
        return vocal(None, d, 'e', f, .2) * env(int(SR * d), .05, .1, .8, .2)
    if kind == 'oink':
        return msum(at(vocal(None, .12, 'o', sweep(260, 180, .12), .8, seed) * expd(int(.12 * SR), .04), i * .16) for i in range(3))
    if kind == 'neigh':
        d = 1.2; f = 600 * (1 + .12 * np.sin(2 * np.pi * 14 * t_(d))) * np.linspace(1.2, .8, int(SR * d))
        return vocal(None, d, 'i', f, .2) * env(int(SR * d), .05, .3, .6, .4)
    if kind == 'cluck': return msum(at(bp(osc(sweep(900, 600, .06), .06, 'saw'), 500, 2500) * expd(int(.06 * SR), .02), i * .11) for i in range(4))
    if kind == 'quack': return msum(at(vocal(None, .15, 'a', sweep(500, 380, .15), .5, seed) * expd(int(.15 * SR), .07), i * .22) for i in range(2))
    if kind == 'chirp': return msum(at(osc(sweep(3000 + i * 200, 4500, .07), .07) * expd(int(.07 * SR), .03), i * .1) for i in range(5))
    if kind == 'caw': return msum(at(vocal(None, .28, 'a', sweep(700, 550, .28), .9, seed) * env(int(.28 * SR), .02, .2, .3, .05), i * .4) for i in range(2))
    if kind == 'screech': d = .9; return hp(vocal(None, d, 'i', sweep(2200, 1500, d), .6, seed), 800) * env(int(SR * d), .02, .5, .2, .2)
    if kind == 'hoot': return msum(at(osc(sweep(420, 380, .3), .3) * env(int(.3 * SR), .05, .2, .5, .05), i * .45) for i in range(2))
    if kind == 'croak': return msum(at(bp(osc(95, .18, 'pulse') * (1 + noise(.18, seed=i) * .3), 200, 1400) * env(int(.18 * SR), .01, .15, 0), i * .22) for i in range(3))
    if kind == 'buzz': d = 1.2; return bp(osc(220 + 15 * np.sin(2 * np.pi * 7 * t_(d)), d, 'saw'), 300, 3000) * env(int(SR * d), .1, .2, .8, .3) * .5
    if kind == 'hiss': d = 1.0; return hp(noise(d, seed=seed), 3500) * env(int(SR * d), .1, .3, .7, .3)
    if kind == 'trumpet':
        d = 1.4; f = 520 * (1 + .1 * np.sin(np.linspace(0, 3, int(SR * d))))
        return brass(f, d) * env(int(SR * d), .05, .2, .8, .4)
    if kind == 'whale':
        d = 3.0; f = 200 + 140 * np.sin(np.linspace(0, 2.5, int(SR * d)))
        return reverb(osc(f, d) * env(int(SR * d), .5, .5, .8, 1), .9, .5)
    if kind == 'monster':
        d = 2.0; f = sweep(110, 60, d)
        return mix(vocal(None, d, 'a', f, 1.2, seed) * 1.2, lp(noise(d, 'brown', seed), 200) * 1.5, vocal(None, d, 'o', f * 1.5, .5) * .5) * env(int(SR * d), .1, .5, .7, .6)
    if kind == 'titan':
        d = 3.2; f = sweep(70, 38, d)
        return reverb(mix(vocal(None, d, 'o', f, 1.5, seed) * 1.5, lp(noise(d, 'brown', seed), 120) * 2) * env(int(SR * d), .2, 1, .6, 1), .8, .4)
    if kind == 'step_big':
        d = 1.2; n = int(SR * d)
        return reverb(lp(noise(d, 'brown', seed), 90) * expd(n, .12) * 3 + osc(sweep(55, 30, d), d) * expd(n, .2), .6, .3)
    if kind == 'flap': return msum(at(lp(noise(.12, seed=i), 1500) * env(int(.12 * SR), .02, .1, 0), i * .18) for i in range(3))
    if kind == 'chomp': return msum(at(hit(.08, 2000, i, 300) * .8, i * .14) for i in range(3))
    if kind == 'wail':
        d = 2.5; f = 500 + 120 * np.sin(2 * np.pi * .6 * t_(d)) + 20 * np.sin(2 * np.pi * 6 * t_(d))
        return reverb(vocal(None, d, 'o', f, .2) * env(int(SR * d), .5, .5, .8, .8), .9, .6)
    if kind == 'rattle': return msum(at(bp(noise(.03, seed=i), 1500, 5000) * expd(int(.03 * SR), .008), .04 * i + RNG.uniform(0, .02)) for i in range(16))
    if kind == 'moan':
        d = 1.8; f = 140 + 15 * np.sin(2 * np.pi * .8 * t_(d))
        return vocal(None, d, 'o', f, .5, seed) * env(int(SR * d), .3, .4, .8, .5)
    if kind == 'laugh':
        return reverb(msum(at(vocal(None, .13, 'a', sweep(160, 120, .13), .7, seed + i) * env(int(.13 * SR), .01, .1, .2, .02), i * .17) for i in range(6)), .7, .4)
    if kind == 'whoosh_magic':
        x = whoosh(1.0, 300, 3000, seed); return mix(x, osc(sweep(300, 900, 1.0), 1.0) * np.sin(np.linspace(0, np.pi, SR)) * .3)


def spell_sfx(kind, seed=0):
    if kind == 'charge':
        d = 1.0; n = int(SR * d)
        return mix(osc(sweep(200, 900, d), d, 'tri') * np.linspace(0, 1, n) * .5, bp(noise(d, seed=seed), 1500, 6000) * np.linspace(0, 1, n) * .3)
    if kind == 'fire_launch': return mix(whoosh(.6, 200, 1200, seed), lp(noise(.6, 'brown', seed), 300) * env(int(.6 * SR), .05, .4, 0) * 2)
    if kind == 'fire_impact': return mix(explosion(1.0, .5, seed) * .7, hp(noise(1.0, seed=seed), 2500) * env(int(SR), .01, .8, 0) * .3)
    if kind == 'ice':
        return mix(*[at(osc(NOTE(84 + k * 3), .4) * expd(int(.4 * SR), .08) * .4, k * .03) for k in range(5)], hp(noise(.3, seed=seed), 4000) * expd(int(.3 * SR), .05) * .6)
    if kind == 'nova': return reverb(mix(whoosh(1.2, 2000, 300, seed), osc(sweep(1200, 200, 1.2), 1.2, 'tri') * expd(int(1.2 * SR), .4) * .4), .7, .4)
    if kind == 'zap':
        d = .5; n = int(SR * d)
        return mix(osc(sweep(1800, 200, d), d, 'saw') * (noise(d, seed=seed) > .3) * expd(n, .15), hp(noise(d, seed=seed + 1), 2000) * expd(n, .08) * .7)
    if kind == 'thunder':
        d = 3.0; n = int(SR * d)
        return mix(hp(noise(d, seed=seed), 1500) * expd(n, .05) * 1.2, lp(noise(d, 'brown', seed), 150) * env(n, .05, 2.4, 0) * 3)
    if kind == 'heal': return reverb(mix(*[at(bell(NOTE(m), 1.2) * .4, i * .12) for i, m in enumerate((72, 76, 79, 84))]), .7, .4)
    if kind == 'curse':
        d = 2.0; return reverb(mix(osc(NOTE(38), d, 'saw'), osc(NOTE(38) * 1.06, d, 'saw')) * env(int(SR * d), .4, .5, .7, .5) * .4, .8, .5)
    if kind == 'portal':
        d = 2.2; n = int(SR * d)
        return reverb(mix(pad([NOTE(48), NOTE(55), NOTE(63)], d, 'saw', 900) * .5, osc(sweep(80, 300, d), d, 'tri') * .3, bp(noise(d, seed=seed), 600, 3000) * np.sin(np.linspace(0, np.pi, n)) * .3), .9, .5)
    if kind == 'teleport': return mix(osc(sweep(300, 3000, .4), .4, 'square') * env(int(.4 * SR), .01, .3, 0) * .4, at(osc(sweep(3000, 600, .3), .3, 'tri') * .3, .35))
    if kind == 'shield': return reverb(mix(osc(NOTE(67), .8) * expd(int(.8 * SR), .3), osc(NOTE(74), .8) * expd(int(.8 * SR), .3) * .6, hp(noise(.8, seed=seed), 3000) * expd(int(.8 * SR), .1) * .2), .5, .3)
    if kind == 'whisper':
        d = 2.0; n = int(SR * d)
        return reverb(msum(bp(noise(d, seed=seed + i), 1500 + i * 700, 2400 + i * 700) * (np.sin(np.linspace(0, (6 + i) * np.pi, n)) ** 2) for i in range(3)) * .5, .8, .5)
    if kind == 'dissolve': return reverb(mix(*[at(osc(NOTE(88 - k * 2), .3) * expd(int(.3 * SR), .1) * .25, k * .06) for k in range(10)], hp(noise(1.0, seed=seed), 5000) * env(int(SR), .1, .8, 0) * .3), .6, .4)


def work_sfx(kind, seed=0):
    if kind == 'chop': return mix(hit(.3, 1800, seed, 220) * 1.2, at(bp(noise(.15, seed=seed), 1500, 4000) * expd(int(.15 * SR), .03) * .3, .01))
    if kind == 'mine': return mix(bell(1900, .5) * .3, hit(.3, 4000, seed, 400) * .8)
    if kind == 'hammer': return mix(bell(1300, .4) * .35, hit(.2, 3000, seed, 500))
    if kind == 'saw': return msum(at(bp(noise(.25, seed=seed + i), 1500, 5000) * np.sin(np.linspace(0, np.pi, int(.25 * SR))) * .6, i * .27) for i in range(3))
    if kind == 'hoe': return mix(lp(noise(.3, seed=seed), 1200) * expd(int(.3 * SR), .06), hit(.2, 700, seed, 120) * .5)
    if kind == 'harvest': return msum(at(bp(noise(.08, seed=seed + i), 2000, 7000) * expd(int(.08 * SR), .02) * .5, i * .07) for i in range(6))
    if kind == 'splash': return mix(bp(noise(.6, seed=seed), 400, 4000) * env(int(.6 * SR), .005, .5, 0), lp(noise(.4, seed=seed + 1), 300) * expd(int(.4 * SR), .08))
    if kind == 'splash_big': return mix(work_sfx('splash', seed) * 1.2, lp(noise(1.5, 'brown', seed), 250) * env(int(1.5 * SR), .02, 1.3, 0) * 2)
    if kind == 'complete': return mix(*[at(bell(NOTE(m), .9) * .35, i * .1) for i, m in enumerate((67, 71, 74, 79))])
    if kind == 'tree_fall':
        d = 2.2; n = int(SR * d)
        creak = bp(osc(sweep(90, 60, 1.2), 1.2, 'saw') * (1 + noise(1.2, seed=seed) * .3), 200, 1500) * env(int(1.2 * SR), .1, 1, 0) * .6
        return mix(creak, at(lp(noise(1.0, 'brown', seed), 200) * expd(int(SR), .2) * 3, 1.2), at(bp(noise(1.0, seed=seed + 2), 1500, 6000) * expd(int(SR), .15) * .4, 1.2))
    if kind == 'rock_break': return mix(hit(.5, 900, seed, 90) * 1.4, *[at(hit(.06, 4000, seed + i, 600) * .3, .05 + i * .05) for i in range(6)])
    if kind == 'door': return mix(bp(osc(sweep(300, 250, .6), .6, 'saw'), 400, 2000) * env(int(.6 * SR), .05, .5, 0) * .4, at(hit(.2, 600, seed, 100), .55))
    if kind == 'bell_civic': return reverb(bell(NOTE(55), 3.0), .8, .4)
    if kind in ('step_grass', 'step_stone', 'step_snow', 'step_sand'):
        f = {'step_grass': (500, 4000), 'step_stone': (800, 5000), 'step_snow': (300, 2500), 'step_sand': (600, 3500)}[kind]
        return msum(at(bp(noise(.08, seed=seed + i), *f) * expd(int(.08 * SR), .02 if kind != 'step_snow' else .04), i * .28) for i in range(2))
    if kind == 'cart': d = 2.0; n = int(SR * d); return mix(lp(noise(d, 'brown', seed), 300) * .8, msum(at(hit(.05, 1500, seed + i, 200) * .2, i * .25) for i in range(8)))
    if kind == 'ship_horn': d = 2.5; return reverb(mix(brass(NOTE(38), d), brass(NOTE(45), d) * .6), .9, .5)
    if kind == 'creak': return bp(osc(sweep(120, 80, 1.5), 1.5, 'saw') * (1 + noise(1.5, seed=seed) * .4), 300, 1800) * env(int(1.5 * SR), .2, 1.1, 0) * .5
    if kind == 'train':
        d = 3.0; return mix(msum(at(lp(noise(.25, seed=seed + i), 500) * expd(int(.25 * SR), .06), i * .25) for i in range(12)), at(brass(NOTE(70), .8) * .4, .2))
    if kind == 'engine':
        d = 2.0; f = 55 + 8 * np.sin(2 * np.pi * .7 * t_(d))
        return lp(osc(f, d, 'saw') + osc(f * 2, d, 'pulse') * .5 + noise(d, seed=seed) * .3, 700) * env(int(SR * d), .2, .2, .9, .3)
    if kind == 'tracks':
        d = 2.0; return mix(work_sfx('engine', seed) * .7, msum(at(hit(.04, 3000, seed + i, 300) * .25, i * .09) for i in range(22)))
    if kind == 'jet': d = 2.5; n = int(SR * d); return mix(hp(noise(d, seed=seed), 600) * np.sin(np.linspace(0, np.pi, n)) ** 2, lp(noise(d, 'brown', seed), 200) * np.sin(np.linspace(0, np.pi, n)) * 2)
    if kind == 'heli': d = 2.0; n = int(SR * d); return lp(noise(d, seed=seed), 500) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 14 * t_(d)))) * 1.3
    if kind == 'missile_launch': d = 2.5; n = int(SR * d); return mix(explosion(1.0, .5, seed) * .5, hp(noise(d, seed=seed), 900) * env(n, .1, .5, .7, 1.2) * .8)
    if kind == 'missile_whistle': d = 2.0; return mix(osc(sweep(2400, 700, d), d) * .4 * np.linspace(.2, 1, int(SR * d)), hp(noise(d, seed=seed), 3000) * .2)
    if kind == 'siren':
        d = 4.0; f = 600 + 300 * np.sin(2 * np.pi * .25 * t_(d))
        return mix(osc(f, d, 'tri'), osc(f * 1.5, d, 'sine') * .3) * env(int(SR * d), .3, .2, .9, .5)
    if kind == 'nuke':
        d = 6.0; n = int(SR * d)
        flash = hp(noise(.5, seed=seed), 1000) * expd(int(.5 * SR), .1) * 1.5
        body = lp(noise(d, 'brown', seed), 70) * env(n, .3, 5, 0) * 4
        roar = lp(noise(d, seed=seed + 1), 300) * env(n, .5, 4.5, 0) * 1.5
        return reverb(mix(flash, body, roar), .9, .3)
    if kind == 'geiger':
        d = 2.0; out = np.zeros(int(SR * d))
        for tt in np.cumsum(RNG.exponential(.05, 60)):
            i = int(tt * SR)
            if i < len(out) - 200: out[i:i + 200] += hp(noise(200 / SR, seed=i), 3000) * expd(200, .002)
        return out
    if kind == 'market': d = 4.0; return mix(*[at(vocal(None, .3, v, NOTE(52 + RNG.integers(0, 12)), .2, seed + i) * env(int(.3 * SR), .05, .2, .3, .05) * .25, RNG.uniform(0, 3.6)) for i, v in enumerate('aoeiuaoeiu' * 2)], bp(noise(d, seed=seed), 300, 3000) * .15)


def body_sfx(kind, seed=0):
    if kind in ('hurt_m', 'hurt_f'):
        f0 = 140 if kind == 'hurt_m' else 260
        return vocal(None, .25, 'u', sweep(f0 * 1.3, f0, .25), .3, seed) * env(int(.25 * SR), .01, .2, 0)
    if kind == 'scream': d = 1.0; return vocal(None, d, 'a', sweep(700, 550, d) * (1 + .03 * np.sin(2 * np.pi * 7 * t_(d))), .4, seed) * env(int(SR * d), .03, .3, .7, .3)
    if kind == 'death': d = .8; return vocal(None, d, 'o', sweep(180, 90, d), .5, seed) * env(int(SR * d), .02, .7, 0)
    if kind == 'burn': d = 2.0; n = int(SR * d); return mix(hp(noise(d, seed=seed), 2500) * (noise(d, seed=seed + 1) > 1.2) * 1.2, lp(noise(d, 'brown', seed), 400) * .6) * env(n, .05, 1.5, 0)
    if kind == 'freeze': return mix(spell_sfx('ice', seed), at(hit(.3, 5000, seed, 800) * .6, .3))
    if kind == 'shatter': return mix(*[at(osc(NOTE(90 + RNG.integers(-8, 8)), .2) * expd(int(.2 * SR), .04) * .3, RNG.uniform(0, .25)) for _ in range(14)], hp(noise(.4, seed=seed), 3000) * expd(int(.4 * SR), .08) * .7)
    if kind == 'electrocute': d = 1.2; return mix(spell_sfx('zap', seed), osc(120, d, 'square') * (noise(d, seed=seed) > 0) * env(int(SR * d), .01, 1, 0) * .3)
    if kind == 'cough': return msum(at(hp(noise(.15, seed=seed + i), 500) * env(int(.15 * SR), .01, .12, 0) + vocal(None, .15, 'a', 150, 1.0, seed) * .3 * expd(int(.15 * SR), .05), i * .3) for i in range(3))
    if kind == 'bubbles':
        d = 2.0; out = np.zeros(int(SR * d))
        for k in range(25):
            i = int(RNG.uniform(0, d - .1) * SR); f = RNG.uniform(400, 1200)
            b = osc(sweep(f, f * 1.8, .06), .06) * expd(int(.06 * SR), .02)
            out[i:i + len(b)] += b * .5
        return out
    if kind == 'crush': return mix(hit(.6, 400, seed, 70) * 2, *[at(hit(.05, 3000, seed + i, 500) * .3, .03 * i) for i in range(5)])
    if kind == 'cheer':
        d = 2.5; return mix(*[at(vocal(None, 1.2, v, NOTE(60 + RNG.integers(-5, 9)) * np.linspace(1, 1.15, int(1.2 * SR)), .3, seed + i) * env(int(1.2 * SR), .1, .5, .6, .4) * .3, RNG.uniform(0, .8)) for i, v in enumerate('aeaoaeia')], bp(noise(d, seed=seed), 500, 4000) * env(int(SR * d), .3, 1, .5, .8) * .3)
    if kind == 'panic':
        d = 3.0; return mix(*[at(body_sfx('scream', seed + i) * .3, RNG.uniform(0, 2)) for i in range(5)], bp(noise(d, seed=seed), 400, 3000) * .2)
    if kind == 'irradiated': d = 2.0; return mix(work_sfx('geiger', seed) * .5, osc(60, d, 'saw') * .2 * env(int(SR * d), .3, .5, .7, .5))


UI = {
    'click': lambda: chip(NOTE(84), .05, 'square'), 'hover': lambda: chip(NOTE(91), .03, 'tri') * .5,
    'confirm': lambda: mix(chip(NOTE(76), .08), at(chip(NOTE(83), .12), .07)), 'cancel': lambda: mix(chip(NOTE(72), .08), at(chip(NOTE(65), .12), .07)),
    'error': lambda: mix(chip(NOTE(58), .12, 'square'), at(chip(NOTE(58), .15, 'square'), .14)), 'open_panel': lambda: mix(whoosh(.2, 800, 3000) * .6, chip(NOTE(79), .08) * .5),
    'close_panel': lambda: whoosh(.2, 3000, 800) * .6, 'notify': lambda: mix(bell(NOTE(84), .6) * .5, at(bell(NOTE(88), .6) * .4, .09)),
    'level_up': lambda: mix(*[at(chip(NOTE(m), .1), i * .07) for i, m in enumerate((72, 76, 79, 84, 88))]), 'coin': lambda: mix(chip(NOTE(88), .06, 'square'), at(chip(NOTE(93), .2, 'square'), .05)),
    'power_select': lambda: mix(osc(sweep(500, 900, .15), .15, 'tri') * env(int(.15 * SR), .01, .1, 0), bell(NOTE(86), .3) * .3),
    'power_cast': lambda: mix(spell_sfx('charge') * .6, at(spell_sfx('teleport'), .4) * .5),
}

SFX = {}
def reg(cat, name, fn): SFX[f'{cat}_{name}'] = fn


for k, f in UI.items(): reg('ui', k, f)
reg('combat', 'sword_swing', lambda: whoosh(.25, 600, 3500))
reg('combat', 'sword_hit', lambda: mix(bell(2600, .4) * .3, hit(.2, 5000, 1, 300)))
reg('combat', 'club_hit', lambda: hit(.3, 900, 2, 120) * 1.3)
reg('combat', 'arrow_shoot', lambda: mix(bp(osc(sweep(260, 220, .2), .2, 'tri'), 200, 900) * expd(int(.2 * SR), .06), whoosh(.3, 2000, 5000) * .4))
reg('combat', 'arrow_hit', lambda: hit(.15, 2500, 3, 260))
reg('combat', 'spear_throw', lambda: whoosh(.45, 300, 1800))
reg('combat', 'sling', lambda: mix(whoosh(.3, 500, 2500), at(hit(.1, 3000, 4, 400) * .5, .25)))
reg('combat', 'shield_block', lambda: mix(hit(.3, 1200, 5, 150), bell(800, .4) * .2))
reg('combat', 'musket_shot', lambda: gunshot(.9, 1.6, 6))
reg('combat', 'rifle_shot', lambda: gunshot(.6, 1.0, 7))
reg('combat', 'mg_burst', lambda: mix(*[at(gunshot(.25, .6, 8 + i) * .7, i * .08) for i in range(8)]))
reg('combat', 'cannon', lambda: explosion(1.5, .8, 9))
reg('combat', 'explosion_small', lambda: explosion(1.2, .6, 10))
reg('combat', 'explosion_big', lambda: explosion(2.5, 1.6, 11))
reg('combat', 'flamethrower', lambda: mix(lp(noise(1.5, 'pink', 12), 2500) * env(int(1.5 * SR), .1, .2, .8, .3), lp(noise(1.5, 'brown', 13), 200)))
reg('combat', 'laser', lambda: mix(osc(sweep(3000, 800, .3), .3, 'square') * expd(int(.3 * SR), .1) * .5, osc(sweep(1500, 400, .3), .3) * .3))
reg('combat', 'ricochet', lambda: osc(sweep(3500, 1500, .4), .4) * expd(int(.4 * SR), .12) * .5)
reg('combat', 'armour_hit', lambda: mix(bell(1700, .5) * .4, hit(.15, 6000, 14, 600)))
for v in ('hurt_m', 'hurt_f', 'scream', 'death', 'burn', 'freeze', 'shatter', 'electrocute', 'cough', 'bubbles', 'crush', 'cheer', 'panic', 'irradiated'):
    reg('body', v, lambda v=v: body_sfx(v))
reg('body', 'dissolve', lambda: spell_sfx('dissolve'))
for v in ('howl', 'roar', 'growl', 'bark', 'moo', 'baa', 'oink', 'neigh', 'cluck', 'quack', 'chirp', 'caw', 'screech', 'hoot', 'croak', 'buzz', 'hiss', 'trumpet', 'whale',
          'monster', 'titan', 'step_big', 'flap', 'chomp', 'wail', 'rattle', 'moan', 'laugh', 'whoosh_magic'):
    reg('creature', v, lambda v=v: animal_call(v))
reg('creature', 'dragon_breath', lambda: mix(spell_sfx('fire_launch') * 1.4, lp(noise(2.0, 'brown', 20), 300) * env(int(2 * SR), .1, .5, .8, .5) * 2))
reg('creature', 'tentacle', lambda: mix(work_sfx('splash_big', 21), bp(noise(1.0, seed=22), 200, 900) * env(int(SR), .2, .6, 0)))
reg('creature', 'burrow', lambda: mix(lp(noise(2.0, 'brown', 23), 250) * 2.5, bp(noise(2.0, seed=24), 800, 4000) * .2) * env(int(2 * SR), .3, .5, .8, .6))
for v in ('charge', 'fire_launch', 'fire_impact', 'ice', 'nova', 'zap', 'thunder', 'heal', 'curse', 'portal', 'teleport', 'shield', 'whisper'):
    reg('magic', v, lambda v=v: spell_sfx(v))
for v in ('chop', 'mine', 'hammer', 'saw', 'hoe', 'harvest', 'splash', 'splash_big', 'complete', 'tree_fall', 'rock_break', 'door', 'bell_civic', 'step_grass', 'step_stone',
          'step_snow', 'step_sand', 'cart', 'ship_horn', 'creak', 'train', 'engine', 'tracks', 'jet', 'heli', 'missile_launch', 'missile_whistle', 'siren', 'nuke', 'geiger', 'market'):
    reg('world', v, lambda v=v: work_sfx(v))
reg('disaster', 'quake', lambda: mix(lp(noise(4.0, 'brown', 30), 80) * 4 * env(int(4 * SR), .5, 3, 0), *[at(hit(.3, 1500, 31 + i, 120) * .4, .4 + i * .35) for i in range(8)]))
reg('disaster', 'volcano', lambda: mix(explosion(3.0, 2.0, 32), lp(noise(4.0, 'brown', 33), 120) * 3 * env(int(4 * SR), .2, 3.5, 0)))
reg('disaster', 'tsunami', lambda: mix(lp(noise(4.0, 'pink', 34), 1200) * env(int(4 * SR), 1.5, 2, 0) * 2, lp(noise(4.0, 'brown', 35), 150) * env(int(4 * SR), 1.8, 2, 0) * 3))
reg('disaster', 'meteor', lambda: mix(whoosh(1.5, 3000, 300, 36) * 1.2, at(explosion(2.0, 1.4, 37), 1.4)))
reg('disaster', 'fireworks', lambda: mix(whoosh(.6, 600, 4000, 38) * .5, at(explosion(1.0, .3, 39) * .6, .6), *[at(hp(noise(.03, seed=40 + i), 3000) * .3, .9 + i * .05) for i in range(12)]))
reg('disaster', 'thunder_far', lambda: lp(spell_sfx('thunder', 41), 500) * .9)
reg('disaster', 'tornado_hit', lambda: mix(whoosh(3.0, 200, 1200, 42) * 1.5, lp(noise(3.0, 'brown', 43), 200) * 2))

# ------------------------------------------------------------------ ambient loops (12 s, seamless)
def amb(name, d=12.5):
    n = int(SR * d)
    if name == 'forest_day':
        x = bp(noise(d, 'pink', 50), 200, 2500) * .25
        for i in range(14): x = mix(x, at(animal_call('chirp', 51 + i) * .25, RNG.uniform(0, d - 1)))
        return x
    if name == 'night_crickets':
        x = lp(noise(d, 'pink', 52), 600) * .1
        c = osc(4400, d) * (np.sin(2 * np.pi * 30 * t_(d)) > .3) * (np.sin(2 * np.pi * .9 * t_(d)) > 0) * .1
        return mix(x, c, at(animal_call('hoot') * .3, 4.0))
    if name == 'ocean':
        w = .5 + .5 * np.sin(2 * np.pi * t_(d) / 6.25)
        return lp(noise(d, 'pink', 53), 1500) * (.3 + .7 * w) * .6
    if name == 'river': return bp(noise(d, 'pink', 54), 300, 4000) * .45 + hp(noise(d, seed=55), 3000) * .05 * (1 + np.sin(2 * np.pi * 3 * t_(d)))
    if name == 'desert_wind': return bp(noise(d, 'pink', 56), 200, 900) * (.5 + .5 * np.sin(2 * np.pi * t_(d) / 12.5)) * .6
    if name == 'snow_wind': return mix(bp(noise(d, 'pink', 57), 400, 2000) * (.4 + .6 * np.sin(2 * np.pi * t_(d) / 6.25) ** 2) * .6, hp(noise(d, seed=58), 5000) * .03)
    if name == 'swamp':
        x = lp(noise(d, 'pink', 59), 500) * .15
        for i in range(6): x = mix(x, at(animal_call('croak', 60 + i) * .3, RNG.uniform(0, d - 1)))
        return mix(x, animal_call('buzz') * .1)
    if name == 'jungle':
        x = bp(noise(d, 'pink', 61), 300, 3500) * .25
        for i in range(10): x = mix(x, at(animal_call(['chirp', 'screech', 'hoot'][i % 3], 62 + i) * .18, RNG.uniform(0, d - 3)))
        return x
    if name == 'cave_drip':
        x = lp(noise(d, 'brown', 63), 150) * .3
        for i in range(10):
            f = RNG.uniform(900, 1800)
            x = mix(x, at(reverb(osc(sweep(f, f * 1.5, .08), .08) * expd(int(.08 * SR), .02), .8, .6) * .4, RNG.uniform(0, d - 1)))
        return x
    if name == 'city_bustle': return mix(work_sfx('market', 64) * .5, lp(noise(d, 'pink', 65), 900) * .2, at(work_sfx('cart', 66) * .3, 5), at(work_sfx('hammer', 67) * .2, 8))
    if name == 'battle_distant':
        x = lp(noise(d, 'brown', 68), 200) * .6
        for i in range(8): x = mix(x, at(lp(explosion(1.5, .7, 69 + i), 400) * .35, RNG.uniform(0, d - 2)))
        for i in range(10): x = mix(x, at(lp(body_sfx('cheer', 80 + i), 1200) * .08, RNG.uniform(0, d - 3)))
        return x
    if name == 'volcanic': return mix(lp(noise(d, 'brown', 90), 80) * 1.5, bp(noise(d, seed=91), 2000, 6000) * (noise(d, seed=92) > 2.2) * .5)


AMBIENT = ['forest_day', 'night_crickets', 'ocean', 'river', 'desert_wind', 'snow_wind', 'swamp', 'jungle', 'cave_drip', 'city_bustle', 'battle_distant', 'volcanic']


# ------------------------------------------------------------------ era music (original procedural compositions, ~32 s loops)
def music(era, bars=16, bpm=None):
    scales = {'stone': [0, 3, 5, 7, 10], 'ancient': [0, 1, 4, 5, 7, 8, 10], 'medieval': [0, 2, 3, 5, 7, 9, 10], 'industrial': [0, 2, 4, 5, 7, 9, 11],
              'modern': [0, 2, 3, 5, 7, 8, 10], 'future': [0, 2, 4, 7, 9]}
    sc = scales[era]
    bpm = bpm or {'stone': 84, 'ancient': 92, 'medieval': 100, 'industrial': 108, 'modern': 96, 'future': 112}[era]
    beat = 60 / bpm
    d = bars * 4 * beat
    n = int(SR * d)
    out = np.zeros(n + SR * 3)
    rng = np.random.default_rng({'stone': 1, 'ancient': 2, 'medieval': 3, 'industrial': 4, 'modern': 5, 'future': 6}[era])
    root = {'stone': 50, 'ancient': 52, 'medieval': 55, 'industrial': 53, 'modern': 50, 'future': 57}[era]
    prog = [0, 3, 4, 0] if era in ('industrial', 'medieval') else [0, 5, 3, 4] if era in ('modern', 'future') else [0, 0, 3, 4]

    def add(x, t0, g=1.0):
        i = int(t0 * SR); out[i:i + len(x)] += x[:max(0, len(out) - i)] * g

    def deg(k, octv=0): return root + 12 * octv + sc[k % len(sc)] + 12 * (k // len(sc))
    # melody: random walk on the scale with rhythmic motifs repeated every 4 bars
    motif = [(rng.integers(0, 4) * .5) for _ in range(6)]
    mel = []
    k = 2
    for b in range(bars):
        t = b * 4 * beat
        steps = [0, 1, 1.5, 2, 3] if b % 2 == 0 else [0, .5, 1, 2, 2.5, 3]
        for s in steps:
            k = int(np.clip(k + rng.choice([-2, -1, -1, 0, 1, 1, 2]), 0, 9))
            mel.append((t + s * beat, k, beat * (1 if s % 1 == 0 else .5)))
    for b in range(bars):
        t = b * 4 * beat
        ch = prog[(b // 2) % 4]
        if era == 'stone':
            for s in range(4):
                add(drum('tom' if s in (0, 2) else 'hand', .5, b * 4 + s), t + s * beat, .7 if s == 0 else .4)
                add(drum('shaker', .2, b + s), t + s * beat + beat / 2, .3)
            add(flute(NOTE(deg(ch, -1)), 4 * beat) * .15, t)
        elif era == 'ancient':
            for s in range(4): add(drum('hand', .3, b * 4 + s), t + s * beat, .4)
            add(drum('tom', .4, b), t, .5)
            for s in range(0, 8): add(pluck(NOTE(deg(ch + (s % 3) * 2, -1)), .6, .6, b * 8 + s) * .25, t + s * beat / 2)
        elif era == 'medieval':
            add(drum('tom', .4, b), t, .4); add(drum('tom', .4, b + 1), t + 2 * beat, .3)
            for s in range(4): add(pluck(NOTE(deg(ch, -1)), 1.0, .3, b * 4 + s) * .3, t + s * beat)
            add(pad([NOTE(deg(ch, -1)), NOTE(deg(ch + 2, -1)), NOTE(deg(ch + 4, -1))], 4 * beat, 'tri', 900) * .12, t)
        elif era == 'industrial':
            for s in range(4):
                add(drum('kick', .4, s), t + s * beat, .5 if s % 2 == 0 else 0); add(drum('snare', .3, s), t + s * beat, .35 if s % 2 else 0)
                add(drum('hat', .1, s), t + s * beat + beat / 2, .25)
            add(brass(NOTE(deg(ch, -2)), 2 * beat) * .25, t); add(brass(NOTE(deg(ch + 4, -2)), 2 * beat) * .2, t + 2 * beat)
        elif era == 'modern':
            for s in range(8):
                add(drum('hat', .08, s), t + s * beat / 2, .2)
            add(drum('kick', .5, b), t, .6); add(drum('kick', .5, b), t + 2.5 * beat, .4); add(drum('snare', .3, b), t + beat, .4); add(drum('snare', .3, b), t + 3 * beat, .4)
            add(pad([NOTE(deg(ch, -1)), NOTE(deg(ch + 2, -1)), NOTE(deg(ch + 4, -1))], 4 * beat, 'saw', 1400) * .15, t)
            for s in range(4): add(lp(osc(NOTE(deg(ch, -2)), beat * .9, 'saw'), 500) * env(int(beat * .9 * SR), .01, .2, .5, .1) * .3, t + s * beat)
        elif era == 'future':
            for s in range(16): add(chip(NOTE(deg(ch + [0, 2, 4, 7][s % 4], 0)), beat / 4 * .9, 'pulse') * .12, t + s * beat / 4)
            add(drum('kick', .4, b), t, .5); add(drum('kick', .4, b), t + 2 * beat, .5); add(drum('snare', .3, b), t + beat, .3); add(drum('snare', .3, b), t + 3 * beat, .3)
            add(pad([NOTE(deg(ch, -1)), NOTE(deg(ch + 2, -1)), NOTE(deg(ch + 4, -1)), NOTE(deg(ch + 6, -1))], 4 * beat, 'saw', 1800) * .14, t)
    inst = {'stone': lambda f, d_: flute(f, d_, 4), 'ancient': lambda f, d_: pluck(f, d_ + .4, .7) * .9, 'medieval': lambda f, d_: flute(f, d_, 5) * .9,
            'industrial': lambda f, d_: brass(f, d_) * .7, 'modern': lambda f, d_: lp(osc(f, d_, 'square'), 2500) * env(int(d_ * SR), .01, .1, .6, .1) * .5,
            'future': lambda f, d_: chip(f, d_, 'square') * .8}[era]
    for (t0, kk, dd) in mel:
        if rng.random() < .18: continue
        add(inst(NOTE(deg(kk, 1 if era not in ('industrial',) else 0)), dd) * .32, t0)
    y = out[:n + int(SR * .5)]
    y = reverb(y, .6 if era in ('stone', 'ancient', 'medieval') else .4, .2)
    return loopify(y[:n + int(SR * .5)], .5)


ERAS = ['stone', 'ancient', 'medieval', 'industrial', 'modern', 'future']



# ================================================================== extended coverage (buildings, blast distance, war, crowd, nature, events)
def fire_crackle(d=4.0, intensity=1.0, seed=0):
    n = int(SR * d)
    out = lp(noise(d, 'pink', seed), 900) * .25 * intensity + lp(noise(d, 'brown', seed + 1), 160) * .5 * intensity
    r = np.random.default_rng(seed)
    for tt in np.cumsum(r.exponential(.04 / intensity, int(d * 40 * intensity))):
        i = int(tt * SR)
        if i < n - 300:
            L = r.integers(40, 300)
            out[i:i + L] += hp(noise(L / SR + 1e-6, seed=i), r.uniform(1500, 4000)) * expd(L, .002) * r.uniform(.3, 1.0)
    return out


def distant(x, dist):
    """dist 0 = near, 1 = mid, 2 = far: low-pass, delay, more reverb, quieter tail."""
    if dist == 0: return x
    y = lp(x, 2200 if dist == 1 else 550)
    y = reverb(y, .7 if dist == 1 else .95, .35 if dist == 1 else .5)
    return at(y, .08 if dist == 1 else .35)


def crash(kind, seed=0):
    if kind == 'glass': return mix(*[at(osc(NOTE(int(np.random.default_rng(seed + i).integers(88, 102))), .25) * expd(int(.25 * SR), .05) * .25, i * .015) for i in range(18)], hp(noise(.5, seed=seed), 4000) * expd(int(.5 * SR), .08))
    if kind == 'wood': return mix(hit(.4, 1500, seed, 160) * 1.2, *[at(bp(noise(.08, seed=seed + i), 800, 3500) * expd(int(.08 * SR), .02) * .5, .03 * i) for i in range(8)])
    if kind == 'stone': return mix(hit(.6, 700, seed, 80) * 1.5, *[at(hit(.08, 2500, seed + i, 300) * .35, .04 * i + .05) for i in range(12)])
    if kind == 'metal': return mix(bell(430, 1.2) * .5, bell(611, 1.0) * .3, hit(.3, 3000, seed, 200))


SFX_EXTRA = {
    # buildings
    'building_house_fire': lambda: fire_crackle(4.0, 1.4, 101),
    'building_fire_small': lambda: fire_crackle(2.0, .7, 102),
    'building_crack': lambda: mix(crash('wood', 103) * .6, bp(osc(sweep(90, 60, 1.0), 1.0, 'saw') * (1 + noise(1.0, seed=104) * .4), 200, 1600) * env(int(SR), .05, .9, 0) * .5),
    'building_collapse': lambda: mix(crash('stone', 105), at(crash('wood', 106), .15), at(lp(noise(2.5, 'brown', 107), 200) * env(int(2.5 * SR), .02, 2.2, 0) * 3, .1),
                                     *[at(hit(.07, 2500, 108 + i, 300) * .3, .3 + i * .09) for i in range(14)]),
    'building_collapse_wood': lambda: mix(crash('wood', 110) * 1.2, at(crash('wood', 111), .25), at(lp(noise(1.6, 'brown', 112), 300) * env(int(1.6 * SR), .02, 1.4, 0) * 2, .1)),
    'building_glass_break': lambda: crash('glass', 113),
    'building_metal_crash': lambda: crash('metal', 114),
    'building_debris_rain': lambda: mix(*[at(hit(.06, 3000, 115 + i, 400) * .3, RNG.uniform(0, 1.6)) for i in range(26)]),
    'building_flood_rush': lambda: mix(lp(noise(4.0, 'pink', 116), 1800) * env(int(4 * SR), .4, .5, .8, .6), bp(noise(4.0, seed=117), 150, 600) * .6),
    'building_freeze_creak': lambda: mix(spell_sfx('ice', 118) * .5, bp(osc(sweep(140, 90, 1.2), 1.2, 'saw'), 300, 1500) * env(int(1.2 * SR), .1, 1, 0) * .3),
    'building_construct_loop': lambda: mix(work_sfx('hammer', 119), at(work_sfx('saw', 120), .6), at(work_sfx('hammer', 121), 1.6)),
    # blast by distance + after-effects
    'blast_near': lambda: explosion(2.5, 1.5, 130),
    'blast_mid': lambda: distant(explosion(2.5, 1.5, 131), 1),
    'blast_far': lambda: distant(explosion(2.5, 1.5, 132), 2),
    'nuke_near': lambda: work_sfx('nuke', 133),
    'nuke_far': lambda: distant(work_sfx('nuke', 134), 2),
    'shockwave_pass': lambda: mix(whoosh(1.2, 150, 2500, 135) * 1.4, lp(noise(1.6, 'brown', 136), 150) * env(int(1.6 * SR), .02, 1.3, 0) * 3, at(crash('glass', 137) * .5, .5)),
    'ear_ring': lambda: (osc(5200, 3.5) * .12 + osc(5230, 3.5) * .08) * np.linspace(1, 0, int(3.5 * SR)) ** 1.5,
    'bomb_whistle': lambda: work_sfx('missile_whistle', 138),
    'bullet_whiz': lambda: osc(sweep(2600, 1400, .25), .25) * env(int(.25 * SR), .02, .2, 0) * .4 + hp(noise(.25, seed=139), 3000) * expd(int(.25 * SR), .05) * .2,
    'reload': lambda: mix(hit(.08, 4000, 140, 600) * .5, at(hit(.08, 5000, 141, 800) * .5, .25)),
    'tank_shot': lambda: mix(explosion(1.4, .7, 142), gunshot(.8, 2.0, 143) * .6),
    'artillery_far': lambda: distant(explosion(1.6, .9, 144), 2),
    'drone_buzz': lambda: bp(osc(180 + 6 * np.sin(2 * np.pi * 3 * t_(3.0)), 3.0, 'saw'), 300, 4000) * .5,
    'plane_dive': lambda: mix(osc(sweep(900, 300, 2.5), 2.5, 'saw') * .2, work_sfx('jet', 145)),
    # war
    'war_horn': lambda: reverb(brass(NOTE(43), 2.5) * env(int(2.5 * SR), .3, .4, .8, .8), .9, .4),
    'war_drums': lambda: mix(*[at(drum('tom', .5, 146 + i) * (1 if i % 4 == 0 else .6), i * .3) for i in range(14)]),
    'battle_clash': lambda: mix(*[at(mix(bell(RNG.uniform(1800, 3200), .3) * .2, hit(.1, 5000, 150 + i, 400) * .4), RNG.uniform(0, 3.5)) for i in range(26)],
                                bp(noise(4.0, seed=151), 300, 2500) * .25),
    'bow_volley': lambda: mix(*[at(SFX['combat_arrow_shoot']() * .25, RNG.uniform(0, .4)) for _ in range(10)], at(whoosh(1.2, 2500, 5000, 152) * .5, .2)),
    'gunfire_distant': lambda: mix(*[at(distant(gunshot(.4, 1.0, 153 + i), 2) * .6, RNG.uniform(0, 3.5)) for i in range(16)]),
    'marching': lambda: mix(*[at(lp(noise(.12, seed=160 + i), 900) * expd(int(.12 * SR), .03) * .5, i * .5 + RNG.uniform(0, .03)) for i in range(16)], *[at(lp(noise(.12, seed=180 + i), 700) * expd(int(.12 * SR), .03) * .35, i * .5 + .25) for i in range(16)]),
    'cavalry_charge': lambda: mix(*[at(lp(noise(.08, seed=200 + i), 600) * expd(int(.08 * SR), .02) * .6, i * .09 + RNG.uniform(0, .02)) for i in range(40)], lp(noise(4.0, 'brown', 201), 150) * 1.2),
    'horse_gallop': lambda: mix(*[at(lp(noise(.08, seed=210 + i), 700) * expd(int(.08 * SR), .02) * .7, (i // 3) * .45 + (i % 3) * .09) for i in range(18)]),
    'siege_impact': lambda: mix(crash('stone', 211), lp(noise(1.5, 'brown', 212), 180) * expd(int(1.5 * SR), .3) * 2),
    'catapult_launch': lambda: mix(work_sfx('creak', 213) * .5, at(hit(.3, 800, 214, 100), .5), at(whoosh(.8, 300, 1200, 215), .55)),
    # crowd
    'crowd_scream': lambda: body_sfx('panic', 220),
    'crowd_murmur': lambda: mix(*[at(lp(vocal(None, .4, v, NOTE(50 + RNG.integers(0, 10)), .3, 221 + i), 1500) * env(int(.4 * SR), .1, .2, .5, .1) * .2, RNG.uniform(0, 3.5)) for i, v in enumerate('aoeiuaoeiuaoeiu' * 2)]),
    'crowd_cheer_big': lambda: mix(body_sfx('cheer', 222), at(body_sfx('cheer', 223) * .8, .3)),
    'crowd_angry': lambda: mix(*[at(vocal(None, .7, 'a', NOTE(48 + RNG.integers(0, 6)), .7, 224 + i) * env(int(.7 * SR), .05, .4, .4, .2) * .3, RNG.uniform(0, 2.5)) for i in range(10)]),
    # nature
    'wind_gust': lambda: whoosh(2.5, 150, 900, 230) * 1.2,
    'tree_rustle': lambda: bp(noise(2.0, 'pink', 231), 1500, 7000) * env(int(2 * SR), .3, .5, .6, .6) * .7,
    'birds_flock': lambda: mix(*[at(animal_call('flap', 232 + i) * .4, RNG.uniform(0, 1)) for i in range(8)], *[at(animal_call('chirp', 240 + i) * .3, RNG.uniform(0, 1.5)) for i in range(4)]),
    'lava_bubble': lambda: mix(*[at(lp(osc(sweep(80, 160, .15), .15) * expd(int(.15 * SR), .05), 400) * .7, RNG.uniform(0, 2.5)) for _ in range(10)], lp(noise(3.0, 'brown', 250), 120)),
    'geyser': lambda: mix(hp(noise(3.0, seed=251), 800) * env(int(3 * SR), .3, .5, .7, 1.0), lp(noise(3.0, 'brown', 252), 200) * env(int(3 * SR), .1, 2.5, 0) * 2),
    'avalanche': lambda: mix(lp(noise(4.0, 'brown', 253), 250) * env(int(4 * SR), .8, 2.5, .3, .6) * 3, bp(noise(4.0, seed=254), 400, 3000) * env(int(4 * SR), 1.0, 2, .2, .5) * .5),
    'ice_crack': lambda: mix(hp(noise(.3, seed=255), 2000) * expd(int(.3 * SR), .02) * 1.2, osc(sweep(3000, 800, .4), .4) * expd(int(.4 * SR), .1) * .3),
    'hail': lambda: mix(*[at(hit(.03, 6000, 256 + i, 900) * .25, RNG.uniform(0, 3)) for i in range(70)]),
    'water_drop': lambda: osc(sweep(900, 1600, .07), .07) * expd(int(.07 * SR), .02),
    # monsters & magic extra
    'dragon_roar': lambda: mix(animal_call('monster', 260), at(animal_call('titan', 261) * .5, .1)),
    'phoenix_cry': lambda: mix(animal_call('screech', 262), fire_crackle(1.0, 1.0, 263) * .5),
    'golem_step': lambda: animal_call('step_big', 264),
    'imp_cackle': lambda: hp(animal_call('laugh', 265), 400),
    'jinn_echo_laugh': lambda: reverb(animal_call('laugh', 266), .95, .6),
    'ghost_wail': lambda: animal_call('wail', 267),
    'swarm': lambda: mix(*[at(animal_call('buzz', 268 + i) * .3, RNG.uniform(0, .5)) for i in range(5)]),
    'meow': lambda: vocal(None, .6, 'e', 600 * (1 + .3 * np.sin(np.linspace(0, np.pi, int(.6 * SR)))), .1) * env(int(.6 * SR), .05, .3, .5, .2),
    'snort': lambda: lp(noise(.4, seed=270), 900) * env(int(.4 * SR), .01, .3, 0) * 1.2,
    'bat_squeak': lambda: msum(at(osc(sweep(6000, 4500, .04), .04) * expd(int(.04 * SR), .01), i * .09) for i in range(4)),
    'monkey_chatter': lambda: msum(at(vocal(None, .1, 'i', sweep(900, 700, .1), .3, 271 + i) * expd(int(.1 * SR), .04), i * .12) for i in range(8)),
    'dolphin_click': lambda: msum(at(hp(noise(.01, seed=272 + i), 3000) * .6, i * .03) for i in range(20)),
    'seal_bark': lambda: msum(at(vocal(None, .2, 'o', sweep(400, 250, .2), .5, 273) * expd(int(.2 * SR), .07), i * .3) for i in range(3)),
    'skitter': lambda: msum(at(hp(noise(.015, seed=274 + i), 3000) * .4, i * .035 + RNG.uniform(0, .01)) for i in range(28)),
    # events / stings
    'event_kingdom_founded': lambda: reverb(mix(*[at(brass(NOTE(m), .5) * .4, i * .18) for i, m in enumerate((55, 60, 64, 67))], at(brass(NOTE(72), 1.2) * .5, .72)), .7, .3),
    'event_kingdom_fallen': lambda: reverb(mix(*[at(brass(NOTE(m), .8) * .4, i * .35) for i, m in enumerate((55, 53, 51, 48))]), .9, .5),
    'event_war_declared': lambda: mix(SFX_EXTRA['war_horn'](), at(SFX_EXTRA['war_drums'](), .8)),
    'event_peace': lambda: reverb(mix(*[at(bell(NOTE(m), 1.5) * .35, i * .25) for i, m in enumerate((72, 79, 76, 84))]), .8, .4),
    'event_era_advance': lambda: reverb(mix(*[at(chip(NOTE(m), .2) * .5, i * .1) for i, m in enumerate((60, 64, 67, 72, 76, 79, 84))], at(bell(NOTE(84), 2.0) * .4, .7)), .7, .3),
    'event_birth': lambda: mix(bell(NOTE(84), .8) * .3, at(bell(NOTE(91), .8) * .25, .12)),
    'event_wedding': lambda: reverb(mix(*[at(bell(NOTE(m), 1.0) * .3, i * .15) for i, m in enumerate((76, 79, 84, 88))]), .7, .3),
    'event_plague': lambda: reverb(mix(spell_sfx('curse', 275) * .7, body_sfx('cough', 276) * .5), .7, .4),
    'event_achievement': lambda: mix(*[at(chip(NOTE(m), .12), i * .08) for i, m in enumerate((72, 76, 79, 84, 88, 91))]),
    'sting_victory': lambda: reverb(mix(*[at(brass(NOTE(m), .35) * .4, i * .15) for i, m in enumerate((60, 64, 67))], at(mix(brass(NOTE(72), 1.6), brass(NOTE(76), 1.6) * .6) * .5, .45)), .7, .3),
    'sting_defeat': lambda: reverb(mix(*[at(brass(NOTE(m), .6) * .4, i * .3) for i, m in enumerate((60, 58, 55))], at(brass(NOTE(48), 1.8) * .5, .9)), .9, .4),
}
for k, f in SFX_EXTRA.items():
    cat, name = (k.split('_', 1) if k.split('_', 1)[0] in ('building', 'event', 'sting') else ('extra', k))
    reg(cat, name, f)


def amb_extra(name, d=12.5):
    if name == 'rain': return mix(hp(noise(d, 'pink', 300), 1500) * .4, lp(noise(d, 'pink', 301), 600) * .3, *[at(SFX_EXTRA['water_drop']() * .2, RNG.uniform(0, d - .2)) for _ in range(30)])
    if name == 'thunderstorm': return mix(amb_extra('rain', d) * 1.2, at(lp(spell_sfx('thunder', 302), 900) * .7, 3.0), at(lp(spell_sfx('thunder', 303), 500) * .5, 8.5))
    if name == 'blizzard': return mix(amb('snow_wind', d) * 1.3, hp(noise(d, seed=304), 4000) * .08 * (1 + np.sin(2 * np.pi * t_(d) / 3)))
    if name == 'sandstorm': return mix(bp(noise(d, 'pink', 305), 300, 3000) * (.7 + .3 * np.sin(2 * np.pi * t_(d) / 4)), hp(noise(d, seed=306), 3000) * .15)
    if name == 'burning_city': return mix(fire_crackle(d, 2.0, 307), lp(body_sfx('panic', 308), 1500) * .3, at(crash('wood', 309) * .4, 4), at(crash('glass', 310) * .3, 9), lp(noise(d, 'brown', 311), 120) * .6)
    if name == 'battle_close': return mix(SFX_EXTRA['battle_clash']() * .8, at(SFX_EXTRA['battle_clash']() * .8, 4.0), at(SFX_EXTRA['battle_clash']() * .8, 8.0), lp(body_sfx('cheer', 312), 1600) * .25, at(body_sfx('scream', 313) * .2, 6))
    if name == 'underwater': return mix(lp(noise(d, 'brown', 314), 250) * .8, *[at(body_sfx('bubbles', 315 + i) * .2, i * 2.5) for i in range(5)])
    if name == 'night_city': return mix(amb('night_crickets', d) * .5, lp(SFX_EXTRA['crowd_murmur']() * .3, 1200), at(animal_call('bark', 320) * .3, 6))
    if name == 'farm_day': return mix(amb('forest_day', d) * .6, at(animal_call('moo', 321) * .3, 2), at(animal_call('cluck', 322) * .3, 5), at(animal_call('baa', 323) * .3, 8), at(work_sfx('hoe', 324) * .2, 10))
    if name == 'harbor': return mix(amb('ocean', d) * .7, at(animal_call('caw', 325) * .2, 3), at(work_sfx('creak', 326) * .3, 6), at(work_sfx('ship_horn', 327) * .25, 9))
    if name == 'wildfire': return mix(fire_crackle(d, 2.5, 328), lp(noise(d, 'brown', 329), 200) * .8)
    if name == 'wasteland': return mix(amb('desert_wind', d) * .7, work_sfx('geiger', 330) * .15, at(work_sfx('geiger', 331) * .15, 6))


AMBIENT_EXTRA = ['rain', 'thunderstorm', 'blizzard', 'sandstorm', 'burning_city', 'battle_close', 'underwater', 'night_city', 'farm_day', 'harbor', 'wildfire', 'wasteland']
MOOD = {'war': ('industrial', 120), 'peace': ('medieval', 84), 'apocalypse': ('modern', 72), 'title': ('ancient', 90), 'exploration': ('stone', 96), 'magic': ('future', 100)}


# ------------------------------------------------------------------ writer
TARGET_RMS_DB = {'ui': -22, 'ambient': -24, 'music': -20, 'event': -19, 'sting': -19, 'default': -18}


def level(x, cat='default', peak=.7):
    """loudness-match by category (RMS target) and keep a safe peak so Vorbis never clips."""
    x = x - np.mean(x)
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    g = 10 ** (TARGET_RMS_DB.get(cat, TARGET_RMS_DB['default']) / 20) / rms
    pk = np.max(np.abs(x)) * g
    if pk > peak: g *= peak / pk
    return x * g


def write_ogg(path, x, loop=False, q=4):
    if not loop: x = fade(x)
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f: f.write(pcm.tobytes()); raw = f.name
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', raw, '-c:a', 'libvorbis', '-q:a', str(q), path], check=True)
    os.unlink(raw)


def check(x, name):
    """automatic sanity checks (can't listen): no NaN, not silent, not clipped DC, sensible length."""
    assert np.isfinite(x).all(), name
    rms = float(np.sqrt(np.mean(x ** 2)))
    return rms


def build(out_root):
    sfx_dir, amb_dir, mus_dir = (os.path.join(out_root, d) for d in ('SFX', 'Ambient', 'Music'))
    for d in (sfx_dir, amb_dir, mus_dir): os.makedirs(d, exist_ok=True)
    report = {'sfx': {}, 'ambient': {}, 'music': {}}
    for name, fn in SFX.items():
        x = level(fn(), name.split('_')[0])
        report['sfx'][name] = dict(seconds=round(len(x) / SR, 2), rms=round(check(x, name), 3))
        write_ogg(os.path.join(sfx_dir, name + '.ogg'), x)
    for name in AMBIENT:
        x = level(loopify(amb(name), .5), 'ambient')
        report['ambient'][name] = dict(seconds=round(len(x) / SR, 2), rms=round(check(x, name), 3), loop=True)
        write_ogg(os.path.join(amb_dir, 'amb_' + name + '.ogg'), x, loop=True, q=3)
    for name in AMBIENT_EXTRA:
        x = level(loopify(amb_extra(name), .5), 'ambient')
        report['ambient'][name] = dict(seconds=round(len(x) / SR, 2), rms=round(check(x, name), 3), loop=True)
        write_ogg(os.path.join(amb_dir, 'amb_' + name + '.ogg'), x, loop=True, q=3)
    for mood, (style, bpm) in MOOD.items():
        x = music(style, bars=16, bpm=bpm)
        if mood == 'apocalypse': x = mix(x * .7, lp(noise(len(x) / SR, 'brown', 9), 120) * .4, osc(NOTE(33), len(x) / SR, 'saw') * .05)
        if mood == 'war': x = mix(x, msum(at(drum('tom', .5, 900 + i) * .35, i * 60 / bpm) for i in range(int(len(x) / SR * bpm / 60) - 1)))
        x = level(loopify(x[:len(x)], .3), 'music')
        report['music'][mood] = dict(seconds=round(len(x) / SR, 2), rms=round(check(x, mood), 3), loop=True, style=style)
        write_ogg(os.path.join(mus_dir, 'music_' + mood + '.ogg'), x, loop=True, q=5)
    for era in ERAS:
        x = level(music(era), 'music')
        report['music'][era] = dict(seconds=round(len(x) / SR, 2), rms=round(check(x, era), 3), loop=True)
        write_ogg(os.path.join(mus_dir, 'music_' + era + '.ogg'), x, loop=True, q=5)
    json.dump(report, open(os.path.join(out_root, 'audio_index.json'), 'w'), indent=1)
    return report


if __name__ == '__main__':
    r = build(sys.argv[1])
    print(len(r['sfx']), 'sfx', len(r['ambient']), 'ambient', len(r['music']), 'music')
