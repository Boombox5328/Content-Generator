"""Shared timing / copy for "The Last Light" so video, audio and captions stay in sync."""
import math
import numpy as np

W, H = 270, 480          # native pixel canvas; upscaled 4x -> 1080x1920
SCALE = 4
FPS = 24
DUR = 64.0
CHANNEL = "@YourChannel"  # <- put your channel name here

SCENES = [(0, 4), (4, 12), (12, 17), (17, 24), (24, 31), (31, 38), (38, 45), (45, 53), (53, 64)]
ACT_NAMES = ["", "I · THE PAST", "II · HUMANITY", "III · EARTH", "IV · THE GALAXY",
             "V · THE LAST STARS", "VI · DEGENERATE ERA", "VII · BLACK HOLE ERA", "VIII · HEAT DEATH"]

# Scene 2 vignettes: start times (12.0 ends the scene)
VIGN = [4.0, 4.8, 5.4, 6.1, 6.9, 7.7, 8.5, 9.4, 10.1, 11.1, 12.0]

# --- voice over: (earliest start, text, espeak voice variant, speed wpm) ---
VO = [
    (0.35, "Everything that has ever happened is barely the opening frame.", "en-us+m3", 150),
    (4.15, "Fourteen billion years. Stars, planets, life, us. That's the whole story so far. Now let's go forward.", "en-us+m3", 175),
    (12.15, "Our species might last a million years. Maybe less. Maybe far more. But Earth has a deadline either way.", "en-us+m3", 195),
    (17.15, "In about a billion years, a brightening Sun boils the oceans. In five billion, it swells into a red giant. Then it shrinks into a cooling ember.", "en-us+m3", 215),
    (24.15, "Our galaxy may merge with Andromeda. And as space expands, every other galaxy slips out of view. Future astronomers would see one galaxy, alone, in an empty sky.", "en-us+m3", 225),
    (31.25, "The smallest stars burn for trillions of years. Then the last one goes dark. No new stars will ever form again.", "en-us+m3", 190),
    (38.2, "Galaxies dissolve, flinging dead stars into the void. And if protons decay, even matter itself fades away.", "en-us+m3", 185),
    (45.2, "Black holes are the last things standing. Over a googol years, even they evaporate, ending in one final flash.", "en-us+m3", 170),
    (56.5, "No light. No heat. Nothing left to happen. This is heat death.", "en-us+whisper", 140),
]

# --- counter: (t, years, mode) mode = how the segment ENDING at this key interpolates
YEAR_KF = [(4.0, 0.0, "lin"), (6.1, 9.3e9, "lin"), (7.7, 9.9e9, "lin"), (8.5, 13.73e9, "lin"),
           (10.1, 13.8e9, "lin"), (17.0, 1.38e10, "lin"),
           (18.5, 1.48e10, "lin"), (20.5, 1.88e10, "lin"), (23.5, 2.2e10, "lin"),
           (24.2, 2.2e10, "lin"), (30.8, 1e11, "log"), (31.2, 1e11, "log"),
           (34.0, 1e13, "log"), (37.8, 1e14, "log"),
           (38.3, 1e14, "log"), (40.5, 1e19, "log"), (42.3, 1e20, "log"), (44.8, 1e34, "log"),
           (45.2, 1e40, "log"), (48.5, 1e67, "log"), (52.6, 1e100, "log"), (64.0, 1e100, "log")]

# --- timeline bar span (log10 years at right edge) ---
SPAN_KF = [(0, 100.0), (3.4, 100.0), (4.5, 10.3), (23.7, 10.3), (25.0, 11.5), (30.8, 11.5),
           (31.0, 11.5), (31.8, 14.3), (37.9, 14.3), (39.0, 36.0), (44.9, 36.0), (46.3, 101.0), (64, 101.0)]
NOW_YEARS = 1.38e10

_rng = np.random.default_rng(1234)
# red dwarfs winking out (Scene 6)
N_DWARFS = 34
WINKS = np.sort(32.1 + 4.6 * (_rng.random(N_DWARFS) ** 0.8))
# black hole pops (Scene 8): small, medium, huge
BH_POPS = [49.3, 50.9, 52.45]
BH_START = 45.6
LAST_PIXEL = (53.2, 54.7)   # flicker window
MUSIC_END = 54.4
SILENCE_END = 56.4

def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def kf_interp(kfs, t, log=False):
    ts = [k[0] for k in kfs]; vs = [k[1] for k in kfs]
    return float(np.interp(t, ts, vs))

def year_at(t):
    """-> (years, mode) or None when the counter is hidden"""
    if t < 4.0:
        return None
    for i in range(1, len(YEAR_KF)):
        t0, y0, _ = YEAR_KF[i - 1]; t1, y1, m = YEAR_KF[i]
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            if m == "log" and y0 > 0 and y1 > 0:
                return 10 ** (math.log10(y0) + f * (math.log10(y1) - math.log10(y0))), m
            return y0 + f * (y1 - y0), "lin"
    return YEAR_KF[-1][1], "log"

def span_log(t):
    # ease each zoom segment
    for i in range(1, len(SPAN_KF)):
        t0, a = SPAN_KF[i - 1]; t1, b = SPAN_KF[i]
        if t <= t1:
            if t1 == t0: return b
            f = smooth((t - t0) / (t1 - t0))
            return a + (b - a) * (f if abs(b - a) > 0.01 else 0)
    return SPAN_KF[-1][1]

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def sup(n): return str(n).translate(SUP)

def fmt_years(v, mode):
    if v < 10000:
        return f"{int(v):,}"
    e = int(math.floor(math.log10(v) + 1e-9))
    m = v / 10 ** e
    if mode == "log":
        return f"10{sup(e)}"
    return f"{m:.1f}×10{sup(e)}"
