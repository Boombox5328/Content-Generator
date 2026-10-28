"""Scenes 1-4: Moon (hook), Moon base, Mars, outer solar system."""
import math
import numpy as np
from gfx import *
from chars import *
import spec

SUN_L = (-0.55, -0.45, 0.70)


class Cam:
    """Parallax camera: depth 0 = far (moves little), 1 = near."""
    def __init__(s, z=1.0, px=0.0, py=0.0, cx=W / 2, cy=H / 2):
        s.z, s.px, s.py, s.cx, s.cy = z, px, py, cx, cy

    def p(s, x, y, d=1.0):
        k = 0.2 + 0.8 * d
        return s.cx + (x - s.cx - s.px * k) * s.z, s.cy + (y - s.cy - s.py * k) * s.z

    def r(s, v): return v * s.z


def seg(cv, t, segs, fade=0.28):
    """segs: [(t0, t1, fn)]. Crossfade between consecutive segments."""
    for i, (t0, t1, fn) in enumerate(segs):
        if t0 <= t < t1:
            nxt = segs[i + 1] if i + 1 < len(segs) else None
            if nxt and t > t1 - fade:
                f = smooth((t - (t1 - fade)) / fade)
                b = np.zeros_like(cv); fn(cv, t); nxt[2](b, t)
                cv += (b - cv) * f
            else:
                fn(cv, t)
            return
    segs[-1][2](cv, t)


def pcol(v, lo, hi):
    return np.asarray(lo, np.float32) * (1 - v) + np.asarray(hi, np.float32) * v


def dust_puff(cv, x, y, r, color, a):
    if a <= 0: return
    ell(cv, x, y, r, r * 0.6, np.asarray(color, np.float32), a=a * 0.8, flat=True)


# ======================================================================
# MOON
# ======================================================================
MOON_G0 = col(0.74, 0.74, 0.80); MOON_G1 = col(0.40, 0.41, 0.50)


def moon_ground(cv, horizon, cam, seed=3):
    r = np.random.default_rng(seed)
    y0 = int(cam.p(0, horizon, 0.3)[1])
    if y0 < H:
        Y = YY[max(0, y0):]; X = XX[max(0, y0):]
        f = np.clip((Y - y0) / (H - y0 + 1e-3), 0, 1)
        base = MOON_G0 * (1 - f[..., None] * 0.55) + MOON_G1 * (f[..., None] * 0.55)
        n = tex(NZ_A, (X + cam.px * 0.5) / 190.0, Y / 140.0)
        n2 = tex(NZ_C, (X + cam.px * 0.5) / 60.0, Y / 50.0)
        base = base * (0.82 + 0.3 * n[..., None] + 0.08 * (n2[..., None] - 0.5))
        sub = cv[max(0, y0):]
        sub[:] = base
        # hazy horizon glow
        g = np.clip(1 - (Y - y0) / 40.0, 0, 1) ** 2
        sub += g[..., None] * np.array([0.14, 0.14, 0.2], np.float32)
    # craters
    for i in range(14):
        wx = r.random() * W * 1.4 - 60; wy = horizon + 30 + r.random() * (H - horizon)
        d = 0.35 + 0.65 * (wy - horizon) / (H - horizon)
        cx_, cy_ = cam.p(wx, wy, d)
        rx = (18 + r.random() * 46) * d * cam.z; ry = rx * 0.36
        ell(cv, cx_, cy_, rx, ry, MOON_G1 * 0.78, flat=True, a=0.55)
        ell(cv, cx_ + rx * 0.06, cy_ - ry * 0.12, rx * 0.88, ry * 0.8, MOON_G0 * 0.8, flat=True, a=0.35)
    for i in range(30):
        wx = r.random() * W * 1.4 - 60; wy = horizon + 20 + r.random() * (H - horizon)
        d = 0.3 + 0.7 * (wy - horizon) / (H - horizon)
        cx_, cy_ = cam.p(wx, wy, d)
        circ(cv, cx_, cy_, (2 + r.random() * 4) * d * cam.z, MOON_G0 * 0.85)


def moon_stage(cv, t, z, fx, fy, ava):
    """Shared by scene 1 and the closing scene. World = 540x960 layout; Ava at (170, 770)."""
    set_light(SUN_L, 0.40, rim_dir=(0.8, -0.5), rim_col=(0.45, 0.65, 1.0), rim_amt=0.6)
    fill_bg(cv, (0.01, 0.015, 0.05), (0.03, 0.05, 0.12))
    starfield(cv, t, off=(-fx * 0.04, -fy * 0.04), n=380, bright=0.9)
    S = lambda x, y: (W / 2 + (x - fx) * z, H / 2 + (y - fy) * z)
    ex, ey = S(350, 330)
    sphere(cv, ex, ey, 92 * z, earth_tex(t), SUN_L, 0.10, rot=t * 0.12, atmo=(0.25, 0.45, 1.0), halo=(0.10, 0.22, 0.55), spec=0.12)
    # ground = huge disc
    gx, gy = S(200, 770 + 2600)
    circ(cv, gx, gy, 2600 * z, MOON_G0 * 0.92, bevel=60 * z, rim=False, amb=0.62)
    # ground detail via noise on the visible lunar surface
    gy0 = int(max(0, S(0, 770)[1] - 6))
    if gy0 < H:
        Y = YY[gy0:]; X = XX[gy0:]
        n = tex(NZ_A, (X / z + fx) / 120.0, (Y / z + fy) / 90.0)
        n2 = tex(NZ_C, (X / z + fx) / 30.0, (Y / z + fy) / 24.0)
        sub = cv[gy0:]
        hmask = (np.sqrt((X - gx) ** 2 + (Y - gy) ** 2) < 2600 * z).astype(np.float32)[..., None]
        sub *= 1 - hmask * (0.28 - 0.5 * (n[..., None] * 0.35 + n2[..., None] * 0.08 - 0.15))
        # earthshine tint toward horizon
        gl = np.clip(1 - (Y - gy0) / (80 * z), 0, 1) ** 2
        sub += gl[..., None] * np.array([0.06, 0.1, 0.2], np.float32) * hmask
    # craters & rocks
    rr = np.random.default_rng(8)
    for i in range(9):
        wx = 20 + rr.random() * 460; wy = 800 + rr.random() * 230
        cx_, cy_ = S(wx, wy)
        rx = (24 + rr.random() * 60) * z
        ell(cv, cx_, cy_, rx, rx * 0.32, MOON_G1 * 0.7, flat=True, a=0.5)
        ell(cv, cx_ + rx * 0.05, cy_ - rx * 0.05, rx * 0.9, rx * 0.26, MOON_G0 * 0.85, flat=True, a=0.4)
    for i in range(14):
        cx_, cy_ = S(rr.random() * 560 - 10, 790 + rr.random() * 200)
        circ(cv, cx_, cy_, (2.5 + rr.random() * 5) * z, MOON_G0 * 0.8)
    # Ava
    ax, ay = S(170 + ava.get("dx", 0), 770 + ava.get("dy", 0))
    kw = {k: v for k, v in ava.items() if k not in ("dx", "dy")}
    sc = 1.25 * z
    # soft contact shadow
    ell(cv, ax + 14 * sc, ay + 2 * sc, 36 * sc, 7 * sc, (0.0, 0.0, 0.04), a=0.4, flat=True)
    return person(cv, ax, ay, sc, t, **kw)


def scene1(cv, t):
    z = lerp(5.4, 1.0, ease_io(t / 2.6))
    pan = ease_io((t - 2.0) / 2.0)
    fx0 = lerp(171, 270, ease_io(t / 2.6)); fy0 = lerp(612, 560, ease_io(t / 2.6))
    fx = lerp(fx0, 338, pan); fy = lerp(fy0, 392, pan)
    z = z * lerp(1.0, 1.22, pan)
    blink = 1.0 if 1.05 < t < 1.18 else 0.0
    look = (lerp(0.0, 0.9, smooth((t - 2.0) / 1.0)), lerp(0.0, -0.7, smooth((t - 2.0) / 1.0)))
    expr = "awe" if t < 1.8 else "smile"
    refl = dict(tex=earth_tex(t), size=lerp(0.62, 0.4, smooth(t / 2.5)), alpha=0.85, dx=-0.18, dy=-0.12)
    moon_stage(cv, t, z, fx, fy, dict(expr=expr, blink=blink, look=look, reflect=refl, arm_r=0.12, arm_l=0.12))


def scene9(cv, t):
    u = t - 66.0
    step = smooth((u - 0.3) / 1.4)
    walk = math.sin(step * math.pi) * 0.8 if 0.3 < u < 1.7 else 0.0
    gl = 0.55 + 0.45 * math.sin(u * 5.0)
    z = 1.05 + 0.03 * u
    moon_stage(cv, t, z, 318, 470 - 4 * u, dict(expr="smile", look=(0.9, -0.7), walk=walk, dx=12 * step, glow_patch=gl, arm_r=0.3, arm_l=0.1, lean=0.0))
    # Earth glow pulse
    glow(cv, W / 2 + 32 * z, H / 2 - 140 * z, 200, (0.1, 0.2, 0.5), 0.35 * gl, 2.0)


# ======================================================================
# SCENE 2 - lunar base
# ======================================================================
def drone(cv, x, y, s, t):
    bob = math.sin(t * 3.1) * 4 * s
    y += bob
    ell(cv, x, y + 38 * s, 20 * s, 4 * s, (0, 0, 0.03), a=0.25, flat=True)
    for sg in (-1, 1):
        capsule(cv, x, y, x + sg * 30 * s, y - 12 * s, 2.5 * s, (0.7, 0.72, 0.8), flat=True)
        spin = (t * 40) % 6.28
        ell(cv, x + sg * 30 * s, y - 14 * s, 15 * s, 2.5 * s * (0.5 + 0.5 * abs(math.sin(spin))), (0.9, 0.95, 1.0), a=0.5, flat=True)
    circ(cv, x, y, 17 * s, (0.96, 0.96, 0.98), gloss=0.3)
    circ(cv, x, y + 1 * s, 10 * s, (0.05, 0.08, 0.18), gloss=0.7)
    circ(cv, x + 1 * s, y, 5.5 * s, (0.3, 0.6, 1.0), flat=True)
    circ(cv, x - 1 * s, y - 2 * s, 1.8 * s, (1, 1, 1), flat=True)
    if int(t * 2) % 2 == 0:
        circ(cv, x + 13 * s, y - 12 * s, 2.5 * s, (1.0, 0.2, 0.2), flat=True)
        glow(cv, x + 13 * s, y - 12 * s, 14 * s, (1.0, 0.2, 0.2), 0.6, 2.0)


def solar_panel(cv, x, y, s, t, k, d_light):
    if k <= 0: return
    s = s * ease_out(k * 1.6)
    capsule(cv, x, y, x, y - 26 * s, 2.2 * s, (0.7, 0.7, 0.78), flat=True)
    pts = [(x - 24 * s, y - 24 * s), (x + 26 * s, y - 32 * s), (x + 22 * s, y - 52 * s), (x - 28 * s, y - 44 * s)]
    poly(cv, pts, (0.10, 0.20, 0.50), (0.05, 0.10, 0.30))
    for i in range(1, 4):
        a = i / 4
        line(cv, lerp(pts[0][0], pts[3][0], 0), lerp(pts[0][1], pts[3][1], 0), pts[0][0], pts[0][1], 0.1, (0, 0, 0), 0)
        p0 = (lerp(pts[0][0], pts[1][0], a), lerp(pts[0][1], pts[1][1], a)); p1 = (lerp(pts[3][0], pts[2][0], a), lerp(pts[3][1], pts[2][1], a))
        line(cv, p0[0], p0[1], p1[0], p1[1], 0.9, (0.4, 0.55, 0.9), 0.7)
    line(cv, (pts[0][0] + pts[3][0]) / 2, (pts[0][1] + pts[3][1]) / 2, (pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2, 0.9, (0.4, 0.55, 0.9), 0.7)
    gl = max(0.0, math.sin(t * 2.2 + d_light)) ** 8
    if gl > 0.05:
        glow(cv, x, y - 38 * s, 26 * s, (0.6, 0.8, 1.0), gl * 0.8, 2.0)


def habitat(cv, x, y, r, inflate, cover, t, lit):
    """dome habitat at ground point (x,y); inflate 0..1, cover 0..1 (regolith)."""
    ry = r * 0.78 * ease_out(inflate) + 1
    rx = r * (0.5 + 0.5 * ease_out(inflate))
    ell(cv, x, y + 3, rx * 1.15, r * 0.2, (0, 0, 0.04), a=0.3, flat=True)
    ell(cv, x, y, rx, ry, (0.96, 0.96, 0.98), clip_y=y, gloss=0.35)
    for k in (-0.5, 0.0, 0.5):                          # ribs
        ell(cv, x + k * rx * 0.6, y, rx * (1 - abs(k) * 0.8) * 0.9, ry * 0.97, (0.7, 0.72, 0.8), clip_y=y, flat=True, a=0.0)
        ring(cv, x + k * rx * 0.5, y, max(1, rx * (0.45 - abs(k) * 0.2)), ry * 0.97, 1.6, (0.62, 0.65, 0.76), 0.8,
             arc=lambda ang: (np.sin(ang) < 0).astype(np.float32))
    if cover > 0:
        mr = ry * 1.12 * cover
        ell(cv, x, y + 1, rx * 1.18, mr, MOON_G1 * 0.95 + np.array([0.05, 0.03, 0.0], np.float32), clip_y=y + 1, bevel=mr * 0.8)
        for i in range(6):
            ell(cv, x - rx * 0.8 + rx * 1.6 * ((i * 0.37) % 1.0), y - mr * (0.2 + 0.5 * ((i * 0.61) % 1.0)), 5 + (i % 3) * 2, 3, MOON_G0 * 0.7, flat=True, a=0.5)
    if cover > 0.4:
        # lit airlock window
        circ(cv, x + rx * 0.62, y - 6, 4.5, (1.0, 0.85, 0.5), flat=True)
        glow(cv, x + rx * 0.62, y - 6, 22, (1.0, 0.7, 0.3), lit * 0.6, 2.0)


def rover(cv, x, y, s, t, carrying, face=1):
    ell(cv, x, y + 9 * s, 20 * s, 4 * s, (0, 0, 0.03), a=0.3, flat=True)
    for wx in (-12, 12):
        circ(cv, x + wx * s, y + 5 * s, 6.5 * s, (0.2, 0.2, 0.26))
    rrect(cv, x, y - 4 * s, 18 * s, 9 * s, 5 * s, (0.95, 0.75, 0.2))
    rrect(cv, x + 4 * face * s, y - 13 * s, 8 * s, 5 * s, 3 * s, (0.15, 0.2, 0.35), flat=True)
    circ(cv, x + 6 * face * s, y - 13 * s, 2 * s, (0.5, 1.0, 0.9), flat=True)
    capsule(cv, x - 10 * face * s, y - 8 * s, x - 18 * face * s, y - 18 * s, 2.5 * s, (0.7, 0.7, 0.78), flat=True)
    if carrying > 0:
        ell(cv, x - 20 * face * s, y - 18 * s, 7 * s, 4 * s, MOON_G1, a=carrying)


def scene2(cv, t):
    u = t - 4.0
    set_light(SUN_L, 0.42, rim_dir=(0.8, -0.4), rim_col=(0.5, 0.7, 1.0), rim_amt=0.45)
    z = lerp(1.0, 1.14, smooth(u / 7.0))
    cam = Cam(z, px=lerp(-8, 24, u / 7), py=lerp(0, 14, u / 7))
    fill_bg(cv, (0.01, 0.015, 0.05), (0.05, 0.07, 0.16))
    starfield(cv, t, off=(cam.px * 0.2, 0), n=340, bright=0.85)
    ex, ey = cam.p(110, 150, 0.05)
    sphere(cv, ex, ey, 36 * z, earth_tex(t), SUN_L, 0.1, rot=t * 0.2, atmo=(0.25, 0.45, 1.0), halo=(0.1, 0.2, 0.5))
    horizon = 430
    # crater rim ridge (far)
    rim_pts = [(-40, horizon + 20)]
    for i in range(0, 12):
        xx = -40 + i * 52
        rim_pts.append((xx, horizon - 14 - 14 * math.sin(i * 1.3) - 8 * math.sin(i * 0.5)))
    rim_pts += [(W + 60, horizon + 20), (W + 60, horizon + 70), (-40, horizon + 70)]
    rp = [cam.p(x, y, 0.3) for x, y in rim_pts]
    poly(cv, rp, (0.52, 0.53, 0.62), (0.34, 0.35, 0.44))
    moon_ground(cv, horizon + 8, cam)
    # solar panels on rim
    for i in range(9):
        wx = 20 + i * 58; wy = horizon - 8 - 12 * math.sin(i * 1.3) * 0.4
        k = smooth((u - 0.5 - i * 0.18) / 0.6)
        px_, py_ = cam.p(wx, wy + 26, 0.3)
        solar_panel(cv, px_, py_, 0.62 * z, t, k, i * 0.55)
    # ----- habitats (mid ground)
    HAB = [(130, 590, 78, 0.2), (300, 548, 60, 0.9), (440, 598, 66, 1.6)]
    for (hx, hy, hr, t0) in HAB:
        x_, y_ = cam.p(hx, hy, 0.6)
        infl = smooth((u - t0 * 0.45) / 1.3)
        cover = smooth((u - 2.0 - t0 * 0.8) / 4.2) * 0.9
        if infl > 0:
            habitat(cv, x_, y_, hr * z, infl, cover, t, smooth((u - 3.5) / 2))
    # connecting tunnel
    tx0, ty0 = cam.p(190, 596, 0.6); tx1, ty1 = cam.p(250, 560, 0.6)
    if u > 3.8:
        a_ = smooth((u - 3.8) / 1.0)
        capsule(cv, tx0, ty0, tx1, ty1, 8 * z, (0.82, 0.83, 0.9), a=a_)
    # robots piling regolith
    for i, (hx, hy, hr, t0) in enumerate(HAB):
        ph = (u * 0.55 + i * 0.37) % 1.0
        hxw = hx - hr * 1.3 + (hr * 1.1) * ph if ph < 0.5 else hx - hr * 1.3 + (hr * 1.1) * (1 - ph)
        x_, y_ = cam.p(hx + (-hr * 1.35 + hr * 1.25 * (math.sin(ph * 6.28) * 0.5 + 0.5)), hy + 28, 0.8)
        if u > 1.2 + t0 * 0.5:
            rover(cv, x_, y_, 0.85 * z, t, 1.0 if math.cos(ph * 6.28) > 0 else 0.0, 1 if math.cos(ph * 6.28) > 0 else -1)
            if int(u * 6 + i) % 3 == 0:
                dust_puff(cv, x_ - 14 * z, y_ + 4 * z, 12 * z, (0.7, 0.7, 0.76), 0.5)
    # ----- shadowed crater with ice-mining rig (right foreground)
    kx, ky = cam.p(380, 790, 1.0)
    rx_, ry_ = 190 * z, 92 * z
    ell(cv, kx, ky, rx_ * 1.06, ry_ * 1.1, MOON_G0 * 0.95, flat=True)
    ell(cv, kx, ky + 3 * z, rx_, ry_, (0.03, 0.05, 0.1), flat=True)
    ell(cv, kx, ky + 8 * z, rx_ * 0.9, ry_ * 0.8, (0.02, 0.04, 0.09), flat=True, a=0.8)
    ice_t = smooth((u - 3.0) / 1.2)
    # ice patch glow
    glow(cv, kx - 20 * z, ky + 20 * z, 110 * z, (0.25, 0.7, 1.0), 0.55 * ice_t, 2.0, ry=56 * z)
    for i in range(9):
        a_ = i * 0.9
        ix = kx - 90 * z + (i * 23 % 120) * z; iy = ky + (14 + (i * 13 % 36)) * z
        poly(cv, [(ix, iy), (ix + 7 * z, iy - 14 * z), (ix + 14 * z, iy)], (0.7, 0.95, 1.0), (0.3, 0.7, 0.95), a=ice_t)
    # rig
    rgx, rgy = kx + 40 * z, ky + 6 * z
    if u > 3.0:
        k = ice_t
        for sg in (-1, 1):
            capsule(cv, rgx + sg * 22 * z, rgy + 14 * z, rgx + sg * 6 * z, rgy - 82 * z * k, 3.2 * z, (0.78, 0.8, 0.88), flat=True)
        for yy_ in (-20, -48, -72):
            line(cv, rgx - 16 * z, rgy + yy_ * z * k, rgx + 16 * z, rgy + yy_ * z * k, 2 * z, (0.78, 0.8, 0.88))
        rrect(cv, rgx, rgy - 90 * z * k, 20 * z, 10 * z, 4 * z, (0.95, 0.5, 0.2))
        circ(cv, rgx, rgy - 90 * z * k, 4 * z, (1, 0.9, 0.5), flat=True)
        dr = rgy - 80 * z * k
        capsule(cv, rgx, dr, rgx + math.sin(t * 24) * 2.2 * z, rgy + 18 * z, 3 * z, (0.55, 0.58, 0.66), r1=1.2 * z, flat=True)
        beam(cv, rgx, rgy + 18 * z, rgx - 10 * z, rgy + 40 * z, 14 * z, 26 * z, (0.4, 0.85, 1.0), 0.5 * k)
        # ice cubes up the pipe to tanks
        for j in range(5):
            f = ((u * 0.8 + j / 5) % 1.0)
            cx_ = lerp(rgx, kx - 175 * z, f); cy_ = lerp(rgy - 85 * z, ky - 100 * z, f) - math.sin(f * math.pi) * 28 * z
            rrect(cv, cx_, cy_, 4.5 * z, 4.5 * z, 1.5 * z, (0.7, 0.95, 1.0), flat=True)
            glow(cv, cx_, cy_, 14 * z, (0.4, 0.8, 1.0), 0.6 * k, 2.0)
        line(cv, rgx, rgy - 85 * z, kx - 175 * z, ky - 100 * z, 1.6 * z, (0.7, 0.75, 0.9), 0.35)
        for j in range(2):                              # tanks outside the crater
            tx, ty = kx - 190 * z + j * 36 * z, ky - 84 * z
            rrect(cv, tx, ty, 14 * z, 22 * z, 8 * z, (0.93, 0.94, 0.98), gloss=0.3)
            rrect(cv, tx, ty + 6 * z, 14 * z, 5 * z, 2 * z, (0.3, 0.8, 1.0) if j == 0 else (1.0, 0.6, 0.3), flat=True)
    # ----- Ava waving at the camera drone (foreground left)
    ax, ay = cam.p(96, 905, 1.0)
    blink = 1.0 if int(t * 1.3) % 4 == 0 and (t * 1.3) % 1 < 0.1 else 0.0
    ell(cv, ax + 16 * z, ay + 3 * z, 44 * z, 8 * z, (0, 0, 0.04), a=0.4, flat=True)
    person(cv, ax, ay, 1.35 * z, t, wave=True, expr="grin", look=(0.8, -0.4), blink=blink, arm_l=0.12)
    dx_, dy_ = cam.p(262 + 8 * math.sin(t * 1.4), 700 + 4 * math.sin(t * 0.9), 1.0)
    drone(cv, dx_, dy_, 0.95 * z, t)
    # drone camera light cone toward Ava
    beam(cv, dx_ - 10 * z, dy_ + 6 * z, ax + 18 * z, ay - 140 * z, 4 * z, 34 * z, (0.5, 0.75, 1.0), 0.14)


# ======================================================================
# SCENE 3 - Mars
# ======================================================================
def ship(cv, x, y, s, ang, thrust, t):
    ca, sa = math.cos(ang), math.sin(ang)

    def R(px, py): return x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s
    if thrust > 0:
        ex_, ey_ = R(-34, 0)
        gx, gy = R(-34 - 22 * thrust, 0)
        beam(cv, ex_, ey_, gx, gy, 9 * s, 2 * s, (1.0, 0.7, 0.35), 0.9 * thrust, 1.0)
        glow(cv, ex_, ey_, 26 * s, (1.0, 0.6, 0.25), 0.7 * thrust, 2.0)
    for sg in (-1, 1):                                   # solar wings
        a = R(-6, sg * 12); b = R(-6, sg * 44); c = R(10, sg * 44); d = R(10, sg * 12)
        poly(cv, [a, b, c, d], (0.15, 0.3, 0.7), (0.08, 0.15, 0.45))
        for k in (0.33, 0.66):
            p0 = R(-6 + 16 * k, sg * 12); p1 = R(-6 + 16 * k, sg * 44)
            line(cv, p0[0], p0[1], p1[0], p1[1], 0.8 * s, (0.5, 0.65, 1.0), 0.6)
    bx, by = R(0, 0)
    rrect(cv, bx, by, 32 * s, 12 * s, 8 * s, (0.95, 0.95, 0.97), ang=ang, gloss=0.3)
    nx, ny = R(30, 0)
    circ(cv, nx, ny, 10 * s, (0.95, 0.5, 0.2))
    wx, wy = R(8, 0)
    circ(cv, wx, wy, 4 * s, (0.25, 0.55, 0.95), flat=True)
    star(cv, *R(-14, 0), 5 * s, ORANGE, ang=ang, flat=True)


MARS_SKY0 = col(0.45, 0.17, 0.12); MARS_SKY1 = col(0.98, 0.66, 0.42)


def mars_orbit(cv, t):
    u = t - 11.0
    set_light((-0.7, -0.5, 0.55), 0.08, rim_dir=(0.8, -0.3), rim_col=(1.0, 0.6, 0.3), rim_amt=0.4)
    fill_bg(cv, (0.02, 0.01, 0.02), (0.06, 0.03, 0.04))
    starfield(cv, t, n=360, bright=0.9, tint=(1.0, 0.92, 0.85))
    z = lerp(0.8, 1.15, ease_io(u / 2.6))
    mx, my = 340, 780
    sphere(cv, mx, my, 330 * z, mars_tex(t), (-0.7, -0.5, 0.55), 0.06, rot=t * 0.1, atmo=(1.0, 0.55, 0.3), halo=(0.5, 0.2, 0.1), spec=0.04)
    # Earth + dotted journey time-lapse
    ex, ey = 72, 160
    sphere(cv, ex, ey, 20, earth_tex(t), SUN_L, 0.1, atmo=(0.3, 0.5, 1.0), halo=(0.1, 0.2, 0.5))
    P0 = np.array([ex, ey]); P1 = np.array([300, 120]); P2 = np.array([430, 520])
    prog = ease_io(u / 2.4)
    for i in range(46):
        a = i / 45
        if a > prog: break
        q = (1 - a) ** 2 * P0 + 2 * (1 - a) * a * P1 + a * a * P2
        circ(cv, q[0], q[1], 1.6 + 1.2 * a, (1.0, 0.85, 0.6), flat=True, a=0.35 + 0.6 * a)
    a = prog
    q = (1 - a) ** 2 * P0 + 2 * (1 - a) * a * P1 + a * a * P2
    dq = 2 * (1 - a) * (P1 - P0) + 2 * a * (P2 - P1)
    ang = math.atan2(dq[1], dq[0])
    ship(cv, q[0], q[1], 1.0 + 0.5 * prog, ang, 0.2 + 0.8 * (1 - prog) ** 0.5 * (u > 1.2), t)


def mars_ground_bg(cv, t, night=0.0, cam=None):
    cam = cam or Cam()
    top = pcol(night, MARS_SKY0, (0.03, 0.02, 0.08)); bot = pcol(night, MARS_SKY1, (0.30, 0.13, 0.12))
    fill_bg(cv, top, bot, 0, 600)
    if night > 0.2:
        starfield(cv, t, n=300, bright=night, ymax=520, tint=(1.0, 0.9, 0.95))
    # pale small sun with blue halo (day)
    sx, sy = cam.p(110 + 280 * 0, 170, 0.1)
    glow(cv, sx, sy, 90, (0.55, 0.7, 1.0), 0.5 * (1 - night), 2.0)
    circ(cv, sx, sy, 11, (1, 0.96, 0.9), flat=True, a=1 - night)
    # ridges
    for k, (hh, c, dd) in enumerate(((60, (0.62, 0.30, 0.22), 0.1), (36, (0.55, 0.24, 0.18), 0.25), (18, (0.46, 0.2, 0.15), 0.5))):
        pts = [(-30, 560)]
        for i in range(0, 12):
            pts.append((-30 + i * 52, 548 - hh * (0.5 + 0.5 * math.sin(i * 1.7 + k * 2.1)) - hh * 0.2 * math.sin(i * 0.6)))
        pts += [(W + 40, 560), (W + 40, 700), (-30, 700)]
        cc = np.asarray(c, np.float32) * (1 - night * 0.7)
        poly(cv, [cam.p(x, y, dd) for x, y in pts], cc * 1.05, cc * 0.8)
    hy = int(cam.p(0, 556, 0.5)[1])
    Y = YY[hy:]; X = XX[hy:]
    f = np.clip((Y - hy) / (H - hy), 0, 1)[..., None]
    g0 = np.asarray((0.80, 0.40, 0.22), np.float32) * (1 - night * 0.75); g1 = np.asarray((0.5, 0.2, 0.12), np.float32) * (1 - night * 0.75)
    n = tex(NZ_A, (X + cam.px * 0.5) / 160.0, Y / 120.0); n2 = tex(NZ_C, (X + cam.px * 0.5) / 40.0, Y / 32.0)
    cv[hy:] = (g0 * (1 - f) + g1 * f) * (0.82 + 0.34 * n[..., None] + 0.1 * (n2[..., None] - 0.5))
    rr = np.random.default_rng(11)
    for i in range(36):
        x_, y_ = cam.p(rr.random() * 600 - 30, 580 + rr.random() * 380, 0.9)
        circ(cv, x_, y_, 2 + rr.random() * 7, (0.42, 0.2, 0.14) if rr.random() < 0.7 else (0.7, 0.38, 0.24))


def mars_landing(cv, t):
    u = t - 13.4
    set_light((-0.4, -0.5, 0.75), 0.44, rim_dir=(0.8, -0.4), rim_col=(1.0, 0.7, 0.4), rim_amt=0.5)
    cam = Cam(1.0 + 0.04 * u, px=-6 + 8 * u, py=0)
    mars_ground_bg(cv, t, 0.0, cam)
    land = smooth(u / 1.5)
    ys = lerp(-80, 690, 1 - (1 - land) ** 2.2)
    xs = 300
    sy = ys
    # ground contact dust
    near = clamp01((ys - 520) / 170)
    if near > 0:
        for i in range(18):
            ang = i / 18 * math.pi
            rr_ = (30 + 190 * near) * (0.6 + 0.4 * ((i * 7) % 5) / 5)
            for sg in (-1, 1):
                dust_puff(cv, xs + sg * rr_ * (0.3 + 0.7 * (i % 6) / 6), 706 - (i % 4) * 6 - 10 * near, 16 + 22 * near, (0.95, 0.62, 0.42), 0.45 * near * (1 - clamp01((u - 1.6) / 0.6)))
    # lander
    thrust = 1.0 if u < 1.4 else max(0.0, 1 - (u - 1.4) * 4)
    ls = 1.5
    if thrust > 0:
        beam(cv, xs, sy + 12, xs, sy + 12 + 90 * thrust, 12, 3, (1.0, 0.7, 0.3), 0.9 * thrust)
        glow(cv, xs, sy + 18, 60, (1.0, 0.6, 0.25), 0.7 * thrust, 2.0)
    for sg in (-1, 1):
        a = (xs + sg * 18 * ls, sy)
        capsule(cv, a[0], a[1] - 6 * ls, xs + sg * 40 * ls, sy + 30 * ls, 3 * ls, (0.7, 0.72, 0.8), flat=True)
        ell(cv, xs + sg * 42 * ls, sy + 32 * ls, 9 * ls, 3 * ls, (0.5, 0.52, 0.6))
    rrect(cv, xs, sy - 12 * ls, 22 * ls, 28 * ls, 12 * ls, (0.95, 0.95, 0.97), gloss=0.3)
    circ(cv, xs, sy - 26 * ls, 14 * ls, (0.95, 0.5, 0.2))
    circ(cv, xs, sy - 8 * ls, 7 * ls, (0.25, 0.55, 0.95), flat=True)
    star(cv, xs - 10 * ls, sy + 6 * ls, 5 * ls, ORANGE, flat=True)


def dome(cv, x, y, r, glass_col, glow_col, night, a=1.0, ribs=True):
    if a <= 0: return
    rx = r; ry = r * 0.8
    ell(cv, x, y + 3, rx * 1.1, r * 0.17, (0, 0, 0.03), a=0.35 * a, flat=True)
    inner = np.asarray(glow_col, np.float32) * (0.25 + 0.75 * night)
    ell(cv, x, y, rx, ry, inner * 0.85 + 0.12, clip_y=y, a=a, flat=True)
    glow(cv, x, y - ry * 0.4, rx * 1.2, np.asarray(glow_col, np.float32), 0.55 * night * a, 2.0, ry=ry)
    # plants
    for i in range(5):
        px_ = x + (i - 2) * rx * 0.34
        ell(cv, px_, y - 7 - (i % 2) * 4, rx * 0.12, rx * 0.2, (0.3, 0.85, 0.4) if night > 0.3 else (0.25, 0.6, 0.3), flat=True, a=a)
    ell(cv, x, y, rx, ry, glass_col, clip_y=y, a=0.38 * a, gloss=0.5)
    if ribs:
        for k in (-0.5, 0.0, 0.5):
            ring(cv, x + k * rx * 0.5, y, max(1, rx * (0.5 - abs(k) * 0.25)), ry * 0.98, 1.4, (0.9, 0.95, 1.0), 0.6 * a,
                 arc=lambda ang: (np.sin(ang) < 0).astype(np.float32))


def mars_timelapse(cv, t):
    u = t - 15.2
    set_light((-0.3, -0.6, 0.75), 0.40, rim_dir=(0.8, -0.4), rim_col=(1.0, 0.7, 0.4), rim_amt=0.4)
    night = smooth((u - 1.0) / 1.9)
    cam = Cam(1.0 + 0.05 * u, px=-10 + 16 * u, py=0)
    mars_ground_bg(cv, t, night, cam)
    # sun arcs across sky in time-lapse
    sun_p = clamp01(u / 1.9)
    if sun_p < 1:
        sx = lerp(40, 500, sun_p); sy = 330 - math.sin(sun_p * math.pi) * 230
        glow(cv, sx, sy, 80, (1.0, 0.85, 0.6), 0.6, 2.0)
        circ(cv, sx, sy, 10, (1, 0.96, 0.9), flat=True)
    # underground cutaway strip with tunnels
    strip_top = 700
    sub = cv[strip_top:]
    sub *= 0.0; sub += np.array([0.26, 0.11, 0.08], np.float32)
    n = tex(NZ_A, XX[strip_top:] / 90.0, YY[strip_top:] / 90.0)
    sub *= (0.8 + 0.4 * n[..., None])
    line(cv, 0, strip_top, W, strip_top, 3, (0.9, 0.55, 0.35), 0.9)
    tun = smooth((u - 0.6) / 2.0)
    pts = [(80, strip_top + 60), (200, strip_top + 60), (330, strip_top + 92), (470, strip_top + 92)]
    for i in range(3):
        a_ = smooth(tun * 3 - i)
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        capsule(cv, x0, y0, lerp(x0, x1, a_), lerp(y0, y1, a_), 14, (0.68, 0.7, 0.8), flat=False, a=1.0)
        capsule(cv, x0, y0, lerp(x0, x1, a_), lerp(y0, y1, a_), 9, (0.15, 0.08, 0.1) + np.asarray((1.0, 0.7, 0.35)) * 0.55 * (0.4 + 0.6 * night), flat=True)
    for i, (x0, y0) in enumerate(pts):
        a_ = smooth(tun * 3 - i + 0.4)
        circ(cv, x0, y0, 24 * a_, (0.7, 0.72, 0.82)); circ(cv, x0, y0, 17 * a_, (1.0, 0.82, 0.5), flat=True)
        glow(cv, x0, y0, 70 * a_, (1.0, 0.65, 0.3), 0.5 * night, 2.0)
        for k in range(3):
            circ(cv, x0 - 8 + k * 8, y0 + 4, 2.4 * a_, (0.25, 0.14, 0.12), flat=True)
    # surface structures
    items = [(120, 640, 58, 0.5, "dome"), (260, 612, 44, 1.0, "gh"), (380, 650, 66, 1.4, "dome"), (480, 616, 40, 1.9, "gh"), (60, 612, 34, 2.2, "gh")]
    for (x, y, r, t0, kind) in items:
        k = smooth((u - t0 * 0.7) / 0.7)
        if k <= 0: continue
        px_, py_ = cam.p(x, y, 0.8)
        if kind == "dome":
            dome(cv, px_, py_, r * (0.4 + 0.6 * ease_out(k)) * cam.z, (0.8, 0.9, 1.0), (1.0, 0.82, 0.5), night, k)
        else:
            dome(cv, px_, py_, r * (0.4 + 0.6 * ease_out(k)) * cam.z, (0.7, 1.0, 0.8), (0.4, 1.0, 0.55), night, k, ribs=False)
            for j in range(3):
                pass
    # rover trundling
    rx_ = lerp(60, 480, (u * 0.25) % 1.0)
    rover(cv, rx_, 676, 1.0, t, 0.0, 1)
    if night > 0.4:
        glow(cv, rx_ + 20, 672, 36, (1.0, 0.9, 0.7), 0.5 * night, 2.0)


def mars_child(cv, t):
    u = t - 18.5
    set_light((-0.3, -0.5, 0.75), 0.36, rim_dir=(0.5, -0.8), rim_col=(0.4, 0.7, 1.0), rim_amt=0.7)
    fill_bg(cv, (0.01, 0.01, 0.06), (0.10, 0.05, 0.12))
    zz = 1.0 + 0.06 * u
    starfield(cv, t, off=(0, -u * 3), n=400, bright=1.0, tint=(0.9, 0.9, 1.0))
    # Earth as a tiny blue dot
    ex, ey = 360, 230
    tw = 0.7 + 0.3 * math.sin(t * 3)
    glow(cv, ex, ey, 54, (0.2, 0.5, 1.0), 0.9 * tw, 2.0)
    circ(cv, ex, ey, 4.0, (0.7, 0.9, 1.0), flat=True)
    line(cv, ex - 14, ey, ex + 14, ey, 1, (0.6, 0.85, 1.0), 0.5 * tw); line(cv, ex, ey - 14, ex, ey + 14, 1, (0.6, 0.85, 1.0), 0.5 * tw)
    # dome glass arcs
    for k, rr_ in enumerate((470, 410, 350)):
        ring(cv, 270, 960, rr_, rr_ * 0.95, 2.0, (0.6, 0.8, 1.0), 0.28 - 0.05 * k, arc=lambda a: (np.sin(a) < 0).astype(np.float32))
    for i in range(7):
        ang = math.pi * (0.1 + 0.8 * i / 6)
        line(cv, 270 + 470 * math.cos(ang) * 0.1, 960, 270 + 480 * math.cos(ang), 960 - 450 * math.sin(ang), 1.2, (0.6, 0.8, 1.0), 0.18)
    # floor + plants
    poly(cv, [(0, 800), (W, 800), (W, H), (0, H)], (0.16, 0.10, 0.12), (0.07, 0.04, 0.07))
    for i in range(10):
        px_ = 20 + i * 54; hh = 40 + (i * 37 % 60)
        ell(cv, px_, 800 - hh * 0.4, 16, hh, (0.2, 0.75, 0.4) if i % 2 else (0.3, 0.9, 0.5), ang=(0.3 if i % 2 else -0.3), a=0.9)
        glow(cv, px_, 780 - hh * 0.3, 60, (0.3, 1.0, 0.5), 0.2, 2.0)
    # parent + child looking up at Earth
    s_p = 1.9 * zz
    person(cv, 190, 930, s_p, t, helmet=False, hair=(0.12, 0.07, 0.05), hair_style="long", suit=(0.28, 0.58, 0.62), skin=(0.78, 0.55, 0.42),
           expr="awe", look=(0.7, -0.9), arm_l=0.2, arm_r=0.7, patch_r=9, pack=False)
    person(cv, 330, 930, 1.15 * zz, t, helmet=False, hair=(0.1, 0.06, 0.04), hair_style="cap", suit=(0.92, 0.9, 0.86), skin=(0.9, 0.68, 0.55),
           expr="awe", look=(0.55, -1.0), arm_l=0.15, arm_r=2.9, head_k=1.35, patch_r=9.5, pack=False, blink=1.0 if 0.7 < (t % 3) < 0.78 else 0.0)
    # dotted sight-line from the child's finger to Earth
    for i in range(10):
        a = i / 10
        circ(cv, lerp(372, ex - 8, a), lerp(660, ey + 8, a), 1.6, (0.6, 0.85, 1.0), flat=True, a=0.7 * (1 - a * 0.5))


def scene3(cv, t):
    seg(cv, t, [(11, 13.4, mars_orbit), (13.4, 15.2, mars_landing), (15.2, 18.5, mars_timelapse), (18.5, 21, mars_child)], 0.3)


# ======================================================================
# SCENE 4 - outer solar system
# ======================================================================
def asteroid_scene(cv, t):
    u = t - 21.0
    set_light((-0.6, -0.5, 0.65), 0.24, rim_dir=(0.8, -0.2), rim_col=(0.4, 0.9, 1.0), rim_amt=0.7)
    fill_bg(cv, (0.01, 0.05, 0.09), (0.03, 0.12, 0.20))
    starfield(cv, t, off=(-u * 6, 0), n=380, bright=0.95, tint=(0.8, 1.0, 1.0))
    z = lerp(0.9, 1.1, smooth(u / 3.4))
    cx, cy = 270, 500
    rot = t * 0.35
    # distant rocks
    for i in range(9):
        a_ = i * 1.7 + t * 0.05 * (1 + i % 3)
        circ(cv, 270 + math.cos(a_) * (230 + 20 * i), 120 + (i * 97) % 760, 5 + (i % 4) * 3, (0.35, 0.42, 0.48), bevel=3)
    rock = rock_tex((0.48, 0.5, 0.52))
    sphere(cv, cx - 40 * z, cy + 20 * z, 150 * z, rock, (-0.6, -0.5, 0.65), 0.12, rot=rot, spec=0.0)
    sphere(cv, cx + 100 * z, cy - 20 * z, 98 * z, rock_tex((0.52, 0.5, 0.5), 0.3), (-0.6, -0.5, 0.65), 0.12, rot=rot + 1.0)
    sphere(cv, cx + 10 * z, cy - 110 * z, 70 * z, rock_tex((0.45, 0.5, 0.5), 0.6), (-0.6, -0.5, 0.65), 0.12, rot=rot + 2.0)
    # ore glints (metal veins)
    for i in range(7):
        a = rot * 0.9 + i * 0.95
        if math.cos(a) > 0.1:
            gx = cx - 40 * z + math.sin(a) * 130 * z; gy = cy + 20 * z + math.sin(i * 2.1) * 100 * z
            glow(cv, gx, gy, 14, (1.0, 0.9, 0.5), 0.8 * (0.5 + 0.5 * math.sin(t * 6 + i)), 2.0)
    # miners tethered to spikes
    def miner(spike, pos, flip, k, phase):
        sx_, sy_ = spike
        circ(cv, sx_, sy_, 5, (0.9, 0.55, 0.2), flat=True)
        px_, py_ = pos
        mid = ((sx_ + px_) / 2 + 20 * math.sin(t * 1.3 + phase), (sy_ + py_) / 2 + 24)
        pts = [((1 - a) ** 2 * sx_ + 2 * (1 - a) * a * mid[0] + a * a * px_, (1 - a) ** 2 * sy_ + 2 * (1 - a) * a * mid[1] + a * a * (py_ - 60 * k)) for a in np.linspace(0, 1, 14)]
        for a_, b_ in zip(pts[:-1], pts[1:]):
            line(cv, a_[0], a_[1], b_[0], b_[1], 1.6, (0.95, 0.95, 1.0), 0.8)
        person(cv, px_, py_, 0.75 * k, t, flip=flip, expr="grin" if phase < 1 else "calm", arm_r=1.3 + 0.2 * math.sin(t * 6 + phase), arm_l=0.6,
               lean=0.0, patch=1.0, suit=(0.92, 0.94, 0.97))
        # drill sparks
        for j in range(5):
            f = (t * 3 + j * 0.37 + phase) % 1.0
            circ(cv, px_ + (-1 if flip else 1) * (46 + 14 * f) * k, py_ - 30 * k + (f * 14 - 6), 1.8, (1.0, 0.8 * (1 - f), 0.3), flat=True, a=1 - f)
    k = smooth(u / 0.8)
    miner((cx - 140 * z, cy + 100 * z), (128 + 6 * math.sin(t), 400 + 5 * math.sin(t * 1.3)), False, 1.25 * k, 0.0)
    miner((cx + 140 * z, cy + 60 * z), (430 + 6 * math.sin(t * 1.1), 690 + 4 * math.sin(t)), True, 1.25 * k, 1.3)
    # mining drones
    for i in range(3):
        a_ = t * 0.7 + i * 2.1
        dx_ = cx + math.cos(a_) * 200; dy_ = cy + 20 + math.sin(a_) * 90 * (1 if i % 2 else -1)
        rrect(cv, dx_, dy_, 11, 7, 4, (0.95, 0.75, 0.25))
        circ(cv, dx_ + 4, dy_, 2.6, (0.5, 1, 0.9), flat=True)
        beam(cv, dx_, dy_ + 5, cx + math.cos(a_) * 120, cy + 20 + math.sin(a_) * 60, 2, 8, (0.5, 1.0, 1.0), 0.2)
    glow(cv, 0, 0, 340, (0.4, 0.8, 1.0), 0.25, 2.0)


def europa_scene(cv, t):
    u = t - 24.2
    set_light((-0.3, -0.7, 0.65), 0.34, rim_dir=(0.6, -0.5), rim_col=(0.5, 0.9, 1.0), rim_amt=0.6)
    scroll = smooth((u - 0.5) / 2.0) * 640           # camera pans down
    # space/jupiter sky (top, scrolls away)
    sky_h = 330 - scroll
    fill_bg(cv, (0.04, 0.10, 0.18), (0.30, 0.55, 0.72))
    if sky_h > -250:
        fill_bg(cv, (0.01, 0.02, 0.07), (0.05, 0.10, 0.20), 0, int(max(1, sky_h + 20)))
        starfield(cv, t, n=200, ymax=max(1, int(sky_h)), bright=0.8)
        sphere(cv, 120, sky_h - 120, 160, jupiter_tex(t), (0.6, -0.2, 0.7), 0.12, rot=t * 0.05, halo=(0.35, 0.22, 0.12))
    ice_top = sky_h + 20
    # ice crust with layers
    Y = YY; X = XX
    ice = np.clip((Y - ice_top) / 700.0, 0, 1)
    n = tex(NZ_A, X / 170.0, (Y + scroll * 0.0) / 200.0); n2 = tex(NZ_C, X / 40.0, Y / 38.0)
    c0 = np.array([0.88, 0.96, 1.0], np.float32); c1 = np.array([0.38, 0.62, 0.82], np.float32)
    ice_col = (c0 * (1 - ice[..., None]) + c1 * ice[..., None]) * (0.86 + 0.22 * n[..., None] + 0.06 * (n2[..., None] - 0.5))
    m = (Y >= ice_top)[..., None]
    cv[:] = np.where(m, ice_col, cv)
    # ocean
    oc = 870 - scroll
    Yo = YY[int(max(0, oc)):]
    if oc < H:
        o0 = int(max(0, oc))
        f = np.clip((Yo - oc) / 600.0, 0, 1)[..., None]
        cv[o0:] = np.array([0.02, 0.10, 0.20], np.float32) * (1 - f) + np.array([0.0, 0.02, 0.07], np.float32) * f
        for i in range(60):
            px_ = (i * 97 + t * (8 + i % 7)) % W; py_ = oc + 40 + (i * 53) % 520
            glow(cv, px_, py_, 6 + (i % 3) * 2, (0.2, 0.9, 0.9), 0.5 * (0.5 + 0.5 * math.sin(t * 2 + i)), 2.0)
        line(cv, 0, oc, W, oc, 6, (0.7, 0.9, 1.0), 0.7)
    # station on surface + melt shaft
    sx = 270; shaft_x = 270
    if ice_top > -120:
        for sg in (-1, 1):
            capsule(cv, sx + sg * 40, ice_top + 4, sx + sg * 55, ice_top - 16, 3, (0.6, 0.66, 0.74), flat=True)
        rrect(cv, sx, ice_top - 26, 56, 26, 12, (0.95, 0.95, 0.98), gloss=0.3)
        circ(cv, sx, ice_top - 36, 11, (1.0, 0.6, 0.25))
        circ(cv, sx + 20, ice_top - 22, 4.5, (1, 0.85, 0.5), flat=True)
        capsule(cv, sx - 70, ice_top, sx - 62, ice_top - 36, 2.5, (0.7, 0.72, 0.8), flat=True)
        circ(cv, sx - 62, ice_top - 38, 4, (1.0, 0.45, 0.2), flat=True)
    # sub path: descends along the shaft
    dsc = smooth(u / 2.7)
    sub_y = lerp(ice_top + 40, oc + 160, dsc ** 1.15)
    shaft_top = ice_top + 36
    if sub_y > shaft_top:
        ell(cv, shaft_x, (shaft_top + sub_y) / 2, 24, (sub_y - shaft_top) / 2 + 10, (0.12, 0.20, 0.34), flat=True, a=1.0)
        glow(cv, shaft_x, (shaft_top + sub_y) / 2, 100, (0.35, 0.8, 1.0), 0.35, 2.0, ry=(sub_y - shaft_top) / 2 + 40)
        # steam / bubbles
        for i in range(12):
            f = (t * 0.9 + i / 12) % 1.0
            circ(cv, shaft_x + math.sin(i * 3.3 + t * 2) * 10, lerp(sub_y, shaft_top, f), 1.6 + (i % 3), (0.85, 0.97, 1.0), flat=True, a=0.7 * (1 - f))
    if sub_y > shaft_top + 20 or True:
        in_ocean = sub_y > oc
        beam(cv, shaft_x, sub_y + 8, shaft_x + 34, sub_y + 120, 7, 56, (1.0, 0.95, 0.7), 0.55 if in_ocean else 0.4)
        rrect(cv, shaft_x, sub_y, 22, 14, 8, (1.0, 0.8, 0.2), ang=math.pi / 2 * 0.0 + 1.55, gloss=0.4)
        ell(cv, shaft_x, sub_y - 6, 10, 8, (0.85, 0.95, 1.0), a=0.9, clip_y=sub_y - 4)
        circ(cv, shaft_x, sub_y + 14, 4, (1.0, 1.0, 0.8), flat=True)
        glow(cv, shaft_x, sub_y + 14, 40, (1.0, 0.95, 0.6), 0.9, 2.0)
        spin = t * 30
        ell(cv, shaft_x, sub_y - 18, 14, 2 + 3 * abs(math.sin(spin)), (0.7, 0.75, 0.85), flat=True, a=0.8)
    # curious glowing sea creature
    if u > 1.8:
        fa = smooth((u - 1.8) / 0.9)
        cx_ = lerp(480, 390, fa) + math.sin(t * 2) * 6; cy_ = oc + 250 + math.sin(t * 1.4) * 10
        glow(cv, cx_, cy_, 66, (0.2, 1.0, 0.9), 0.55 * fa, 2.0)
        ell(cv, cx_, cy_, 20, 12, (0.4, 1.0, 0.95), a=fa, flat=True)
        for k in range(5):
            capsule(cv, cx_ + 14 + k * 5, cy_ + (k - 2) * 3, cx_ + 34 + k * 7, cy_ + (k - 2) * 8 + math.sin(t * 5 + k) * 4, 1.6, (0.4, 1.0, 0.95), flat=True, a=fa)
        circ(cv, cx_ - 8, cy_ - 2, 2.2, (0.0, 0.1, 0.2), flat=True, a=fa)


def titan_scene(cv, t):
    u = t - 27.2
    set_light((-0.4, -0.5, 0.75), 0.44, rim_dir=(0.8, -0.4), rim_col=(1.0, 0.8, 0.45), rim_amt=0.5)
    cam = Cam(1.0 + 0.05 * u, px=lerp(-40, 40, u / 2.8), py=0)
    fill_bg(cv, (0.12, 0.30, 0.34), (0.95, 0.62, 0.28), 0, 560)
    haze(cv, 80, 520, (1.0, 0.75, 0.4), 0.55, t, 1.0)
    glow(cv, cam.p(340, 250, 0.1)[0], 250, 150, (1.0, 0.7, 0.3), 0.45, 2.0)
    for k, (hh, c, dd) in enumerate(((50, (0.38, 0.42, 0.36), 0.1), (30, (0.52, 0.42, 0.28), 0.3))):
        pts = [(-30, 560)]
        for i in range(0, 12):
            pts.append((-30 + i * 52, 540 - hh * (0.5 + 0.5 * math.sin(i * 1.9 + k * 3)) - hh * 0.2 * math.sin(i * 0.7)))
        pts += [(W + 40, 560), (W + 40, 700), (-30, 700)]
        cc = np.asarray(c, np.float32)
        poly(cv, [cam.p(x, y, dd) for x, y in pts], cc * 1.1, cc * 0.8, a=0.95)
    # shore sand
    hy = int(cam.p(0, 548, 0.5)[1])
    Y = YY[hy:]; X = XX[hy:]
    f = np.clip((Y - hy) / (H - hy), 0, 1)[..., None]
    sand = np.array([0.82, 0.58, 0.28], np.float32) * (1 - f) + np.array([0.48, 0.3, 0.14], np.float32) * f
    n = tex(NZ_A, (X + cam.px * 0.5) / 150.0, Y / 100.0)
    cv[hy:] = sand * (0.85 + 0.3 * n[..., None])
    # methane lake
    lk = cam.p(250, 640, 0.7)
    ell(cv, lk[0], lk[1], 300 * cam.z, 110 * cam.z, (0.58, 0.40, 0.2), flat=True)
    ell(cv, lk[0], lk[1] + 3, 290 * cam.z, 100 * cam.z, (0.03, 0.10, 0.14), flat=True)
    Xl = XX; Yl = YY
    for i in range(7):
        ry_ = (6 + i * 12) * cam.z
        ring(cv, lk[0] + 40 * math.sin(t + i), lk[1] + 20 * (i - 3) * cam.z * 0.6, (50 + i * 36) * cam.z, ry_ * 0.4, 1.4, (0.55, 0.85, 0.85), 0.16)
    # reflection of sky glow
    glow(cv, lk[0] + 60, lk[1] - 12, 130, (1.0, 0.75, 0.4), 0.25, 2.0, ry=24)
    # wing walker: walks, hops, glides
    v = smooth(u / 0.7)
    jump = max(0.0, math.sin(clamp01((u - 0.9) / 1.6) * math.pi))
    wx = lerp(60, 330, ease_io(u / 2.8))
    wy = 790 - jump * 270 * cam.z
    wing_rate = 4 + 6 * jump
    walk = math.sin(t * 7) * 0.8 * (1 - jump) * (1 if u < 2.6 else 0.2)
    ell(cv, wx + 12, 796, 40 * (1 - 0.4 * jump), 8 * (1 - 0.4 * jump), (0, 0, 0.03), a=0.4, flat=True)
    out = person(cv, wx, wy, 1.4 * cam.z, t, wings=dict(rate=wing_rate, col=(0.7, 0.95, 1.0)), suit=(0.82, 0.92, 1.0), expr="awe" if jump > 0.1 else "grin",
                 walk=walk, arm_l=0.5 + 0.8 * jump, arm_r=0.5 + 0.8 * jump, look=(0.7, -0.4), lean=0.0, pack=True)
    # haze foreground wisps
    haze(cv, 560, 960, (1.0, 0.75, 0.4), 0.12, t, 0.7)


def scene4(cv, t):
    seg(cv, t, [(21, 24.2, asteroid_scene), (24.2, 27.2, europa_scene), (27.2, 30, titan_scene)], 0.3)
