"""Block props: people, buildings, vehicles, ships, explosions, debris."""
import math
import numpy as np
from engine import *

SKINS = [(0.96, 0.78, 0.62), (0.85, 0.62, 0.46), (0.62, 0.42, 0.30), (0.45, 0.30, 0.22), (0.98, 0.85, 0.72)]
SHIRTS = [(0.85, 0.2, 0.2), (0.2, 0.5, 0.85), (0.95, 0.8, 0.2), (0.3, 0.7, 0.4), (0.9, 0.45, 0.7), (0.95, 0.95, 0.95), (0.25, 0.25, 0.3), (0.95, 0.55, 0.15), (0.55, 0.35, 0.8)]
PANTS = [(0.15, 0.17, 0.3), (0.2, 0.2, 0.22), (0.4, 0.3, 0.2), (0.12, 0.12, 0.14), (0.25, 0.35, 0.55)]
HAIRS = [(0.1, 0.07, 0.05), (0.3, 0.18, 0.1), (0.85, 0.7, 0.3), (0.06, 0.06, 0.08), (0.7, 0.7, 0.72)]
ORANGE = (1.0, 0.56, 0.14)


def hsh(*a):
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def person(w, pos, yaw=0.0, seed=0, anim="idle", t=0.0, scale=1.0, shirt=None, pants=None, skin=None, hair=None,
           look_up=0.0, cam_pos=None, helmet=False, hat=None, mouth=False, patch=False, arm_pose=None, pack=False, arm_pose_l=None):
    Y = rot_y(yaw)
    pos = np.asarray(pos, np.float32)
    shirt = shirt or SHIRTS[int(hsh(seed, 1) * len(SHIRTS))]
    pants = pants or PANTS[int(hsh(seed, 2) * len(PANTS))]
    skin = skin or SKINS[int(hsh(seed, 3) * len(SKINS))]
    hair = hair or HAIRS[int(hsh(seed, 4) * len(HAIRS))]
    ph = hsh(seed, 5) * 6.28
    far = cam_pos is not None and np.linalg.norm(pos - np.asarray(cam_pos)) > 70

    def P(c, size, R, color, em=0.0):
        cw = pos + Y @ (np.asarray(c, np.float32) * scale)
        w.box(cw, np.asarray(size, np.float32) * scale, color, Y @ R, em)

    amp = arms = lean = 0.0; freq = 1.8; bob = 0.0; arm_up = None
    if anim == "walk": amp, arms, freq = 0.6, 0.5, 1.8
    elif anim == "run": amp, arms, freq, lean = 1.0, 1.0, 3.2, 0.22
    elif anim == "panic": amp, arms, freq, lean, arm_up = 0.9, 0.0, 3.4, 0.16, 2.6
    elif anim == "cheer": amp, arms, freq, arm_up, bob = 0.0, 0.0, 2.6, 2.9, 0.12
    elif anim == "idle": freq = 1.0
    sw = math.sin(t * freq * 2 * math.pi + ph)
    if bob: pos = pos + np.array([0, abs(math.sin(t * freq * math.pi + ph)) * bob * scale, 0], np.float32)
    if anim in ("run", "panic"): pos = pos + np.array([0, abs(sw) * 0.08 * scale, 0], np.float32)
    Rl = rot_x(lean)
    if far:
        P((0, 0.4, 0), (0.46, 0.8, 0.26), I3, pants)
        P((0, 1.15, 0), (0.56, 0.7, 0.3), Rl, shirt)
        P((0, 1.75, 0), (0.42, 0.42, 0.42), I3, skin)
        return
    # legs
    for sg, s_ in ((-1, 1), (1, -1)):
        a = sw * amp * s_
        piv = np.array([0.14 * sg, 0.8, 0], np.float32)
        R = rot_x(a)
        P(piv + R @ np.array([0, -0.4, 0], np.float32), (0.25, 0.8, 0.27), R, pants)
        # shoe
        P(piv + R @ np.array([0, -0.77, 0.04], np.float32), (0.27, 0.12, 0.34), R, (0.12, 0.12, 0.14))
    # torso
    piv = np.array([0, 0.8, 0], np.float32)
    P(piv + Rl @ np.array([0, 0.35, 0], np.float32), (0.56, 0.7, 0.3), Rl, shirt)
    if patch:
        pc = piv + Rl @ np.array([-0.14, 0.5, 0.16], np.float32)
        P(pc, (0.14, 0.14, 0.03), Rl, ORANGE, 0.9)
    if pack:
        P(piv + Rl @ np.array([0, 0.4, -0.27], np.float32), (0.5, 0.62, 0.24), Rl, (0.72, 0.74, 0.8))
    # head
    hc = piv + Rl @ np.array([0, 0.95, 0], np.float32)
    Rh = Rl @ rot_x(-look_up)
    hcw = hc + Rl @ np.array([0, 0, 0], np.float32)
    P(hcw, (0.42, 0.42, 0.42), Rh, skin if not helmet else (0.85, 0.88, 0.95))
    if helmet:
        P(hcw + Rh @ np.array([0, 0, 0.12], np.float32), (0.36, 0.3, 0.2), Rh, (0.1, 0.15, 0.3))
    P(hcw + Rh @ np.array([0, 0.2, -0.01], np.float32), (0.45, 0.12, 0.45), Rh, hair if not helmet else (0.8, 0.82, 0.9))
    if hat:
        P(hcw + Rh @ np.array([0, 0.28, 0], np.float32), (0.5, 0.14, 0.5), Rh, hat)
    for ex in (-0.1, 0.1):
        P(hcw + Rh @ np.array([ex, 0.03, 0.215], np.float32), (0.07, 0.08, 0.02), Rh, (0.05, 0.05, 0.08))
    if mouth:
        P(hcw + Rh @ np.array([0, -0.1, 0.215], np.float32), (0.12, 0.1, 0.02), Rh, (0.3, 0.05, 0.08))
    # arms
    for sg, s_ in ((-1, -1), (1, 1)):
        if arm_pose is not None and sg == 1: a = arm_pose
        elif arm_pose_l is not None and sg == -1: a = arm_pose_l
        elif arm_up is not None: a = arm_up + 0.25 * math.sin(t * 9 + ph + sg)
        else: a = sw * arms * s_
        R = Rl @ rot_x(a)
        sh = piv + Rl @ np.array([0.39 * sg, 0.62, 0], np.float32)
        P(sh + (Rl @ rot_x(a)) @ np.array([0, -0.33, 0], np.float32) * 1.0 - (Rl @ np.array([0, 0, 0], np.float32)), (0.2, 0.7, 0.2), R, shirt)
        P(sh + R @ np.array([0, -0.7, 0], np.float32), (0.2, 0.14, 0.2), R, skin if not helmet else (0.55, 0.6, 0.72))


def crowd(w, cam_pos, t, n, center, spread, anim, seed=0, yaw=0.0, speed=0.0, direction=(0, 0, 1), look_up=0.0, scale=1.0, mouth=False, **kw):
    d = np.asarray(direction, np.float32)
    for i in range(n):
        h1 = hsh(seed, i, 1); h2 = hsh(seed, i, 2); h3 = hsh(seed, i, 3)
        p = np.array([center[0] + (h1 - 0.5) * spread[0], center[1], center[2] + (h2 - 0.5) * spread[1]], np.float32)
        p = p + d * speed * t * (0.8 + 0.4 * h3)
        y = yaw + (h3 - 0.5) * 0.5
        person(w, p, y, seed * 100 + i, anim, t, scale, cam_pos=cam_pos, look_up=look_up, mouth=mouth, **kw)


def building(w, x, z, bw, bd, h, color, cam_pos, lit=1.0, seed=0, roof=None, neon=True):
    c = np.asarray(color, np.float32)
    cp = np.asarray(cam_pos, np.float32)
    dist = float(np.linalg.norm(np.array([x, 0, z]) - cp * np.array([1, 0, 1])))
    # (wall centre at ground, u axis along wall, outward normal, wall width, box face index)
    sides = [((x, 0, z + bd / 2), (1, 0, 0), (0, 0, 1), bw, 4),
             ((x, 0, z - bd / 2), (-1, 0, 0), (0, 0, -1), bw, 5),
             ((x + bw / 2, 0, z), (0, 0, -1), (1, 0, 0), bd, 0),
             ((x - bw / 2, 0, z), (0, 0, 1), (-1, 0, 0), bd, 1)]
    wind = []
    keep = [2, 3]
    for sd in sides:
        o, u, nrm, width, fi = sd
        facing = float(np.dot(cp - np.asarray(o, np.float32) - np.array([0, cp[1], 0], np.float32) * 0, np.asarray(nrm, np.float32)))
        if dist < 150 and facing > -3: wind.append(sd)
        else: keep.append(fi)
    w.box((x, h / 2, z), (bw, h, bd), c, faces=keep)
    w.box((x, h + 0.4, z), (bw * 0.7, 0.8, bd * 0.7), c * 0.8)
    if roof is not None:
        w.box((x, h + 1.4, z), (1.2, 1.4, 1.2), roof, em=0.6)
    step = 3.4 if dist < 90 else 5.6
    allV = []; allC = []
    for si, (o, u, nrm, width, fi) in enumerate(wind):
        u = np.asarray(u, np.float32); o = np.asarray(o, np.float32); n_ = np.asarray(nrm, np.float32)
        cols = max(1, int(round(width / step))); rows = max(1, int(round(h / step)))
        cw = width / cols; rh = h / rows
        ii, jj = np.meshgrid(np.arange(cols), np.arange(rows), indexing="ij")
        ii = ii.ravel(); jj = jj.ravel()
        u0 = -width / 2 + ii * cw; v0 = jj * rh
        up = np.array([0, 1, 0], np.float32)
        def pt(a, b, off=0.0): return o[None] + u[None] * a[:, None] + up[None] * b[:, None] + n_[None] * off
        # wall tile
        T = np.stack([pt(u0, v0), pt(u0 + cw, v0), pt(u0 + cw, v0 + rh), pt(u0, v0 + rh)], 1)
        hs = np.array([hsh(seed, si, a, b) for a, b in zip(ii, jj)])
        tcol = c[None] * (0.93 + 0.1 * hs[:, None])
        # window
        mx, my = cw * 0.2, rh * 0.18
        Wn = np.stack([pt(u0 + mx, v0 + my, 0.04), pt(u0 + cw - mx, v0 + my, 0.04), pt(u0 + cw - mx, v0 + rh - my, 0.04), pt(u0 + mx, v0 + rh - my, 0.04)], 1)
        on = hs < lit
        wcol = np.where(on[:, None], np.array([1.0, 0.82, 0.45], np.float32)[None] * (0.75 + 0.25 * (hs[:, None] / max(lit, 1e-3))), np.array([0.09, 0.11, 0.19], np.float32)[None])
        allV += [T, Wn]; allC += [tcol.astype(np.float32), wcol.astype(np.float32)]
    if allV:
        # tiles then windows (bias separates them)
        n_t = len(allV) // 2
        w.quads(np.concatenate(allV[0::2]), np.concatenate(allC[0::2]), em=0.0, bias=0.0)
        w.quads(np.concatenate(allV[1::2]), np.concatenate(allC[1::2]), em=0.0, bias=0.5)
    if neon and dist < 110:
        for k in range(2):
            if hsh(seed, 77, k) < 0.6:
                nc = [(1, 0.2, 0.7), (0.2, 0.9, 1), (1, 0.85, 0.2), (0.4, 1, 0.4), (1, 0.4, 0.2)][int(hsh(seed, 88, k) * 5)]
                sx = x - bw / 2 + 1.2 + hsh(seed, 99, k) * (bw - 2.4)
                sy = 3.5 + hsh(seed, 55, k) * max(1.0, h - 8)
                w.box((sx, sy, z + bd / 2 + 0.35), (0.9, 3.4, 0.3), nc, em=1.0 * lit)


def car(w, pos, yaw, color):
    Y = rot_y(yaw); pos = np.asarray(pos, np.float32)
    w.box(pos + Y @ np.array([0, 0.5, 0], np.float32), (1.8, 0.7, 4.0), color, Y)
    w.box(pos + Y @ np.array([0, 1.1, -0.2], np.float32), (1.6, 0.6, 2.0), np.asarray(color) * 0.85, Y)
    for sx in (-1, 1):
        for sz in (-1.3, 1.3):
            w.box(pos + Y @ np.array([0.9 * sx, 0.3, sz], np.float32), (0.25, 0.6, 0.6), (0.08, 0.08, 0.1), Y)
    w.box(pos + Y @ np.array([0, 0.55, 2.0], np.float32), (1.5, 0.2, 0.05), (1, 0.95, 0.7), Y, 0.8)


def tank(w, pos, yaw, t=0.0, barrel_pitch=0.3, recoil=0.0):
    Y = rot_y(yaw); pos = np.asarray(pos, np.float32)
    def P(c, s, col, R=I3, em=0.0): w.box(pos + Y @ np.asarray(c, np.float32), s, col, Y @ R, em)
    for sx in (-1, 1): P((1.5 * sx, 0.45, 0), (0.9, 0.9, 5.2), (0.16, 0.17, 0.15))
    P((0, 1.1, 0), (2.6, 0.9, 4.6), (0.32, 0.4, 0.26))
    P((0, 1.85, -0.2), (1.8, 0.7, 2.2), (0.36, 0.45, 0.3))
    R = rot_x(-barrel_pitch)
    P((0, 1.9, 0.0) + (R @ np.array([0, 0, 2.2 - recoil], np.float32)), (0.28, 0.28, 4.4), (0.2, 0.22, 0.18), R)


def jet(w, pos, yaw=0.0, pitch=0.0, roll=0.0, color=(0.55, 0.6, 0.68), t=0.0, scale=1.0, afterburn=1.0):
    R = rot_y(yaw) @ rot_x(pitch) @ rot_z(roll)
    pos = np.asarray(pos, np.float32)
    s = scale
    def P(c, size, col, em=0.0): w.box(pos + R @ (np.asarray(c, np.float32) * s), np.asarray(size, np.float32) * s, col, R, em)
    P((0, 0, 0), (0.9, 0.7, 6.0), color)
    P((0, 0.45, 1.2), (0.6, 0.4, 1.6), (0.15, 0.25, 0.4))
    for sg in (-1, 1):
        wc = pos + R @ (np.array([2.2 * sg, 0, -0.6], np.float32) * s)
        Rw = R @ rot_y(0.5 * sg)
        w.box(wc, np.array([3.4, 0.14, 1.8], np.float32) * s, np.asarray(color) * 0.9, Rw)
        tc = pos + R @ (np.array([1.0 * sg, 0.1, -2.7], np.float32) * s)
        w.box(tc, np.array([1.4, 0.12, 0.9], np.float32) * s, np.asarray(color) * 0.85, R)
    P((0, 0.9, -2.5), (0.12, 1.3, 1.0), np.asarray(color) * 0.8)
    if afterburn > 0:
        P((0, 0, -3.5 - 0.5 * afterburn), (0.5, 0.45, 1.2 * afterburn + 0.3), (1.0, 0.6, 0.2), 1.0)


def saucer(w, pos, r=3.0, t=0.0, tilt=0.0, color=(0.55, 0.58, 0.66), glow=(0.4, 1.0, 0.7), n=10):
    pos = np.asarray(pos, np.float32)
    R = rot_z(tilt)
    w.cyl(pos, r, r * 0.28, color, n, R, ts=0.35)
    w.cyl(pos + R @ np.array([0, r * 0.14, 0], np.float32), r * 0.78, r * 0.18, np.asarray(color) * 1.1, n, R, ts=0.5)
    w.sphere(pos + R @ np.array([0, r * 0.32, 0], np.float32), r * 0.32, (0.4, 0.9, 0.8), em=0.7, nu=8, nv=4)
    for k in range(8):
        a = k / 8 * 2 * math.pi + t * 2
        w.box(pos + R @ np.array([math.cos(a) * r * 0.82, -r * 0.05, math.sin(a) * r * 0.82], np.float32), (r * 0.12,) * 3, glow, R, 1.0)


def mothership(w, pos, r=60.0, t=0.0, damage=0.0, glow=(0.4, 1.0, 0.7), core=1.0):
    pos = np.asarray(pos, np.float32)
    dark = (0.16, 0.17, 0.22)
    w.cyl(pos, r, r * 0.12, dark, 12, ts=0.55)
    w.cyl(pos + np.array([0, r * 0.1, 0], np.float32), r * 0.62, r * 0.14, (0.2, 0.21, 0.28), 12, ts=0.6)
    w.cyl(pos + np.array([0, r * 0.2, 0], np.float32), r * 0.3, r * 0.14, (0.24, 0.26, 0.34), 8, ts=0.7)
    # underside ring lights + spikes
    for k in range(24):
        a = k / 24 * 2 * math.pi + t * 0.25
        pl = pos + np.array([math.cos(a) * r * 0.82, -r * 0.065, math.sin(a) * r * 0.82], np.float32)
        w.box(pl, (r * 0.04, r * 0.02, r * 0.04), glow, I3, 1.0)
    for k in range(12):
        a = k / 12 * 2 * math.pi + 0.2
        pl = pos + np.array([math.cos(a) * r * 0.5, -r * 0.1, math.sin(a) * r * 0.5], np.float32)
        w.box(pl, (r * 0.03, r * 0.1, r * 0.03), (0.12, 0.12, 0.16), I3)
    # glowing core on the underside
    w.cyl(pos + np.array([0, -r * 0.08, 0], np.float32), r * 0.14, r * 0.05, (1.0, 0.35, 0.3) if damage > 0 else glow, 8, I3, 1.0 * core)


# ------------------------------------------------------------------ effects
def explosion(w, pos, age, size=3.0, seed=0):
    if age < 0 or age > 2.0: return
    pos = np.asarray(pos, np.float32)
    k = age / 2.0
    for i in range(14):
        h1, h2, h3 = hsh(seed, i, 1), hsh(seed, i, 2), hsh(seed, i, 3)
        d = np.array([h1 - 0.5, h2 * 0.8 - 0.1, h3 - 0.5], np.float32)
        d /= np.linalg.norm(d) + 1e-6
        dist = size * (0.2 + 1.6 * (1 - (1 - min(1, age / 0.9)) ** 2)) * (0.5 + h1)
        rise = size * 0.9 * k
        p = pos + d * dist + np.array([0, rise, 0], np.float32)
        s = size * (0.5 + h2 * 0.7) * (min(1, age * 6) * (1 - 0.6 * k))
        if age < 0.35: col = (1.0, 0.95, 0.6); em = 1.0
        elif age < 0.9: col = (1.0, 0.5, 0.12); em = 1.0
        else:
            g = 0.25 * (1 - (age - 0.9) / 1.1); col = (g + 0.08,) * 3; em = 0.0
        w.box(p, (s, s, s), col, rot_y(h3 * 6) @ rot_x(h1 * 3), em)
    debris(w, pos, age, 8, seed + 5, size * 6, (0.2, 0.2, 0.22), size * 0.18)


def debris(w, origin, age, n, seed, speed, color, sz=0.5, gravity=9.8, ground=0.0, em=0.0):
    if age < 0: return
    origin = np.asarray(origin, np.float32)
    for i in range(n):
        h1, h2, h3, h4 = (hsh(seed, i, k) for k in range(1, 5))
        v = np.array([(h1 - 0.5) * 2, 0.6 + h2 * 1.2, (h3 - 0.5) * 2], np.float32) * speed * (0.4 + h4)
        p = origin + v * age + np.array([0, -0.5 * gravity * age * age, 0], np.float32)
        if p[1] < ground + sz * 0.5: p[1] = ground + sz * 0.5
        s = sz * (0.6 + h3)
        c = np.asarray(color, np.float32) * (0.7 + 0.5 * h1)
        w.box(p, (s, s, s), c, rot_y(age * 4 * h1 + h2 * 6) @ rot_x(age * 3 * h3), em)


def ground(w, x0, x1, z0, z1, color, step=24.0, y=0.0):
    """Tiled ground quad so fog / sorting stay sane."""
    xs = np.arange(x0, x1, step); zs = np.arange(z0, z1, step)
    V = []
    for a in xs:
        for b in zs:
            a1 = min(a + step, x1); b1 = min(b + step, z1)
            V.append([(a, y, b), (a, y, b1), (a1, y, b1), (a1, y, b)])
    w.quads(np.array(V, np.float32), np.broadcast_to(np.asarray(color, np.float32), (len(V), 3)).copy(), bias=0.0)


def stripe_road(w, z0, z1, x_half=8.0, col=(0.2, 0.2, 0.24), dash=(0.9, 0.9, 0.75), y=0.0):
    ground(w, -x_half, x_half, z0, z1, col, 24.0, y)
    zs = np.arange(math.floor(z0 / 8) * 8, z1, 8.0)
    V = [[(-0.15, y + 0.02, z), (-0.15, y + 0.02, z + 3), (0.15, y + 0.02, z + 3), (0.15, y + 0.02, z)] for z in zs]
    if V: w.quads(np.array(V, np.float32), np.broadcast_to(np.asarray(dash, np.float32), (len(V), 3)).copy(), bias=0.2)


def _noise3(dx, dy, dz, k=1.0):
    return (np.sin(dx * 7.1 * k + dy * 3.3 + dz * 5.7) + np.sin(dx * 3.9 - dy * 6.1 * k + dz * 2.2) + np.sin(dz * 8.3 + dx * 2.1 - dy * 4.4)) / 3.0


def planet(w, c, r, kind, rot=0.0, nu=14, nv=9, em=0.0):
    unit = sphere_unit(nu, nv)
    cen = unit.mean(1)
    d = cen / (np.linalg.norm(cen, axis=1, keepdims=True) + 1e-9)
    ca, sa = math.cos(rot), math.sin(rot)
    dx = d[:, 0] * ca - d[:, 2] * sa; dz = d[:, 0] * sa + d[:, 2] * ca; dy = d[:, 1]
    n = _noise3(dx, dy, dz)
    if kind == "earth":
        land = n > 0.12
        col = np.where(land[:, None], np.array([0.30, 0.68, 0.30], np.float32), np.array([0.12, 0.38, 0.85], np.float32))
        col = np.where((np.abs(dy) > 0.84)[:, None], np.array([0.95, 0.97, 1.0], np.float32), col)
        cloud = _noise3(dx * 1.7 + 3, dy * 1.7, dz * 1.7) > 0.45
        col = np.where(cloud[:, None], np.array([0.95, 0.96, 1.0], np.float32), col)
    elif kind == "mars":
        base = np.array([0.82, 0.38, 0.2], np.float32)
        col = base[None] * (0.8 + 0.35 * n[:, None])
        col = np.where((np.abs(dy) > 0.9)[:, None], np.array([0.95, 0.9, 0.88], np.float32), col)
    elif kind == "jupiter":
        band = (np.sin(dy * 14 + n * 2) > 0).astype(np.float32)[:, None]
        col = np.array([0.9, 0.75, 0.55], np.float32) * band + np.array([0.62, 0.38, 0.25], np.float32) * (1 - band)
    elif kind == "sun":
        col = np.array([1.0, 0.85, 0.4], np.float32)[None] * (0.9 + 0.2 * n[:, None]); em = max(em, 1.0)
    elif kind == "titan":
        col = np.array([0.95, 0.65, 0.25], np.float32)[None] * (0.85 + 0.2 * n[:, None])
    else:
        col = np.array([0.6, 0.6, 0.65], np.float32)[None] * (0.8 + 0.3 * n[:, None])
    w.mesh(unit, c, (2 * r,) * 3, col.astype(np.float32), None, em)


def starbox(w, center, seed=1, n=220, radius=600.0, bright=1.0):
    center = np.asarray(center, np.float32)
    a = np.array([hsh(seed, i, 1) * 6.283 for i in range(n)]); b = np.array([math.acos(2 * hsh(seed, i, 2) - 1) for i in range(n)])
    d = np.stack([np.sin(b) * np.cos(a), np.cos(b), np.sin(b) * np.sin(a)], 1).astype(np.float32)
    sz = np.array([1.4 + 3.2 * hsh(seed, i, 3) ** 3 for i in range(n)], np.float32)
    col = np.array([[1.0, 0.95 - 0.2 * hsh(seed, i, 4), 0.8 + 0.2 * hsh(seed, i, 4)] for i in range(n)], np.float32) * bright
    w.cubes(center + d * radius, sz, col, em=1.0)
