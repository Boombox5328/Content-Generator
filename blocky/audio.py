"""Synth toolkit: music instruments, SFX, reverb, mixdown. No speech."""
import wave
import numpy as np

SR = 44100
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name):
    n = NOTE[name[0]]; o = int(name[-1]); acc = 1 if "#" in name else (-1 if "b" in name[1:2] else 0)
    return 440.0 * 2 ** ((12 * (o + 1) + n + acc - 69) / 12)


def ramp(t, pts): return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])


class Mixer:
    def __init__(self, dur, seed=5):
        self.N = int(dur * SR); self.dur = dur
        self.rng = np.random.default_rng(seed)
        self.L = {}; self.R = {}
        self.send = {}

    def layer(self, name, reverb=0.3, gain=1.0):
        self.L[name] = np.zeros(self.N); self.R[name] = np.zeros(self.N); self.send[name] = (reverb, gain)

    def put(self, name, t0, x, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= self.N or i + len(x) <= 0: return
        a = 0 if i >= 0 else -i; i = max(0, i)
        j = min(self.N, i + len(x) - a); seg = x[a: a + (j - i)] * gain
        self.L[name][i:j] += seg * (1 - 0.5 * pan); self.R[name][i:j] += seg * (1 + 0.5 * pan)

    # ---------------- instruments
    def env(self, n, a, r, curve=2.0):
        e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, min(n, int(r * SR)))
        e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr) ** curve
        return e

    def saw(self, f, n, harm=8, ph0=0.0, p=1.3):
        ph = np.cumsum(np.full(n, f / SR)) + ph0
        out = np.zeros(n)
        for k in range(1, harm + 1):
            if f * k > 7000: break
            out += np.sin(2 * np.pi * k * ph) / k ** p
        return out

    def piano(self, f, dur=2.4, vel=1.0):
        n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
        for k in range(1, 9):
            fk = f * k * (1 + 0.0004 * k * k)
            if fk > 9000: break
            out += np.sin(2 * np.pi * fk * t + 0.3 * k) / k ** 1.15 * np.exp(-t * (1.1 + 0.9 * k) * (1.0 if f < 500 else 1.5))
        out *= np.minimum(1, t / 0.004)
        return out * 0.5 * vel

    def pad(self, freqs, dur, side=1, a=1.2, r=1.2, harm=7):
        n = int(dur * SR); out = np.zeros(n)
        for f in freqs:
            for dt in (-0.0045, 0.0, 0.0048):
                out += self.saw(f * (1 + dt * side), n, harm, self.rng.random(), 1.6)
        return out / (len(freqs) * 3) * self.env(n, a, r, 1.0)

    def bass(self, f, dur, a=0.01, r=0.15):
        n = int(dur * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * f * t) + 0.35 * self.saw(f, n, 4, 0, 1.0) * 0.5 + 0.2 * np.sin(4 * np.pi * f * t)) * self.env(n, a, r)

    def pluck(self, f, dur=0.4):
        n = int(dur * SR); t = np.arange(n) / SR
        return (self.saw(f, n, 6, 0, 1.4) * np.exp(-t * 8) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 12)) * self.env(n, 0.003, 0.05)

    def brass(self, f, dur, vol=1.0):
        n = int(dur * SR)
        x = self.saw(f, n, 12, 0, 0.9) + self.saw(f * 1.006, n, 12, 0.3, 0.9)
        return x * 0.25 * self.env(n, 0.06, 0.25, 1.0) * vol

    def tom(self, f=70.0, vel=1.0, dur=0.7):
        n = int(dur * SR); t = np.arange(n) / SR
        fr = f * (1 + 0.8 * np.exp(-t * 22))
        x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 6.5)
        x += self.rng.standard_normal(n) * np.exp(-t * 80) * 0.25
        return x * vel

    def noise(self, n, lp=0.2):
        x = self.rng.standard_normal(n); y = np.zeros(n)
        for i in range(1, n): y[i] = y[i - 1] + lp * (x[i] - y[i - 1])
        return y

    # ---------------- sfx
    def boom(self, t, size=1.0, layer="sfx", vol=1.0):
        n = int((1.6 + 1.2 * size) * SR); tt = np.arange(n) / SR
        thump = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 4) + 28) / SR) * np.exp(-tt * (3.0 / (0.6 + size)))
        nz = self.noise(n, 0.08 + 0.1 / (size + 0.3)); nz = nz / (np.abs(nz).max() + 1e-9)
        x = thump * 0.9 + nz * np.exp(-tt * (4.0 / (0.7 + size))) * 0.6
        self.put(layer, t, x * vol * 0.8)

    def zap(self, t, dur=0.35, f0=2400, f1=240, vol=0.3, layer="sfx", kind="saw", pan=0.0):
        n = int(dur * SR); f = np.geomspace(f0, f1, n); ph = np.cumsum(f / SR)
        x = (2 * (ph % 1) - 1) if kind == "saw" else np.sin(2 * np.pi * ph)
        self.put(layer, t, x * self.env(n, 0.002, dur * 0.6) * vol, pan)

    def whoosh(self, t_end, dur=1.0, vol=0.5, layer="sfx"):
        n = int(dur * SR); tt = np.linspace(0, 1, n); x = self.rng.standard_normal(n)
        fc = 300 * (4200 / 300) ** tt; f_ = 2 * np.sin(np.pi * fc / SR); q = 0.35
        l = b = 0.0; bp = np.zeros(n)
        for i in range(n):
            h = x[i] - l - q * b; b += f_[i] * h; l += f_[i] * b; bp[i] = b
        bp /= np.abs(bp).max() + 1e-9
        self.put(layer, t_end - dur * 0.75, bp * np.sin(np.pi * tt ** 0.8) ** 1.5 * vol)
        nb = int(1.0 * SR); tb = np.arange(nb) / SR
        self.put(layer, t_end, np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tb * 2.5) + 32) / SR) * np.exp(-tb * 3.2) * vol * 0.8)

    def tick(self, t, f=1500.0, vol=0.12, layer="sfx"):
        n = int(0.05 * SR); tt = np.arange(n) / SR
        self.put(layer, t, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 70) * vol)

    def siren(self, t0, dur, vol=0.12, layer="sfx"):
        n = int(dur * SR); tt = np.arange(n) / SR
        f = 620 + 280 * np.sin(2 * np.pi * 0.9 * tt)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
        self.put(layer, t0, x * vol * self.env(n, 0.3, 0.6, 1.0))

    def riser(self, t0, t1, vol=0.3, layer="sfx"):
        n = int((t1 - t0) * SR); tt = np.linspace(0, 1, n)
        nz = self.noise(n, 0.5) - self.noise(n, 0.03)
        nz /= np.abs(nz).max() + 1e-9
        tone = np.sin(2 * np.pi * np.cumsum(120 * (1 + 6 * tt ** 2)) / SR)
        self.put(layer, t0, (nz * 0.6 + tone * 0.4) * tt ** 2.2 * vol)

    def sweep_down(self, t0, dur, f0=900, f1=40, vol=0.3, layer="sfx"):
        n = int(dur * SR); f = np.geomspace(f0, f1, n)
        self.put(layer, t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * self.env(n, 0.01, dur * 0.5) * vol)

    def rumble(self, t0, dur, vol=0.2, layer="sfx"):
        n = int(dur * SR); x = self.noise(n, 0.015); x /= np.abs(x).max() + 1e-9
        self.put(layer, t0, x * vol * self.env(n, dur * 0.3, dur * 0.3, 1.0))

    # ---------------- reverb + master
    def _ir(self, seed, sec=2.2):
        r = np.random.default_rng(seed); n = int(sec * SR); t = np.arange(n) / SR
        ir = r.standard_normal(n) * np.exp(-t * 2.8)
        ir = np.convolve(ir, np.ones(12) / 12, mode="same")
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        return ir / np.abs(ir).sum() * 6

    @staticmethod
    def _conv(x, ir):
        n = len(x) + len(ir); m = 1 << (n - 1).bit_length()
        return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]

    def master(self, out_wav, fade_out=1.0):
        irl, irr = self._ir(1), self._ir(2)
        L = np.zeros(self.N); R = np.zeros(self.N)
        for k in self.L:
            wet, g = self.send[k]
            L += g * (self.L[k] + wet * self._conv(self.L[k], irl)); R += g * (self.R[k] + wet * self._conv(self.R[k], irr))
        mix = np.stack([L, R], 1)
        mix[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
        nf = int(fade_out * SR); mix[-nf:] *= np.linspace(1, 0, nf)[:, None]
        mix = np.tanh(mix); mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
        pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        print("wrote", out_wav, len(pcm) / SR, "s")
