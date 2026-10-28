"""Scenes 5-8: spinning worlds + Dyson swarm, the first star, the galaxy, the limit."""
import math
import numpy as np
from gfx import *
from chars import *
from scenes1 import seg, Cam, pcol, SUN_L

GOLD = col(1.0, 0.82, 0.42)


# ======================================================================
# SCENE 5
# ======================================================================
def oneill_inside(cv, t):
    u = t - 30.0
    cx, cy = 270.0, 400.0
    dx = XX - cx; dy = (YY - cy) * 0.9
    rho = np.sqrt(dx * dx + dy * dy) + 1e-3
    th = np.arctan2(dy, dx) + 0.08 * u
    depth = 62.0 / rho                         # perspective depth along axis
    v = depth + 1.4 * u                        # travelling forward
    strip = (th / (2 * math.pi) + 0.5) * 6.0
    si = np.floor(strip).astype(int)
    su = strip - si                            # 0..1 across strip
    land = (si % 2 == 0)
    # land texture
    cell_u = np.floor(su * 5).astype(int); cell_v = np.floor(v * 3.0).astype(int)
    h = ((cell_u * 7919 + cell_v * 104729 + si * 31) % 97) / 97.0
    field = np.where(h[..., None] > 0.5, np.array([0.48, 0.74, 0.28], np.float32), np.array([0.82, 0.74, 0.30], np.float32))
    field = np.where((h[..., None] > 0.86), np.array([0.35, 0.60, 0.25], np.float32), field)
    nz = tex(NZ_A, su * 3, v * 0.35)
    ground = field * (0.8 + 0.35 * nz[..., None])
    # river
    river = np.clip((0.07 - np.abs(su - 0.5)) * 40, 0, 1)
    ground = ground * (1 - river[..., None]) + np.array([0.25, 0.6, 0.95], np.float32) * river[..., None]
    # houses
    fu = (su * 5) % 1.0; fv = (v * 3.0) % 1.0
    house = (h > 0.9) & (fu > 0.25) & (fu < 0.75) & (fv > 0.25) & (fv < 0.7)
    roof = (h > 0.9) & (fu > 0.2) & (fu < 0.8) & (fv >= 0.15) & (fv <= 0.25)
    ground = np.where(house[..., None], np.array([0.97, 0.94, 0.88], np.float32), ground)
    ground = np.where(roof[..., None], np.array([0.85, 0.3, 0.2], np.float32), ground)
    # window strips
    wlat = ((v * 2.0) % 1.0 < 0.08) | (np.abs(su - 0.5) < 0.02)
    sky = np.array([0.72, 0.9, 1.0], np.float32) * (1.0 - 0.15 * wlat[..., None])
    sky = sky + np.array([0.3, 0.25, 0.1], np.float32) * np.clip(1 - rho / 140.0, 0, 1)[..., None]
    c = np.where(land[..., None], ground, sky)
    # edge shading between strips
    edge = np.clip(np.minimum(su, 1 - su) * 24, 0, 1)
    c = c * (0.55 + 0.45 * edge[..., None])
    # distance haze to bright axis
    fog = np.clip(1 - rho / 190.0, 0, 1) ** 1.8
    c = c * (1 - fog[..., None]) + np.array([1.0, 0.95, 0.82], np.float32) * fog[..., None]
    c *= np.clip(0.45 + rho / 160.0, 0, 1.15)[..., None] * 0 + 1.0
    cv[:] = c
    # outer darkening
    d = np.clip((rho - 330) / 320.0, 0, 1)
    cv *= (1 - 0.55 * d)[..., None]
    glow(cv, cx, cy, 110, (1.0, 0.92, 0.7), 0.9, 2.0)
    # people for scale: a tiny family at the bottom
    set_light((-0.2, -0.7, 0.7), 0.5, rim_dir=(0.5, -0.8), rim_col=(1.0, 0.9, 0.6), rim_amt=0.6)
    k = smooth(u / 0.8)
    person(cv, 150, 930, 1.6, t, helmet=False, hair=(0.3, 0.18, 0.1), hair_style="long", suit=(0.9, 0.55, 0.3), skin=(0.9, 0.68, 0.55), expr="awe",
           look=(0.6, -1.0), arm_l=0.2, arm_r=2.6 + 0.1 * math.sin(t * 3), patch_r=9, pack=False)
    person(cv, 250, 940, 1.1, t, helmet=False, hair=(0.1, 0.06, 0.05), hair_style="cap", suit=(0.4, 0.7, 0.9), skin=(0.82, 0.6, 0.45), expr="awe",
           look=(0.2, -1.0), head_k=1.3, patch_r=10, pack=False)


def cylinder_outside(cv, t, zoom, ang=-0.5, cxy=(270, 470)):
    cx, cy = cxy
    L = 330 * zoom; R = 98 * zoom
    ca, sa = math.cos(ang), math.sin(ang)
    sp = t * 0.9
    # mirrors (three long gold panels)
    for k in (-1, 0, 1):
        off = k * R * 1.45
        a0 = (cx - ca * L * 0.55 - sa * off, cy - sa * L * 0.55 + ca * off)
        a1 = (cx + ca * L * 0.55 - sa * off, cy + sa * L * 0.55 + ca * off)
        w = R * 0.34
        pts = [(a0[0] - sa * w * -1, a0[1] + ca * w * -1), (a1[0] + sa * w, a1[1] - ca * w), (a1[0] - sa * w, a1[1] + ca * w), (a0[0] + sa * w, a0[1] - ca * w)]
        poly(cv, [(a0[0] + sa * w, a0[1] - ca * w), (a1[0] + sa * w, a1[1] - ca * w), (a1[0] - sa * w, a1[1] + ca * w), (a0[0] - sa * w, a0[1] + ca * w)],
             (1.0, 0.9, 0.55), (0.75, 0.55, 0.25), a=0.85)
        line(cv, a0[0], a0[1], a1[0], a1[1], 1.5, (1.0, 0.95, 0.8), 0.6)
    # cylinder body per-pixel
    R2 = R + L * 0.5 + 6
    bb = bbox(cx - R2, cy - R2, cx + R2, cy + R2)
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb] - cx; Y = YY[ya:yb, xa:xb] - cy
    a = X * ca + Y * sa; b = -X * sa + Y * ca          # a along axis, b across
    inside = (np.abs(a) < L / 2) & (np.abs(b) < R)
    cov = np.clip(R - np.abs(b) + 0.5, 0, 1) * np.clip(L / 2 - np.abs(a) + 0.5, 0, 1)
    phi = np.arcsin(np.clip(b / R, -1, 1))
    nz = np.cos(phi)
    stripe = np.floor((phi / math.pi + 0.5 + sp * 0.1) * 6).astype(int) % 2
    land = np.array([0.30, 0.52, 0.34], np.float32); win = np.array([0.75, 0.9, 1.0], np.float32)
    base = np.where(stripe[..., None] == 0, land, win)
    ridge = np.clip(np.abs(((phi / math.pi + 0.5 + sp * 0.1) * 6) % 1 - 0.5) * 18 - 7.0, 0, 1)
    base = base * (0.7 + 0.3 * ridge[..., None])
    seam = (np.abs(((a / L + 0.5) * 14) % 1 - 0.5) > 0.47)
    base = np.where(seam[..., None], base * 0.6, base)
    Lh = np.array([-0.5, -0.6, 0.62], np.float32); Lh /= np.linalg.norm(Lh)
    lx = (Lh[0] * ca + Lh[1] * sa); ly = (-Lh[0] * sa + Lh[1] * ca)
    lam = np.clip(ly * (b / R) + Lh[2] * nz + lx * 0.0, 0, 1)
    c = base * (0.18 + 0.95 * lam[..., None] ** 0.9)
    c += (np.clip(1 - np.abs(b / R - 0.0), 0, 1) ** 12 * 0.0)[..., None]
    sub = cv[ya:yb, xa:xb]
    sub += (c - sub) * cov[..., None]
    # end caps
    for sg in (-1, 1):
        ex, ey = cx + ca * L / 2 * sg, cy + sa * L / 2 * sg
        ell(cv, ex, ey, R * 0.24, R, (0.62, 0.66, 0.74) if sg > 0 else (0.5, 0.54, 0.62), ang=ang, a=1.0)
    glow(cv, cx - ca * L * 0.2 + 0, cy - sa * L * 0.2, R * 1.8, (1.0, 0.85, 0.5), 0.12, 2.0)


def dyson(cv, t, zoom, build):
    cx, cy = 270, 470
    sr = 30 * zoom
    glow(cv, cx, cy, 260 * zoom, (1.0, 0.7, 0.25), 0.9, 2.2)
    glow(cv, cx, cy, 120 * zoom, (1.0, 0.9, 0.6), 1.0, 2.0)
    circ(cv, cx, cy, sr, (1.0, 0.96, 0.8), flat=True)
    rng = np.random.default_rng(5)
    N = 5200
    a = 55 + rng.random(N) * 230
    inc = (rng.random(N) - 0.5) * 2.2
    node = rng.random(N) * 6.28
    ph = rng.random(N) * 6.28
    sp = 1.4 / (a / 60.0) ** 1.5
    nu = ph + sp * t * 0.9
    x = a * np.cos(nu); y = a * np.sin(nu)
    y2 = y * np.cos(inc); z2 = y * np.sin(inc)
    xr = x * np.cos(node) - y2 * np.sin(node); yr = x * np.sin(node) + y2 * np.cos(node)
    tilt = 1.15
    sy = yr * math.cos(tilt) - z2 * math.sin(tilt); depth = yr * math.sin(tilt) + z2 * math.cos(tilt)
    sx_ = cx + xr * zoom; sy_ = cy + sy * 0.55 * zoom
    vis = rng.random(N) < build
    br = (0.35 + 0.65 * (depth > 0)) * (0.55 + 0.45 * np.sin(t * 3 + ph * 5) ** 2)
    ok = vis & (sx_ >= 0) & (sx_ < W - 1) & (sy_ >= 0) & (sy_ < H - 1)
    # collectors behind the sun are hidden
    behind = (depth < 0) & (np.hypot(sx_ - cx, sy_ - cy) < sr * 1.05)
    ok &= ~behind
    px = sx_[ok].astype(int); py = sy_[ok].astype(int); bb_ = br[ok]
    gold = np.array([1.0, 0.8, 0.35], np.float32)
    for dxo, dyo, w in ((0, 0, 1.0), (1, 0, 0.5), (0, 1, 0.5)):
        np.add.at(cv, (py + dyo, px + dxo), gold[None, :] * (bb_ * w)[:, None] * 1.6)
    # orbital rings (faint)
    for k in (1, 2, 3):
        ring(cv, cx, cy, (90 + 55 * k) * zoom, (90 + 55 * k) * 0.35 * zoom, 1.0, (1.0, 0.8, 0.4), 0.12)


def scene5(cv, t):
    def a(cv_, t_): oneill_inside(cv_, t_)

    def b(cv_, t_):
        set_light((-0.5, -0.6, 0.62), 0.3, rim_dir=(0.8, -0.2), rim_col=(1.0, 0.85, 0.5), rim_amt=0.6)
        fill_bg(cv_, (0.03, 0.03, 0.10), (0.10, 0.07, 0.14))
        starfield(cv_, t_, off=(-(t_ - 34.4) * 5, 0), n=380, tint=(1.0, 0.95, 0.9))
        glow(cv_, 460, 130, 330, (1.0, 0.7, 0.25), 0.55, 2.0)
        circ(cv_, 460, 130, 40, (1.0, 0.95, 0.8), flat=True)
        zoom = lerp(1.7, 0.95, ease_io((t_ - 34.4) / 2.6))
        cylinder_outside(cv_, t_, zoom)

    def c(cv_, t_):
        fill_bg(cv_, (0.04, 0.03, 0.09), (0.12, 0.07, 0.13))
        starfield(cv_, t_, n=300, bright=0.8, tint=(1.0, 0.92, 0.85))
        zoom = lerp(2.2, 1.0, ease_io((t_ - 36.6) / 2.2))
        dyson(cv_, t_, zoom, smooth((t_ - 36.8) / 2.0) * 0.95 + 0.03)

    seg(cv, t, [(30, 34.4, a), (34.4, 36.7, b), (36.7, 39, c)], 0.35)


# ======================================================================
# SCENE 6
# ======================================================================
def sail_scene(cv, t):
    u = t - 39.0
    set_light((-0.5, -0.5, 0.7), 0.35, rim_dir=(0.8, -0.2), rim_col=(1.0, 0.8, 0.5), rim_amt=0.5)
    fill_bg(cv, (0.05, 0.03, 0.12), (0.16, 0.08, 0.20))
    starfield(cv, t, off=(-u * 40, 0), n=400, tint=(0.95, 0.9, 1.0))
    glow(cv, -20, 480, 420, (1.0, 0.68, 0.2), 0.8, 2.0)
    circ(cv, -140, 480, 200, (1.0, 0.93, 0.7), flat=True)
    # station
    sx, sy = 120, 480
    rrect(cv, sx, sy, 10, 80, 5, (0.9, 0.92, 0.98))
    ring(cv, sx, sy, 30, 76, 6, (0.8, 0.84, 0.94), 1.0)
    ell(cv, sx + 22, sy, 14, 40, (0.95, 0.95, 1.0), gloss=0.4)
    circ(cv, sx + 8, sy, 6, (0.5, 1.0, 1.0), flat=True)
    glow(cv, sx + 22, sy, 70, (0.5, 0.9, 1.0), 0.5, 2.0)
    n = 9
    for i in range(n):
        yy = 150 + i * (660 / (n - 1))
        k = smooth((u - 0.25 - i * 0.07) / 0.5)
        x = 190 + max(0.0, u - 0.4 - i * 0.07) ** 2.1 * 120
        if k <= 0: continue
        # laser
        beam(cv, sx + 26, sy + (yy - sy) * 0.08, x, yy, 1.8, 3.5, (0.6, 1.0, 1.0), 0.85 * k, 1.0)
        line(cv, sx + 26, sy + (yy - sy) * 0.08, x, yy, 1.0, (0.9, 1.0, 1.0), 0.8 * k)
        # sail
        s = 18 * (0.9 + 0.1 * math.sin(t * 5 + i))
        pts = [(x, yy - s), (x + s * 0.35, yy), (x, yy + s), (x - s * 0.35, yy)]
        poly(cv, pts, (1.0, 0.95, 0.8), (0.7, 0.8, 1.0))
        glow(cv, x, yy, 30, (0.9, 0.95, 1.0), 0.7 * k, 2.0)
        # streak trail
        tl = max(0.0, u - 0.4 - i * 0.07)
        beam(cv, x, yy, x - 30 - 140 * tl, yy, 3, 1, (0.6, 0.8, 1.0), 0.5 * smooth(tl))


def starship_scene(cv, t):
    u = t - 42.0
    set_light((-0.5, -0.5, 0.7), 0.32, rim_dir=(0.8, -0.3), rim_col=(0.7, 0.6, 1.0), rim_amt=0.7)
    fill_bg(cv, (0.04, 0.02, 0.11), (0.12, 0.06, 0.20))
    starfield(cv, t, off=(u * 20, 0), n=420, bright=1.0, tint=(0.9, 0.9, 1.0))
    z = lerp(0.88, 1.22, smooth(u / 3.2))
    drift = lerp(40, -30, smooth(u / 3.2))
    cam = Cam(z, px=-drift, py=0)
    cx, cy = cam.p(270, 480, 1.0)
    # engine plume (right side)
    ex, ey = cam.p(466, 480, 1.0)
    fl = 0.6 + 0.4 * smooth(u / 2.0)
    beam(cv, ex, ey, ex + 160 * fl * z, ey, 34 * z, 6 * z, (0.7, 0.55, 1.0), 0.85 * fl, 1.0)
    glow(cv, ex, ey, 90 * z, (0.8, 0.6, 1.0), 0.7 * fl, 2.0)
    # hull spine
    x0, x1 = cam.p(80, 480)[0], cam.p(470, 480)[0]
    capsule(cv, x0, cy, x1, cy, 26 * z, (0.78, 0.8, 0.9), r1=34 * z)
    # nose
    nx, ny = cam.p(62, 480)
    ell(cv, nx + 14 * z, ny, 30 * z, 24 * z, (0.9, 0.92, 0.98), gloss=0.3)
    # engine bell
    poly(cv, [(x1 - 6 * z, cy - 36 * z), (x1 + 34 * z, cy - 54 * z), (x1 + 34 * z, cy + 54 * z), (x1 - 6 * z, cy + 36 * z)], (0.62, 0.66, 0.8), (0.4, 0.42, 0.55))
    # habitat ring: wheel seen side-on (tall ellipse band) with lit windows & gardens
    rx_, ry_ = cam.p(265, 480)
    ring(cv, rx_, ry_, 38 * z, 190 * z, 26 * z, (0.62, 0.66, 0.8), 1.0)
    ring(cv, rx_, ry_, 38 * z, 190 * z, 18 * z, (0.88, 0.9, 0.97), 1.0)
    for i in range(18):
        a = i / 18 * 6.28 + u * 0.4
        wx = rx_ + math.cos(a) * 38 * z; wy = ry_ + math.sin(a) * 190 * z
        if math.cos(a) < -0.05: continue
        garden = (i % 3 == 0)
        rrect(cv, wx, wy, 7 * z, 9 * z, 3 * z, (0.3, 0.9, 0.45) if garden else (1.0, 0.85, 0.5), flat=True)
        glow(cv, wx, wy, 24 * z, (0.4, 1.0, 0.5) if garden else (1.0, 0.8, 0.4), 0.55, 2.0)
        if garden:
            circ(cv, wx, wy + 2 * z, 2.2 * z, (0.15, 0.2, 0.2), flat=True)
    # spokes
    for sg in (-1, 1):
        capsule(cv, rx_, cy, rx_, cy + sg * 150 * z, 5 * z, (0.7, 0.74, 0.86), flat=True)
    # fuel tanks
    for k in range(3):
        tx = cam.p(330 + k * 40, 480)[0]
        rrect(cv, tx, cy, 16 * z, 40 * z, 8 * z, (0.92, 0.93, 0.98), gloss=0.3)
        rrect(cv, tx, cy - 8 * z, 16 * z, 4 * z, 2 * z, (1.0, 0.56, 0.14), flat=True)
    # hull windows along the spine
    for i in range(12):
        wx = cam.p(100 + i * 14, 480)[0]
        if abs(wx - rx_) < 36 * z: continue
        circ(cv, wx, cy - 8 * z, 2.2 * z, (1.0, 0.85, 0.5), flat=True)
    star(cv, cam.p(150, 466)[0], cam.p(150, 466)[1], 8 * z, ORANGE, gloss=0.2)


def window_scene(cv, t):
    u = t - 45.0
    set_light((0.5, -0.4, 0.7), 0.36, rim_dir=(0.9, -0.2), rim_col=(1.0, 0.85, 0.6), rim_amt=0.8)
    fill_bg(cv, (0.10, 0.06, 0.14), (0.20, 0.12, 0.16))
    # window frame
    wx0, wx1, wy0, wy1 = 70, 470, 120, 560
    rrect(cv, 270, 340, 214, 236, 40, (0.18, 0.12, 0.20), flat=True)
    # starry view
    bbx = bbox(wx0, wy0, wx1, wy1)
    xa, xb, ya, yb = bbx
    sub = cv[ya:yb, xa:xb]
    Xl = XX[ya:yb, xa:xb]; Yl = YY[ya:yb, xa:xb]
    m = np.clip(0.5 - (np.maximum(np.abs(Xl - 270) - 190, 0) ** 2 + np.maximum(np.abs(Yl - 340) - 212, 0) ** 2) ** 0.5 + 0.5, 0, 1)
    space = np.stack([0.02 + 0.03 * (Yl - ya) / (yb - ya), 0.02 + 0.02 * (Yl - ya) / (yb - ya), 0.08 + 0.10 * (Yl - ya) / (yb - ya)], -1)
    sub += (space - sub) * m[..., None]
    tmp = np.zeros_like(cv)
    starfield(tmp, t, off=(-u * 6, 0), n=320, bright=1.0)
    mm = np.zeros((H, W), np.float32); mm[ya:yb, xa:xb] = m
    cv += tmp * mm[..., None]
    # Alpha Centauri approaching
    sz = lerp(10, 26, smooth(u / 3.0))
    ax, ay = 340, 290
    for k in range(4):
        glow(cv, ax, ay, sz * (4 + k * 3), (1.0, 0.85, 0.55), 0.6 / (k + 1), 2.0)
    circ(cv, ax, ay, sz * 0.6, (1.0, 0.98, 0.9), flat=True)
    line(cv, ax - sz * 5, ay, ax + sz * 5, ay, 1.4, (1, 0.92, 0.75), 0.6); line(cv, ax, ay - sz * 5, ax, ay + sz * 5, 1.4, (1, 0.92, 0.75), 0.6)
    glow(cv, 340, 300, 380, (1.0, 0.8, 0.5), 0.12, 2.0)
    # sill
    rrect(cv, 270, 586, 232, 22, 10, (0.30, 0.20, 0.26))
    # room floor
    poly(cv, [(0, 760), (W, 760), (W, H), (0, H)], (0.20, 0.13, 0.17), (0.09, 0.06, 0.09))
    # old woman (Ava's descendant) + child at the window
    person(cv, 150, 930, 2.1, t, helmet=False, hair=(0.95, 0.95, 0.98), hair_style="bun", suit=(0.55, 0.52, 0.70), skin=(0.88, 0.66, 0.52),
           expr="calm", look=(0.8, -0.5), arm_l=0.2, arm_r=0.95, patch_r=9.5, pack=False, blink=1.0 if 1.2 < (t % 4) < 1.3 else 0.0)
    person(cv, 345, 930, 1.45, t, helmet=False, hair=(0.08, 0.05, 0.04), hair_style="cap", suit=(0.93, 0.9, 0.86), skin=(0.9, 0.68, 0.56),
           expr="awe", look=(0.5, -0.9), head_k=1.3, patch_r=10, pack=False, arm_r=0.3)
    # warm light spill from the star
    glow(cv, 270, 700, 300, (1.0, 0.7, 0.4), 0.12, 2.0)


def scene6(cv, t):
    seg(cv, t, [(39, 42, sail_scene), (42, 45, starship_scene), (45, 48, window_scene)], 0.3)


# ======================================================================
# Galaxy helpers
# ======================================================================
def make_galaxy(n, seed, arms=2, wind=3.0, noise=0.22):
    r = np.random.default_rng(seed)
    rr = r.random(n) ** 0.65
    th = (r.integers(0, arms, n) * 2 * math.pi / arms) + wind * np.log1p(rr * 6) + r.normal(0, noise, n) * (1.0 - 0.55 * rr)
    x = rr * np.cos(th); y = rr * np.sin(th)
    bulge = r.normal(0, 1, (n, 2)) * (0.1 / (1 + 6 * rr))[:, None]
    pts = np.stack([x, y], 1) + bulge
    return pts.astype(np.float32), rr.astype(np.float32), r.random(n).astype(np.float32)


GAL = make_galaxy(9000, 21)
GAL_B = make_galaxy(4000, 33, arms=3, wind=2.4)


def draw_galaxy_pts(cv, gal, cx, cy, R, ang, tilt, core, arm, bright=1.0, colonize=None, wave=0.0, origin=None, tint_amt=0.0):
    pts, rr, rnd = gal
    ca, sa = math.cos(ang), math.sin(ang)
    x = pts[:, 0] * ca - pts[:, 1] * sa; y = pts[:, 0] * sa + pts[:, 1] * ca
    px = (cx + x * R); py = (cy + y * R * tilt)
    ok = (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1)
    f = np.clip(1.05 - rr * 0.8, 0.1, 1.0)
    core = np.asarray(core, np.float32); arm = np.asarray(arm, np.float32)
    mixk = np.clip(1 - rr * 1.7, 0, 1)[:, None]
    cols = arm[None] * (1 - mixk) + core[None] * mixk
    cols = cols * (f * (0.45 + 0.55 * rnd) * bright)[:, None]
    if colonize is not None:
        dist = np.hypot(pts[:, 0] - origin[0], pts[:, 1] - origin[1])
        inn = dist < wave
        front = np.abs(dist - wave) < 0.05
        goldc = np.array([1.0, 0.78, 0.3], np.float32)
        cols = np.where(inn[:, None], goldc[None] * (0.5 + 0.7 * rnd)[:, None] * bright * 1.2, cols)
        cols = np.where(front[:, None], np.array([1.0, 1.0, 0.95], np.float32)[None] * 1.4, cols)
    sel = ok
    ix = px[sel].astype(int); iy = py[sel].astype(int)
    cc = cols[sel]
    np.add.at(cv, (iy, ix), cc)
    big = cc.sum(1) > 1.0
    np.add.at(cv, (np.clip(iy[big] + 1, 0, H - 1), ix[big]), cc[big] * 0.5)
    np.add.at(cv, (iy[big], np.clip(ix[big] + 1, 0, W - 1)), cc[big] * 0.5)
    glow(cv, cx, cy, R * 0.42, core * 0.7 * bright, 1.0, 2.4, ry=R * 0.42 * tilt)
    glow(cv, cx, cy, R * 1.1, arm * 0.35 * bright, 1.0, 2.6, ry=R * 1.1 * tilt)


# ======================================================================
# SCENE 7 - the galaxy
# ======================================================================
CULT = [
    dict(sky=((0.15, 0.45, 0.55), (0.95, 0.65, 0.60)), skin=(0.70, 0.50, 0.38), hair=(0.08, 0.08, 0.14), hs="crest", outfit=(0.12, 0.45, 0.55),
         o2=(0.95, 0.75, 0.30), hat="halo", patch="collar", arch="spires"),
    dict(sky=((0.28, 0.20, 0.55), (0.80, 0.55, 0.80)), skin=(0.94, 0.78, 0.68), hair=(0.55, 0.20, 0.10), hs="long", outfit=(0.55, 0.22, 0.50),
         o2=(0.95, 0.92, 0.80), hat="turban", patch="brow", arch="islands"),
    dict(sky=((0.85, 0.40, 0.15), (1.00, 0.80, 0.45)), skin=(0.45, 0.30, 0.24), hair=(0.05, 0.05, 0.06), hs="cap", outfit=(0.22, 0.24, 0.30),
         o2=(0.55, 0.60, 0.70), hat="visor", patch="shoulder", arch="blocks"),
    dict(sky=((0.02, 0.05, 0.22), (0.20, 0.30, 0.60)), skin=(0.60, 0.80, 0.72), hair=(0.15, 0.35, 0.35), hs="bald", outfit=(0.75, 0.78, 0.88),
         o2=(0.45, 0.55, 0.85), hat="antenna", patch="chest", arch="ring"),
    dict(sky=((0.70, 0.85, 0.95), (0.98, 0.98, 1.0)), skin=(0.86, 0.66, 0.56), hair=(0.9, 0.9, 0.95), hs="bun", outfit=(0.35, 0.50, 0.70),
         o2=(0.92, 0.95, 1.0), hat="hood", patch="brow", arch="domes"),
]


def culture_card(cv, t, c, x0, y0, w, h, tl):
    """Draw a culture panel into cv inside the box; uses a temp canvas + rounded mask."""
    tmp = np.zeros_like(cv)
    cx = x0 + w / 2
    top = np.asarray(c["sky"][0], np.float32); bot = np.asarray(c["sky"][1], np.float32)
    vgrad(tmp, y0, y0 + h, top, bot)
    if c["arch"] == "spires":
        for i in range(7):
            hh = 70 + (i * 53 % 110); bx = x0 + 30 + i * (w - 60) / 6
            rrect(tmp, bx, y0 + h - hh / 2 - 20, 18, hh / 2, 8, (0.8, 0.95, 1.0), gloss=0.5)
            glow(tmp, bx, y0 + h - hh - 20, 20, (1, 0.9, 0.7), 0.4, 2.0)
    elif c["arch"] == "islands":
        for i in range(4):
            ix = x0 + 60 + i * 100 + 10 * math.sin(t * 1.3 + i); iy = y0 + 60 + (i * 47 % 120) + 6 * math.sin(t * 1.7 + i)
            ell(tmp, ix, iy, 46, 12, (0.45, 0.75, 0.4)); ell(tmp, ix, iy + 14, 30, 16, (0.5, 0.35, 0.3))
            circ(tmp, ix - 14, iy - 10, 9, (0.2, 0.55, 0.3))
    elif c["arch"] == "blocks":
        for i in range(8):
            hh = 60 + (i * 37 % 120); bx = x0 + 24 + i * (w - 48) / 7
            rrect(tmp, bx, y0 + h - hh / 2 - 10, 20, hh / 2, 4, (0.22, 0.2, 0.28))
            for k in range(int(hh / 20)):
                rrect(tmp, bx, y0 + h - 18 - k * 20, 10, 3, 1, (1.0, 0.85, 0.4), flat=True)
    elif c["arch"] == "ring":
        ring(tmp, cx, y0 + h + 140, 280, 280, 18, (0.8, 0.85, 1.0), 0.9)
        for i in range(12):
            a = -math.pi * (0.2 + 0.6 * i / 11)
            circ(tmp, cx + math.cos(a) * 280, y0 + h + 140 + math.sin(a) * 280, 3, (1, 0.9, 0.6), flat=True)
        starfield(tmp, t, n=140, ymax=int(y0 + h))
    elif c["arch"] == "domes":
        for i in range(5):
            r_ = 40 + (i * 29 % 40); bx = x0 + 40 + i * (w - 80) / 4
            ell(tmp, bx, y0 + h - 12, r_, r_ * 0.8, (0.95, 0.97, 1.0), clip_y=y0 + h - 12, gloss=0.4)
    # faded star carved on the wall / sky
    star(tmp, x0 + 56, y0 + 52, 22, (1.0, 0.6, 0.2), a=0.35, flat=True)
    # portrait
    set_light((-0.5, -0.6, 0.62), 0.45, rim_dir=(0.8, -0.3), rim_col=(1.0, 0.9, 0.7), rim_amt=0.5)
    bust(tmp, cx + 40, y0 + h + 6, 1.55, skin=c["skin"], hair=c["hair"], hair_style=c["hs"], outfit=c["outfit"], outfit2=c["o2"],
         hat=c["hat"], patch=c["patch"], faded=0.6, expr="smile", t=t, blink=0.0)
    tmp *= 1.0
    # rounded mask + border
    X = XX; Y = YY
    qx = np.abs(X - cx) - (w / 2 - 26); qy = np.abs(Y - (y0 + h / 2)) - (h / 2 - 26)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - 26
    m = np.clip(0.5 - d, 0, 1)
    k = tl
    cv += (tmp - cv) * (m * k)[..., None]
    br = np.clip(2.0 - np.abs(d + 1.0), 0, 1) * 0.6 * k
    cv += br[..., None] * np.array([1.0, 0.9, 0.75], np.float32)


def scene7(cv, t):
    u = t - 48.0
    set_light((-0.5, -0.6, 0.62), 0.4)
    fill_bg(cv, (0.04, 0.02, 0.12), (0.10, 0.04, 0.20))
    starfield(cv, t, n=300, bright=0.7, tint=(0.9, 0.85, 1.0))
    cx, cy = 270, 215
    R = lerp(115, 175, ease_io(u / 8.0))
    ang = 0.25 + u * 0.035
    origin = (0.52, 0.12)
    wave = ease_io((u - 0.4) / 8.0) * 1.9
    # world->screen origin position for pulse
    draw_galaxy_pts(cv, GAL, cx, cy, R, ang, 0.62, (1.0, 0.92, 0.75), (0.55, 0.45, 1.0), 1.0, colonize=True, wave=wave, origin=origin)
    ca, sa = math.cos(ang), math.sin(ang)
    ox = cx + (origin[0] * ca - origin[1] * sa) * R; oy = cy + (origin[0] * sa + origin[1] * ca) * R * 0.62
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    glow(cv, ox, oy, 26, (1.0, 0.9, 0.5), 0.9 * pulse, 2.0)
    circ(cv, ox, oy, 2.5, (1, 1, 1), flat=True)
    if u < 3.0:
        for dx, dy in ((0, 0),):
            ring(cv, ox, oy, 12 + 8 * (u % 1), (12 + 8 * (u % 1)) * 0.6, 1.4, (1.0, 0.95, 0.6), 0.8 * (1 - (u % 1)))
    # culture cards
    times = [49.2, 50.8, 52.4, 54.0, 55.6]
    for i, tc in enumerate(times):
        te = tc + 1.6 if i < 4 else 56.9
        if tc <= t < te:
            k = smooth((t - tc) / 0.18) * (1 - smooth((t - (te - 0.12)) / 0.12))
            off = (1 - smooth((t - tc) / 0.25)) * 40
            culture_card(cv, t, CULT[i], 56 + off * 0, 345, 428, 280, k)


# ======================================================================
# SCENE 8 - the limit
# ======================================================================
_gr = np.random.default_rng(77)
FAR_N = 150
FAR_D = 0.55 + _gr.random(FAR_N) ** 0.8 * 2.2
FAR_A = _gr.random(FAR_N) * 6.28
FAR_S = 0.6 + _gr.random(FAR_N) * 1.4
FAR_T = _gr.random(FAR_N) * 6.28
FAR_E = _gr.random(FAR_N)


def scene8(cv, t):
    u = t - 57.0
    set_light((-0.5, -0.6, 0.62), 0.4)
    fill_bg(cv, (0.03, 0.01, 0.09), (0.09, 0.03, 0.16))
    cx, cy = 270, 430
    zoom = lerp(3.0, 0.5, ease_io((u - 0.2) / 5.5))
    starfield(cv, t, n=260, bright=0.55, tint=(0.9, 0.85, 1.0))
    # reachable horizon
    hor = 0.9 * zoom * 150
    fade_rec = smooth((u - 3.0) / 4.0)
    recede = smooth((u - 3.5) / 5.0)
    # far galaxies
    for i in range(FAR_N):
        D = FAR_D[i]
        outside = D > 1.0
        k = 1 + (recede * (0.9 + 1.5 * FAR_E[i]) if outside else 0.0)
        r = D * 150 * zoom * k
        x = cx + math.cos(FAR_A[i]) * r; y = cy + math.sin(FAR_A[i]) * r * 0.9
        if not (-20 < x < W + 20 and -20 < y < H + 20): continue
        br = 1.0 if not outside else max(0.0, 1.0 - recede * 1.15)
        if br <= 0.02: continue
        warm = recede * 0.9 if outside else 0.0
        c = np.array([0.8, 0.85, 1.0], np.float32) * (1 - warm) + np.array([1.0, 0.25, 0.1], np.float32) * warm
        s = FAR_S[i] * max(0.5, min(1.0, zoom * 0.7))
        ell(cv, x, y, 5 * s, 2.6 * s, c * br * 0.9, ang=FAR_T[i], flat=True, a=0.9)
        glow(cv, x, y, 9 * s, c * br, 0.5, 2.0)
    # horizon ring (dashed gold)
    if u > 2.2:
        a_ = smooth((u - 2.2) / 1.2) * 0.8
        ring(cv, cx, cy, hor, hor * 0.9, 1.8, (1.0, 0.8, 0.4), a_, arc=lambda ang: (np.sin(ang * 36) > -0.1).astype(np.float32))
    # Andromeda
    ax = cx + 0.45 * 150 * zoom * 1.0; ay = cy - 0.26 * 150 * zoom
    if zoom < 2.6:
        draw_galaxy_pts(cv, GAL_B, ax, ay, 46 * zoom * 1.1, -0.6, 0.38, (1.0, 0.9, 0.8), (0.6, 0.6, 1.0), 0.9 * smooth((3.0 - zoom) / 1.0))
    # Milky Way (gold: settled)
    R = 150 * zoom * 0.6 * (1.0 if zoom > 0.6 else zoom / 0.6 * 1.0 + 0.0)
    draw_galaxy_pts(cv, GAL, cx, cy, R, 0.25 + 0.035 * 8, 0.62, (1.0, 0.92, 0.75), (1.0, 0.75, 0.35), 1.0)
    glow(cv, cx, cy, 12 + 40 * (1 - fade_rec * 0), (1.0, 0.85, 0.5), 0.5, 2.0)


FN = [None, None, None, None, scene5, scene6, scene7, scene8, None]
