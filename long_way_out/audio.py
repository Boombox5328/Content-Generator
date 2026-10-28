"""Score (solo piano motif -> full orchestral swell), era whooshes and espeak voice-over for "The Long Way Out"."""
import subprocess, wave, os, sys
import numpy as np
import spec

SR = 44100
N = int(spec.DUR * SR)
rng = np.random.default_rng(7)
BEAT = 60 / 72.0
BAR = BEAT * 4

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
def hz(name):
    n = NOTE[name[0]]; o = int(name[-1]); acc = 1 if "#" in name else 0
    return 440.0 * 2 ** ((12 * (o + 1) + n + acc - 69) / 12)

def ramp(t, pts): return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])

# stereo buffers per layer: dict name -> [L, R]
L = {k: np.zeros(N) for k in ("piano", "pad", "arp", "bass", "perc", "orch", "fx")}
R = {k: np.zeros(N) for k in L}

def put(layer, t0, x, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0: return
    j = min(N, i + len(x)); seg = x[: j - i]
    L[layer][i:j] += seg * (1 - 0.5 * pan); R[layer][i:j] += seg * (1 + 0.5 * pan)

def env(n, a, r, curve=2.0):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e

# ---------------- instruments ----------------
def piano(f, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 9000: break
        out += np.sin(2 * np.pi * fk * t + 0.3 * k) * (1.0 / k ** 1.15) * np.exp(-t * (1.1 + 0.9 * k) * (1.0 if f < 500 else 1.5))
    click = rng.standard_normal(int(0.012 * SR)) * np.linspace(1, 0, int(0.012 * SR)) * 0.05
    out[:len(click)] += click
    out *= np.minimum(1, t / 0.004)
    return out * 0.5 * vel

def saw_bl(f, n, harm=8, ph0=0.0, p=1.3):
    ph = (np.cumsum(np.full(n, f / SR)) + ph0)
    out = np.zeros(n)
    for k in range(1, harm + 1):
        if f * k > 6000: break
        out += np.sin(2 * np.pi * k * ph) / k ** p
    return out

def pad_voice(freqs, dur, side):
    n = int(dur * SR); out = np.zeros(n)
    for f in freqs:
        for dt in (-0.0045, 0.0, 0.0048):
            out += saw_bl(f * (1 + dt * side), n, 7, rng.random(), 1.6)
    return out / (len(freqs) * 3) * env(n, 1.3, 1.4, 1.0)

def pluck(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = saw_bl(f, n, 6, 0, 1.4) * np.exp(-t * 7) + 0.5 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 11)
    return x * env(n, 0.003, 0.05)

def sub_bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * env(n, 0.02, 0.25)

def timpani(f, vel=1.0):
    n = int(1.1 * SR); t = np.arange(n) / SR
    fr = f * (1 + 0.5 * np.exp(-t * 18))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 4.5)
    x += rng.standard_normal(n) * np.exp(-t * 60) * 0.25
    return x * vel

def noise_filtered(n, lp):
    x = rng.standard_normal(n); y = np.zeros(n); a = lp
    for i in range(1, n): y[i] = y[i - 1] + a * (x[i] - y[i - 1])
    return y

def whoosh(t_end, dur=1.0, vol=0.5):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    lp = np.zeros(n); bp = np.zeros(n)
    fc = 300 * (4000 / 300) ** t
    f_ = 2 * np.sin(np.pi * fc / SR); q = 0.35
    l = b = 0.0
    for i in range(n):                                    # state-variable bandpass sweep
        h = x[i] - l - q * b
        b += f_[i] * h; l += f_[i] * b
        bp[i] = b
    bp /= np.abs(bp).max() + 1e-9
    e = np.sin(np.pi * t ** 0.8) ** 1.5
    put("fx", t_end - dur * 0.75, bp * e * vol)
    # sub boom on the cut
    nb = int(1.2 * SR); tb = np.arange(nb) / SR
    boom = np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tb * 2.5) + 32) / SR) * np.exp(-tb * 3.2)
    put("fx", t_end, boom * vol * 0.8)

# ---------------- harmony ----------------
CH = [("D", ["D3", "A3", "F#4"], "D2", ["D4", "F#4", "A4", "E5"]),
      ("A", ["A2", "E3", "C#4"], "A1", ["C#5", "E5", "A4", "E4"]),
      ("Bm", ["B2", "F#3", "D4"], "B1", ["D5", "F#4", "B4", "F#5"]),
      ("G", ["G2", "D3", "B3"], "G1", ["B4", "D5", "G4", "D5"])]
CH[1] = ("A", ["A2", "E3", "C#4" if False else "C#4"], "A1", ["C#5", "E5", "A4", "E4"])
def fix(n): return n if "#" not in n else n

def build():
    nbars = int(spec.DUR / BAR) + 1
    gain_pad = lambda t: ramp(t, [(0, 0), (7, 0), (11, 0.35), (30, 0.55), (48, 0.9), (63, 1.4), (66, 1.0), (69, 0.25), (70, 0)])
    gain_arp = lambda t: ramp(t, [(0, 0), (20, 0), (22, 0.5), (39, 0.7), (57, 0.9), (66, 0.2), (67, 0)])
    gain_bass = lambda t: ramp(t, [(0, 0), (29, 0), (31, 0.7), (66, 0.9), (66.5, 0)])
    gain_perc = lambda t: ramp(t, [(0, 0), (38, 0), (40, 0.5), (57, 0.9), (65.8, 1.2), (66.3, 0)])
    gain_orch = lambda t: ramp(t, [(0, 0), (47, 0), (50, 0.5), (62, 1.0), (65.9, 1.5), (66.3, 0)])
    for b in range(nbars):
        t0 = b * BAR
        if t0 >= spec.DUR: break
        name, pad_notes, bass_note, arp = CH[b % 4]
        # piano: motif / broken chords
        pv = ramp(t0, [(0, 1.0), (30, 0.8), (57, 0.6), (66, 1.0)])
        motif = [(0, arp[0]), (1, arp[1]), (2, arp[2]), (3, arp[3])] if b % 2 == 0 else [(0, arp[3]), (1.5, arp[2]), (2.5, arp[1]), (3.5, arp[0])]
        if b < 2: motif = [(0.4, "D4"), (1.4, "F#4"), (2.4, "A4"), (3.4, "E5")] if b == 0 else [(0.4, "D5"), (1.9, "B4"), (3.0, "A4")]
        if t0 >= 66: motif = [(0, "D4"), (1, "F#4"), (2, "A4"), (3, "D5")]
        for bt, nn in motif:
            tt = t0 + bt * BEAT
            if tt < spec.DUR - 0.1:
                put("piano", tt, piano(hz(nn), 2.6, pv), pan=-0.2)
        if t0 >= 6 and t0 < 66.1:
            put("piano", t0, piano(hz(bass_note) * 2, 3.2, 0.7 * min(1, (t0 - 6) / 6)), pan=0.1)
        # pad
        g = float(gain_pad(t0 + BAR / 2))
        if g > 0.01 and t0 < spec.DUR:
            fr = [hz(x) for x in pad_notes]
            dur = BAR + 2.4
            if t0 + BAR > 66: dur = max(2.0, spec.DUR - t0)
            put("pad", t0 - 0.2, pad_voice(fr, dur, -1) * g * 0.55, pan=-0.6)
            put("pad", t0 - 0.2, pad_voice(fr, dur, +1) * g * 0.55, pan=0.6)
            if t0 > 47:        # upper octave swell
                fr2 = [f * 2 for f in fr]
                put("pad", t0 - 0.2, pad_voice(fr2, dur, 1) * g * 0.30, pan=0.3)
        # arp 8ths
        ga = float(gain_arp(t0 + 1))
        if ga > 0.01:
            for k in range(8):
                tt = t0 + k * BEAT / 2
                nn = arp[[0, 1, 2, 3, 2, 1, 3, 2][k]]
                put("arp", tt, pluck(hz(nn) * (2 if k % 4 == 3 else 1), 0.5) * 0.18 * ga, pan=0.5 if k % 2 else -0.5)
        # bass
        gb = float(gain_bass(t0 + 1))
        if gb > 0.01:
            put("bass", t0, sub_bass(hz(bass_note) * 1.0, BAR * 0.95) * 0.5 * gb)
            put("bass", t0 + 2 * BEAT, sub_bass(hz(bass_note) * 1.0, BEAT * 1.8) * 0.35 * gb)
        # timpani on 1 and 3 (soft), more beats at the climax
        gp = float(gain_perc(t0 + 1))
        if gp > 0.01:
            for k in range(4):
                if k % 2 == 0 or t0 > 56:
                    tt = t0 + k * BEAT
                    if tt < 66.0:
                        put("perc", tt, timpani(hz(bass_note) * 2, 0.55 * gp * (1.0 if k == 0 else 0.7)))
        # orchestral brass-ish: stacked saws on chord, octave up
        go = float(gain_orch(t0 + 1))
        if go > 0.01 and t0 < 66:
            fr = [hz(x) * 2 for x in pad_notes]
            nn_ = int(BAR * SR)
            br = np.zeros(nn_)
            for f in fr:
                br += saw_bl(f, nn_, 10, 0, 1.0) * 0.2 + saw_bl(f * 1.004, nn_, 10, 0.3, 1.0) * 0.2
            br *= env(nn_, 0.35, 0.5, 1.0) * go * 0.28
            put("orch", t0, br)

    # swell cymbal / riser into the final push
    n = int(9 * SR); t = np.linspace(0, 1, n)
    ns = noise_filtered(n, 0.6) - noise_filtered(n, 0.04)
    put("fx", 57.0, ns / (np.abs(ns).max() + 1e-9) * (t ** 2.5) * 0.35)
    for tt in (4, 11, 21, 30, 39, 48, 57, 66):
        whoosh(float(tt), 1.0, 0.55 if tt != 66 else 0.45)
    # final shimmer
    tb = np.arange(int(2.6 * SR)) / SR
    put("fx", 66.0, np.sin(2 * np.pi * hz("D6") * tb) * np.exp(-tb * 1.6) * 0.08)

# ---------------- reverb ----------------
def reverb_ir(seed, sec=2.6):
    r = np.random.default_rng(seed)
    n = int(sec * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 2.6)
    k = int(0.002 * SR)
    ir = np.convolve(ir, np.ones(12) / 12, mode="same") * np.exp(-t * 0.4)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    return ir / np.abs(ir).sum() * 6

def fft_conv(x, ir):
    n = len(x) + len(ir)
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]

# ---------------- voice over ----------------
def make_vo(text, voice, wpm, path):
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(wpm), "-p", "30", "-g", "4", "-w", path, text], check=True)

def read_wav(path):
    with wave.open(path) as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return d, w.getframerate()

def resample(x, sr_in, speed=1.0):
    n_out = int(len(x) * SR / sr_in / speed)
    return np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x)

def build_vo(workdir):
    vo = np.zeros(N); cursor = 0.0; rep = []
    ends = [s[0] for s in spec.SCENES[1:]] + [spec.DUR]
    for i, (ts, text, voice, wpm) in enumerate(spec.VO):
        p = os.path.join(workdir, f"vo{i}.wav"); make_vo(text, voice, wpm, p)
        x, sr = read_wav(p); x = resample(x, sr)
        # trim silence
        nz = np.where(np.abs(x) > 0.01)[0]
        if len(nz): x = x[nz[0]: nz[-1] + 1]
        start = max(ts, cursor + 0.1)
        limit = ends[i] + 0.6 - start
        dur = len(x) / SR; sp = 1.0
        if dur > limit: sp = min(1.35, dur / limit); x = resample(x, SR, sp)
        x = x / (np.abs(x).max() + 1e-9) * 0.9
        # warm it up: soft low-pass blend, gentle saturation
        lp = np.convolve(x, np.ones(4) / 4, mode="same")
        x = np.tanh((0.55 * x + 0.45 * lp) * 1.5) / np.tanh(1.5)
        i0 = int(start * SR); j = min(N, i0 + len(x)); vo[i0:j] += x[: j - i0]
        cursor = start + len(x) / SR
        rep.append((i, round(start, 2), round(cursor, 2), round(sp, 2), ends[i]))
    return vo, rep

def main(out_wav, workdir):
    os.makedirs(workdir, exist_ok=True)
    build()
    vo, rep = build_vo(workdir)
    for r in rep: print("VO %d: %.2f -> %.2f (x%.2f)  scene ends %.1f" % r)
    vo_env = np.convolve(np.abs(vo), np.ones(3000) / 3000, mode="same")
    duck = 1 - 0.42 * np.clip(vo_env * 10, 0, 1)
    ir_l, ir_r = reverb_ir(1), reverb_ir(2)
    mixL = np.zeros(N); mixR = np.zeros(N)
    send = {"piano": (1.0, 0.45), "pad": (0.9, 0.35), "arp": (0.5, 0.4), "bass": (0.9, 0.05), "perc": (0.8, 0.3), "orch": (0.9, 0.4), "fx": (0.9, 0.25)}
    for k in L:
        g, wet = send[k]
        dryL, dryR = L[k] * g, R[k] * g
        mixL += dryL + wet * fft_conv(dryL, ir_l)
        mixR += dryR + wet * fft_conv(dryR, ir_r)
    mixL *= duck; mixR *= duck
    vwet = fft_conv(vo, reverb_ir(3, 1.0))
    mixL += vo + 0.12 * vwet; mixR += vo + 0.12 * vwet
    mix = np.stack([mixL, mixR], 1)
    mix[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    mix[-int(1.0 * SR):] *= np.linspace(1, 0, int(1.0 * SR))[:, None]
    mix = np.tanh(mix * 1.0)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print("wrote", out_wav, len(pcm) / SR, "s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
