"""'What if aliens declared war on Earth?' - blocky 3D scenes."""
import math, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
from engine import *
from props import *
from ui import smooth

RW, RH = 720, 1280


def lerp(a, b, f): return a + (b - a) * f
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def mixc(a, b, f): return tuple(float(x) * (1 - f) + float(y) * f for x, y in zip(a, b))
def shake(t, amp, f=14.0): return np.array([math.sin(t * f * 1.3) * amp, math.sin(t * f * 0.9 + 1) * amp, math.sin(t * f * 1.7 + 2) * amp * 0.5], np.float32)


R = Renderer(RW, RH)
BCOL = [(0.36, 0.30, 0.46), (0.30, 0.38, 0.50), (0.50, 0.32, 0.38), (0.28, 0.42, 0.42), (0.42, 0.38, 0.30)]


def city(w, cp, lit, seed=1, zmin=-60, zmax=300, wd=150.0, hscale=None, rows=((15, 1.0), (46, 1.6)), skip=None):
    cp = np.asarray(cp, np.float32)
    for side in (-1, 1):
        for ri, (xo, hs) in enumerate(rows):
            for i in range(int((zmax - zmin) / 17) + 1):
                z = zmin + i * 17
                key = (side, ri, i)
                if skip and skip(key): continue
                h1 = hsh(seed, side, ri, i, 1); h2 = hsh(seed, side, ri, i, 2)
                bw = 13 + h2 * 5; bd = 12 + h1 * 3
                x = side * (xo + 5 + (h2 * 6))
                hh = (14 + h1 * 44) * hs
                if hscale: hh *= hscale(key)
                if hh < 1.0: continue
                if abs(z - cp[2]) > 330: continue
                building(w, x, z, bw, bd, hh, BCOL[int(h1 * 5) % 5], cp, lit, seed=int(h1 * 9999) + i, neon=True)


def street(w, z0, z1, sidew=True):
    stripe_road(w, z0, z1, 8.0)
    if sidew:
        ground(w, 8, 22, z0, z1, (0.46, 0.46, 0.52), y=0.12)
        ground(w, -22, -8, z0, z1, (0.46, 0.46, 0.52), y=0.12)
    ground(w, 22, 140, z0, z1, (0.25, 0.26, 0.3), 40.0)
    ground(w, -140, -22, z0, z1, (0.25, 0.26, 0.3), 40.0)
    zs = np.arange(math.floor(z0 / 6) * 6, z1, 6.0)


def crosswalk(w, z, col=(0.92, 0.92, 0.9)):
    V = [[(x, 0.03, z), (x, 0.03, z + 3), (x + 0.9, 0.03, z + 3), (x + 0.9, 0.03, z)] for x in np.arange(-7.5, 7.5, 1.8)]
    w.quads(np.array(V, np.float32), np.broadcast_to(np.asarray(col, np.float32), (len(V), 3)).copy(), bias=0.3)


def finish(img, bloom_amt=0.5):
    img = bloom(img, 205, bloom_amt)
    return img.resize((1080, 1920), Image.LANCZOS)


# ===================================================================== scene 1: normal evening (0-7)
def s1(t):
    w = World()
    z0 = lerp(-26, -18, t / 7)
    up = smooth((t - 3.4) / 3.6)
    cp = np.array([0, 1.75, z0], np.float32)
    tgt = cp + np.array([0, lerp(1.2, 47, up), 40], np.float32)
    cam = Camera(cp + shake(t, 0.01 + 0.03 * smooth((t - 5.5) / 1.5)), tgt, 66)
    dark = smooth((t - 4.0) / 3.0)
    street(w, -70, 330)
    for z in (30, 120): crosswalk(w, z)
    city(w, cp, 1.0, 11, -70, 330)
    for k, c in enumerate(((0.8, 0.15, 0.15), (0.2, 0.4, 0.8), (0.9, 0.8, 0.2), (0.3, 0.7, 0.4))):
        car(w, (3.5 if k % 2 else -3.5, 0, 18 + k * 30), 0.0, c)
    walkers = "walk" if t < 4.3 else "idle"
    look = clamp((t - 4.3) / 1.2) * 0.9
    crowd(w, cp, t if t < 4.3 else 4.3, 22, (0, 0, -8), (13, 30), walkers, seed=4, yaw=math.pi, speed=-1.3, direction=(0, 0, 1), look_up=look, mouth=False)
    crowd(w, cp, t if t < 4.3 else 4.3, 10, (0, 0, 40), (13, 20), walkers, seed=9, yaw=0.0, speed=1.2, direction=(0, 0, 1), look_up=look)
    # the ship
    sz = lerp(900, 140, smooth((t - 3.2) / 3.8))
    if t > 3.2:
        mothership(w, (0, 110, sz), 95, t)
    sky_top = mixc((0.25, 0.12, 0.4), (0.03, 0.02, 0.07), dark); sky_hor = mixc((1.0, 0.62, 0.45), (0.25, 0.1, 0.2), dark)
    bg, yh, F = R.background(cam, sky_top, sky_hor, sky_hor, (0.2, 0.2, 0.25))
    img = R.render(w, cam, bg, light=(0.4, 0.8, 0.45), amb=lerp(0.5, 0.28, dark), fog=sky_hor, fog_range=(70, 380))
    return finish(img)


# ===================================================================== scene 2: arrival (7-15)
SAUCERS = [(hsh(3, i, 1) - 0.5, hsh(3, i, 2), hsh(3, i, 3)) for i in range(9)]


def s2(t):
    u = t - 7.0
    w = World()
    cp = np.array([0, 1.8, -14 + 0.5 * u], np.float32)
    tgt = np.array([math.sin(u * 0.3) * 6, 22 + 4 * math.sin(u * 0.4), 40], np.float32)
    cam = Camera(cp + shake(t, 0.04), tgt, 70, roll=0.04 * math.sin(u * 0.7))
    street(w, -70, 330)
    city(w, cp, 1.0 - 0.05 * u, 11, -70, 330)
    mothership(w, (0, 105, 60), 100, t)
    # beams down + saucers
    for k in range(3):
        a = 0.6 + 0.35 * k
        x = (k - 1) * 40
        w.beam((x, 100, 60), (x * 1.3, 0, 60 + 30 * k), 4.0, (0.4, 1.0, 0.7), em=1.0, alpha=0.16)
    for i, (hx, hy, hz) in enumerate(SAUCERS):
        ph = clamp((u - 0.3 - i * 0.25) / 4.0)
        pos = (hx * 160 * ph + math.sin(t + i) * 3, 85 - 18 * ph + hy * 30 * ph, 60 + 20 * i + 120 * ph * hz)
        saucer(w, pos, 6.0, t + i, tilt=0.15 * math.sin(t + i))
    fl = clamp((u - 0.5) / 1.0)
    crowd(w, cp, t, 34, (0, 0, 6 + 0.5 * u), (13, 22), "panic", seed=21, yaw=0.0, speed=3.2, direction=(0, 0, 1), mouth=True)
    crowd(w, cp, t, 12, (0, 0, 40), (13, 22), "panic", seed=25, yaw=math.pi, speed=-3.0, direction=(0, 0, 1), mouth=True)
    car(w, (-3.5, 0, 25), 0.3, (0.9, 0.7, 0.1))
    sky_top = (0.02, 0.02, 0.06); sky_hor = (0.22, 0.1, 0.2)
    bg, yh, F = R.background(cam, sky_top, sky_hor, sky_hor, (0.15, 0.15, 0.2))
    img = R.render(w, cam, bg, light=(0.2, 0.9, 0.2), amb=0.25, fog=sky_hor, fog_range=(70, 380))
    return finish(img, 0.6)


# ===================================================================== scene 3: first strike (15-24)
STRIKES = [(16.0, (-26, 0, 40)), (17.4, (30, 0, 105)), (18.6, (-22, 0, 150)), (19.8, (20, 0, 215)), (21.0, (-30, 0, 95)), (22.2, (14, 0, 60))]


def s3(t):
    u = t - 15.0
    w = World()
    ang = lerp(-0.5, 0.5, u / 9.0)
    cp = np.array([math.sin(ang) * 85, lerp(72, 52, u / 9), -30 + math.cos(ang) * 40], np.float32)
    tgt = np.array([0, 8, 110], np.float32)
    cam = Camera(cp + shake(t, 0.15 * (1 if int(u * 3) % 5 == 0 else 0.3)), tgt, 62)
    lit = clamp(1 - (u - 0.6) / 7.2)
    street(w, -70, 330)
    for z in (30, 120, 210): crosswalk(w, z)
    def hscale(key):
        side, ri, i = key
        z = -60 + i * 17
        f = 1.0
        for (ts, p) in STRIKES:
            if abs(p[2] - z) < 18 and (p[0] * side > 0):
                f = min(f, 1 - 0.8 * smooth((t - ts) / 1.1))
        return f
    city(w, cp, lit, 11, -60, 300, wd=400, hscale=hscale)
    mothership(w, (0, 230, 150), 110, t)
    for (ts, p) in STRIKES:
        a = t - ts
        if -0.5 < a < 0.9:
            top = (p[0] * 0.3, 225, 150)
            w.beam(top, (p[0], 3, p[2]), 3.2 * (1 - abs(a) / 1.0 if a > 0 else 1), (1.0, 0.25, 0.2), em=1.0)
        if a > 0:
            explosion(w, (p[0], 8, p[2]), a, 9.0, seed=int(ts * 10))
            debris(w, (p[0], 12, p[2]), a, 16, int(ts * 7), 22, (0.35, 0.32, 0.4), 1.6)
    crowd(w, cp, t, 14, (0, 0, 90), (14, 80), "run", seed=33, yaw=0, speed=-4.0, direction=(0, 0, 1), scale=1.2)
    flash = 0.15 * (int(u * 6) % 2) * smooth((u - 1.5) / 2)
    sky_top = mixc((0.02, 0.02, 0.05), (0.12, 0.02, 0.04), flash * 4); sky_hor = mixc((0.2, 0.1, 0.18), (0.5, 0.12, 0.1), smooth((u - 2) / 6))
    bg, yh, F = R.background(cam, sky_top, sky_hor, sky_hor, (0.1, 0.1, 0.14))
    img = R.render(w, cam, bg, light=(0.3, 0.9, 0.2), amb=lerp(0.32, 0.18, smooth(u / 7)), fog=sky_hor, fog_range=(90, 520))
    return finish(img, 0.55)


# ===================================================================== scene 4: military (24-33)
MISSILE_T = [24.4 + i * 0.2 for i in range(44)]
SHIELD_C = np.array([0, 150, 260], np.float32)


def s4(t):
    u = t - 24.0
    w = World()
    cp = np.array([lerp(-6, 4, u / 9), 3.4, -16], np.float32)
    tgt = np.array([0, 50, 80], np.float32)
    cam = Camera(cp + shake(t, 0.03 + 0.05 * math.sin(u * 9) ** 8), tgt, 66)
    ground(w, -400, 400, -80, 700, (0.22, 0.3, 0.2), 60.0)
    stripe_road(w, -80, 700, 9.0)
    # skyline far away
    for i in range(20):
        h = 20 + hsh(5, i) * 60
        building(w, -200 + i * 21 + hsh(6, i) * 8, 520 + hsh(7, i) * 40, 14, 14, h, BCOL[i % 5], cp, 0.0, seed=i, neon=False)
    # tanks lined across the field
    for i in range(7):
        x = -26 + i * 8.7 + (4 if i % 2 else 0)
        z = -4 + (i % 2) * 14
        fire_phase = 0.0
        rec = 0.0
        for tm in MISSILE_T:
            if (int(tm * 5) + i) % 7 == 0 and 0 < t - tm < 0.25: rec = 0.8 * (1 - (t - tm) / 0.25)
        tank(w, (x, 0, z), 0.0, t, 0.75, rec)
    for i in range(10):
        person(w, (-24 + i * 5.4, 0, -12 + (i % 3) * 2), 0.0, 60 + i, "idle", t, 1.0, shirt=(0.3, 0.4, 0.25), pants=(0.25, 0.3, 0.2), helmet=True, look_up=0.5)
    # shield + ship
    pulse = 0.14 + 0.04 * math.sin(t * 4)
    mothership(w, (0, 150, 260), 95, t)
    hits = []
    for k, tm in enumerate(MISSILE_T):
        a = t - tm
        if a < 0 or a > 3.4: continue
        src = np.array([-26 + (k * 7 % 7) * 8.7, 3.5, -4], np.float32)
        dirv = np.array([math.sin(k * 1.7) * 0.5, 0.5, 1.0], np.float32)
        end = SHIELD_C + np.array([math.sin(k * 2.3) * 70, -40 + math.cos(k * 1.1) * 30, -100 + 20 * math.cos(k)], np.float32)
        s = clamp(a / 2.6)
        p = src + (end - src) * s + np.array([0, 18 * math.sin(s * math.pi), 0], np.float32)
        s2_ = clamp((a - 0.06) / 2.6)
        p2 = src + (end - src) * s2_ + np.array([0, 18 * math.sin(s2_ * math.pi), 0], np.float32)
        if s < 1:
            w.beam(p2, p, 0.45, (1.0, 0.95, 0.85), em=1.0)
            for j in range(1, 7):
                sj = clamp(s - j * 0.012)
                pj = src + (end - src) * sj + np.array([0, 18 * math.sin(sj * math.pi), 0], np.float32)
                g = 0.9 - j * 0.1
                w.box(pj, (0.9 + j * 0.15,) * 3, (g, g, g), em=0.0)
        else:
            hits.append((end, a - 2.6))
    for (pos, a) in hits:
        if a < 0.5:
            w.sphere(pos, 7 + 22 * a, (0.6, 0.9, 1.0), em=1.0, alpha=max(0.1, 0.7 - a * 1.3), nu=8, nv=5)
    w.sphere(SHIELD_C, 108, (0.3, 0.6, 1.0), em=1.0, alpha=pulse, nu=16, nv=9)
    sky_top = (0.03, 0.04, 0.12); sky_hor = (0.45, 0.22, 0.26)
    bg, yh, F = R.background(cam, sky_top, sky_hor, (0.3, 0.2, 0.24), (0.18, 0.24, 0.16))
    img = R.render(w, cam, bg, light=(-0.3, 0.7, 0.4), amb=0.38, fog=sky_hor, fog_range=(110, 700))
    return finish(img)


# ===================================================================== scene 5: the lab (33-42)
def s5(t):
    u = t - 33.0
    w = World()
    cp = np.array([lerp(-4, 2, u / 9), 1.5, lerp(0, 5, u / 9)], np.float32)
    tgt = np.array([0, 4.6, 14], np.float32)
    cam = Camera(cp, tgt, 66)
    floor_c = (0.28, 0.3, 0.36)
    w.box((0, -0.2, 8), (30, 0.4, 36), floor_c)
    w.box((0, 6, 22), (30, 12, 0.6), (0.18, 0.2, 0.28))          # back wall
    w.box((-15, 6, 8), (0.6, 12, 36), (0.2, 0.22, 0.3)); w.box((15, 6, 8), (0.6, 12, 36), (0.2, 0.22, 0.3))
    w.box((0, 12.2, 8), (30, 0.4, 36), (0.14, 0.16, 0.22))
    # big screen with waveform
    w.box((0, 6.2, 21.6), (17, 8.4, 0.3), (0.03, 0.05, 0.08))
    for gy in range(-3, 4):
        w.box((0, 6.2 + gy * 1.0, 21.4), (16, 0.04, 0.05), (0.1, 0.35, 0.3), em=0.6)
    n = 64
    for k in range(n):
        x = -7.6 + k * 15.2 / (n - 1)
        ph = x * 0.9 + t * 3.0
        y = 6.2 + math.sin(ph) * 1.0 + math.sin(ph * 2.3) * 0.4
        d = abs(x - lerp(-6, 7, clamp((u - 3.5) / 3.2)))
        dip = max(0.0, 1 - d / 0.9)
        y = y - dip * 2.6 * smooth((u - 3.5) / 0.4)
        col = (0.3, 1.0, 0.7) if dip < 0.2 else (1.0, 0.4, 0.3)
        w.box((x, y, 21.3), (0.26, 0.26, 0.1), col, em=1.0)
    # desks with monitors
    for i in range(3):
        for sd in (-1, 1):
            x = sd * (5 + i * 3.2 * 0 + 1.5 * i); z = 4 + i * 5.5
            w.box((x, 0.9, z), (4.4, 0.18, 2.0), (0.55, 0.45, 0.35))
            for lx in (-1.9, 1.9): w.box((x + lx, 0.45, z), (0.2, 0.9, 1.8), (0.3, 0.25, 0.2))
            w.box((x, 1.9, z + 0.6), (1.8, 1.1, 0.12), (0.04, 0.05, 0.08))
            w.box((x, 1.9, z + 0.52), (1.6, 0.9, 0.05), (0.2, 0.7, 1.0), em=0.9)
    # scientists
    sc = [(-2.2, 10, 0.0, "idle"), (0.6, 11.5, 0.0, "idle"), (3.0, 9.8, 0.0, "idle"), (-4.6, 8.0, 0.3, "idle"), (5.2, 8.0, -0.3, "idle")]
    for i, (x, z, yaw, an) in enumerate(sc):
        person(w, (x, 0, z), yaw, 200 + i, an, t, 1.0, shirt=(0.95, 0.95, 0.97), pants=(0.2, 0.2, 0.25), look_up=0.2 * math.sin(t + i) + 0.15,
               arm_pose=(1.5 if i == 1 and u > 3.0 else None))
    sky = (0.05, 0.07, 0.12)
    bg, yh, F = R.background(cam, sky, sky, sky, sky)
    img = R.render(w, cam, bg, light=(0.1, 0.9, -0.3), amb=0.42, fog=(0.08, 0.1, 0.15), fog_range=(40, 120))
    return finish(img, 0.7)


# ===================================================================== scene 6: dogfight (42-52)
JETS = [(hsh(8, i, 1) - 0.5, hsh(8, i, 2) - 0.3, hsh(8, i, 3)) for i in range(16)]
LOSSES = [(43.0, 3), (43.8, 7), (44.5, 1), (45.2, 11), (46.0, 5), (46.6, 13), (47.3, 9), (48.2, 2), (48.9, 14), (49.6, 6)]


def s6(t):
    u = t - 42.0
    w = World()
    speed = 48.0
    ship_z = lerp(560, 150, smooth(u / 8.4))
    cp = np.array([math.sin(u * 0.8) * 2.0, 3.2 + math.sin(u * 1.1) * 0.6, -13], np.float32)
    cam = Camera(cp + shake(t, 0.05 + 0.18 * smooth((u - 8.0) / 2.0)), np.array([0, 2.2, 30], np.float32), 74, roll=0.05 * math.sin(u * 0.9))
    # sky ground below
    ground(w, -900, 900, -200, 1400, (0.2, 0.26, 0.2), 120.0, y=-60.0)
    # clouds as pale boxes streaming past
    for i in range(26):
        cz = ((hsh(1, i) * 700 - speed * u) % 700) - 100
        cx = (hsh(2, i) - 0.5) * 260; cy = -20 + hsh(3, i) * 30
        w.box((cx, cy, cz), (24 + hsh(4, i) * 30, 5, 18), (0.92, 0.9, 0.95))
    # the mothership & shield
    shield_up = u < 8.2
    mothership(w, (0, 8, ship_z + 100), 120, t, damage=0.0 if shield_up else 1.0)
    if shield_up:
        flick = 0.12 + 0.05 * math.sin(t * 9) + (0.2 if int(t * 12) % 9 == 0 else 0)
        w.sphere((0, 14, ship_z + 100), 140, (0.3, 0.6, 1.0), em=1.0, alpha=flick, nu=16, nv=9)
    # lead jet and wingmen
    jet(w, (0, 0, 0), 0, 0.0, 0.2 * math.sin(u * 0.9), (0.6, 0.65, 0.75), t, 1.0, 1.0)
    for i, (jx, jy, jz) in enumerate(JETS):
        lost = next((tm for tm, k in LOSSES if k == i), None)
        if lost is not None and t > lost + 0.05: continue
        p = np.array([jx * 70 + math.sin(t * 0.8 + i) * 2, jy * 28 + math.sin(t * 1.1 + i * 2) * 1.5, 4 + jz * 55], np.float32)
        if abs(p[0]) < 5: p[0] += 8 * (1 if jx >= 0 else -1)
        jet(w, p, 0, 0, 0.3 * math.sin(t * 0.7 + i), (0.55 + 0.1 * hsh(i, 1), 0.6, 0.7), t, 1.0)
        if lost is not None and lost - 0.5 < t <= lost + 0.05:
            pass
    # alien saucers sweeping past
    for i in range(12):
        zc = ((hsh(9, i) * 460 - speed * 1.15 * u) % 460) + 20
        pos = (np.array([(hsh(10, i) - 0.5) * 90, (hsh(11, i) - 0.5) * 30, zc], np.float32))
        saucer(w, pos, 3.2, t + i, tilt=0.3 * math.sin(t + i))
        # laser shots from saucers towards our jets
        if (int(t * 4) + i) % 5 == 0:
            tgt_i = JETS[i % 16]
            tp = np.array([tgt_i[0] * 70, tgt_i[1] * 28, 4 + tgt_i[2] * 55], np.float32)
            w.beam(pos, tp, 0.18, (0.3, 1.0, 0.5) if i % 2 else (1.0, 0.3, 0.3), em=1.0)
    # missiles / tracers streaking toward the ship
    for k in range(18):
        a = (u * 1.6 + k * 0.37) % 1.0
        src = np.array([(hsh(12, k) - 0.5) * 30, (hsh(13, k) - 0.5) * 8, 6.0], np.float32)
        end = np.array([(hsh(14, k) - 0.5) * 80, 10, ship_z + 30], np.float32)
        p = src + (end - src) * a; p2 = src + (end - src) * max(0, a - 0.05)
        w.beam(p2, p, 0.22, (1.0, 0.9, 0.6), em=1.0)
    # explosions where jets are lost
    for tm, k in LOSSES:
        a = t - tm
        if -0.0 <= a < 1.6:
            jx, jy, jz = JETS[k]
            explosion(w, (jx * 70, jy * 28, 4 + jz * 55), a, 7.0, seed=k * 3)
    # shield drops -> six missiles slip through into the core
    if u > 8.0:
        a = u - 8.0
        for k in range(6):
            s = clamp((a - k * 0.04) / 0.45)
            src = np.array([(k - 2.5) * 3, 0, 8], np.float32)
            core = np.array([0, 5, ship_z + 100], np.float32)
            p = src + (core - src) * s
            if s < 1: w.beam(src + (core - src) * max(0, s - 0.08), p, 0.5, (1.0, 1.0, 0.9), em=1.0)
        if a > 0.45:
            b = a - 0.45
            explosion(w, (0, 8, ship_z + 90), b, 36.0, seed=99)
            if b > 0.3: explosion(w, (30, 10, ship_z + 105), b - 0.3, 24.0, seed=98)
            if b > 0.55: explosion(w, (-34, 6, ship_z + 95), b - 0.55, 28.0, seed=97)
    sky_top = (0.1, 0.2, 0.5); sky_hor = (0.95, 0.7, 0.55)
    bg, yh, F = R.background(cam, sky_top, sky_hor, sky_hor, (0.2, 0.26, 0.2))
    img = R.render(w, cam, bg, light=(0.3, 0.9, 0.3), amb=0.5, fog=sky_hor, fog_range=(150, 900))
    return finish(img, 0.6)


# ===================================================================== scene 7: aftermath (52-62)
def s7(t):
    u = t - 52.0
    w = World()
    cp = np.array([0, lerp(2.4, 5.5, u / 10), lerp(-34, -50, u / 10)], np.float32)
    tgt = np.array([0, lerp(14, 22, smooth((u - 3) / 5)), 40], np.float32)
    cam = Camera(cp + shake(t, 0.02), tgt, 66)
    street(w, -80, 330)
    # damaged skyline: some low, some intact; lit warm with dawn
    def hscale(key):
        return 0.45 + 0.55 * hsh(31, *key)
    city(w, cp, 0.28, 11, -80, 330, hscale=hscale)
    # falling wreckage of the mothership
    for i in range(12):
        a = u + hsh(5, i) * 3.0
        x = (hsh(6, i) - 0.5) * 120; z = 130 + hsh(7, i) * 120
        y = 150 - 9.8 * 0.5 * (min(a, 3.8) ** 2) * 3.0 + hsh(8, i) * 40
        if y > 2 and u < 4.8:
            w.box((x, y, z), (12 + 10 * hsh(9, i),) * 3, (0.2, 0.21, 0.26), rot_y(a) @ rot_x(a * 0.6))
            w.box((x, y + 4, z), (3, 3, 3), (1.0, 0.5, 0.15), em=1.0)
        if u > 3.6 and u < 6.0 and y <= 2:
            explosion(w, (x, 4, z), (u - 3.6 - hsh(5, i)), 12.0, seed=i)
    # fires
    for i in range(8):
        x = (hsh(41, i) - 0.5) * 60; z = 20 + i * 24
        for j in range(4):
            fy = 6 + j * 3 + math.sin(t * 6 + i + j) * 1.5
            w.box((x, fy, z), (2.4 - j * 0.4,) * 3, (1.0, 0.45 + 0.1 * j, 0.1), em=1.0)
    # survivors cheering
    crowd(w, cp, t, 24, (0, 0, -14), (13, 18), "cheer", seed=51, yaw=math.pi, speed=0.0, scale=1.1)
    crowd(w, cp, t, 16, (0, 0, 25), (14, 40), "walk", seed=57, yaw=math.pi, speed=-1.0, direction=(0, 0, 1))
    rise = smooth(u / 7)
    sky_top = mixc((0.08, 0.08, 0.2), (0.35, 0.45, 0.8), rise); sky_hor = mixc((0.45, 0.2, 0.2), (1.0, 0.75, 0.5), rise)
    bg, yh, F = R.background(cam, sky_top, sky_hor, sky_hor, (0.2, 0.2, 0.24))
    # sun disc
    arr = np.asarray(bg)
    sy = int(yh - 120 - 120 * rise); sx = RW // 2 + 160
    if 0 <= sy < RH:
        yy, xx = np.ogrid[:RH, :RW]
        dd = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
        arr = np.asarray(bg).copy()
        arr += (np.clip(1 - dd / 260, 0, 1) ** 2)[..., None] * np.array([1.0, 0.7, 0.3], np.float32) * 0.8
        arr = np.where((dd < 34)[..., None], np.array([1.0, 0.95, 0.75], np.float32), arr)
        bg = arr
    img = R.render(w, cam, bg, light=(0.6, 0.5, 0.6), amb=0.45, fog=sky_hor, fog_range=(80, 400))
    return finish(img, 0.55)


SCENES = [(0, 7, s1), (7, 15, s2), (15, 24, s3), (24, 33, s4), (33, 42, s5), (42, 52, s6), (52, 62, s7)]


def render3d(t):
    for a, b, fn in SCENES:
        if a <= t < b: return fn(t)
    return SCENES[-1][2](SCENES[-1][1] - 0.01)
