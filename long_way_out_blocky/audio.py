"""Score + sound design for the blocky Long Way Out (no speech): solo piano motif -> full orchestral swell."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
import numpy as np
from audio import Mixer, hz, ramp
import spec

BPM = 72.0; BEAT = 60 / BPM; BAR = BEAT * 4
CH = [("D", ["D3", "A3", "F#4"], "D2", ["D4", "F#4", "A4", "E5"]),
      ("A", ["A2", "E3", "C#4"], "A1", ["C#5", "E5", "A4", "E4"]),
      ("Bm", ["B2", "F#3", "D4"], "B1", ["D5", "F#4", "B4", "F#5"]),
      ("G", ["G2", "D3", "B3"], "G1", ["B4", "D5", "G4", "D5"])]


def build(out_wav):
    m = Mixer(spec.DUR)
    for k, (rv, g) in dict(piano=(0.5, 1.0), pad=(0.5, 0.8), arp=(0.4, 0.6), bass=(0.1, 0.9), perc=(0.35, 0.9), brass=(0.5, 0.6), sfx=(0.3, 0.9)).items():
        m.layer(k, rv, g)
    pad_g = lambda t: float(ramp(t, [(0, 0), (7, 0), (11, 0.35), (30, 0.55), (48, 0.9), (63, 1.4), (66, 1.0), (69, 0.25), (70, 0)]))
    arp_g = lambda t: float(ramp(t, [(0, 0), (20, 0), (22, 0.5), (39, 0.7), (57, 0.9), (66, 0.2), (67, 0)]))
    bass_g = lambda t: float(ramp(t, [(0, 0), (29, 0), (31, 0.7), (66, 0.9), (66.5, 0)]))
    perc_g = lambda t: float(ramp(t, [(0, 0), (38, 0), (40, 0.5), (57, 0.9), (65.8, 1.2), (66.3, 0)]))
    brass_g = lambda t: float(ramp(t, [(0, 0), (47, 0), (50, 0.5), (62, 1.0), (65.9, 1.4), (66.3, 0)]))
    for b in range(int(spec.DUR / BAR) + 1):
        t0 = b * BAR
        if t0 >= spec.DUR: break
        name, pad_notes, bass_note, arp = CH[b % 4]
        pv = float(ramp(t0, [(0, 1.0), (30, 0.8), (57, 0.6), (66, 1.0)]))
        if t0 >= 66: motif = [(0, "D4"), (1, "F#4"), (2, "A4"), (3, "D5")]
        elif b == 0: motif = [(0.4, "D4"), (1.4, "F#4"), (2.4, "A4"), (3.4, "E5")]
        elif b == 1: motif = [(0.4, "D5"), (1.9, "B4"), (3.0, "A4")]
        elif b % 2 == 0: motif = [(0, arp[0]), (1, arp[1]), (2, arp[2]), (3, arp[3])]
        else: motif = [(0, arp[3]), (1.5, arp[2]), (2.5, arp[1]), (3.5, arp[0])]
        for bt, nn in motif:
            if t0 + bt * BEAT < spec.DUR - 0.1: m.put("piano", t0 + bt * BEAT, m.piano(hz(nn), 2.6, pv), -0.2)
        if 6 <= t0 < 66.1: m.put("piano", t0, m.piano(hz(bass_note) * 2, 3.2, 0.7 * min(1, (t0 - 6) / 6)), 0.1)
        g = pad_g(t0 + BAR / 2)
        if g > 0.01:
            fr = [hz(x) for x in pad_notes]; dur = BAR + 2.4 if t0 + BAR <= 66 else max(2.0, spec.DUR - t0)
            m.put("pad", t0 - 0.2, m.pad(fr, dur, -1) * g * 0.5, -0.6); m.put("pad", t0 - 0.2, m.pad(fr, dur, 1) * g * 0.5, 0.6)
            if t0 > 47: m.put("pad", t0 - 0.2, m.pad([f * 2 for f in fr], dur, 1) * g * 0.28, 0.3)
        ga = arp_g(t0 + 1)
        if ga > 0.01:
            for k in range(8): m.put("arp", t0 + k * BEAT / 2, m.pluck(hz(arp[[0, 1, 2, 3, 2, 1, 3, 2][k]]) * (2 if k % 4 == 3 else 1), 0.5) * 0.18 * ga, 0.5 if k % 2 else -0.5)
        gb = bass_g(t0 + 1)
        if gb > 0.01:
            m.put("bass", t0, m.bass(hz(bass_note), BAR * 0.95, 0.02, 0.25) * 0.5 * gb)
            m.put("bass", t0 + 2 * BEAT, m.bass(hz(bass_note), BEAT * 1.8, 0.02, 0.25) * 0.35 * gb)
        gp = perc_g(t0 + 1)
        if gp > 0.01:
            for k in range(4):
                tt = t0 + k * BEAT
                if (k % 2 == 0 or t0 > 56) and tt < 66: m.put("perc", tt, m.tom(hz(bass_note) * 2, 0.55 * gp * (1.0 if k == 0 else 0.7)))
        go = brass_g(t0 + 1)
        if go > 0.01 and t0 < 66:
            for nn in pad_notes: m.put("brass", t0, m.brass(hz(nn) * 2, BAR, go * 0.9))
    m.riser(57.0, 66.0, 0.3)
    for c in (4, 11, 21, 30, 39, 48, 57, 66): m.whoosh(float(c), 1.0, 0.55 if c != 66 else 0.45)
    # events on screen
    m.boom(14.2, 0.9, vol=0.5)           # Mars touchdown
    m.rumble(13.4, 1.8, 0.2)
    for s in range(5): m.zap(21.3 + s * 0.6, 0.2, 3000, 600, 0.05)      # drill sparks
    m.zap(24.4 + 0.6, 1.2, 600, 140, 0.1, kind="sine")                  # melting through Europa's ice
    m.zap(28.2, 0.5, 500, 1300, 0.08, kind="sine")                      # Titan hop
    m.rumble(30.0, 4.0, 0.12)
    for i in range(7): m.zap(39.4 + 0.08 * i, 1.0, 900, 4000, 0.05, kind="sine", pan=(i - 3) / 4)   # light-sail lasers
    m.boom(66.0, 0.5, vol=0.35)
    m.master(out_wav, 1.2)


if __name__ == "__main__":
    build(sys.argv[1])
