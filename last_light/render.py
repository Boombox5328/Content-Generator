"""Procedural 16-bit pixel-art renderer for "The Last Light". Native 270x480, upscaled 4x by ffmpeg."""
import math, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import spec
from spec import W, H, smooth

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16 - 0.5
BAYER_T = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]
LEVELS = 6      # per-channel levels -> chunky limited palette with ordered dither
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_BIG = ImageFont.truetype(FONT_B, 13); F_SM = ImageFont.truetype(FONT_B, 10)
F_XS = ImageFont.truetype(FONT_B, 8); F_CNT = ImageFont.truetype(FONT_B, 14)
F_END = ImageFont.truetype(FONT_B, 16)

def lerp(a, b, f): return a + (b - a) * f
def col(r, g, b): return np.array([r, g, b], np.float32)
def clamp01(x): return min(1.0, max(0.0, x))

# ---------------- noise ----------------
def _fbm(size, seed, octs=(4, 8, 16, 32), amps=(1, .5, .25, .12)):
    r = np.random.default_rng(seed); out = np.zeros((size, size), np.float32)
    for o, a in zip(octs, amps):
        g = r.random((o, o)).astype(np.float32)
        u = np.arange(size) * o / size; i0 = u.astype(int); f = u - i0; f = f * f * (3 - 2 * f)
        i1 = (i0 + 1) % o
        top = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        bot = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        out += a * (top * (1 - f)[:, None] + bot * f[:, None])
    out -= out.min(); return out / out.max()
NZ_A = _fbm(256, 1); NZ_B = _fbm(256, 2); NZ_C = _fbm(256, 3)
def tex(nz, u, v):
    S = nz.shape[0]
    return nz[(v * S).astype(int) % S, (u * S).astype(int) % S]

# ---------------- primitives ----------------
def put_px(cv, x, y, c, a=1.0):
    x = int(x); y = int(y)
    if 0 <= x < W and 0 <= y < H: cv[y, x] = cv[y, x] * (1 - a) + np.asarray(c, np.float32) * a
def rect(cv, x0, y0, x1, y1, c, a=1.0):
    x0, x1 = max(0, int(x0)), min(W, int(x1)); y0, y1 = max(0, int(y0)), min(H, int(y1))
    if x1 > x0 and y1 > y0: cv[y0:y1, x0:x1] = cv[y0:y1, x0:x1] * (1 - a) + np.asarray(c, np.float32) * a
def vgrad(cv, y0, y1, c0, c1, x0=0, x1=W):
    f = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    cv[y0:y1, x0:x1] = np.asarray(c0, np.float32) * (1 - f) + np.asarray(c1, np.float32) * f
def glow(cv, cx, cy, r, c, amt=1.0, power=2.0):
    x0, x1 = max(0, int(cx - r)), min(W, int(cx + r) + 1); y0, y1 = max(0, int(cy - r)), min(H, int(cy + r) + 1)
    if x1 <= x0 or y1 <= y0: return
    d = np.sqrt((XX[y0:y1, x0:x1] - cx) ** 2 + (YY[y0:y1, x0:x1] - cy) ** 2) / r
    g = np.clip(1 - d, 0, 1) ** power * amt
    cv[y0:y1, x0:x1] += g[..., None] * np.asarray(c, np.float32)
def disc_mask(cx, cy, r):
    x0, x1 = max(0, int(cx - r - 1)), min(W, int(cx + r + 2)); y0, y1 = max(0, int(cy - r - 1)), min(H, int(cy + r + 2))
    return x0, x1, y0, y1
def flat_disc(cv, cx, cy, r, c, a=1.0):
    x0, x1, y0, y1 = disc_mask(cx, cy, r)
    if x1 <= x0 or y1 <= y0: return
    m = (XX[y0:y1, x0:x1] - cx) ** 2 + (YY[y0:y1, x0:x1] - cy) ** 2 <= r * r
    sub = cv[y0:y1, x0:x1]; sub[m] = sub[m] * (1 - a) + np.asarray(c, np.float32) * a
def ring(cv, cx, cy, r0, r1, c, a=1.0):
    x0, x1, y0, y1 = disc_mask(cx, cy, r1)
    if x1 <= x0 or y1 <= y0: return
    d2 = (XX[y0:y1, x0:x1] - cx) ** 2 + (YY[y0:y1, x0:x1] - cy) ** 2
    m = (d2 <= r1 * r1) & (d2 >= r0 * r0)
    sub = cv[y0:y1, x0:x1]; sub[m] = sub[m] * (1 - a) + np.asarray(c, np.float32) * a
def planet(cv, cx, cy, r, texfun, light=(-0.6, -0.5), amb=0.16, rot=0.0, atmo=None):
    x0, x1, y0, y1 = disc_mask(cx, cy, r)
    if x1 <= x0 or y1 <= y0: return
    dx = (XX[y0:y1, x0:x1] - cx) / r; dy = (YY[y0:y1, x0:x1] - cy) / r
    d2 = dx * dx + dy * dy; m = d2 <= 1
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    lx, ly = light; lz = math.sqrt(max(0.0, 1 - lx * lx - ly * ly))
    lam = np.clip(dx * lx + dy * ly + nz * lz, 0, 1)
    lon = np.arctan2(dx, np.maximum(nz, 1e-3)) / (2 * math.pi) + rot
    lat = np.arcsin(np.clip(dy, -1, 1)) / math.pi + 0.5
    c = texfun(lon, lat, dx, dy, nz) * (amb + (1 - amb) * lam)[..., None]
    if atmo is not None:
        rim = np.clip((d2 - 0.72) / 0.28, 0, 1) ** 2 * (0.35 + 0.65 * lam)
        c = c + rim[..., None] * np.asarray(atmo, np.float32)
    sub = cv[y0:y1, x0:x1]; sub[m] = c[m]
def stamp(cv, sprite, cmap, x, y, s=1, flip=False, a=1.0):
    for j, row in enumerate(sprite):
        row = row[::-1] if flip else row
        for i, ch in enumerate(row):
            if ch in cmap:
                rect(cv, x + i * s, y + j * s, x + (i + 1) * s, y + (j + 1) * s, cmap[ch], a)

# ---------------- starfield ----------------
_sr = np.random.default_rng(42)
ST_X = _sr.integers(0, W, 220); ST_Y = _sr.integers(0, 430, 220)
ST_P = _sr.random(220) * 6.28; ST_R = 0.6 + _sr.random(220) * 2.2; ST_K = _sr.random(220)
def stars(cv, t, n=160, bright=1.0, tint=(0.8, 0.85, 1.0), fade_in=None, ymax=430):
    for i in range(n):
        if ST_Y[i] >= ymax: continue
        if fade_in is not None and ST_K[i] > fade_in: continue
        lv = int(((math.sin(t * ST_R[i] + ST_P[i]) + 1) / 2) * 3) / 2.0   # stepped twinkle
        b = (0.25 + 0.75 * lv) * bright
        c = np.asarray(tint, np.float32) * b
        if ST_K[i] > 0.93: c = np.asarray((1.0, 0.85, 0.5), np.float32) * b
        put_px(cv, ST_X[i], ST_Y[i], c)
        if ST_K[i] < 0.06 and lv >= 1:       # sparkle cross
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): put_px(cv, ST_X[i] + dx, ST_Y[i] + dy, c * 0.5)

# ---------------- galaxies ----------------
def make_galaxy(n, seed, arms=2, wind=2.6, noise=0.28):
    r = np.random.default_rng(seed)
    rr = r.random(n) ** 0.75
    th = (r.integers(0, arms, n) * 2 * math.pi / arms) + wind * np.log1p(rr * 5) + r.normal(0, noise, n) * (1.0 - 0.5 * rr)
    x = rr * np.cos(th); y = rr * np.sin(th)
    ell = r.normal(0, 0.45, (n, 2)) * (0.55 / (1 + 5 * rr))[:, None]    # bulge fuzz
    pts = np.stack([x, y], 1) + ell
    tgt = r.normal(0, 0.33, (n, 2)) * np.array([1.0, 0.7])
    return pts.astype(np.float32), rr.astype(np.float32), tgt.astype(np.float32)
GAL_A = make_galaxy(900, 11); GAL_B = make_galaxy(900, 12, arms=3, wind=2.2)
def draw_galaxy(cv, gal, cx, cy, size, ang, tilt, tint_core, tint_arm, merge=0.0, bright=1.0, rot_tgt=0.0, tgt_scale=1.0):
    pts, rr, tgt = gal
    c, s = math.cos(ang), math.sin(ang)
    x = pts[:, 0] * c - pts[:, 1] * s; y = pts[:, 0] * s + pts[:, 1] * c
    y = y * tilt
    if merge > 0:
        tx = tgt[:, 0] * tgt_scale; ty = tgt[:, 1] * tgt_scale
        x = lerp(x, tx, merge); y = lerp(y, ty, merge)
    px = (cx + x * size).astype(int); py = (cy + y * size).astype(int)
    f = np.clip(1 - rr * 0.85, 0.15, 1)[:, None] * bright
    cols = np.asarray(tint_arm, np.float32) * (1 - np.clip(1 - rr * 1.6, 0, 1))[:, None] + \
           np.asarray(tint_core, np.float32) * np.clip(1 - rr * 1.6, 0, 1)[:, None]
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    cv[py[ok], px[ok]] = np.maximum(cv[py[ok], px[ok]], (cols * f)[ok])
    glow(cv, cx, cy, size * 0.35, np.asarray(tint_core, np.float32) * 0.6 * bright, 1.0, 2.2)

# ---------------- sprites ----------------
DINO = [
"..............................XXXX..",
".............................XXXXXX.",
".............................XXoXXXX",
"..............................XXXXX.",
".............................XXX....",
"............................XXX.....",
"...........XXXXXXXXX.......XXX......",
".........XXXXXXXXXXXXX....XXX.......",
"......XXXXXXXXXXXXXXXXXX.XXX........",
"..XXXXXXXXXXXXXXXXXXXXXXXXX.........",
"XXXXXXXXXXXXXXXXXXXXXXXXXX..........",
"..XXXXXXXXXXXXXXXXXXXXXX............",
"....XX..XXX.....XXX..XX.............",
"....XX..XXX.....XXX..XX.............",
"....XX..XXX.....XXX..XX.............",
"....XXX.XXXX....XXXX.XXX............",
]
HUMAN = [
"..XX..",
".XXXX.",
".XXXX.",
"..XX..",
".XXXX.",
"X.XX.X",
"X.XX.X",
"..XX..",
".X..X.",
".X..X.",
"XX..XX",
]
FIRE = [[
"..r..",
".rOr.",
"rOYOr",
"rOYOr",
".rOr.",
], [
".r...",
".rOr.",
"rOYOr",
"rOYOr",
".rOr.",
]]
PALM = [
"..GG.GG..",
".GGGGGGG.",
"GG.GGG.GG",
"G..BBB..G",
"...BBB...",
"...BBB...",
"...BBB...",
"...BBB...",
]

# =====================================================================
# SCENES   (each draws into cv in 0..1 float RGB; ov = un-graded additive overlay applied last)
# =====================================================================
def scene1(cv, ov, t):
    # blinking pixel, then it shrinks
    blink = (t < 1.6 and int(t * 3) % 2 == 0) or (1.6 <= t < 2.4)
    if t < 2.4 or True:
        if t < 3.0:
            sz = 3 if t < 2.4 else (2 if t < 2.7 else 1)
            if blink or t > 2.4: rect(cv, 135 - sz // 2, 150, 135 - sz // 2 + sz, 150 + sz, (1.0, 0.85, 0.35))
            if blink and t < 2.4: glow(cv, 135, 151, 7, (0.9, 0.6, 0.15), 0.6, 2)
        elif t < 3.6:
            if int((t - 3.0) * 12) % 2 == 0: put_px(cv, 135, 150, (1.0, 0.85, 0.35), 0.8)
        else:
            put_px(cv, 135, 150, (1.0, 0.85, 0.35), 0.45)

def bigbang(cv, ov, tl, u):
    cx, cy = 135, 175
    r = 6 + 150 * (1 - (1 - u) ** 2.2)
    x0, x1, y0, y1 = 0, W, 0, 400
    d = np.sqrt((XX[y0:y1] - cx) ** 2 + (YY[y0:y1] - cy) ** 2) / max(r, 1)
    g = np.clip(1 - d, 0, 1)
    ramp = np.stack([np.clip(g * 2.2, 0, 1), np.clip(g * 1.7 - 0.25, 0, 1), np.clip(g * 1.9 - 0.8, 0, 1)], -1)
    cv[y0:y1] += ramp * (1.0 if u < 0.7 else 1.0 - (u - 0.7) / 0.3)
    flash = clamp01(1 - tl / 0.3) ** 2
    cv += flash * 0.9
    rng = np.random.default_rng(3)
    for k in range(70):
        a = rng.random() * 6.28; sp = 40 + rng.random() * 150
        rr = sp * (1 - (1 - u) ** 2)
        put_px(cv, cx + math.cos(a) * rr, cy + math.sin(a) * rr, (1, 0.9, 0.6) if k % 3 else (0.6, 0.8, 1))

def first_stars(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.02, 0.04, 0.16) , (0.0, 0.0, 0.03))
    rng = np.random.default_rng(8)
    for k in range(130):
        t0 = rng.random() * 0.45
        x, y = rng.integers(8, W - 8), rng.integers(10, 400)
        if tl > t0:
            a = min(1, (tl - t0) * 8)
            c = np.array((0.7, 0.85, 1.0) if k % 4 else (1.0, 0.85, 0.5), np.float32) * a
            put_px(cv, x, y, c)
            if k % 9 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): put_px(cv, x + dx, y + dy, c * .5)
                if tl - t0 < 0.15: glow(cv, x, y, 8, (0.6, 0.8, 1.0), 0.8, 2)

def galaxy_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.01, 0.01, 0.07), (0, 0, 0))
    stars(cv, tl, 70, 0.7)
    draw_galaxy(cv, GAL_A, 135, 170, 52 + 22 * u, 0.9 + tl * 1.6, 0.55, (1.0, 0.85, 0.5), (0.45, 0.65, 1.0))

def earth_tex_molten(t):
    def f(lon, lat, dx, dy, nz):
        n = tex(NZ_A, lon * 1.0 + t * 0.05, lat); n2 = tex(NZ_B, lon * 2 - t * 0.04, lat * 1.4)
        crack = np.abs(n - 0.5) < 0.07 + 0.03 * np.sin(t * 5)
        base = np.where((n2 > 0.5)[..., None], col(0.35, 0.07, 0.04), col(0.55, 0.12, 0.05))
        out = np.where(crack[..., None], col(1.0, 0.65, 0.12), base)
        return out
    return f
def earth_tex_blue(t, dry=0.0, red=0.0):
    def f(lon, lat, dx, dy, nz):
        n = tex(NZ_A, lon + t * 0.02, lat * 1.0)
        land = n > 0.52 - dry * 0.22
        ocean = np.asarray(lerp(col(0.12, 0.35, 0.85), col(0.45, 0.30, 0.15), dry), np.float32)
        ocean = ocean + (col(0.5, 0.1, 0.05) - ocean) * red
        grass = np.asarray(lerp(col(0.2, 0.65, 0.25), col(0.55, 0.38, 0.18), dry), np.float32)
        grass = grass + (col(0.4, 0.1, 0.05) - grass) * red
        out = np.where(land[..., None], grass, ocean)
        deep = tex(NZ_C, lon * 2, lat * 2)
        out = out * (0.85 + 0.3 * deep)[..., None]
        cl = tex(NZ_B, lon * 1.5 + t * 0.05, lat * 1.5) > 0.62 - dry * 0.3
        out = np.where(cl[..., None], out * (1 - 0.8 * (1 - dry)) + col(1, 1, 1) * 0.8 * (1 - dry), out)
        if red > 0:
            cr = (np.abs(tex(NZ_A, lon * 3, lat * 3) - 0.5) < 0.03) | (np.abs(tex(NZ_C, lon * 5, lat * 5) - 0.5) < 0.02)
            out = np.where(cr[..., None], col(0.12, 0.01, 0.0) * red + out * (1 - red), out)
        return out
    return f

def molten_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.05, 0.0, 0.0), (0.0, 0.0, 0.0))
    glow(cv, 135, 170, 120, (0.5, 0.12, 0.02), 0.8, 2)
    planet(cv, 135, 170, 62, earth_tex_molten(tl), rot=tl * 0.1, atmo=(0.6, 0.2, 0.0))
    rng = np.random.default_rng(5)
    for k in range(18):
        a = rng.random() * 6.28; sp = 20 + rng.random() * 30; ph = (tl * 0.9 + rng.random()) % 1
        put_px(cv, 135 + math.cos(a) * (62 + sp * ph), 170 + math.sin(a) * (62 + sp * ph), (1, 0.6, 0.15), 1 - ph)

def blue_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.0, 0.01, 0.08), (0, 0, 0))
    stars(cv, tl, 120, 0.8)
    glow(cv, 135, 170, 95, (0.1, 0.3, 0.7), 0.5, 2)
    planet(cv, 135, 170, 62, earth_tex_blue(tl), rot=tl * 0.12, atmo=(0.3, 0.55, 1.0))

def cells_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.02, 0.14, 0.2), (0.0, 0.05, 0.08))
    rng = np.random.default_rng(21)
    for k in range(60):                                      # drifting plankton specks
        put_px(cv, (rng.integers(0, W) + tl * 6 * (1 + k % 3)) % W, rng.integers(0, 430), (0.2, 0.5, 0.5), 0.5)
    for k in range(9):
        bx = 40 + rng.random() * 190; by = 70 + rng.random() * 220; r0 = 9 + rng.random() * 9
        ph = rng.random() * 6.28
        x = bx + 8 * math.sin(tl * 1.2 + ph); y = by + 8 * math.cos(tl * 0.9 + ph)
        divide = (k == 0)
        if divide:
            s = smooth(tl / 0.8) * 7
            for sg in (-1, 1): _cell(cv, x + sg * s, y, r0 * (0.8 + 0.2 * (1 - smooth(tl / 0.8))))
        else: _cell(cv, x, y, r0)
def _cell(cv, x, y, r):
    flat_disc(cv, x, y, r, (0.15, 0.55, 0.3)); flat_disc(cv, x, y, r - 2, (0.3, 0.8, 0.45))
    flat_disc(cv, x - r * 0.1, y, r * 0.35, (0.85, 0.8, 0.3)); put_px(cv, x - r * 0.45, y - r * 0.45, (0.9, 1, 0.9))

def sky_dusk(cv, tl, tint=0.0):
    vgrad(cv, 0, 300, (0.95 - tint * .3, 0.45 - tint * .2, 0.25), (1.0, 0.85, 0.5))
    flat_disc(cv, 215, 70, 14, (1.0, 0.95, 0.7)); glow(cv, 215, 70, 60, (1, 0.6, 0.2), 0.5, 2)
    rect(cv, 0, 300, W, 430, (0.2, 0.45, 0.15)); rect(cv, 0, 300, W, 304, (0.35, 0.65, 0.2))
    vgrad(cv, 304, 430, (0.2, 0.45, 0.15), (0.08, 0.2, 0.08))
def dino_v(cv, ov, tl, u):
    sky_dusk(cv, tl)
    stamp(cv, PALM, {"G": (0.1, 0.5, 0.15), "B": (0.4, 0.25, 0.1)}, 20, 220, 6)
    stamp(cv, PALM, {"G": (0.1, 0.5, 0.15), "B": (0.4, 0.25, 0.1)}, 205, 240, 5)
    dx = 30 + 18 * tl
    stamp(cv, DINO, {"X": (0.35, 0.5, 0.3), "o": (0.05, 0.05, 0.05)}, dx, 225, 4)
    stamp(cv, DINO, {"X": (0.3, 0.4, 0.5), "o": (0.05, 0.05, 0.05)}, dx + 90, 258, 3, flip=False)
def asteroid_v(cv, ov, tl, u):
    sky_dusk(cv, tl)
    stamp(cv, PALM, {"G": (0.1, 0.5, 0.15), "B": (0.4, 0.25, 0.1)}, 20, 220, 6)
    stamp(cv, DINO, {"X": (0.35, 0.5, 0.3), "o": (0.05, 0.05, 0.05)}, 66, 225, 4)
    f = clamp01(tl / 0.45)
    x = lerp(20, 140, f); y = lerp(-10, 300, f)
    for k in range(40):
        q = k / 40; put_px(cv, x - 30 * q * 0.6, y - 30 * q, (1.0, 0.7 - 0.5 * q, 0.2 * (1 - q)), 1 - q)
        put_px(cv, x - 30 * q * 0.6 + 1, y - 30 * q, (1.0, 0.9 - 0.5 * q, 0.3), 1 - q)
    flat_disc(cv, x, y, 5, (1, 0.95, 0.7)); glow(cv, x, y, 20, (1, 0.5, 0.1), 1, 2)
    if tl > 0.45:
        q = (tl - 0.45) / 0.25
        cv += clamp01(1 - q * 1.2) * 0.8
        glow(cv, 140, 300, 40 + 160 * q, (1, 0.55, 0.15), 1.2 * (1 - 0.6 * q), 1.5)
        ring(cv, 140, 300, 20 + 150 * q, 24 + 150 * q, (1, 0.9, 0.6), 1 - q * 0.7)
def human_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.02, 0.02, 0.12), (0.06, 0.04, 0.12))
    stars(cv, tl, 130, 0.9)
    flat_disc(cv, 60, 70, 10, (0.9, 0.9, 0.8)); flat_disc(cv, 64, 67, 9, (0.03, 0.03, 0.12))
    rect(cv, 0, 300, W, 430, (0.06, 0.07, 0.1)); rect(cv, 0, 300, 160, 304, (0.07, 0.08, 0.12))
    fl = 0.7 + 0.3 * math.sin(tl * 25)
    glow(cv, 135, 300, 90, (1.0, 0.45, 0.1), 0.6 * fl, 2)
    stamp(cv, HUMAN, {"X": (0.04, 0.04, 0.06)}, 100, 276, 4)
    cmap = {"r": (0.9, 0.2, 0.05), "O": (1.0, 0.55, 0.1), "Y": (1.0, 0.95, 0.4)}
    stamp(cv, FIRE[int(tl * 10) % 2], cmap, 126, 280, 5)
    for k in range(10):
        ph = (tl * 0.8 + k * 0.173) % 1
        put_px(cv, 140 + math.sin(k * 3 + tl * 2) * 10 * ph, 285 - ph * 60, (1, 0.7, 0.2), 1 - ph)
def city_v(cv, ov, tl, u):
    vgrad(cv, 0, 430, (0.02, 0.02, 0.1), (0.2, 0.08, 0.15))
    stars(cv, tl, 70, 0.6, ymax=200)
    rng = np.random.default_rng(31)
    x = 0
    while x < W:
        w = int(rng.integers(14, 30)); h = int(rng.integers(50, 190))
        rect(cv, x, 330 - h, x + w, 400, (0.05, 0.05, 0.12))
        for wy in range(330 - h + 6, 396, 8):
            for wx in range(x + 3, x + w - 3, 6):
                if rng.random() < 0.55 and (int(tl * 3 + wx * 7 + wy) % 11 != 0):
                    put_px(cv, wx, wy, (1.0, 0.82, 0.35)); put_px(cv, wx + 1, wy, (1.0, 0.82, 0.35))
        x += w + int(rng.integers(0, 4))
    glow(cv, 135, 400, 200, (1.0, 0.5, 0.2), 0.35, 2)
    rect(cv, 0, 400, W, 430, (0.02, 0.02, 0.05))

VIGS = [bigbang, first_stars, galaxy_v, molten_v, blue_v, cells_v, dino_v, asteroid_v, human_v, city_v]
def scene2(cv, ov, t):
    for i in range(10):
        a, b = spec.VIGN[i], spec.VIGN[i + 1]
        if a <= t < b:
            VIGS[i](cv, ov, t - a, (t - a) / (b - a))
            # glitchy wipe between vignettes
            if t - a < 0.08 and i > 0: cv[(int(t * 99) % 6)::6] *= 0.3
            return

# ---- Scene 3: humanity's clock ----
_cr = np.random.default_rng(77)
def _city_points(n=170):
    pts = []
    while len(pts) < n:
        dx, dy = _cr.uniform(-1, 1, 2)
        if dx * dx + dy * dy < 0.93:
            lon = math.atan2(dx, math.sqrt(1 - dx * dx - dy * dy)) / (2 * math.pi)
            lat = math.asin(dy) / math.pi + 0.5
            if tex(NZ_A, np.array([lon]), np.array([lat]))[0] > 0.5: pts.append((dx, dy))
    return np.array(pts)
CITY_PTS = _city_points()
CITY_OFF = np.sort(13.0 + 3.7 * _cr.random(len(CITY_PTS)) ** 0.7)
def scene3(cv, ov, t):
    tl = t - 12.0
    vgrad(cv, 0, 430, (0.0, 0.0, 0.05), (0, 0, 0))
    stars(cv, t, 110, 0.7)
    def night(lon, lat, dx, dy, nz):
        n = tex(NZ_A, lon, lat)
        return np.where((n > 0.5)[..., None], col(0.16, 0.20, 0.36), col(0.07, 0.11, 0.30)) * np.ones_like(dx)[..., None]
    cx, cy, R = 135, 165, 70
    planet(cv, cx, cy, R, night, light=(0.7, -0.3), amb=0.75, atmo=(0.12, 0.25, 0.7))
    for (dx, dy), off in zip(CITY_PTS, CITY_OFF):
        if t < off - 0.35: b = 1.0
        elif t < off + 0.0: b = 1.0 if int(t * 14 + dx * 9) % 2 == 0 else 0.0     # flicker out
        else: b = 0.0
        if off > 16.1 and b == 0.0 and (dx * 17 % 1) < 0.6: b = 0.28 + 0.2 * math.sin(t * 2 + dx * 20)   # lingering, uncertain
        if b > 0:
            c = (1.0, 0.8, 0.35) if (dx * 13 % 1) < 0.8 else (0.8, 0.9, 1.0)
            px_, py_ = cx + dx * R * 0.97, cy + dy * R * 0.97
            put_px(cv, px_, py_, np.asarray(c) * b)
            if b > 0.5: put_px(cv, px_ + 1, py_, np.asarray(c) * b * 0.8); put_px(cv, px_, py_ + 1, np.asarray(c) * b * 0.55)

# ---- Scene 4: earth's end ----
def scene4(cv, ov, t):
    tl = t - 17.0
    stars_b = 1 - smooth((t - 20.5) / 1.2)
    vgrad(cv, 0, 430, (0.0, 0.0, 0.05), (0, 0, 0))
    if stars_b > 0: stars(cv, t, 100, 0.8 * stars_b)
    # sun parameters
    c0 = np.array([48.0, 78.0]); c1 = np.array([135.0, 165.0])
    mv = smooth((t - 21.2) / 1.6)
    sx, sy = (c0 + (c1 - c0) * mv)
    if t < 19.4: r = 26 + 7 * smooth(tl / 2.4)
    elif t < 22.5: r = 33 + 460 * smooth((t - 19.4) / 3.0) ** 1.6
    elif t < 23.25: r = 493 * (1 - smooth((t - 22.5) / 0.75)) ** 1.4 + 3
    else: r = 3 - (1 if t > 23.8 else 0)
    # earth
    ex, ey, er = 168, 270, 46
    dist = math.hypot(sx - ex, sy - ey)
    engulfed = r > dist + er
    boil = smooth((t - 17.4) / 1.2) * (1 - smooth((t - 19.6) / 0.6))
    dry = smooth((t - 18.2) / 1.4); red = smooth((t - 19.3) / 1.3)
    sun_c = tuple(lerp(np.array([1.0, 0.85, 0.3]), np.array([1.0, 0.98, 0.85]), smooth(tl / 2.2)))
    if t < 22.5 and not engulfed:
        L = ((sx - ex) / dist, (sy - ey) / dist)
        planet(cv, ex, ey, er, earth_tex_blue(t, dry, red), light=(L[0] * .8, L[1] * .8), amb=0.12, rot=t * 0.05,
               atmo=tuple(col(0.3, 0.5, 1.0) * (1 - dry) + col(0.7, 0.3, 0.1) * dry))
        rng = np.random.default_rng(9)
        for k in range(80):                       # steam
            if boil <= 0.02: break
            if rng.random() > boil: continue
            a = rng.random() * 6.28; ph = (t * 0.7 + rng.random()) % 1
            put_px(cv, ex + math.cos(a) * er * 0.9 + math.sin(t * 3 + k) * 3, ey + math.sin(a) * er * 0.9 - ph * 40, (1, 1, 1), 1 - ph)
    # sun body
    if r > 2.5 or t < 23.8:
        warm = smooth((t - 19.4) / 1.3)
        base = np.asarray(sun_c, np.float32) * (1 - warm) + col(1.0, 0.32, 0.1) * warm
        if t > 22.5: base = base * (1 - smooth((t - 22.5) / 0.7)) + col(1, 0.95, 0.9) * smooth((t - 22.5) / 0.7)
        def surf(lon, lat, dx, dy, nz):
            n = tex(NZ_A, lon * 2 + t * 0.15, lat * 2)
            return base * (0.7 + 0.5 * n)[..., None] * np.ones((1, 1, 3), np.float32)
        glow(cv, sx, sy, min(r * 1.5 + 20, 700), base * 0.5, 0.7, 2)
        if r > 0:
            rr = min(r, 700)
            x0, x1, y0, y1 = 0, W, 0, H
            d = np.sqrt((XX - sx) ** 2 + (YY - sy) ** 2)
            m = d <= rr
            n = tex(NZ_A, (XX - sx) / 120 + t * 0.1, (YY - sy) / 120)
            lim = (0.65 + 0.35 * np.clip(1 - (d / max(rr, 1)) ** 3, 0, 1))
            cv[m] = (base * (0.62 + 0.55 * n[..., None]) * lim[..., None])[m]
    # nebula shell + white dwarf
    if t >= 22.9:
        q = (t - 22.9) / 1.1
        ring(cv, c1[0], c1[1], 5 + 130 * q ** 0.7, 8 + 130 * q ** 0.7, (1.0, 0.4, 0.15), clamp01(1 - q))
        if q > 0.15: flat_disc(cv, c1[0], c1[1], 2, (1, 1, 1)); glow(cv, c1[0], c1[1], 10, (0.7, 0.8, 1.0), 0.9, 2)

# ---- Scene 5: milky way + andromeda ----
_ar = np.random.default_rng(50)
BG_GAL = [(_ar.integers(10, W - 10), _ar.integers(20, 320), 2 + _ar.random() * 3, _ar.random() * 3) for _ in range(16)]
def scene5(cv, ov, t):
    tl = t - 24.0
    vgrad(cv, 0, 430, (0.02, 0.0, 0.07), (0, 0, 0))
    stars(cv, t, 50, 0.4)
    esc = smooth((t - 28.2) / 2.6)
    for i, (x, y, r, ph) in enumerate(BG_GAL):
        dx, dy = x - 135, y - 170
        k = 1 + 9 * esc ** 2.2
        px, py = 135 + dx * k, 170 + dy * k
        a = 1 - smooth((esc - 0.15) / 0.8)
        if a <= 0: continue
        redsh = esc
        c = np.asarray((1 - 0.4 * redsh, 0.75 - 0.5 * redsh, 0.8 - 0.65 * redsh), np.float32) * a
        c = np.clip(c * 1.5, 0, 1)
        for ox in range(-2, 3):
            for oy in range(-1, 2):
                if abs(ox) + 2 * abs(oy) <= 3: put_px(cv, px + ox, py + oy, c * (1.0 if abs(ox) + abs(oy) < 2 else 0.5))
        glow(cv, px, py, 7, c * 0.5, 0.6, 2)
    f = smooth((t - 24.6) / 3.2)               # approach
    mg = smooth((t - 27.0) / 2.8)               # merge into blob
    ax, ay = lerp(70, 135, f), lerp(110, 165, f)
    bx, by = lerp(205, 135, f), lerp(235, 165, f)
    size = 50 - 6 * mg
    draw_galaxy(cv, GAL_A, ax, ay, size, 0.5 + tl * 0.7, 0.55, (1.0, 0.85, 0.6), (0.4, 0.6, 1.0), merge=mg, bright=1.0, tgt_scale=1.7)
    draw_galaxy(cv, GAL_B, bx, by, size, -0.8 - tl * 0.6, 0.6, (1.0, 0.7, 0.7), (0.9, 0.5, 0.9), merge=mg, bright=1.0, tgt_scale=1.9)
    if mg > 0.8: glow(cv, 135, 165, 55, (0.9, 0.55, 0.35), 0.5 * smooth((mg - 0.8) / 0.2), 2)
    if t < 28.0:
        a = 1 - smooth((t - 26.2) / 1.2)
        ov_text.append((int(ax), int(ay + 42), "MILKY WAY", F_XS, (0.5, 0.7, 1.0), a))
        ov_text.append((int(bx), int(by + 40), "ANDROMEDA", F_XS, (0.9, 0.55, 0.9), a))

# ---- Scene 6: last stars ----
_dr = np.random.default_rng(61)
DW = [(float(_dr.normal(135, 62)), float(_dr.normal(190, 85)), int(_dr.integers(1, 3))) for _ in range(spec.N_DWARFS)]
DW = [(min(max(x, 14), W - 14), min(max(y, 40), 400), s) for x, y, s in DW]
order = _dr.permutation(spec.N_DWARFS)
def scene6(cv, ov, t):
    tl = t - 31.0
    # collapse of everything before into one pixel
    if tl < 0.9:
        z = 0.5 ** (tl * 9)                          # violent zoom out
        prev = np.zeros_like(cv); s5_end = []
        scene5(prev, [], 30.99) if False else _render_prev(prev)
        zw, zh = max(1, int(W * z)), max(1, int(H * z))
        img = Image.fromarray((np.clip(prev, 0, 1) * 255).astype(np.uint8)).resize((zw, zh), Image.NEAREST)
        a = np.asarray(img, np.float32) / 255
        x0, y0 = 135 - zw // 2, 165 - zh // 2
        for yy in range(zh):
            for xx in range(zw):
                put_px(cv, x0 + xx, y0 + yy, a[yy, xx])
        if zw <= 2: put_px(cv, 135, 165, (1.0, 0.7, 0.5))
        for k in range(6):                            # speed streaks
            yy = (int(t * 800) * (k + 3)) % 400; rect(cv, 0, yy, W, yy + 1, (0.4, 0.2, 0.5), 0.35 * (1 - tl / .9))
    else:
        put_px(cv, 135, 165, (1, 0.7, 0.5), clamp01(1 - (tl - 0.9) / 1.0) * 0.8)
    vgrad(cv, 0, 430, (0.05, 0.0, 0.04) * 1, (0, 0, 0)) if tl > 0.6 else None
    if tl > 0.9: cv[:430] = np.maximum(cv[:430], 0)
    # red dwarfs
    for rank, idx in enumerate(order):
        x, y, s = DW[idx]; tw = spec.WINKS[rank]
        vis_in = smooth((t - 31.6 - (idx % 7) * 0.05) / 0.5)
        if vis_in <= 0 or t > tw + 0.02: continue
        b = vis_in
        if t > tw - 0.3 and int((t - tw) * 28 + idx) % 2 == 0: b *= 0.15      # dying LED flicker
        b *= 0.75 + 0.25 * math.sin(t * 1.5 + idx)
        c = np.array([1.0, 0.3, 0.2], np.float32) * b
        glow(cv, x, y, 13 + 4 * s, c * 0.9, 1, 1.6)
        rect(cv, x - 1, y - 1, x + s + 1, y + s + 1, np.array([1.0, 0.75, 0.55]) * b)
        # cardboard-like diffraction in nearest ones
    # faint embers where dwarfs died
    for rank, idx in enumerate(order):
        x, y, s = DW[idx]
        if t > spec.WINKS[rank] + 0.05: put_px(cv, x, y, (0.18, 0.04, 0.08), 0.8)

_prev_cache = {}
def _render_prev(buf):
    key = "p"
    if key not in _prev_cache:
        c = np.zeros((H, W, 3), np.float32); global ov_text
        save = ov_text[:]; ov_text.clear()
        scene5(c, [], 30.99)
        c = grade(c, 30.99); c = quantize(c)
        ov_text[:] = save
        _prev_cache[key] = c
    buf[:] = _prev_cache[key]

# ---- Scene 7: degenerate era ----
_gr = np.random.default_rng(72)
N7 = 760
th7 = _gr.random(N7) * 6.28; rad7 = _gr.random(N7) ** 0.6
G7_X = np.cos(th7) * rad7 * 105; G7_Y = np.sin(th7) * rad7 * 66
G7_KIND = _gr.choice(3, N7, p=[0.62, 0.17, 0.21])     # 0 white->black dwarf, 1 neutron star, 2 rogue planet
G7_FLING = np.sort(38.7 + 4.4 * _gr.random(N7) ** 1.3)[_gr.permutation(N7)]
G7_ANG = np.arctan2(G7_Y + 1e-3, G7_X + 1e-3) + _gr.normal(0, 0.4, N7)
G7_SP = 25 + 60 * _gr.random(N7)
G7_DISS = 43.0 + 2.0 * _gr.random(N7)
def scene7(cv, ov, t):
    tl = t - 38.0
    fi = smooth(tl / 1.0)
    stars(cv, t, 30, 0.2 * (1 - smooth((t - 41) / 2)))
    cx, cy = 135, 170
    glow(cv, cx, cy, 90, (0.3, 0.1, 0.35), 0.18 * fi * (1 - smooth((t - 42) / 2.5)), 2)
    fade = 1 - 0.55 * smooth(tl / 6)       # white dwarfs cooling
    for i in range(N7):
        x, y = cx + G7_X[i], cy + G7_Y[i]
        tf = G7_FLING[i]
        if t > tf:
            d = (t - tf) ** 1.6 * G7_SP[i]
            x += math.cos(G7_ANG[i]) * d; y += math.sin(G7_ANG[i]) * d * 1.2
        if not (-4 < x < W + 4 and -4 < y < 430): continue
        if t > G7_DISS[i] and t > 43.0:
            ph = (t - G7_DISS[i]) / 0.5
            if ph > 1 or int(t * 30 + i) % 2: continue
        k = G7_KIND[i]
        if k == 0:
            b = (1.0 if i % 5 == 0 else 0.75) * fade * fi
            put_px(cv, x, y, (0.85 * b, 0.9 * b, 1.0 * b))
            if i % 5 == 0: put_px(cv, x + 1, y, (0.6 * b, 0.65 * b, 0.8 * b))
        elif k == 1:
            p = 0.5 + 0.5 * math.sin(t * 9 + i)
            put_px(cv, x, y, np.array((0.5, 0.9, 1.0)) * (0.4 + 0.6 * p) * fi)
            if p > 0.8: put_px(cv, x + 1, y, (0.4, 0.7, 0.9)); put_px(cv, x - 1, y, (0.4, 0.7, 0.9))
        else:
            x2, y2 = x + math.sin(t * 0.5 + i) * 3, y + t * 0.8 % 3
            rect(cv, x2, y2, x2 + 2, y2 + 2, np.array((0.5, 0.3, 0.2)) * 0.7 * fi)
    # static: matter dissolving (hypothetical)
    if t > 42.8:
        dens = smooth((t - 42.8) / 1.2) * (1 - smooth((t - 44.0) / 1.0))
        rng = np.random.default_rng(int(t * 24))
        n = int(2200 * dens)
        px = rng.integers(0, W, n); py = rng.integers(0, 430, n)
        v = rng.random(n)[:, None] * np.array([0.8, 0.8, 0.9])[None]
        m = ((px - 135) ** 2 / 130 ** 2 + (py - 170) ** 2 / 190 ** 2) < 1
        cv[py[m], px[m]] = np.maximum(cv[py[m], px[m]], v[m])

# ---- Scene 8: black hole era ----
BH = [(95, 135, 34.0), (190, 255, 21.0), (80, 330, 13.0)]
def scene8(cv, ov, t):
    stars(cv, t, 12, 0.12 * (1 - smooth((t - 45) / 1)))
    for i, (x, y, r0) in enumerate(BH):
        tp = spec.BH_POPS[i]
        if t >= tp + 0.55: continue
        if t < tp:
            life = clamp01((t - spec.BH_START) / (tp - spec.BH_START))
            r = r0 * (1 - life) ** (1 / 3) + 0.0
            hot = 0.35 + 0.65 * life
            rng = np.random.default_rng(int(t * 24) * 7 + i)
            rim = (0.85, 0.35, 0.9)
            for k in range(int(26 + 40 * r / r0 * 0.6)):
                a = rng.random() * 6.28
                put_px(cv, x + math.cos(a) * (r + 1.5 + rng.random() * 2), y + math.sin(a) * (r + 1.5 + rng.random() * 2),
                       np.asarray(rim, np.float32) * (0.35 + 0.65 * rng.random()) * hot)
            ring(cv, x, y, r + 0.5, r + 1.6, np.array([0.5, 0.2, 0.6]) * (0.4 + 0.3 * math.sin(t * 3 + i)))
            flat_disc(cv, x, y, r, (0, 0, 0))
            for k in range(int(3 + 14 * life)):         # Hawking radiation pixels drifting out
                a = rng.random() * 6.28; ph = (t * 0.6 + rng.random()) % 1
                put_px(cv, x + math.cos(a) * (r + 4 + ph * 22), y + math.sin(a) * (r + 4 + ph * 22), (0.9, 0.7, 1.0), (1 - ph) * 0.9)
        else:
            q = (t - tp) / 0.55
            big = (i == 0)
            R = (10 + 70 * q) * (3 if big else 1)
            flat_disc(cv, x, y, max(1, R * (1 - q) ** 0.5), (1, 1, 1), 1 - q)
            ring(cv, x, y, R, R + 2, (1.0, 0.8, 1.0), 1 - q)
            rng = np.random.default_rng(i + 100)
            for k in range(40):
                a = rng.random() * 6.28; sp = 30 + rng.random() * 70
                put_px(cv, x + math.cos(a) * sp * q * (2 if big else 1), y + math.sin(a) * sp * q * (2 if big else 1), (1, .85, 1), 1 - q)
            if big: ov += 0     # flash handled below
    big_t = spec.BH_POPS[0]
# NOTE: BH list index 0 is the biggest hole but spec.BH_POPS[2] is the final pop -> order below maps big hole to last pop
BH = [(95, 135, 34.0), (190, 255, 21.0), (80, 330, 13.0)]
BH_POP_FOR = [spec.BH_POPS[2], spec.BH_POPS[1], spec.BH_POPS[0]]

# ---- Scene 9: heat death ----
_dim = np.random.default_rng(90)
DIM = [(int(_dim.integers(12, W - 12)), int(_dim.integers(20, 400)), 0.11 + 0.1 * _dim.random()) for _ in range(5)]
def scene9(cv, ov, t):
    lp0, lp1 = spec.LAST_PIXEL
    # persistent barely-there pixels
    for i, (x, y, b) in enumerate(DIM):
        fade = 1 - smooth((t - 58.5 - i * 0.5) / 1.0) if t > 58.5 else 1
        if t >= lp0 + 0.4 + i * 0.1:
            ov_px.append((x, y, b * fade * (0.7 + 0.3 * math.sin(t * 0.7 + i))))
    # the last pixel
    if t < lp1:
        q = (t - lp0) / (lp1 - lp0)
        on = (q < 0.5 and int(t * 8) % 3 != 0) or (0.5 <= q < 0.8 and int(t * 5) % 3 == 0) or (q < 0.15)
        a = (1 - q) ** 1.5
        if on and t >= lp0 - 0.4: ov_px.append((135, 215, 0.95 * a + 0.05))
        elif t >= lp0 - 0.4: ov_px.append((135, 215, 0.12 * a))
    elif t < lp1 + 0.8:
        ov_px.append((135, 215, 0.10 * (1 - (t - lp1) / 0.8)))

SCENE_FN = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9]

# =====================================================================
# GRADE: palette drains warm -> red -> purple -> black
# =====================================================================
RAMP_KF = [  # t, mid, hi, brightness
    (0, (0, 0, 0), (0, 0, 0), 1.0),
    (31.0, (0.45, 0.08, 0.16), (1.0, 0.45, 0.3), 1.0),
    (37.9, (0.40, 0.05, 0.14), (1.0, 0.40, 0.28), 0.95),
    (39.0, (0.22, 0.07, 0.36), (0.75, 0.55, 0.95), 0.9),
    (44.9, (0.20, 0.06, 0.32), (0.75, 0.5, 0.95), 0.85),
    (46.0, (0.14, 0.04, 0.2), (0.6, 0.35, 0.75), 0.75),
    (52.9, (0.12, 0.03, 0.16), (0.55, 0.3, 0.7), 0.7),
    (54.5, (0.08, 0.03, 0.1), (0.4, 0.3, 0.5), 0.6),
    (64, (0.06, 0.03, 0.08), (0.3, 0.25, 0.4), 0.5),
]
def grade(cv, t):
    duo = smooth((t - 27.0) / 4.0) if t < 31 else 1.0           # drain colour over the tail of act IV
    # slow global warmth loss from Act III on
    if t >= 12:
        w = smooth((t - 17) / 14.0) * 0.35
        lum = (cv * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1, keepdims=True)
        cv = cv * (1 - w) + (lum * np.array([1.0, 0.75, 0.8], np.float32)) * w
    if duo <= 0: return cv
    lum = np.clip((cv * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1), 0, 1.6)[..., None]
    ts = [k[0] for k in RAMP_KF]; tt = max(t, 31.0)
    mid = np.array([np.interp(tt, ts, [k[1][c] for k in RAMP_KF]) for c in range(3)], np.float32)
    hi = np.array([np.interp(tt, ts, [k[2][c] for k in RAMP_KF]) for c in range(3)], np.float32)
    br = float(np.interp(tt, ts, [k[3] for k in RAMP_KF]))
    l1 = np.clip(lum * 2, 0, 1); l2 = np.clip(lum * 2 - 1, 0, 1)
    ramp = (mid * l1) * (1 - l2) + (mid * (1 - l2) + hi * l2) * l2 * 1.0
    ramp = np.where(lum < 0.5, mid * (lum * 2), mid + (hi - mid) * np.clip(lum * 2 - 1, 0, 1))
    return (cv * (1 - duo) + ramp * duo) * br

def quantize(cv):
    n = LEVELS - 1
    return np.clip(np.floor(np.clip(cv, 0, 1) * n + 0.5 + BAYER_T[..., None] * 0.95), 0, n) / n

# =====================================================================
# HUD: timeline bar, counter, text
# =====================================================================

_FC = {}
def font_sz(n):
    if n not in _FC: _FC[n] = ImageFont.truetype(FONT_B, n)
    return _FC[n]
SUPMAP = {c: str(i) for i, c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")}; SUPMAP["⁻"] = "-"; SUPMAP["⁺"] = "+"
def text_sci(d, xy, s, font, fill, anchor="la", shadow=False):
    """draw text where unicode superscripts become real raised small digits"""
    x, y = xy; base = font.size; sf = font_sz(max(6, int(base * 0.7)))
    runs = []
    for ch in s:
        is_sup = ch in SUPMAP
        ch2 = SUPMAP.get(ch, ch)
        if runs and runs[-1][0] == is_sup: runs[-1][1] += ch2
        else: runs.append([is_sup, ch2])
    wid = sum(d.textlength(t, font=sf if sp else font) for sp, t in runs)
    if anchor[0] == "m": x -= wid / 2
    elif anchor[0] == "r": x -= wid
    cx = x
    for sp, t in runs:
        f = sf if sp else font
        yy = y - (int(base * 0.4) if sp else 0)
        if shadow: d.text((cx + 1, yy + 1), t, font=f, fill=(0, 0, 0), anchor="l" + anchor[1])
        d.text((cx, yy), t, font=f, fill=fill, anchor="l" + anchor[1])
        cx += d.textlength(t, font=f)

ov_text = []; ov_px = []; ov_rgb = []
def wrap(s, n):
    words = s.split(" "); lines = []; cur = ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > n: lines.append(cur); cur = w
        else: cur = (cur + " " + w) if cur else w
    return lines + [cur]
def hud_ink(t):
    """text colour drains with the universe"""
    f = smooth((t - 17) / 20.0); g = smooth((t - 38) / 12.0)
    a = np.array([1.0, 0.92, 0.7]); b = np.array([0.95, 0.5, 0.45]); c = np.array([0.6, 0.45, 0.75])
    base = a * (1 - f) + b * f
    base = base * (1 - g) + c * g
    return base * (1 - 0.35 * smooth((t - 50) / 6))
# text items: (t0, t1, kind, text, y, align, cps)
TXT = [
    (0.3, 2.45, "big", "Everything that has ever happened…", 208, "mid", 28),
    (2.7, 4.0, "big", "…is the first 0.000…001% of the universe's life.", 208, "mid", 40),
    (4.05, 12.0, "lab", "Big Bang: 13.8 billion years ago", 345, "left", 60),
    (6.15, 12.0, "lab", "Earth forms: 4.5 billion years ago", 360, "left", 60),
    (7.75, 12.0, "lab", "First life: ~3.8 billion years ago", 375, "left", 60),
    (9.45, 12.0, "lab", "Dinosaurs die: 66 million years ago", 390, "left", 60),
    (10.15, 12.0, "lab", "Humans appear: ~300,000 years ago", 405, "left", 60),
    (12.3, 17.0, "big", "How long do humans last?", 335, "top", 30),
    (13.4, 17.0, "big", "Nobody knows.", 354, "top", 22),
    (14.5, 17.0, "lab", "Most species last ~1–10 million years.", 384, "top", 45),
    (17.3, 19.7, "lab", "~1 billion years: Sun brightens, oceans evaporate", 355, "top", 45),
    (19.8, 22.5, "lab", "~5 billion years: Sun becomes a red giant", 355, "top", 45),
    (22.9, 24.0, "lab", "~7–8 billion years: Sun becomes a white dwarf", 355, "top", 45),
    (24.4, 28.7, "lab", "Andromeda may collide with us — recent models put it around a coin flip within 10 billion years.", 345, "top", 60),
    (28.9, 31.0, "lab", "~100+ billion years: all other galaxies vanish past our horizon.", 345, "top", 60),
    (32.0, 34.9, "lab", "Up to ~10 trillion years: the longest-lived red dwarfs burn out", 350, "top", 45),
    (35.0, 38.0, "lab", "~100 trillion years: no new stars form", 350, "top", 45),
    (38.4, 42.2, "lab", "~10¹⁹–10²⁰ years: dead galaxies evaporate as stars are flung away", 350, "top", 45),
    (42.3, 45.0, "lab", "10³⁴+ years: protons may decay (if they decay at all)", 350, "top", 45),
    (45.3, 49.5, "big", "Black holes slowly evaporate…", 345, "top", 24),
    (49.8, 53.0, "lab", "~10¹⁰⁰ years: the largest black holes vanish", 375, "top", 45),
    (56.4, 62.0, "big", "No light. No heat. No change.", 150, "mid", 11),
    (58.4, 62.0, "big", "Maximum entropy.", 175, "mid", 10),
    (60.0, 62.0, "big", "And all of human history happened in the first instant.", 250, "mid", 13),
    (62.35, 64.0, "end", spec.CHANNEL, 205, "mid", 40),
    (62.8, 64.0, "lab", "Follow for more cosmic scale.", 232, "mid", 40),
]
def text_alpha(t, t1):
    return 1.0 - smooth((t - (t1 - 0.3)) / 0.3) if t1 < 62.2 or True else 1.0
def draw_texts(img, d, t):
    ink = hud_ink(t)
    for (t0, t1, kind, s, y, al, cps) in TXT:
        if not (t0 <= t < t1): continue
        n = int((t - t0) * cps) + 1
        sp = max(0, 1 - smooth((t - (t1 - 0.25)) / 0.25)) if t1 < 62.2 else (1 if t < 63.7 else 1 - (t - 63.7) / 0.3)
        font = F_BIG if kind == "big" else (F_END if kind == "end" else F_SM)
        width = 30 if kind == "big" else (22 if kind == "end" else 38)
        full = wrap(s, width)
        shown = s[:n]
        # reveal the full wrapped layout char-by-char
        lines = []; rem = n
        for ln in full:
            lines.append(ln[:max(0, rem)]); rem -= len(ln) + 1
        lh = 17 if kind == "big" else (20 if kind == "end" else 13)
        y0 = y - (len(full) * lh // 2 if al == "mid" else 0)
        c = ink * sp
        if kind == "end": c = np.array([0.85, 0.75, 0.95]) * sp
        for j, ln in enumerate(lines):
            if not ln: continue
            if al == "left": x = 10; anchor = "la"
            else: x = W // 2; anchor = "ma"
            col_i = tuple(int(255 * v) for v in np.clip(c, 0, 1))
            text_sci(d, (x, y0 + j * lh), ln, font, col_i, anchor, shadow=True)
    if 42.4 < t < 45.0 and int(t * 3) % 2 == 0:
        d.text((W // 2, 332), "[ HYPOTHETICAL ]", font=F_XS, fill=(170, 140, 220), anchor="ma")
    for (x, y, s, f, c, a) in ov_text:
        if a <= 0: continue
        ci = tuple(int(255 * v * a) for v in c)
        d.text((x, y), s, font=f, fill=ci, anchor="ma")

def draw_hud(cv, img_fn, t):
    """timeline bar + counter drawn on top of the quantised frame. Returns PIL image."""
    # bar background strip
    rect(cv, 0, 426, W, H, (0, 0, 0), 0.82)
    sl = spec.span_log(t)
    bar_x0, bar_x1, by0, by1 = 10, W - 10, 434, 444
    ink = hud_ink(t); fade = 1.0 - 0.5 * smooth((t - 56) / 4)
    if t >= 62.3: fade = 0.0
    edge = np.clip(ink * 0.55 * fade, 0, 1)
    rect(cv, bar_x0 - 1, by0 - 1, bar_x1 + 1, by0, edge); rect(cv, bar_x0 - 1, by1, bar_x1 + 1, by1 + 1, edge)
    rect(cv, bar_x0 - 1, by0 - 1, bar_x0, by1 + 1, edge); rect(cv, bar_x1, by0 - 1, bar_x1 + 1, by1 + 1, edge)
    for k in range(1, 10):      # ticks
        xk = bar_x0 + (bar_x1 - bar_x0) * k // 10
        rect(cv, xk, by1 + 1, xk + 1, by1 + 4, edge * 0.6)
    width = bar_x1 - bar_x0
    span = 10 ** sl
    now_f = spec.NOW_YEARS / span
    yr = spec.year_at(t)
    head_f = (yr[0] / span) if yr else now_f
    head_f = min(1.0, head_f)
    marker_px = bar_x0 + int(now_f * width)
    # past (lit) and future (dim) segments
    if t >= 2.0:
        past_w = max(0, min(width, int(round(min(now_f, head_f if yr else now_f) * width))))
        if past_w >= 1:
            gold = np.array([1.0, 0.8, 0.3]); grad = np.linspace(0, 1, past_w)[None, :, None]
            seg = (np.array([0.2, 0.5, 1.0]) * (1 - grad) + gold * grad)
            cv[by0:by1, bar_x0:bar_x0 + past_w] = seg * fade * (1.0 - 0.6 * smooth((t - 31) / 12))
        if yr and head_f > now_f:
            fw = int(round(head_f * width)) - int(round(now_f * width))
            if fw >= 1: rect(cv, bar_x0 + int(round(now_f * width)), by0, bar_x0 + int(round(now_f * width)) + fw, by1, ink * 0.45 * fade)
        if yr:
            hx = bar_x0 + int(round(head_f * width))
            rect(cv, hx, by0 - 2, hx + 1, by1 + 2, np.clip(ink * 1.1 * fade, 0, 1))
    # YOU ARE HERE marker (glow) -- fades out entirely during the black-hole era
    ma = 1.0 - smooth((t - 45.0) / 1.3)
    if t < 2.0: ma = 0
    if ma > 0 and fade > 0:
        mx = max(bar_x0, min(bar_x1 - 1, marker_px))
        pulse = 0.65 + 0.35 * math.sin(t * 6)
        mc = np.array([1.0, 0.9, 0.5]) * ma
        rect(cv, mx, by0 - 6, mx + 1, by1 + 6, mc)
        for k in range(1, 5): rect(cv, mx - k, by0 - 6, mx + 1 + k, by1 + 6, mc * 0.5 * pulse / k)
        rect(cv, mx - 2, by1 + 7, mx + 3, by1 + 8, mc); rect(cv, mx - 1, by1 + 8, mx + 2, by1 + 9, mc); rect(cv, mx, by1 + 9, mx + 1, by1 + 10, mc)
    img = Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8))
    return img, (bar_x0, bar_x1, by0, by1, marker_px, ma, fade, yr, sl)

def draw_frame(t):
    global ov_text, ov_px, ov_rgb
    ov_text = []; ov_px = []; ov_rgb = []
    cv = np.zeros((H, W, 3), np.float32); ov = np.zeros((H, W, 3), np.float32)
    for i, (a, b) in enumerate(spec.SCENES):
        if a <= t < b:
            if i == 7: scene8_fix(cv, t)
            else: SCENE_FN[i](cv, ov, t)
            break
    cv = grade(cv, t) if t >= 12 else cv
    cv = quantize(cv)
    for (x, y, b) in ov_px: put_px(cv, x, y, (b, b * 0.9, min(1, b * 1.05)))
    for (x, y, c) in ov_rgb: put_px(cv, x, y, c)
    # un-graded flashes for black hole pops
    if 45 <= t < 53:
        for i, (x, y, r0) in enumerate(BH):
            tp = BH_POP_FOR[i]
            if tp <= t < tp + 0.18:
                q = (t - tp) / 0.18
                flat_disc(cv, x, y, 3 + 14 * (1 if i == 0 else .5) * q, (1, 0.95, 1), 1 - q)
    img, info = draw_hud(cv, None, t)
    d = ImageDraw.Draw(img); d.fontmode = "1"
    bar_x0, bar_x1, by0, by1, mx, ma, fade, yr, sl = info
    ink = hud_ink(t)
    ci = tuple(int(255 * v) for v in np.clip(ink * fade, 0, 1))
    # labels
    if ma > 0 and fade > 0:
        lab = "YOU ARE HERE"
        x = max(36, min(W - 36, mx))
        cc = tuple(int(255 * v * ma) for v in (1.0, 0.9, 0.5))
        d.text((x, by1 + 13), lab, font=F_XS, fill=cc, anchor="ma")
    if fade > 0:
        d.text((bar_x0, by0 - 12 + 0), "BIG BANG", font=F_XS, fill=tuple(int(c * 0.7) for c in ci), anchor="la")
        e = int(round(sl)); text_sci(d, (bar_x1, by0 - 12), f"10{spec.sup(e)} yr" if sl < 99 else "10¹⁰⁰⁺ yr", F_XS, tuple(int(c * 0.7) for c in ci), "ra")
    # act name and counter
    if t >= 4.0 and t < 62.3:
        nm = None
        for i, (a, b) in enumerate(spec.SCENES):
            if a <= t < b: nm = spec.ACT_NAMES[i]
        if nm: d.text((8, 8), "ACT " + nm, font=F_XS, fill=tuple(int(c * 0.75) for c in ci), anchor="la")
        if yr:
            s = spec.fmt_years(yr[0], yr[1])
            d.text((W - 8, 8), "YEAR", font=F_XS, fill=tuple(int(c * 0.6) for c in ci), anchor="ra")
            text_sci(d, (W - 8, 20), s, F_CNT, ci, "ra", shadow=True)
    draw_texts(img, d, t)
    return img

def scene8_fix(cv, t):
    # draw black holes with per-hole pop times
    stars(cv, t, 12, 0.12 * (1 - smooth((t - 45) / 1)))
    for i, (x, y, r0) in enumerate(BH):
        tp = BH_POP_FOR[i]
        if t >= tp + 0.6: continue
        rng = np.random.default_rng(int(t * 24) * 7 + i)
        if t < tp:
            life = clamp01((t - spec.BH_START) / (tp - spec.BH_START))
            r = max(1.0, r0 * (1 - life) ** (1 / 3))
            hot = 0.35 + 0.65 * life
            glow(cv, x, y, r + 16, np.array([0.8, 0.35, 0.9]) * (0.4 + 0.5 * life), 0.9, 2)
            n_rim = int(2.6 * math.pi * (r + 1.5))
            for k in range(n_rim):
                a = k / n_rim * 6.28
                if True:
                    ov_rgb.append((round(x + math.cos(a) * (r + 1.5)), round(y + math.sin(a) * (r + 1.5)),
                                   np.array([1.0, 0.55, 1.0]) * (0.45 + 0.55 * rng.random()) * (0.7 + 0.3 * hot)))
            for k in range(int(10 + r)):
                a = rng.random() * 6.28; rr = r + 2.5 + rng.random() * 3
                ov_rgb.append((round(x + math.cos(a) * rr), round(y + math.sin(a) * rr), np.array([0.8, 0.4, 0.9]) * rng.random() * 0.8))
            flat_disc(cv, x, y, r, (0, 0, 0))
            for k in range(int(3 + 14 * life)):         # Hawking radiation pixels drifting out
                a = rng.random() * 6.28; ph = (t * 0.6 + rng.random()) % 1
                put_px(cv, x + math.cos(a) * (r + 4 + ph * 22), y + math.sin(a) * (r + 4 + ph * 22), (0.9, 0.7, 1.0), (1 - ph) * 0.9)
        else:
            q = (t - tp) / 0.55
            big = (i == 0)
            R = (10 + 70 * q) * (3 if big else 1)
            flat_disc(cv, x, y, max(1, R * (1 - q) ** 0.5), (1, 1, 1), 1 - q)
            ring(cv, x, y, R, R + 2, (1.0, 0.8, 1.0), 1 - q)
            rng = np.random.default_rng(i + 100)
            for k in range(40):
                a = rng.random() * 6.28; sp = 30 + rng.random() * 70
                put_px(cv, x + math.cos(a) * sp * q * (2 if big else 1), y + math.sin(a) * sp * q * (2 if big else 1), (1, .85, 1), 1 - q)
            if big: ov += 0     # flash handled below
    big_t = spec.BH_POPS[0]
# NOTE: BH list index 0 is the biggest hole but spec.BH_POPS[2] is the final pop -> order below maps big hole to last pop
BH = [(95, 135, 34.0), (190, 255, 21.0), (80, 330, 13.0)]
BH_POP_FOR = [spec.BH_POPS[2], spec.BH_POPS[1], spec.BH_POPS[0]]

# ---- Scene 9: heat death ----
_dim = np.random.default_rng(90)
DIM = [(int(_dim.integers(12, W - 12)), int(_dim.integers(20, 400)), 0.11 + 0.1 * _dim.random()) for _ in range(5)]
def scene9(cv, ov, t):
    lp0, lp1 = spec.LAST_PIXEL
    # persistent barely-there pixels
    for i, (x, y, b) in enumerate(DIM):
        fade = 1 - smooth((t - 58.5 - i * 0.5) / 1.0) if t > 58.5 else 1
        if t >= lp0 + 0.4 + i * 0.1:
            ov_px.append((x, y, b * fade * (0.7 + 0.3 * math.sin(t * 0.7 + i))))
    # the last pixel
    if t < lp1:
        q = (t - lp0) / (lp1 - lp0)
        on = (q < 0.5 and int(t * 8) % 3 != 0) or (0.5 <= q < 0.8 and int(t * 5) % 3 == 0) or (q < 0.15)
        a = (1 - q) ** 1.5
        if on and t >= lp0 - 0.4: ov_px.append((135, 215, 0.95 * a + 0.05))
        elif t >= lp0 - 0.4: ov_px.append((135, 215, 0.12 * a))
    elif t < lp1 + 0.8:
        ov_px.append((135, 215, 0.10 * (1 - (t - lp1) / 0.8)))

SCENE_FN = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9]

# =====================================================================
# GRADE: palette drains warm -> red -> purple -> black
# =====================================================================
RAMP_KF = [  # t, mid, hi, brightness
    (0, (0, 0, 0), (0, 0, 0), 1.0),
    (31.0, (0.45, 0.08, 0.16), (1.0, 0.45, 0.3), 1.0),
    (37.9, (0.40, 0.05, 0.14), (1.0, 0.40, 0.28), 0.95),
    (39.0, (0.22, 0.07, 0.36), (0.75, 0.55, 0.95), 0.9),
    (44.9, (0.20, 0.06, 0.32), (0.75, 0.5, 0.95), 0.85),
    (46.0, (0.14, 0.04, 0.2), (0.6, 0.35, 0.75), 0.75),
    (52.9, (0.12, 0.03, 0.16), (0.55, 0.3, 0.7), 0.7),
    (54.5, (0.08, 0.03, 0.1), (0.4, 0.3, 0.5), 0.6),
    (64, (0.06, 0.03, 0.08), (0.3, 0.25, 0.4), 0.5),
]
def grade(cv, t):
    duo = smooth((t - 27.0) / 4.0) if t < 31 else 1.0           # drain colour over the tail of act IV
    # slow global warmth loss from Act III on
    if t >= 12:
        w = smooth((t - 17) / 14.0) * 0.35
        lum = (cv * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1, keepdims=True)
        cv = cv * (1 - w) + (lum * np.array([1.0, 0.75, 0.8], np.float32)) * w
    if duo <= 0: return cv
    lum = np.clip((cv * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1), 0, 1.6)[..., None]
    ts = [k[0] for k in RAMP_KF]; tt = max(t, 31.0)
    mid = np.array([np.interp(tt, ts, [k[1][c] for k in RAMP_KF]) for c in range(3)], np.float32)
    hi = np.array([np.interp(tt, ts, [k[2][c] for k in RAMP_KF]) for c in range(3)], np.float32)
    br = float(np.interp(tt, ts, [k[3] for k in RAMP_KF]))
    l1 = np.clip(lum * 2, 0, 1); l2 = np.clip(lum * 2 - 1, 0, 1)
    ramp = (mid * l1) * (1 - l2) + (mid * (1 - l2) + hi * l2) * l2 * 1.0
    ramp = np.where(lum < 0.5, mid * (lum * 2), mid + (hi - mid) * np.clip(lum * 2 - 1, 0, 1))
    return (cv * (1 - duo) + ramp * duo) * br

def quantize(cv):
    n = LEVELS - 1
    return np.clip(np.floor(np.clip(cv, 0, 1) * n + 0.5 + BAYER_T[..., None] * 0.95), 0, n) / n

# =====================================================================
# HUD: timeline bar, counter, text
# =====================================================================

_FC = {}
def font_sz(n):
    if n not in _FC: _FC[n] = ImageFont.truetype(FONT_B, n)
    return _FC[n]
SUPMAP = {c: str(i) for i, c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")}; SUPMAP["⁻"] = "-"; SUPMAP["⁺"] = "+"
def text_sci(d, xy, s, font, fill, anchor="la", shadow=False):
    """draw text where unicode superscripts become real raised small digits"""
    x, y = xy; base = font.size; sf = font_sz(max(6, int(base * 0.7)))
    runs = []
    for ch in s:
        is_sup = ch in SUPMAP
        ch2 = SUPMAP.get(ch, ch)
        if runs and runs[-1][0] == is_sup: runs[-1][1] += ch2
        else: runs.append([is_sup, ch2])
    wid = sum(d.textlength(t, font=sf if sp else font) for sp, t in runs)
    if anchor[0] == "m": x -= wid / 2
    elif anchor[0] == "r": x -= wid
    cx = x
    for sp, t in runs:
        f = sf if sp else font
        yy = y - (int(base * 0.4) if sp else 0)
        if shadow: d.text((cx + 1, yy + 1), t, font=f, fill=(0, 0, 0), anchor="l" + anchor[1])
        d.text((cx, yy), t, font=f, fill=fill, anchor="l" + anchor[1])
        cx += d.textlength(t, font=f)

ov_text = []; ov_px = []; ov_rgb = []
def wrap(s, n):
    words = s.split(" "); lines = []; cur = ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > n: lines.append(cur); cur = w
        else: cur = (cur + " " + w) if cur else w
    return lines + [cur]
def hud_ink(t):
    """text colour drains with the universe"""
    f = smooth((t - 17) / 20.0); g = smooth((t - 38) / 12.0)
    a = np.array([1.0, 0.92, 0.7]); b = np.array([0.95, 0.5, 0.45]); c = np.array([0.6, 0.45, 0.75])
    base = a * (1 - f) + b * f
    base = base * (1 - g) + c * g
    return base * (1 - 0.35 * smooth((t - 50) / 6))
# text items: (t0, t1, kind, text, y, align, cps)
TXT = [
    (0.3, 2.45, "big", "Everything that has ever happened…", 208, "mid", 28),
    (2.7, 4.0, "big", "…is the first 0.000…001% of the universe's life.", 208, "mid", 40),
    (4.05, 12.0, "lab", "Big Bang: 13.8 billion years ago", 345, "left", 60),
    (6.15, 12.0, "lab", "Earth forms: 4.5 billion years ago", 360, "left", 60),
    (7.75, 12.0, "lab", "First life: ~3.8 billion years ago", 375, "left", 60),
    (9.45, 12.0, "lab", "Dinosaurs die: 66 million years ago", 390, "left", 60),
    (10.15, 12.0, "lab", "Humans appear: ~300,000 years ago", 405, "left", 60),
    (12.3, 17.0, "big", "How long do humans last?", 335, "top", 30),
    (13.4, 17.0, "big", "Nobody knows.", 354, "top", 22),
    (14.5, 17.0, "lab", "Most species last ~1–10 million years.", 384, "top", 45),
    (17.3, 19.7, "lab", "~1 billion years: Sun brightens, oceans evaporate", 355, "top", 45),
    (19.8, 22.5, "lab", "~5 billion years: Sun becomes a red giant", 355, "top", 45),
    (22.9, 24.0, "lab", "~7–8 billion years: Sun becomes a white dwarf", 355, "top", 45),
    (24.4, 28.7, "lab", "Andromeda may collide with us — recent models put it around a coin flip within 10 billion years.", 345, "top", 60),
    (28.9, 31.0, "lab", "~100+ billion years: all other galaxies vanish past our horizon.", 345, "top", 60),
    (32.0, 34.9, "lab", "Up to ~10 trillion years: the longest-lived red dwarfs burn out", 350, "top", 45),
    (35.0, 38.0, "lab", "~100 trillion years: no new stars form", 350, "top", 45),
    (38.4, 42.2, "lab", "~10¹⁹–10²⁰ years: dead galaxies evaporate as stars are flung away", 350, "top", 45),
    (42.3, 45.0, "lab", "10³⁴+ years: protons may decay (if they decay at all)", 350, "top", 45),
    (45.3, 49.5, "big", "Black holes slowly evaporate…", 345, "top", 24),
    (49.8, 53.0, "lab", "~10¹⁰⁰ years: the largest black holes vanish", 375, "top", 45),
    (56.4, 62.0, "big", "No light. No heat. No change.", 150, "mid", 11),
    (58.4, 62.0, "big", "Maximum entropy.", 175, "mid", 10),
    (60.0, 62.0, "big", "And all of human history happened in the first instant.", 250, "mid", 13),
    (62.35, 64.0, "end", spec.CHANNEL, 205, "mid", 40),
    (62.8, 64.0, "lab", "Follow for more cosmic scale.", 232, "mid", 40),
]
def text_alpha(t, t1):
    return 1.0 - smooth((t - (t1 - 0.3)) / 0.3) if t1 < 62.2 or True else 1.0
def draw_texts(img, d, t):
    ink = hud_ink(t)
    for (t0, t1, kind, s, y, al, cps) in TXT:
        if not (t0 <= t < t1): continue
        n = int((t - t0) * cps) + 1
        sp = max(0, 1 - smooth((t - (t1 - 0.25)) / 0.25)) if t1 < 62.2 else (1 if t < 63.7 else 1 - (t - 63.7) / 0.3)
        font = F_BIG if kind == "big" else (F_END if kind == "end" else F_SM)
        width = 30 if kind == "big" else (22 if kind == "end" else 38)
        full = wrap(s, width)
        shown = s[:n]
        # reveal the full wrapped layout char-by-char
        lines = []; rem = n
        for ln in full:
            lines.append(ln[:max(0, rem)]); rem -= len(ln) + 1
        lh = 17 if kind == "big" else (20 if kind == "end" else 13)
        y0 = y - (len(full) * lh // 2 if al == "mid" else 0)
        c = ink * sp
        if kind == "end": c = np.array([0.85, 0.75, 0.95]) * sp
        for j, ln in enumerate(lines):
            if not ln: continue
            if al == "left": x = 10; anchor = "la"
            else: x = W // 2; anchor = "ma"
            col_i = tuple(int(255 * v) for v in np.clip(c, 0, 1))
            text_sci(d, (x, y0 + j * lh), ln, font, col_i, anchor, shadow=True)
    if 42.4 < t < 45.0 and int(t * 3) % 2 == 0:
        d.text((W // 2, 332), "[ HYPOTHETICAL ]", font=F_XS, fill=(170, 140, 220), anchor="ma")
    for (x, y, s, f, c, a) in ov_text:
        if a <= 0: continue
        ci = tuple(int(255 * v * a) for v in c)
        d.text((x, y), s, font=f, fill=ci, anchor="ma")

def draw_hud(cv, img_fn, t):
    """timeline bar + counter drawn on top of the quantised frame. Returns PIL image."""
    # bar background strip
    rect(cv, 0, 426, W, H, (0, 0, 0), 0.82)
    sl = spec.span_log(t)
    bar_x0, bar_x1, by0, by1 = 10, W - 10, 434, 444
    ink = hud_ink(t); fade = 1.0 - 0.5 * smooth((t - 56) / 4)
    if t >= 62.3: fade = 0.0
    edge = np.clip(ink * 0.55 * fade, 0, 1)
    rect(cv, bar_x0 - 1, by0 - 1, bar_x1 + 1, by0, edge); rect(cv, bar_x0 - 1, by1, bar_x1 + 1, by1 + 1, edge)
    rect(cv, bar_x0 - 1, by0 - 1, bar_x0, by1 + 1, edge); rect(cv, bar_x1, by0 - 1, bar_x1 + 1, by1 + 1, edge)
    for k in range(1, 10):      # ticks
        xk = bar_x0 + (bar_x1 - bar_x0) * k // 10
        rect(cv, xk, by1 + 1, xk + 1, by1 + 4, edge * 0.6)
    width = bar_x1 - bar_x0
    span = 10 ** sl
    now_f = spec.NOW_YEARS / span
    yr = spec.year_at(t)
    head_f = (yr[0] / span) if yr else now_f
    head_f = min(1.0, head_f)
    marker_px = bar_x0 + int(now_f * width)
    # past (lit) and future (dim) segments
    if t >= 2.0:
        past_w = max(0, min(width, int(round(min(now_f, head_f if yr else now_f) * width))))
        if past_w >= 1:
            gold = np.array([1.0, 0.8, 0.3]); grad = np.linspace(0, 1, past_w)[None, :, None]
            seg = (np.array([0.2, 0.5, 1.0]) * (1 - grad) + gold * grad)
            cv[by0:by1, bar_x0:bar_x0 + past_w] = seg * fade * (1.0 - 0.6 * smooth((t - 31) / 12))
        if yr and head_f > now_f:
            fw = int(round(head_f * width)) - int(round(now_f * width))
            if fw >= 1: rect(cv, bar_x0 + int(round(now_f * width)), by0, bar_x0 + int(round(now_f * width)) + fw, by1, ink * 0.45 * fade)
        if yr:
            hx = bar_x0 + int(round(head_f * width))
            rect(cv, hx, by0 - 2, hx + 1, by1 + 2, np.clip(ink * 1.1 * fade, 0, 1))
    # YOU ARE HERE marker (glow) -- fades out entirely during the black-hole era
    ma = 1.0 - smooth((t - 45.0) / 1.3)
    if t < 2.0: ma = 0
    if ma > 0 and fade > 0:
        mx = max(bar_x0, min(bar_x1 - 1, marker_px))
        pulse = 0.65 + 0.35 * math.sin(t * 6)
        mc = np.array([1.0, 0.9, 0.5]) * ma
        rect(cv, mx, by0 - 6, mx + 1, by1 + 6, mc)
        for k in range(1, 5): rect(cv, mx - k, by0 - 6, mx + 1 + k, by1 + 6, mc * 0.5 * pulse / k)
        rect(cv, mx - 2, by1 + 7, mx + 3, by1 + 8, mc); rect(cv, mx - 1, by1 + 8, mx + 2, by1 + 9, mc); rect(cv, mx, by1 + 9, mx + 1, by1 + 10, mc)
    img = Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8))
    return img, (bar_x0, bar_x1, by0, by1, marker_px, ma, fade, yr, sl)

def draw_frame(t):
    global ov_text, ov_px, ov_rgb
    ov_text = []; ov_px = []; ov_rgb = []
    cv = np.zeros((H, W, 3), np.float32); ov = np.zeros((H, W, 3), np.float32)
    for i, (a, b) in enumerate(spec.SCENES):
        if a <= t < b:
            if i == 7: scene8_fix(cv, t)
            else: SCENE_FN[i](cv, ov, t)
            break
    cv = grade(cv, t) if t >= 12 else cv
    cv = quantize(cv)
    for (x, y, b) in ov_px: put_px(cv, x, y, (b, b * 0.9, min(1, b * 1.05)))
    for (x, y, c) in ov_rgb: put_px(cv, x, y, c)
    # un-graded flashes for black hole pops
    if 45 <= t < 53:
        for i, (x, y, r0) in enumerate(BH):
            tp = BH_POP_FOR[i]
            if tp <= t < tp + 0.18:
                q = (t - tp) / 0.18
                flat_disc(cv, x, y, 3 + 14 * (1 if i == 0 else .5) * q, (1, 0.95, 1), 1 - q)
    img, info = draw_hud(cv, None, t)
    d = ImageDraw.Draw(img); d.fontmode = "1"
    bar_x0, bar_x1, by0, by1, mx, ma, fade, yr, sl = info
    ink = hud_ink(t)
    ci = tuple(int(255 * v) for v in np.clip(ink * fade, 0, 1))
    # labels
    if ma > 0 and fade > 0:
        lab = "YOU ARE HERE"
        x = max(36, min(W - 36, mx))
        cc = tuple(int(255 * v * ma) for v in (1.0, 0.9, 0.5))
        d.text((x, by1 + 13), lab, font=F_XS, fill=cc, anchor="ma")
    if fade > 0:
        d.text((bar_x0, by0 - 12 + 0), "BIG BANG", font=F_XS, fill=tuple(int(c * 0.7) for c in ci), anchor="la")
        e = int(round(sl)); text_sci(d, (bar_x1, by0 - 12), f"10{spec.sup(e)} yr" if sl < 99 else "10¹⁰⁰⁺ yr", F_XS, tuple(int(c * 0.7) for c in ci), "ra")
    # act name and counter
    if t >= 4.0 and t < 62.3:
        nm = None
        for i, (a, b) in enumerate(spec.SCENES):
            if a <= t < b: nm = spec.ACT_NAMES[i]
        if nm: d.text((8, 8), "ACT " + nm, font=F_XS, fill=tuple(int(c * 0.75) for c in ci), anchor="la")
        if yr:
            s = spec.fmt_years(yr[0], yr[1])
            d.text((W - 8, 8), "YEAR", font=F_XS, fill=tuple(int(c * 0.6) for c in ci), anchor="ra")
            text_sci(d, (W - 8, 20), s, F_CNT, ci, "ra", shadow=True)
    draw_texts(img, d, t)
    return img

def scene8_fix(cv, t):
    # draw black holes with per-hole pop times
    stars(cv, t, 12, 0.12 * (1 - smooth((t - 45) / 1)))
    for i, (x, y, r0) in enumerate(BH):
        tp = BH_POP_FOR[i]
        if t >= tp + 0.6: continue
        rng = np.random.default_rng(int(t * 24) * 7 + i)
        if t < tp:
            life = clamp01((t - spec.BH_START) / (tp - spec.BH_START))
            r = max(1.0, r0 * (1 - life) ** (1 / 3))
            hot = 0.35 + 0.65 * life
            glow(cv, x, y, r + 16, np.array([0.8, 0.35, 0.9]) * (0.4 + 0.5 * life), 0.9, 2)
            for k in range(int(20 + 1.5 * r)):
                a = rng.random() * 6.28; rr = r + 1.5 + rng.random() * 2.5
                put_px(cv, x + math.cos(a) * rr, y + math.sin(a) * rr, np.array([1.0, 0.8, 1.0]) * (0.5 + 0.5 * rng.random()) * (0.6 + 0.4 * hot))
            ring(cv, x, y, r + 0.5, r + 1.8, np.array([1.0, 0.6, 1.0]) * (0.55 + 0.25 * math.sin(t * 3 + i)))
            flat_disc(cv, x, y, r, (0, 0, 0))
            for k in range(int(3 + 16 * life)):
                a = rng.random() * 6.28; ph = (t * 0.6 + rng.random()) % 1
                ov_rgb.append((round(x + math.cos(a) * (r + 4 + ph * 24)), round(y + math.sin(a) * (r + 4 + ph * 24)), np.array([1.0, 0.85, 1.0]) * (1 - ph) * 0.9))
        else:
            q = (t - tp) / 0.6; big = (i == 0); sc = 1.8 if big else 1.0
            R_ = 4 + 60 * sc * q
            for k in range(int(5 * R_)):
                a = k / int(5 * R_) * 6.28
                ov_rgb.append((round(x + math.cos(a) * R_), round(y + math.sin(a) * R_), np.array([1.0, 0.85, 1.0]) * (1 - q)))
            for k in range(46):
                a = rng.random() * 6.28; sp = 20 + rng.random() * 70
                ov_rgb.append((round(x + math.cos(a) * sp * q * sc), round(y + math.sin(a) * sp * q * sc), np.array([1, .85, 1]) * (1 - q)))

# =====================================================================
def render(out_path, audio_path=None, t_from=0.0, t_to=None, preview_dir=None):
    n = int(spec.DUR * spec.FPS)
    if audio_path:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(spec.FPS), "-i", "-",
               "-i", audio_path, "-vf", f"scale={W * spec.SCALE}:{H * spec.SCALE}:flags=neighbor,format=yuv420p",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", str(spec.FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(n):
            img = draw_frame(f / spec.FPS)
            p.stdin.write(np.asarray(img).tobytes())
            if f % 120 == 0: print("frame", f, "/", n, flush=True)
        p.stdin.close(); p.wait()
    print("done", out_path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        import os
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for tt in map(float, sys.argv[3:]):
            im = draw_frame(tt).resize((W * 2, H * 2), Image.NEAREST); im.save(f"{out}/t{tt:06.2f}.png")
    else:
        render(sys.argv[1], sys.argv[2])
