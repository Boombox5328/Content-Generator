"""Timing and captions for "The Long Way Out" (blocky version, no narration)."""
import numpy as np
DUR = 70.0
FPS = 30
CHANNEL = "@YourChannel"
TAG = "A speculative timeline based on real science and proposed concepts, not predictions."

TITLE = [(2.4, 4.0, "What if that changes?"), (66.3, 70.0, "It all starts with one step.")]
CAPS = [
    (0.3, 2.3, "One planet. Every human story so far."),
    (4.3, 7.4, "First, the Moon. Three days away."),
    (7.6, 10.9, "Its ice becomes water, air and rocket fuel. A gas station for the solar system."),
    (11.3, 14.3, "Then Mars. Six to nine months away."),
    (14.5, 18.2, "A thin, toxic sky, so we live underground and under glass."),
    (18.6, 20.9, "One day, a child is born who has never seen Earth, except as a star."),
    (21.3, 24.0, "The asteroid belt holds more metal than humans have ever mined."),
    (24.3, 27.0, "Europa hides an ocean under the ice."),
    (27.3, 29.9, "On Titan the air is so thick you could strap on wings and fly."),
    (30.3, 34.3, "Eventually we stop needing planets. We build spinning worlds with gravity, sky and seasons."),
    (36.5, 38.9, "Around the Sun, a swarm of collectors harvests its power."),
    (39.3, 42.0, "The nearest star is over four light-years away. A tiny probe might get there in decades."),
    (42.2, 45.0, "People could take centuries."),
    (45.2, 47.9, "The ones who leave won't be the ones who arrive."),
    (48.3, 51.4, "Star by star, the wave spreads."),
    (51.7, 54.4, "Even slow ships could cross the whole galaxy in a few million years."),
    (54.6, 56.9, "A blink, compared to Earth's history."),
    (57.3, 60.3, "But there's a limit. Space itself is expanding."),
    (60.5, 65.8, "Most galaxies already recede too fast to ever reach, even at light speed."),
]
END = (67.9, CHANNEL, "Follow for more futures")

YEAR_KF = [(0, -1), (3.9, -1), (4.0, 1.0), (11, 1.5), (21, 2.3), (30, 3.2), (39, 4.0), (48, 5.2), (57, 7.0), (66, 7.0), (66.2, -1), (70, -1)]
DIST_KF = [(0, 5.585), (11, 5.585), (13.5, 7.74), (19, 8.6), (21, 8.65), (24, 8.7), (27, 8.8), (30, 9.15), (39, 10.2), (42, 11.6), (45, 12.6), (48, 13.6),
           (57, 17.98), (60, 19.4), (66, 21.9), (66.2, 5.585), (70, 5.585)]
KM_PER_AU = 1.496e8; KM_PER_LY = 9.4607e12


def kf(k, t): return float(np.interp(t, [a for a, _ in k], [b for _, b in k]))


def years_text(t):
    l = kf(YEAR_KF, t)
    if l < 0: return "NOW"
    v = 10 ** l
    if v >= 1e6: return "10 million" if v >= 9.9e6 else f"{v / 1e6:.1f} million"
    if v >= 1000: return f"{int(round(v, -2 if v < 1e4 else -3)):,}"
    return f"{int(round(v, -1 if v >= 100 else 0)):,}"


def dist_text(t):
    km = 10 ** kf(DIST_KF, t)
    if km < 1e6: return f"{int(round(km, -3)):,} km"
    if km < 1e9: return f"{km / 1e6:.0f} million km"
    ly = km / KM_PER_LY; au = km / KM_PER_AU
    if ly < 0.05: return f"{au:,.0f} AU"
    if ly < 10: return f"{ly:.1f} light-years"
    if ly < 100: return f"{ly:.0f} light-years"
    if ly < 1e6: return f"{int(round(ly, -3 if ly > 1e4 else -2)):,} light-years"
    if ly < 1e9: return f"{ly / 1e6:.1f} million light-years"
    return f"{ly / 1e9:.1f} billion light-years"


def stat(t):
    if t < 0.3 or t >= 66.3 and False: return None
    return ("YEARS FROM NOW", years_text(t), "DISTANCE FROM EARTH  " + dist_text(t).upper())
