"""Score + sound design for the alien-war reel. Every hit is placed on the on-screen event time."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
import numpy as np
from audio import Mixer, hz, ramp
import scenes, spec

BPM = 96.0; BEAT = 60 / BPM; BAR = BEAT * 4


def build(out_wav):
    m = Mixer(spec.DUR)
    for k, (rv, g) in dict(piano=(0.5, 0.9), pad=(0.4, 0.8), bass=(0.1, 1.0), perc=(0.35, 1.0), brass=(0.5, 0.7), sfx=(0.25, 1.0), arp=(0.4, 0.6)).items():
        m.layer(k, rv, g)
    # --- harmony: Dm Bb F C (tense), resolving to D major / Bb / G / A for the aftermath
    TENSE = [("D", ["D3", "A3", "F4"], "D2"), ("Bb", ["Bb2", "F3", "D4"], "Bb1"), ("F", ["F3", "A3", "C4"], "F2"), ("C", ["C3", "G3", "E4"], "C2")]
    HOPE = [("D", ["D3", "A3", "F#4"], "D2"), ("Bb", ["Bb2", "F3", "D4"], "Bb1"), ("G", ["G2", "D3", "B3"], "G1"), ("A", ["A2", "E3", "C#4"], "A1")]
    pad_g = lambda t: float(ramp(t, [(0, 0), (3, 0.25), (15, 0.5), (33, 0.35), (42, 0.7), (51, 0.5), (52, 0.0), (53, 0.7), (60, 0.5), (62, 0)]))
    nb = int(spec.DUR / BAR) + 1
    for b in range(nb):
        t0 = b * BAR
        if t0 >= spec.DUR: break
        hope = t0 >= 52
        name, notes, bass = (HOPE if hope else TENSE)[b % 4]
        g = pad_g(t0 + BAR / 2)
        if g > 0.02:
            fr = [hz(x) for x in notes]
            m.put("pad", t0 - 0.2, m.pad(fr, BAR + 1.8, -1) * g * 0.5, -0.6)
            m.put("pad", t0 - 0.2, m.pad(fr, BAR + 1.8, 1) * g * 0.5, 0.6)
        if t0 < 52 and t0 >= 3:
            gb = float(ramp(t0, [(3, 0.0), (7, 0.55), (24, 0.8), (42, 1.0), (52, 0.0)]))
            for k in range(8):
                tt = t0 + k * BEAT / 2
                m.put("bass", tt, m.bass(hz(bass), BEAT * 0.45) * 0.45 * gb * (1.0 if k % 2 == 0 else 0.6))
        if t0 >= 7 and t0 < 52:
            ga = float(ramp(t0, [(7, 0.0), (15, 0.3), (24, 0.6), (42, 1.0)]))
            for k in range(8):
                nn = notes[[0, 1, 2, 1, 2, 1, 0, 1][k]]
                m.put("arp", t0 + k * BEAT / 2, m.pluck(hz(nn) * 2, 0.4) * 0.2 * ga, 0.5 if k % 2 else -0.5)
        if hope:
            mo = {"D": ["D4", "F#4", "A4", "E5"], "Bb": ["Bb3", "D4", "F4", "D5"], "G": ["B3", "D4", "G4", "D5"], "A": ["C#4", "E4", "A4", "E5"]}[name]
            for k, nn in enumerate(mo):
                m.put("piano", t0 + k * BEAT, m.piano(hz(nn), 2.4, 0.9), -0.2)
            m.put("piano", t0, m.piano(hz(bass) * 2, 3.0, 0.8))
    # --- percussion: slow war drums in the military scene, double-time in the dogfight
    for tt in np.arange(24.4, 33.0, BEAT):
        m.put("perc", tt, m.tom(62, 0.8)); 
    for tt in np.arange(24.4 + BEAT / 2, 33.0, BEAT * 2): m.put("perc", tt, m.tom(95, 0.4))
    for tt in np.arange(42.2, 52.0, BEAT / 2):
        m.put("perc", tt, m.tom(70, 0.7 + 0.3 * ((tt - 42) / 10)))
    for tt in np.arange(15.0, 24.0, BEAT * 2): m.put("perc", tt, m.tom(55, 0.5))
    # brass stabs on key beats
    for tt, notes in ((7.0, ["D3", "A3"]), (15.0, ["D3", "F3"]), (24.0, ["D3", "A3"]), (42.0, ["D3", "F3", "A3"]), (48.8, ["Bb2", "F3"])):
        for nn in notes: m.put("brass", tt, m.brass(hz(nn), 1.3, 0.9), 0.0)
    # --- SFX placed on events ----------------------------------------------------
    for c in (7, 15, 24, 33, 42, 52): m.whoosh(float(c), 1.0, 0.55)
    # scene 1: street hum, countdown ticks, the ship's arrival
    m.rumble(0.0, 7.0, 0.05)
    for s in range(1, 7): m.tick(7.0 - s, 1100, 0.1)
    m.riser(3.6, 7.0, 0.35); m.rumble(4.0, 3.5, 0.35)
    m.boom(7.0, 2.0, vol=1.1)
    # scene 2: sirens, ticks to the first strike
    m.siren(8.0, 6.5, 0.08)
    m.rumble(7.0, 8.0, 0.25)
    for s in range(11, 15): m.tick(float(s), 1500, 0.13)
    m.riser(13.0, 15.0, 0.3)
    # scene 3: strikes + grid shutting down
    for (ts, p) in scenes.STRIKES:
        m.zap(ts - 0.3, 0.5, 3000, 300, 0.25, kind="saw")
        m.boom(ts, 1.4, vol=1.0)
    m.sweep_down(15.5, 7.0, 700, 38, 0.25)
    m.rumble(15.0, 9.0, 0.3)
    # scene 4: missile launches and shield hits
    for tm in scenes.MISSILE_T:
        m.zap(tm, 0.5, 400, 1400, 0.08, kind="saw")
        m.rumble(tm, 0.4, 0.12)
        m.zap(tm + 2.6, 0.3, 3200, 1800, 0.07, kind="sine", pan=0.2)
    # scene 5: the lab - quiet beeps, the dip
    for tt in np.arange(33.6, 41.5, 0.8): m.tick(tt, 880 + 60 * int(tt) % 3, 0.07)
    m.sweep_down(37.0, 0.7, 1200, 200, 0.18)
    m.riser(38.5, 42.0, 0.3)
    # scene 6: dogfight
    for tm, k in scenes.LOSSES: m.boom(tm, 0.8, vol=0.8)
    for tt in np.arange(42.5, 50.0, 0.35): m.zap(tt, 0.2, 2600 + 800 * (int(tt * 3) % 3), 500, 0.07, pan=((int(tt * 7) % 3) - 1) * 0.5)
    m.riser(47.8, 50.6, 0.5)
    m.boom(50.65, 3.0, vol=1.3); m.boom(51.0, 2.4, vol=1.0); m.boom(51.3, 2.0, vol=0.9)
    # scene 7: wreckage falls, then quiet
    for tt in (55.6, 56.2, 57.0): m.boom(tt - 3.4, 0.7, vol=0.35)
    for tt in np.arange(53.5, 56.5, 0.55): m.boom(float(tt), 0.5, vol=0.25)
    m.master(out_wav, 1.2)


if __name__ == "__main__":
    build(sys.argv[1])
