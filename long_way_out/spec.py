"""Shared timing / copy for "The Long Way Out" so video, audio and captions stay in sync."""
import math
import numpy as np

W, H = 540, 960           # internal canvas; upscaled 2x -> 1080x1920
SCALE = 2
FPS = 30
DUR = 70.0
CHANNEL = "@YourChannel"  # <- put your channel name here

# scene boundaries (s)
SCENES = [(0, 4), (4, 11), (11, 21), (21, 30), (30, 39), (39, 48), (48, 57), (57, 66), (66, 70)]
ERA = ["", "THE MOON", "MARS", "THE OUTER SYSTEM", "BUILDING WORLDS", "THE FIRST STAR",
       "THE GALAXY", "THE LIMIT", ""]

# --- voice over: (earliest start, text, espeak voice, wpm) ---
VO = [
    (0.25, "So far, every human story has happened on one planet. What if that changes?", "en-us+m3", 168),
    (4.15, "First, the Moon. Three days away, with ice we can turn into water, oxygen and fuel. It's a gas station for the solar system.", "en-us+m3", 178),
    (11.15, "Then Mars. Months away, with a thin toxic sky, so we live underground and under glass. And one day, a child is born who has never seen Earth, except as a star.", "en-us+m3", 178),
    (21.15, "The asteroid belt holds more metal than humans have ever mined. Europa hides an ocean under ice. And on Titan, the air is so thick a person could strap on wings and fly.", "en-us+m3", 182),
    (30.15, "Eventually we stop needing planets. We build spinning worlds with gravity, sky, and seasons. And around the Sun, a swarm of collectors harvests its power.", "en-us+m3", 178),
    (39.15, "The nearest star is over four light-years away. A tiny probe might get there in decades. People could take centuries, and the ones who leave won't be the ones who arrive.", "en-us+m3", 182),
    (48.15, "Star by star, the wave spreads. Even slow ships could reach across the whole galaxy in a few million years. A blink, compared to Earth's history.", "en-us+m3", 178),
    (57.15, "But there's a limit. Space itself is expanding. Most galaxies are already moving away too fast, so we could never reach them, even at light speed.", "en-us+m3", 178),
    (66.2, "Everything after begins with the first one.", "en-us+m3", 150),
]

# --- on-screen text: (t_in, t_out, kind, text) ; kind: "label" (lower third), "big" (headline), "kard" ---
TEXTS = [
    (2.2, 4.0, "big", "Every human who has ever lived… lived here."),
    (4.6, 7.6, "label", "Lunar base: shielded by moon dust"),
    (7.7, 10.9, "label", "Water ice at the poles → air, water, rocket fuel"),
    (11.4, 14.4, "label", "Trip: ~6–9 months"),
    (14.4, 17.4, "label", "Messages to Earth: 3–22 min delay"),
    (18.4, 20.9, "label", "First Martian-born human"),
    (21.3, 24.0, "label", "Asteroids: metals worth more than Earth's economy"),
    (24.2, 26.9, "label", "Europa: a hidden ocean, maybe life?"),
    (27.2, 29.9, "label", "Titan: air so thick you could fly with wings"),
    (30.4, 34.4, "label", "Spinning habitats: gravity from rotation"),
    (36.4, 38.9, "label", "Dyson swarm: harvesting the Sun's energy"),
    (35.0, 38.9, "kard", "Type I → Type II civilization"),
    (39.4, 42.0, "label", "Fast probes: ~20 years"),
    (42.0, 45.0, "label", "Crewed ships: possibly centuries"),
    (45.0, 47.9, "label", "Alpha Centauri: 4.2 light-years"),
    (48.3, 51.5, "label", "Milky Way: 100,000 light-years across"),
    (51.6, 54.3, "label", "Settling it: maybe millions of years"),
    (54.4, 56.9, "label", "Type III civilization"),
    (57.6, 60.6, "big", "But most of the universe… we can never reach."),
    (61.0, 65.9, "label", "Dark energy: distant galaxies are receding too fast to ever catch"),
    (67.0, 70.0, "big", "It all starts with one step."),
]
END_CARD = (68.0, 70.0, "Follow for more futures.")

# --- "years from now" counter: (t, log10 years). 0 -> NOW ---
YEAR_KF = [(0, -1), (3.9, -1), (4.0, 1.0), (11, 1.5), (21, 2.3), (30, 3.2), (39, 4.0), (48, 5.2), (57, 7.0), (66, 7.0), (66.2, -1), (70, -1)]

# --- distance from Earth: (t, log10 km) ---
DIST_KF = [(0, 5.585), (11, 5.585), (13.5, 7.74), (19, 8.6), (21, 8.65), (24, 8.7), (27, 8.8), (30, 9.15),
           (39, 10.2), (42, 11.6), (45, 12.6), (48, 13.6), (57, 17.98), (60, 19.4), (66, 21.9), (66.2, 5.585), (70, 5.585)]

KM_PER_AU = 1.496e8
KM_PER_LY = 9.4607e12


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def kf(kfs, t):
    ts = [k[0] for k in kfs]; vs = [k[1] for k in kfs]
    return float(np.interp(t, ts, vs))


def scene_of(t):
    for i, (a, b) in enumerate(SCENES):
        if a <= t < b:
            return i
    return len(SCENES) - 1


def years_text(t):
    l = kf(YEAR_KF, t)
    if l < 0:
        return "NOW"
    v = 10 ** l
    if v >= 1e6:
        return f"{v / 1e6:.1f} million".replace(".0 ", " ") if v < 1e7 - 1 else "10 million"
    if v >= 1000:
        return f"{int(round(v, -2 if v < 1e4 else -3)):,}"
    return f"{int(round(v, -1 if v >= 100 else 0)):,}"


def dist_text(t):
    l = kf(DIST_KF, t)
    km = 10 ** l
    if km < 1e6:
        return f"{int(round(km, -3)):,} km"
    if km < 1e9:
        return f"{km / 1e6:.0f} million km"
    au = km / KM_PER_AU
    ly = km / KM_PER_LY
    if ly < 0.05:
        return f"{au:,.0f} AU"
    if ly < 100:
        return f"{ly:.1f} light-years" if ly < 10 else f"{ly:.0f} light-years"
    if ly < 1e6:
        return f"{int(round(ly, -3 if ly > 1e4 else -2)):,} light-years"
    if ly < 1e9:
        return f"{ly / 1e6:.1f} million light-years".replace(".0 ", " ")
    return f"{ly / 1e9:.1f} billion light-years"
