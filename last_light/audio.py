"""Chiptune score + SFX + espeak voice-over for "The Last Light". Writes a 44.1k stereo wav."""
import subprocess, wave, os, sys, math
import numpy as np
import spec

SR = 44100
N = int(spec.DUR * SR)
rng = np.random.default_rng(99)

def tarr(n): return np.arange(n) / SR
def env(n, a=0.004, r=0.05, curve=2.0):
    e = np.ones(n)
    na = max(1, int(a * SR)); nr = max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e
def osc(kind, f, n, duty=0.5):
    ph = np.cumsum(np.full(n, f / SR)) % 1.0 if np.isscalar(f) else np.cumsum(f / SR) % 1.0
    if kind == "pulse": return np.where(ph < duty, 1.0, -1.0)
    if kind == "tri": return 4 * np.abs(ph - 0.5) - 1
    if kind == "sine": return np.sin(2 * np.pi * ph)
    if kind == "saw": return 2 * ph - 1
    if kind == "noise":
        # NES-ish stepped noise
        steps = rng.choice([-1.0, 1.0], size=n // max(1, int(SR / (f * 2))) + 2)
        return np.repeat(steps, max(1, int(SR / (f * 2))))[:n]
    raise ValueError(kind)

buf_music = np.zeros(N); buf_sfx = np.zeros(N); buf_drone = np.zeros(N)
def put(buf, t0, x):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0: return
    j = min(N, i + len(x)); buf[i:j] += x[: j - i]

def bpm(t): return float(np.interp(t, [4, 17, 24, 31, 38, 45, 53, 54.4], [150, 142, 112, 80, 56, 40, 28, 24]))
def pitch(t): return float(np.interp(t, [0, 17, 31, 45, 54.4], [1.0, 1.0, 0.85, 0.65, 0.5]))

# ---------- music ----------
T0 = spec.SCENES[1][0]
tt = np.arange(0, int(spec.MUSIC_END * SR)) / SR
bps = np.interp(tt, [4, 17, 24, 31, 38, 45, 53, 54.4], [150, 142, 112, 80, 56, 40, 28, 24]) / 60.0
beat = np.cumsum(bps) / SR
beat[tt < T0] = 0
beat = np.maximum(0, np.cumsum(np.where(tt >= T0, bps, 0)) / SR)
n_steps = int(beat[-1] * 4)
step_idx = np.searchsorted(beat * 4, np.arange(n_steps))
step_t = step_idx / SR

A = 110.0
def semis(root, s): return root * 2 ** (s / 12)
PROG = [(0, [0, 3, 7]), (-4, [0, 4, 7]), (3, [0, 4, 7]), (-2, [0, 4, 7])]   # Am F C G (semis from A, chord tones)
SCALE_PENT = [0, 3, 5, 7, 10, 12, 15]
melody_rng = np.random.default_rng(5)
mel_idx = 3

def present(inst, t):
    if inst == "drums": return t < 31.2
    if inst == "kick_only": return 24 <= t < 31.2
    if inst == "arp": return t < 38.0
    if inst == "lead": return t < 45.5
    if inst == "bass": return t < 51.5
    return True

for n in range(n_steps):
    t = step_t[n]
    if t >= spec.MUSIC_END - 0.05: break
    bar, s16 = divmod(n, 16)
    root, tones = PROG[(bar // 2) % 4]
    p = pitch(t)
    dt = (step_t[n + 1] - t) if n + 1 < n_steps else 0.1
    # arp
    if present("arp", t):
        thin = t >= 31.2
        if (not thin) or s16 % 4 == 0:
            tone = tones[[0, 1, 2, 1][s16 % 4]] + (12 if (s16 // 4) % 2 else 0) + root
            f = semis(A * 2, tone) * p
            nn = int(dt * SR * 0.9)
            put(buf_music, t, 0.16 * osc("pulse", f, nn, 0.125 if s16 % 8 < 4 else 0.25) * env(nn, 0.002, dt * 0.7))
    # bass
    if present("bass", t) and (s16 % 8 in (0, 6) or (t > 24 and s16 % 8 == 0)):
        sparse = t >= 38 and s16 != 0
        if not sparse:
            f = semis(A / 2, root) * p
            nn = int(dt * SR * (3 if s16 % 8 == 0 else 1.5))
            put(buf_music, t, 0.34 * osc("tri", f, nn) * env(nn, 0.004, dt))
    # lead
    if present("lead", t) and s16 % 2 == 0:
        if melody_rng.random() < (0.75 if t < 31 else 0.5):
            mel_idx = int(np.clip(mel_idx + melody_rng.choice([-2, -1, 0, 1, 1, 2]), 0, len(SCALE_PENT) - 1))
            f = semis(A * 2, SCALE_PENT[mel_idx] + root) * p
            nn = int(dt * SR * melody_rng.choice([1.5, 2.5, 4]))
            vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * np.arange(nn) / SR)
            put(buf_music, t, 0.17 * osc("pulse", f * vib, nn, 0.25) * env(nn, 0.004, dt * 1.2))
    # drums
    if present("drums", t):
        if s16 % 4 == 0:
            nn = int(0.14 * SR); sweep = 150 * np.exp(-np.arange(nn) / SR * 28) + 40
            put(buf_music, t, 0.5 * np.sin(2 * np.pi * np.cumsum(sweep * p) / SR) * env(nn, 0.001, 0.12))
        if not present("kick_only", t) and t < 24:
            if s16 % 8 == 4:
                nn = int(0.12 * SR); put(buf_music, t, 0.22 * osc("noise", 9000 * p, nn) * env(nn, 0.001, 0.1))
            if s16 % 2 == 0:
                nn = int(0.03 * SR); put(buf_music, t, 0.08 * osc("noise", 14000, nn) * env(nn, 0.0005, 0.025))
        elif t < 31.2 and not present("kick_only", t):
            pass

# ---------- drone (the last instrument) ----------
n_d = int((spec.MUSIC_END + 0.01) * SR)
td = tarr(n_d)
d_amp = np.interp(td, [29, 33, 45, 51, 53.5, spec.MUSIC_END], [0, 0.18, 0.3, 0.32, 0.2, 0.0])
d_f = np.interp(td, [29, 54.4], [58, 41])
dr = np.sin(2 * np.pi * np.cumsum(d_f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(d_f * 1.004) / SR) \
     + 0.15 * np.sin(2 * np.pi * np.cumsum(d_f * 2.0) / SR)
buf_drone[:n_d] += dr * d_amp * (1 + 0.1 * np.sin(2 * np.pi * 0.23 * td))

# ---------- sfx ----------
def noise_burst(t0, dur, vol, lp=0.2, sweep=None):
    n = int(dur * SR); x = rng.standard_normal(n)
    y = np.zeros(n); a = lp
    for i in range(1, n): y[i] = y[i - 1] + a * (x[i] - y[i - 1])   # 1-pole lowpass
    put(buf_sfx, t0, vol * y / (np.abs(y).max() + 1e-9) * env(n, 0.003, dur * 0.9, 1.5))
def zap(t0, dur, f0, f1, vol, kind="pulse"):
    n = int(dur * SR); f = np.geomspace(f0, f1, n)
    put(buf_sfx, t0, vol * osc(kind, f, n, 0.25) * env(n, 0.002, dur * 0.5))
def blip(t0, f, vol=0.12, dur=0.07, kind="pulse"):
    n = int(dur * SR); put(buf_sfx, t0, vol * osc(kind, f, n, 0.5) * env(n, 0.001, dur * 0.8))

# hook: pixel blinks
for tb in (0.35, 1.0): blip(tb, 880, 0.08, 0.09, "sine")
zap(2.7, 1.2, 90, 600, 0.05, "tri")            # rising tension
zap(3.2, 0.6, 1400, 180, 0.06, "sine")          # pixel shrinks
# big bang
noise_burst(4.0, 1.4, 0.7, 0.08); zap(4.0, 0.9, 700, 40, 0.35, "tri")
for tv in spec.VIGN[1:-1]: blip(tv, 1320, 0.07, 0.05)
noise_burst(9.4, 1.2, 0.6, 0.05); zap(9.0, 0.4, 1800, 90, 0.12)  # asteroid streak -> impact
# city lights dimming
for i, tc in enumerate(np.linspace(13.2, 16.6, 9)): blip(tc, 700 - i * 55, 0.05, 0.12, "tri")
# sun swell / collapse
zap(17.5, 5.0, 50, 140, 0.18, "saw"); noise_burst(19.0, 1.5, 0.12, 0.3)
zap(22.9, 0.9, 1500, 30, 0.3, "saw"); noise_burst(22.9, 0.8, 0.4, 0.05)
# galaxies merge
zap(26.0, 3.0, 120, 70, 0.1, "tri")
# violent zoom out
zap(31.0, 0.9, 2400, 40, 0.3, "saw"); noise_burst(31.0, 0.9, 0.3, 0.4)
for w in spec.WINKS: blip(float(w), 900, 0.05, 0.1, "pulse"); zap(float(w), 0.18, 900, 160, 0.06)
# static (hypothetical proton decay)
nn = int(2.4 * SR); st = rng.standard_normal(nn) * np.concatenate([np.linspace(0, 0.1, nn // 2), np.linspace(0.1, 0, nn - nn // 2)])
put(buf_sfx, 42.6, st)
# black-hole pops
for i, tp in enumerate(spec.BH_POPS):
    big = i == 2
    zap(tp, 0.35 if not big else 1.2, 2800 if not big else 3600, 400 if not big else 60, 0.14 if not big else 0.3, "sine")
    if big: noise_burst(tp, 1.0, 0.25, 0.1)
# last pixel
for tl_ in np.arange(53.4, 54.6, 0.3): blip(tl_, 440, 0.025, 0.05, "sine")

# ---------- voice-over ----------
def make_vo(i, text, voice, wpm, path):
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(wpm), "-p", "35", "-w", path, text], check=True)
def read_wav(path):
    with wave.open(path) as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return d, w.getframerate()
def resample(x, sr_in, speed=1.0):
    n_out = int(len(x) * SR / sr_in / speed)
    return np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x)

def build_vo(workdir):
    vo = np.zeros(N); cursor = 0.0; report = []
    ends = [s[0] for s in spec.SCENES[1:]] + [spec.DUR]
    for i, (ts, text, voice, wpm) in enumerate(spec.VO):
        p = os.path.join(workdir, f"vo{i}.wav"); make_vo(i, text, voice, wpm, p)
        x, sr = read_wav(p)
        x = resample(x, sr)
        start = max(ts, cursor + 0.05)
        # keep a line from running far past its scene: speed up (tape-style) if needed
        limit = (ends[i] if i < 8 else 61.8) + 0.7 - start
        dur = len(x) / SR
        sp = 1.0
        if dur > limit: sp = min(1.3, dur / limit); x = resample(x, SR, sp)
        x = x / (np.abs(x).max() + 1e-9) * (0.9 if i < 8 else 0.55)
        # light bit-crush for a console-speech feel
        if i < 8: x = np.round(x * 24) / 24
        put(vo, start, x); cursor = start + len(x) / SR
        report.append((i, round(start, 2), round(cursor, 2), round(sp, 2)))
    return vo, report

def main(out_wav, workdir):
    os.makedirs(workdir, exist_ok=True)
    vo, rep = build_vo(workdir)
    for r in rep: print("VO line %d: %.2fs -> %.2fs (speedup x%.2f)" % r)
    vo_env = np.convolve(np.abs(vo), np.ones(2000) / 2000, mode="same")
    duck = 1 - 0.45 * np.clip(vo_env * 12, 0, 1)
    music = buf_music * 0.8 * duck
    mix = music + buf_drone * (0.7 + 0.3 * duck) + buf_sfx * 0.9 * (0.6 + 0.4 * duck) + vo
    # hard silence window: hold 2 seconds of true silence
    sil0, sil1 = int(spec.MUSIC_END * SR), int(spec.SILENCE_END * SR)
    mix[sil0:sil1] = 0
    # start/end fades
    mix[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    # stereo: tiny haas widening on music-ish content
    d = int(0.012 * SR)
    L = mix.copy(); R = np.concatenate([np.zeros(d), mix[:-d]]) * 0.97 + 0 * mix
    R = 0.5 * R + 0.5 * mix
    st = np.stack([L, R], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print("wrote", out_wav, len(pcm) / SR, "s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
