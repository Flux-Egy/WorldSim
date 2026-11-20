"""Audio v3.2: rebuilt versions of the 26 clips the owner rejected in the phone audition.
Better models than v3.1: glottal-pulse voices with jitter/shimmer and moving formants (animals, crowds, cough),
modal synthesis for materials (wood, stone, metal, ice/glass), granular debris, layered events (crack -> fall -> debris -> dust)."""
import numpy as np
from scipy import signal
import audio as A
from audio import SR, lp, hp, bp, mix, at, expd, env, noise, reverb, osc, sweep, msum

R = np.random.default_rng(2026)


# ------------------------------------------------------------------ voices
def glottal(f0, d, jitter=.01, shimmer=.08, oq=.6, seed=0):
    """Rosenberg-style glottal pulse train with jitter/shimmer; f0 scalar or array."""
    r = np.random.default_rng(seed)
    n = int(SR * d); out = np.zeros(n)
    f = np.full(n, float(f0)) if np.isscalar(f0) else np.interp(np.arange(n), np.linspace(0, n - 1, len(f0)), f0)
    t = 0
    while t < n - 2:
        T = SR / max(f[t], 30) * (1 + r.normal(0, jitter))
        L = int(T); op = max(2, int(L * oq))
        amp = 1 + r.normal(0, shimmer)
        k = np.arange(op)
        pulse = .5 * (1 - np.cos(np.pi * k / op)) * (k < op * .8) + np.where(k >= op * .8, np.cos(np.pi / 2 * (k - op * .8) / (op * .2 + 1e-9)), 0)
        e = min(op, n - t); out[t:t + e] += amp * pulse[:e]
        t += max(L, 1)
    return np.diff(out, prepend=0) * 8


def formant_track(x, tracks, bws, gains):
    """time-varying formants: tracks = list of arrays (Hz) per formant, filtered in blocks."""
    n = len(x); out = np.zeros(n); B = 256
    for fi, tr in enumerate(tracks):
        tr = np.interp(np.arange(n), np.linspace(0, n - 1, len(tr)), tr)
        zi = None
        y = np.zeros(n)
        for i in range(0, n, B):
            fc = tr[i]; bw = bws[fi]
            b, a = signal.butter(2, [max(20, fc - bw) / (SR / 2), min(fc + bw, SR / 2 - 200) / (SR / 2)], 'band')
            if zi is None or len(zi) != max(len(a), len(b)) - 1: zi = signal.lfilter_zi(b, a) * 0
            y[i:i + B], zi = signal.lfilter(b, a, x[i:i + B], zi=zi)
        out += y * gains[fi]
    return out


def voice(f0, d, vowels, rough=0., breath=.05, seed=0, bw=(90, 120, 160)):
    """vowels: list of (F1,F2,F3) the voice glides through."""
    src = glottal(f0, d, seed=seed)
    if rough: src *= 1 + rough * np.sin(2 * np.pi * (35 + 10 * R.random()) * A.t_(d))[:len(src)]
    src = src + noise(d, seed=seed + 1)[:len(src)] * breath
    tr = [np.array([v[i] for v in vowels], float) for i in range(3)]
    return formant_track(src, tr, bw, (1, .55, .3))


def envl(n, a, r):
    e = np.ones(n); A_ = max(1, int(a * SR)); R_ = max(1, int(r * SR))
    e[:A_] = np.linspace(0, 1, A_); e[-R_:] *= np.linspace(1, 0, R_)
    return e


# ------------------------------------------------------------------ materials (modal synthesis)
MODES = {'wood': ([1, 2.3, 3.9, 5.2], (.06, .04, .02, .015)), 'stone': ([1, 1.7, 2.6, 3.9, 5.4], (.08, .05, .03, .02, .015)),
         'metal': ([1, 2.76, 5.40, 8.93, 13.3, 1.49], (.9, .6, .4, .25, .15, .7)), 'glass': ([1, 2.32, 4.25, 6.63, 9.38], (.35, .25, .15, .1, .07)),
         'ice': ([1, 2.1, 3.7, 5.9], (.18, .12, .08, .05))}


def strike(mat, f, d=None, bright=1., seed=0):
    ratios, taus = MODES[mat]
    d = d or (max(taus) * 4 + .05)
    n = int(SR * d); r = np.random.default_rng(seed)
    y = np.zeros(n)
    for k, (q, tau) in enumerate(zip(ratios, taus)):
        y += np.sin(2 * np.pi * f * q * (1 + r.normal(0, .01)) * A.t_(d)[:n] + r.random() * 6) * np.exp(-np.arange(n) / (SR * tau)) / (k + 1) ** (1.2 / bright)
    click = hp(noise(.006, seed=seed), 1500 if mat != 'stone' else 600) * np.linspace(1, 0, int(.006 * SR))
    y[:len(click)] += click * (1.5 if mat in ('wood', 'stone') else .8)
    return y


def grains(mat, d, density, f_lo, f_hi, decay_density=True, gain=.3, seed=0):
    """granular debris: many small strikes, density falls off over time."""
    r = np.random.default_rng(seed); out = np.zeros(int(SR * (d + .5)))
    t = 0.
    while t < d:
        rate = density * (np.exp(-t / (d * .45)) if decay_density else 1)
        t += r.exponential(1 / max(rate, .5))
        if t >= d: break
        s = strike(mat, r.uniform(f_lo, f_hi), seed=int(t * 1e4)) * gain * r.uniform(.3, 1) * (np.exp(-t / d) if decay_density else 1)
        i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]
    return out


def rumble(d, f=80, a=.3, r=1.0, seed=0, gain=2.):
    n = int(SR * d)
    return lp(noise(d, 'brown', seed), f) * envl(n, a, r) * gain


def dust(d, seed=0, gain=.25):
    n = int(SR * d)
    return bp(noise(d, 'pink', seed), 1200, 6000) * np.exp(-np.arange(n) / (SR * d * .4)) * gain


def claps(d, n_people, seed=0):
    r = np.random.default_rng(seed); out = np.zeros(int(SR * (d + .2)))
    for p in range(n_people):
        rate = r.uniform(4, 7); t = r.uniform(0, .3)
        while t < d:
            c = bp(noise(.02, seed=int(t * 1e5) + p), r.uniform(900, 1500), r.uniform(2500, 4500)) * np.exp(-np.arange(int(.02 * SR)) / (SR * .004))
            i = int(t * SR); out[i:i + len(c)] += c * r.uniform(.4, 1)
            t += 1 / rate * r.uniform(.85, 1.15)
    return out


VOW = {'a': (750, 1200, 2600), 'e': (450, 1900, 2600), 'i': (300, 2300, 3000), 'o': (500, 850, 2500), 'u': (330, 750, 2400),
       'ae': (650, 1700, 2500), 'y': (300, 1600, 2300)}


def crowd(d, n, f_lo, f_hi, words, rough=.1, seed=0, rise=0.0):
    r = np.random.default_rng(seed); out = np.zeros(int(SR * (d + 1)))
    for p in range(n):
        t0 = r.uniform(0, d * .7); dur = r.uniform(.35, .9)
        f0 = r.uniform(f_lo, f_hi)
        fv = np.linspace(f0, f0 * (1 + rise + r.normal(0, .05)), 20)
        w = words[r.integers(0, len(words))]
        v = voice(fv, dur, [VOW[c] for c in w], rough=rough, breath=.08, seed=seed * 100 + p) * envl(int(SR * dur), .05, .2) * r.uniform(.4, 1)
        i = int(t0 * SR); out[i:i + len(v)] += v[:len(out) - i]
    return out


# ------------------------------------------------------------------ the 26 replacements
def nrm(x): return x / (np.max(np.abs(x)) + 1e-9)


NEW = {}
def new(name):
    def deco(fn): NEW[name] = fn; return fn
    return deco


@new('body_cough')
def _():
    parts = []
    for k, t in enumerate((0, .42, .78)):
        d = .28
        burst = noise(d, seed=k) * envl(int(SR * d), .005, .2) * np.exp(-np.arange(int(SR * d)) / (SR * .09))
        tract = formant_track(burst + glottal(140, d, seed=k) * .25 * np.exp(-np.arange(int(SR * d)) / (SR * .04)), [np.array([700, 600]), np.array([1300, 1100]), np.array([2500, 2400])], (200, 250, 300), (1, .6, .3))
        parts.append(at(tract, t))
    return reverb(mix(*parts), .3, .15)


@new('body_freeze')
def _():
    d = 1.6
    crackles = grains('ice', d, 40, 2500, 6000, decay_density=False, gain=.18, seed=3)
    shimmer = msum(at(np.sin(2 * np.pi * f * A.t_(.9)) * envl(int(.9 * SR), .3, .5) * .05, i * .12) for i, f in enumerate((2600, 3100, 3700, 4200, 5100)))
    return mix(crackles * np.linspace(.3, 1, len(crackles)), shimmer, hp(noise(d, seed=4), 5000) * envl(int(SR * d), .6, .6) * .06)


@new('body_shatter')
def _():
    big = strike('glass', 1800, 1.2, 1.3, 5) * .8
    shards = grains('glass', .9, 70, 2500, 7000, gain=.25, seed=6)
    tinkle = at(grains('glass', 1.2, 14, 3000, 6000, gain=.18, seed=7), .4)
    return mix(big, hp(noise(.2, seed=8), 3000) * np.exp(-np.arange(int(.2 * SR)) / (SR * .03)) * 1.2, shards, tinkle)


@new('building_crack')
def _():
    snaps = msum(at(strike('wood', np.random.default_rng(i).uniform(250, 600), .25, 1.5, i) * (.5 + .1 * i), t) for i, t in enumerate((0, .18, .29, .55, .62, .9)))
    groan = bp(osc(70 + 25 * np.sin(np.linspace(0, 5, int(SR * 1.3))) + 8 * noise(1.3, seed=9)[:int(SR * 1.3)].cumsum() / SR, 1.3, 'saw'), 120, 900) * envl(int(1.3 * SR), .2, .5) * .35
    return mix(snaps, at(groan, .1), at(dust(.8, 10, .1), .6))


@new('building_collapse')
def _():
    crack = NEW['building_crack']()[:int(SR * .9)]
    thud = at(mix(strike('stone', 60, 1.5, .8, 11) * 1.6, rumble(2.4, 110, .02, 1.8, 12, 2.4)), .8)
    debris = at(mix(grains('stone', 2.2, 45, 180, 900, gain=.3, seed=13), grains('wood', 1.8, 25, 200, 700, gain=.25, seed=14)), .85)
    glass = at(NEW['body_shatter']() * .35, 1.0)
    return reverb(mix(crack * .7, thud, debris, glass, at(dust(2.5, 15, .25), 1.2)), .6, .2)


@new('building_debris_rain')
def _():
    return mix(grains('stone', 2.4, 35, 300, 1500, gain=.25, seed=16), grains('wood', 2.0, 15, 300, 900, gain=.2, seed=17), dust(2.6, 18, .15))


@new('building_freeze_creak')
def _():
    d = 1.8; n = int(SR * d)
    f = 55 + 30 * np.abs(np.sin(np.linspace(0, 3, n))) + np.cumsum(np.random.default_rng(19).normal(0, .6, n)) * .02
    stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .7).astype(float)        # stick-slip pulses
    groan = bp(stick, 200, 2200) * envl(n, .2, .6)
    pings = grains('ice', d, 6, 1800, 3500, decay_density=False, gain=.15, seed=20)
    return mix(groan * .5, pings)


@new('building_metal_crash')
def _():
    sheet = mix(strike('metal', 220, 2.0, 1.2, 21), strike('metal', 347, 1.8, 1.1, 22) * .7, strike('metal', 511, 1.5, 1.3, 23) * .5)
    rattle = at(grains('metal', .9, 30, 600, 2500, gain=.12, seed=24), .15)
    return reverb(mix(sheet * .7, rattle, hp(noise(.15, seed=25), 2000) * np.exp(-np.arange(int(.15 * SR)) / (SR * .02))), .5, .2)


@new('combat_arrow_hit')
def _():
    thunk = strike('wood', 330, .35, .9, 26) * 1.2
    d = .6; n = int(SR * d)
    twang = np.sin(2 * np.pi * 140 * A.t_(d)[:n]) * np.exp(-np.arange(n) / (SR * .12)) * (1 + .6 * np.sin(2 * np.pi * 22 * A.t_(d)[:n])) * .35
    return mix(thunk, bp(twang, 90, 600) * 1.5)


@new('creature_bark')
def _():
    out = []
    for k, t in enumerate((0, .32)):
        d = .2; n = int(SR * d)
        v = voice(np.linspace(520, 330, 10), d, [VOW['u'], VOW['a'], VOW['a'], VOW['o']], rough=.35, breath=.2, seed=27 + k)
        out.append(at(v * np.exp(-np.arange(n) / (SR * .07)) * envl(n, .004, .05), t))
    return reverb(mix(*out), .3, .15)


@new('creature_caw')
def _():
    out = []
    for k, t in enumerate((0, .45, .85)):
        d = .32; n = int(SR * d)
        v = voice(np.linspace(560, 470, 10), d, [VOW['ae'], VOW['a'], VOW['a'], VOW['o']], rough=.9, breath=.25, seed=30 + k, bw=(140, 200, 260))
        v = hp(v, 500) * envl(n, .01, .12)
        out.append(at(v * (1 - .15 * k), t))
    return reverb(mix(*out), .5, .2)


@new('creature_flap')
def _():
    out = []; t = 0
    for k in range(7):
        d = .14; n = int(SR * d)
        burst = bp(noise(d, seed=40 + k), 250, 1600) * np.sin(np.linspace(0, np.pi, n)) ** .6 * (1 - .07 * k)
        out.append(at(burst, t)); t += .13 + k * .012
    return mix(*out, lp(noise(t + .2, seed=48), 400) * .15)


@new('creature_laugh')
def _():
    out = []
    for k in range(6):
        d = .16; n = int(SR * d)
        v = voice(np.linspace(150 - k * 6, 120 - k * 6, 8), d, [VOW['a'], VOW['a'], VOW['o']], rough=.6, breath=.35, seed=50 + k)
        out.append(at(v * envl(n, .01, .07), k * .19))
    return reverb(mix(*out), .85, .45)


@new('creature_oink')
def _():
    out = []
    for k, t in enumerate((0, .28, .5)):
        d = .22; n = int(SR * d)
        v = voice(np.linspace(210, 160, 10), d, [VOW['o'], VOW['u']], rough=1.0, breath=.3, seed=60 + k, bw=(80, 110, 150))
        nasal = bp(noise(d, seed=70 + k), 700, 1800) * .25
        out.append(at((v + nasal[:len(v)]) * envl(n, .01, .08), t))
    return mix(*out)


@new('creature_screech')
def _():
    d = 1.1; n = int(SR * d)
    f = np.concatenate([np.linspace(2600, 3100, n // 4), np.linspace(3100, 1900, n - n // 4)])
    tone = np.sin(2 * np.pi * np.cumsum(f * (1 + .02 * np.sin(2 * np.pi * 38 * A.t_(d)[:n]))) / SR)
    harsh = bp(noise(d, seed=80), 1800, 4500) * .45
    return reverb((tone + .5 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * .3 + harsh) * envl(n, .03, .5), .7, .3)


@new('disaster_fireworks')
def _():
    d = .9; n = int(SR * d)
    whistle = np.sin(2 * np.pi * np.cumsum(np.linspace(900, 2400, n)) / SR) * .25 * envl(n, .05, .1)
    boom = at(mix(A.explosion(1.4, .5, 81) * .8, rumble(1.6, 140, .01, 1.2, 82, 1.2)), .95)
    crackle = at(grains('wood', 1.4, 70, 1500, 4000, gain=.2, seed=83), 1.1)
    return reverb(mix(whistle + hp(noise(d, seed=84), 3000)[:n] * .08, boom, crackle), .8, .3)


@new('disaster_meteor')
def _():
    d = 2.2; n = int(SR * d)
    roar = lp(noise(d, 'pink', 85), 1500) * np.linspace(.1, 1.2, n) ** 2
    hiss = hp(noise(d, seed=86), 2500) * np.linspace(.05, .5, n) ** 2
    impact = at(mix(A.explosion(3.0, 1.8, 87) * 1.2, rumble(3.5, 70, .01, 3, 88, 3), grains('stone', 2.5, 30, 150, 800, gain=.3, seed=89)), d)
    return reverb(mix(roar + hiss, impact), .7, .2)


@new('disaster_quake')
def _():
    d = 5.0
    base = rumble(d, 55, .8, 1.8, 90, 3.0) * (1 + .3 * np.sin(2 * np.pi * 3.5 * A.t_(d)))[:int(SR * d)]
    rattle = grains('wood', d * .8, 25, 300, 900, decay_density=False, gain=.18, seed=91) * .8
    pots = at(grains('glass', 2.0, 10, 1500, 4000, decay_density=False, gain=.12, seed=92), 1.0)
    crack = at(strike('stone', 70, 1.2, .8, 93) * 1.3, 1.6)
    return mix(base, rattle, pots, crack)


@new('disaster_volcano')
def _():
    d = 5.0
    blast = mix(A.explosion(3.0, 2.5, 94) * 1.3, rumble(4.0, 60, .02, 3.5, 95, 3.5))
    roar = at(lp(noise(4.0, 'pink', 96), 700) * envl(int(4 * SR), .5, 2) * 1.2, .6)
    rocks = at(grains('stone', 3.5, 20, 120, 600, gain=.35, seed=97), 1.2)
    return reverb(mix(blast, roar, rocks), .8, .25)


@new('extra_crowd_angry')
def _():
    d = 3.5
    voices = crowd(d, 28, 95, 170, ['a', 'ae', 'o', 'ea'], rough=.5, seed=101)
    stomps = msum(at(strike('wood', 80, .3, .7, 110 + i) * .6, i * .55 + .2) for i in range(6))
    return reverb(mix(nrm(voices), nrm(stomps) * .35, nrm(rumble(d, 200, .5, 1, 102, .4)) * .15), .6, .2)


@new('extra_crowd_cheer_big')
def _():
    d = 3.8
    voices = crowd(d, 40, 140, 320, ['ea', 'ae', 'a', 'ei', 'oa'], rough=.1, seed=103, rise=.15)
    return reverb(mix(nrm(voices), at(nrm(claps(d - .4, 30, 104)) * .3, .4)), .65, .25)


@new('extra_hail')
def _():
    d = 4.0
    return mix(grains('ice', d, 60, 2500, 6500, decay_density=False, gain=.12, seed=105), grains('wood', d, 25, 600, 1400, decay_density=False, gain=.12, seed=106),
               bp(noise(d, 'pink', 107), 2000, 8000) * .05)


@new('extra_monkey_chatter')
def _():
    out = []; t = 0
    r = np.random.default_rng(108)
    for k in range(10):
        d = r.uniform(.07, .14); n = int(SR * d)
        f = np.linspace(r.uniform(700, 1100), r.uniform(500, 800), 6)
        v = voice(f, d, [VOW['u'], VOW['a'], VOW['i']] if k % 3 else [VOW['o'], VOW['u']], rough=.3, breath=.15, seed=109 + k)
        out.append(at(v * envl(n, .005, .03), t)); t += d + r.uniform(.03, .12)
    return reverb(mix(*out), .5, .2)


@new('extra_snort')
def _():
    out = []
    for k, (t, d) in enumerate(((0, .22), (.3, .35))):
        n = int(SR * d)
        flutter = 1 + .8 * np.sin(2 * np.pi * 28 * A.t_(d)[:n])
        nose = formant_track(noise(d, seed=111 + k) * flutter, [np.array([500, 450]), np.array([1300, 1200]), np.array([2400, 2300])], (200, 250, 300), (1, .5, .2))
        out.append(at(nose * envl(n, .02, .12) * (1.3 if k else .8), t))
    return mix(*out)


@new('world_harvest')
def _():
    out = []
    for k in range(3):
        d = .38; n = int(SR * d)
        swish = bp(noise(d, seed=120 + k), 1500, 6000) * np.sin(np.linspace(0, np.pi, n)) ** 2 * .7
        rustle = at(grains('wood', .35, 40, 2500, 5000, gain=.05, seed=125 + k), .12)
        out.append(at(mix(swish, rustle), k * .55))
    return mix(*out)


@new('extra_dolphin_click')
def _():
    d = 2.2; n = int(SR * d)
    out = np.zeros(n + SR)
    r = np.random.default_rng(130); t = 0.
    while t < 1.0:
        c = hp(noise(.003, seed=int(t * 1e5)), 4000) * np.hanning(int(.003 * SR)) * 1.2
        i = int(t * SR); out[i:i + len(c)] += c; t += r.uniform(.012, .03)
    wd = 1.0; wn = int(SR * wd)
    f = 6000 + 2500 * np.sin(np.linspace(0, 2.6, wn)) ** 2
    whistle = np.sin(2 * np.pi * np.cumsum(f) / SR) * envl(wn, .08, .2) * .3
    out[int(1.1 * SR):int(1.1 * SR) + wn] += whistle
    return reverb(out[:n], .6, .3)


def build(out_sfx):
    import os, json
    rep = {}
    for name, fn in NEW.items():
        x = fn()
        assert np.isfinite(x).all() and len(x) > 200, name
        x = A.level(x, name.split('_')[0])
        A.write_ogg(os.path.join(out_sfx, name + '.ogg'), x)
        rep[name] = dict(seconds=round(len(x) / SR, 2), rms_db=round(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9), 1))
    return rep


if __name__ == '__main__':
    import sys, json
    print(json.dumps(build(sys.argv[1]), indent=0))


# ------------------------------------------------------------------ v3.3: 3 clips redone with noise-based (non-tonal) impacts
def nburst(d, lo, hi, tau, seed):
    n = int(SR * d)
    return bp(noise(d, seed=seed), lo, hi) * np.exp(-np.arange(n) / (SR * tau))


def crunch_grains(d, rate, lo, hi, gain, seed, thud_every=6):
    r = np.random.default_rng(seed); out = np.zeros(int(SR * (d + .4))); t = 0.; k = 0
    while t < d:
        t += r.exponential(1 / max(rate * np.exp(-t / (d * .5)), .5))
        if t >= d: break
        k += 1
        f = r.uniform(lo, hi)
        g = nburst(.06, f * .6, f * 1.6, r.uniform(.006, .02), int(t * 1e5)) * r.uniform(.3, 1) * gain * np.exp(-t / d)
        if k % thud_every == 0: g = mix(g, lp(noise(.12, seed=k), 250) * np.exp(-np.arange(int(.12 * SR)) / (SR * .03)) * gain * 1.5)
        i = int(t * SR); out[i:i + len(g)] += g[:len(out) - i]
    return out


def creak(d, seed):
    n = int(SR * d)
    f = 45 + 35 * np.abs(np.sin(np.linspace(0, 2.4, n))) + np.cumsum(np.random.default_rng(seed).normal(0, .6, n)) * .02
    stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .75).astype(float)
    return bp(stick, 150, 1800) * envl(n, .15, .4)


def splinter(seed, gain=1.):
    """wood snap: broadband transient + rapid crackle of fibres + short low knock"""
    r = np.random.default_rng(seed)
    snap = hp(noise(.03, seed=seed), 900) * np.exp(-np.arange(int(.03 * SR)) / (SR * .006)) * 1.5
    crack = np.zeros(int(SR * .25))
    for j in range(r.integers(8, 16)):
        i = int(r.uniform(0, .2) * SR); c = hp(noise(.004, seed=seed * 50 + j), 2000) * r.uniform(.2, .7)
        crack[i:i + len(c)] += c[:len(crack) - i]
    knock = lp(noise(.1, seed=seed + 7), 400) * np.exp(-np.arange(int(.1 * SR)) / (SR * .025)) * .8
    return mix(snap, crack, knock) * gain


@new('building_crack')
def _():
    return reverb(mix(at(creak(1.4, 201) * .5, 0), at(splinter(202, .8), .35), at(splinter(203, .6), .62), at(splinter(204, 1.0), .95),
                      at(crunch_grains(.6, 25, 600, 3000, .25, 205), 1.0), at(nburst(1.0, 1500, 6000, .4, 206) * .08, 1.0)), .45, .15)


@new('building_debris_rain')
def _():
    return mix(crunch_grains(2.4, 45, 300, 3500, .5, 207, 5), nburst(2.6, 800, 6000, 1.0, 208) * .1, lp(noise(2.6, 'brown', 209), 180) * envl(int(2.6 * SR), .05, 1.5) * .8)


@new('building_collapse')
def _():
    d = 4.0
    pre = NEW['building_crack']()[:int(SR * 1.1)] * .7
    fall = at(mix(lp(noise(1.6, 'brown', 210), 140) * envl(int(1.6 * SR), .01, 1.3) * 3.2,
                  nburst(.5, 60, 900, .12, 211) * 2.0), 1.05)
    debris = at(mix(crunch_grains(2.5, 60, 200, 3000, .6, 212, 4), crunch_grains(1.8, 30, 1500, 5000, .25, 213, 99)), 1.1)
    tail = at(mix(nburst(2.5, 700, 5000, 1.0, 214) * .12, lp(noise(2.5, 'brown', 215), 120) * envl(int(2.5 * SR), .3, 1.5) * .9), 1.5)
    return reverb(mix(pre, fall, debris, tail), .7, .25)
