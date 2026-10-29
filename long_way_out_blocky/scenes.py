"""'The Long Way Out' - blocky 3D version (no narration; timed captions)."""
import math, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
from engine import *
from props import *
from ui import smooth

RW, RH = 720, 1280
R = Renderer(RW, RH)
FAR = (1e6, 2e6)
SUIT = (0.94, 0.93, 0.9)
MOON = (0.46, 0.47, 0.54)


def lerp(a, b, f): return a + (b - a) * f
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): return smooth(x)
def mixc(a, b, f): return tuple(float(x) * (1 - f) + float(y) * f for x, y in zip(a, b))
def V3(*a): return np.array(a, np.float32)


def finish(img, amt=0.5):
    return bloom(img, 205, amt).resize((1080, 1920), Image.LANCZOS)


def space(w, cp, seed=1, bright=1.0):
    starbox(w, cp, seed, 260, 700, bright)


def render(w, cam, top=(0.01, 0.01, 0.04), hor=(0.03, 0.04, 0.12), light=(-0.5, 0.7, 0.4), amb=0.38, fog=(0.02, 0.03, 0.08), fog_range=FAR, gnd=None):
    bg, yh, F = R.background(cam, top, hor, gnd or hor, gnd or hor)
    return R.render(w, cam, bg, light=light, amb=amb, fog=fog, fog_range=fog_range)


def astro(w, pos, yaw=0.0, t=0.0, seed=0, anim="idle", **kw):
    person(w, pos, yaw, seed, anim, t, 1.0, shirt=SUIT, pants=SUIT, hair=(0.9, 0.9, 0.92), helmet=True, patch=True, pack=True, **kw)


def moon_ground(w, cx=0.0, cz=0.0, half=260, y=0.0):
    ground(w, cx - half, cx + half, cz - half, cz + half, MOON, 30.0, y)
    for i in range(18):
        x = cx + (hsh(1, i) - 0.5) * 2 * half * 0.6; z = cz + (hsh(2, i) - 0.5) * 2 * half * 0.6
        r = 3 + hsh(3, i) * 9
        w.box((x, 0.03, z), (r * 2, 0.04, r * 2), (0.5, 0.5, 0.56))
        w.box((x, 0.05, z), (r * 1.5, 0.04, r * 1.5), (0.44, 0.44, 0.5))
    for i in range(30):
        x = cx + (hsh(4, i) - 0.5) * 120; z = cz + (hsh(5, i) - 0.5) * 120
        w.box((x, 0.2, z), (0.5 + hsh(6, i), 0.4 + hsh(7, i) * 0.4, 0.5 + hsh(8, i)), (0.55, 0.55, 0.6))


EARTH_POS = V3(80, 70, -230)


# ============================================================ scene 1
def s1(t):
    w = World()
    cp0 = V3(0, 1.65, 2.2)
    f = ease(t / 2.2)
    cpos = V3(lerp(0, -2.5, ease((t - 1.5) / 2.5)), lerp(1.66, 2.0, f), lerp(2.0, 9.0, f))
    head = V3(0, 1.68, 0)
    tgt = head + (EARTH_POS - head) * (0.28 * ease((t - 2.0) / 2.0)) * 1.0 + V3(0, 0, 0)
    tgt = V3(*(head + (V3(30, 36, -120) - head) * ease((t - 2.0) / 2.0)))
    cam = Camera(cpos, tgt, lerp(40, 62, f))
    space(w, cpos, 1)
    moon_ground(w)
    planet(w, EARTH_POS, 46, "earth", rot=t * 0.06)
    yaw = lerp(0.0, math.pi * 0.86, ease((t - 2.1) / 1.2))
    astro(w, (0, 0, 0), yaw, t, 1, look_up=0.0)
    if t < 3.0:   # Earth reflected in the visor
        w.box((-0.075, 1.72, 0.222), (0.1, 0.1, 0.02), (0.2, 0.5, 0.95), em=0.9)
        w.box((-0.06, 1.74, 0.225), (0.045, 0.045, 0.02), (0.35, 0.75, 0.35), em=0.9)
    img = render(w, cam, light=(-0.5, 0.6, 0.7), amb=0.36)
    return finish(img)


# ============================================================ scene 2: lunar base
def s2(t):
    u = t - 4.0
    w = World()
    cp = V3(lerp(-8, 3, u / 7), lerp(3.6, 5.2, u / 7), -15)
    cam = Camera(cp, V3(lerp(-3, 7, u / 7), 3.4, 22), 68)
    space(w, cp, 2)
    moon_ground(w, 0, 20)
    planet(w, V3(-90, 70, 190), 12, "earth", rot=t * 0.05)
    # crater rim + solar panels
    for i in range(9):
        x = -42 + i * 10.5
        k = ease((u - 0.8 - i * 0.2) / 0.6)
        w.box((x, 1.3 * k, 52 + 2 * math.sin(i)), (4, 2.6 * k + 0.01, 3), (0.4, 0.4, 0.46))
        if k > 0.01:
            w.box((x, 3.0 * k + 0.6, 52), (0.3, 3.0 * k, 0.3), (0.7, 0.7, 0.75))
            gl = max(0, math.sin(t * 2 + i * 0.6)) ** 6
            w.box((x, 3.8 * k + 1.0, 51.2), (6 * k, 0.25, 3.6 * k), (0.1 + gl * 0.5, 0.2 + gl * 0.5, 0.55 + gl * 0.4), rot_x(-0.45), em=gl)
    # habitats: inflate, then get buried
    HAB = [(-15, 20, 7.5, 0.0), (6, 34, 6.0, 0.7), (27, 22, 6.6, 1.3)]
    for (x, z, r, t0) in HAB:
        infl = ease((u - t0 * 0.4) / 1.6)
        cover = 0.8 * ease((u - 2.5 - t0 * 0.8) / 4.2)
        rr = r * (0.3 + 0.7 * infl)
        if infl > 0.01:
            w.sphere((x, 0, z), rr, (0.96, 0.96, 0.98), nu=10, nv=6)
            n = int(26 * cover)
            for k in range(n):
                a = hsh(5, k, int(x)) * 6.283; b = 0.15 + hsh(6, k, int(z)) * 1.1
                p = V3(x + math.cos(a) * math.cos(b) * rr * 0.95, math.sin(b) * rr * 0.95, z + math.sin(a) * math.cos(b) * rr * 0.95)
                w.box(p, (2.4, 2.0, 2.4), (0.48, 0.48, 0.54) if k % 3 else (0.58, 0.58, 0.63), rot_y(k))
            if cover > 0.4:
                w.box((x, 1.3, z - rr * 0.98), (2.0, 2.0, 0.4), (1.0, 0.85, 0.5), em=0.9)
    # regolith robots
    for i, (x, z, r, t0) in enumerate(HAB):
        ph = (u * 0.5 + i * 0.37) % 1.0
        rx = x - r * 1.5 + 2.5 * r * abs(2 * ph - 1)
        if u > 1.5:
            w.box((rx, 0.5, z - r * 1.2), (1.6, 0.8, 2.4), (0.95, 0.75, 0.2))
            w.box((rx, 1.1, z - r * 1.2 + 0.4), (0.9, 0.5, 0.9), (0.15, 0.2, 0.35))
            w.box((rx - 0.7, 0.9, z - r * 1.2 - 1.3), (0.9, 0.6, 1.0), (0.5, 0.5, 0.55))
    # ice crater + rig
    cx, cz = 22, 2
    w.box((cx, 0.04, cz), (20, 0.06, 15), (0.05, 0.06, 0.12))
    for i in range(9):
        a = hsh(9, i)
        w.box((cx - 6 + hsh(10, i) * 12, 0.5, cz - 4 + a * 8), (0.8, 1.0, 0.8), (0.55, 0.95, 1.0), em=0.8 * ease((u - 3) / 1.0))
    if u > 3.2:
        k = ease((u - 3.2) / 1.3)
        for sx in (-1, 1):
            for sz in (-1, 1):
                w.box((cx + sx * 1.2, 4.2 * k, cz + sz * 1.2), (0.25, 8.4 * k, 0.25), (0.78, 0.8, 0.88))
        w.box((cx, 8.4 * k, cz), (3, 0.8, 3), (0.95, 0.5, 0.2))
        w.box((cx + math.sin(t * 20) * 0.1, 4 * k, cz), (0.4, 8 * k, 0.4), (0.55, 0.58, 0.66))
        for j in range(5):
            f = (u * 0.7 + j / 5) % 1.0
            w.box((lerp(cx, cx - 14, f), lerp(8, 3, f) + math.sin(f * 3.14) * 2, cz), (0.7, 0.7, 0.7), (0.7, 0.95, 1.0), em=1.0)
        for j in range(2):
            w.cyl((cx - 14 + j * 2.4, 2.2, cz), 1.0, 4.4, (0.93, 0.94, 0.98), 8)
    # Ava waving at a drone
    astro(w, (-3.2, 0, -4), math.pi * 0.93, t, 2, anim="idle", arm_pose=2.6 + 0.3 * math.sin(t * 8), look_up=0.1)
    dp = V3(2.2 + math.sin(t * 1.4) * 0.5, 3.8 + math.sin(t * 3) * 0.2, -4.5)
    w.box(dp, (1.2, 0.8, 1.2), (0.96, 0.96, 0.98)); w.box(dp + V3(0, 0, -0.62), (0.5, 0.5, 0.1), (0.2, 0.5, 1.0), em=0.9)
    for sx in (-1, 1):
        w.box(dp + V3(sx * 1.2, 0.5, 0), (1.3, 0.06, 0.5), (0.8, 0.85, 0.95))
    if int(t * 2) % 2 == 0: w.box(dp + V3(0.5, 0.5, -0.6), (0.14, 0.14, 0.14), (1, 0.2, 0.2), em=1.0)
    img = render(w, cam, light=(-0.5, 0.6, 0.55), amb=0.38)
    return finish(img)


# ============================================================ scene 3: Mars
def ship(w, p, yaw=0.0, thrust=0.0, scale=1.0):
    Rm = rot_y(yaw)
    p = np.asarray(p, np.float32)
    w.box(p, np.array([3, 2.4, 9], np.float32) * scale, (0.95, 0.95, 0.97), Rm)
    w.box(p + Rm @ V3(0, 0, 5) * scale, np.array([2.6, 2.0, 2.4], np.float32) * scale, (0.95, 0.5, 0.2), Rm)
    for sg in (-1, 1):
        w.box(p + Rm @ V3(sg * 5.5, 0, -1) * scale, np.array([7, 0.2, 3.5], np.float32) * scale, (0.15, 0.25, 0.7), Rm)
    if thrust > 0:
        w.box(p + Rm @ V3(0, 0, -5.5 - 2 * thrust) * scale, np.array([1.6, 1.4, 3 * thrust + 0.5], np.float32) * scale, (1.0, 0.6, 0.2), Rm, em=1.0)


def mars_orbit(t):
    u = t - 11.0
    w = World()
    cp = V3(0, 4, -40)
    cam = Camera(cp, V3(lerp(-6, 2, u / 2.4), 2, 0), 60)
    space(w, cp, 3)
    planet(w, V3(22, -26, 50 + 4 * (1 - ease(u / 2.4))), 46, "mars", rot=t * 0.08)
    planet(w, V3(-30, 18, 90), 2.2, "earth")
    a = ease(u / 2.4)
    for i in range(18):
        s = i / 17
        if s > a: break
        w.box(V3(lerp(-28, 8, s) + math.sin(s * 3) * 2, lerp(16, 12 - 8 * s, s) + math.sin(s * 3.1) * 5, lerp(88, 14, s)), (0.6, 0.6, 0.6), (1.0, 0.85, 0.6), em=1.0)
    ship(w, V3(lerp(-28, 8, a), lerp(16, 4, a), lerp(88, 14, a)), lerp(0.4, 1.9, a), 1 - a if u > 1 else 0.3, 0.6)
    return render(w, cam, top=(0.02, 0.01, 0.02), hor=(0.06, 0.03, 0.04), light=(-0.6, 0.5, 0.4), amb=0.25)


def mars_ground(w, cp, night=0.0, ground_c=(0.78, 0.38, 0.22), z0=-120):
    ground(w, -300, 300, z0, 400, mixc(ground_c, (0.2, 0.1, 0.1), night * 0.7), 40.0)
    for i in range(22):
        x = (hsh(1, i) - 0.5) * 400; z = 120 + hsh(2, i) * 200
        h = 8 + hsh(3, i) * 26
        w.box((x, h / 2, z), (14 + hsh(4, i) * 24, h, 12 + hsh(5, i) * 14), mixc((0.62, 0.3, 0.2), (0.15, 0.08, 0.1), night * 0.7))
    for i in range(30):
        w.box(((hsh(6, i) - 0.5) * 120, 0.4, -10 + hsh(7, i) * 80), (0.8 + hsh(8, i) * 1.5, 0.7, 0.8 + hsh(9, i) * 1.4), mixc((0.5, 0.24, 0.16), (0.2, 0.1, 0.1), night * 0.6))


def mars_landing(t):
    u = t - 13.4
    w = World()
    cp = V3(-10 + 2 * u, 5, -34)
    cam = Camera(cp, V3(0, 12 - 2 * u, 20), 62)
    mars_ground(w, cp)
    land = ease(u / 1.5)
    y = lerp(70, 3.2, 1 - (1 - land) ** 2.2)
    x = 0
    w.cyl((x, y, 20), 2.2, 6.0, (0.95, 0.95, 0.97), 8, ts=0.75)
    w.cyl((x, y + 3.6, 20), 1.1, 2.0, (0.95, 0.5, 0.2), 8, ts=0.2)
    for sx, sz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        w.box((x + sx * 2.6, y - 2.2, 20 + sz * 2.6), (0.35, 3.4, 0.35), (0.6, 0.62, 0.7), rot_z(0.4 * sx) @ rot_x(-0.4 * sz))
        w.box((x + sx * 3.4, max(0.2, y - 3.6), 20 + sz * 3.4), (1.2, 0.2, 1.2), (0.5, 0.52, 0.6))
    if u < 1.45:
        fl = 1 - u / 1.5
        w.box((x, y - 5.4, 20), (1.6, 5.6 * (0.5 + fl), 1.6), (1.0, 0.7, 0.25), em=1.0)
    d = clamp((u - 1.0) / 1.0)
    for i in range(16):
        a = i / 16 * 6.283
        r = 5 + 24 * ease(d) * (0.6 + 0.4 * hsh(2, i))
        w.box((x + math.cos(a) * r, 1.2 + 2 * (1 - d), 20 + math.sin(a) * r), (3 + 3 * d,) * 3, (0.9, 0.58, 0.4), rot_y(a), em=0.0)
    sky_top = (0.5, 0.2, 0.14); sky_hor = (0.98, 0.65, 0.42)
    img = render(w, cam, top=sky_top, hor=sky_hor, light=(-0.4, 0.7, 0.4), amb=0.5, fog=sky_hor, fog_range=(120, 420))
    return img


def mars_timelapse(t):
    u = t - 15.2
    w = World()
    night = ease((u - 1.0) / 1.9)
    cp = V3(lerp(-14, 6, u / 3.3), 6, -34)
    cam = Camera(cp, V3(0, 0, 10), 64)
    mars_ground(w, cp, night, z0=10.2)
    # cutaway face: the underground base
    w.box((0, -5, 10), (110, 10, 0.5), mixc((0.4, 0.2, 0.14), (0.14, 0.08, 0.09), night * 0.5))
    tun = ease((u - 0.5) / 2.0)
    for i, (x, y) in enumerate(((-30, -4), (-5, -4), (22, -6.5), (44, -6.5))):
        k = ease(tun * 3 - i + 0.3)
        w.box((x, y, 9.6), (13 * k, 4.5 * k, 0.4), (0.75, 0.77, 0.86))
        w.box((x, y, 9.4), (11 * k, 3 * k, 0.2), (1.0, 0.72, 0.38), em=0.5 + 0.5 * night)
        if i < 3:
            w.box((x + 13, y, 9.6), (24 * ease(tun * 3 - i), 2.4, 0.4), (0.7, 0.72, 0.8))
    items = [(-26, 8.0, 0.5, "d"), (0, 6.0, 1.0, "g"), (26, 9.0, 1.4, "d"), (46, 5.5, 1.9, "g"), (-46, 5.5, 2.2, "g")]
    for (x, r, t0, kind) in items:
        k = ease((u - t0 * 0.7) / 0.7)
        if k <= 0.01: continue
        glow_c = (1.0, 0.82, 0.5) if kind == "d" else (0.4, 1.0, 0.55)
        w.sphere((x, 0, 12), r * (0.4 + 0.6 * k), mixc((0.85, 0.92, 1.0), glow_c, night * 0.6), em=0.55 * night, alpha=0.62, nu=10, nv=6)
        w.box((x, 1.2, 12), (r * 0.7, 2.4, 2), glow_c, em=0.6 + 0.4 * night)
    rx = lerp(-50, 50, (u * 0.25) % 1.0)
    w.box((rx, 0.7, 2), (2.2, 1.0, 3.2), (0.95, 0.75, 0.2)); w.box((rx, 1.4, 2.3), (1.2, 0.5, 1.2), (0.15, 0.2, 0.35))
    # sun crossing the sky then stars
    sp = clamp(u / 1.9)
    if sp < 1:
        w.sphere(V3(lerp(-90, 90, sp), 60 + 30 * math.sin(sp * 3.14), 220), 9, (1, 0.95, 0.85), em=1.0, nu=8, nv=5)
    if night > 0.3: starbox(w, cp, 4, 200, 500, night)
    top = mixc((0.5, 0.2, 0.14), (0.02, 0.01, 0.06), night); hor = mixc((0.98, 0.65, 0.42), (0.25, 0.1, 0.14), night)
    return render(w, cam, top=top, hor=hor, light=(-0.3, 0.7, 0.4), amb=lerp(0.5, 0.3, night), fog=hor, fog_range=(130, 420))


def mars_child(t):
    u = t - 18.5
    w = World()
    cp = V3(0, 1.7, -4.2 - 0.3 * u)
    cam = Camera(cp, V3(3, 8.5 + 1.5 * ease(u / 2.5), 14), 72)
    starbox(w, cp, 5, 260, 600, 1.0)
    planet(w, V3(46, 78, 250), 5.0, "earth", em=0.7)
    ground(w, -60, 60, -30, 60, (0.16, 0.1, 0.12), 20.0)
    for i in range(12):
        x = -18 + i * 3.4; h = 1.5 + hsh(2, i) * 3
        w.box((x, h / 2, 6 + (i % 3) * 2), (1.0, h, 1.0), (0.25, 0.8, 0.4), em=0.4)
    for i in range(7):
        a = math.pi * (0.08 + 0.84 * i / 6)
        w.box((math.cos(a) * 44, math.sin(a) * 30 + 3, 30), (0.5, 8, 0.5), (0.6, 0.8, 1.0), rot_z(a - 1.57), em=0.5, alpha=0.5)
    person(w, (-0.9, 0, 2.2), 0.0, 71, "idle", t, 1.0, shirt=(0.28, 0.58, 0.62), pants=(0.2, 0.2, 0.3), skin=(0.78, 0.55, 0.42), hair=(0.12, 0.07, 0.05), look_up=0.9, patch=True, arm_pose_l=0.4)
    person(w, (0.9, 0, 2.2), 0.0, 72, "idle", t, 0.7, shirt=SUIT, pants=(0.4, 0.4, 0.5), skin=(0.9, 0.68, 0.55), hair=(0.1, 0.06, 0.04), look_up=1.0, patch=True, arm_pose=2.9)
    return render(w, cam, top=(0.01, 0.01, 0.05), hor=(0.08, 0.04, 0.1), light=(0.2, 0.7, 0.5), amb=0.45)


def s3(t):
    if t < 13.4: return finish(mars_orbit(t))
    if t < 15.2: return finish(mars_landing(t), 0.4)
    if t < 18.5: return finish(mars_timelapse(t), 0.4)
    return finish(mars_child(t), 0.6)


# ============================================================ scene 4: outer system
def s4(t):
    w = World()
    if t < 24.2:
        u = t - 21.0
        cp = V3(0, 6, -92 + 6 * u)
        cam = Camera(cp, V3(0, 0, 0), 62)
        space(w, cp, 6)
        rr = rot_y(t * 0.3)
        for (c, s_) in (((0, 0, 0), (22, 18, 20)), ((13, 4, 6), (14, 12, 14)), ((-11, -6, -5), (13, 10, 12)), ((4, 12, -2), (12, 9, 11)), ((-4, 8, 10), (9, 8, 9))):
            w.box(rr @ V3(*c), s_, (0.5, 0.52, 0.55) if hsh(c[0], 1) < 0.5 else (0.44, 0.47, 0.5), rr)
        for i in range(6):
            a = t * 0.3 + i * 1.05
            p = rr @ V3(math.cos(a) * 15, math.sin(a * 1.7) * 9, math.sin(a) * 15)
            w.box(p, (1.6, 1.6, 1.6), (1.0, 0.85, 0.4), em=0.8 * (0.5 + 0.5 * math.sin(t * 5 + i)))
        for i, (ang, rad) in enumerate(((0.9, 17), (2.6, 14))):
            a = ang + t * 0.3
            surf = rr @ V3(math.cos(a) * rad, 3, math.sin(a) * rad)
            fp = surf + V3(0, 9, -9 if i == 0 else 8)
            w.beam(surf, fp + V3(0, -2, 0), 0.18, (0.95, 0.95, 1.0), em=0.8)
            w.box(surf, (0.6, 1.4, 0.6), (1.0, 0.6, 0.2), em=1.0)
            person(w, fp + V3(0, -1.8, 0), math.pi if i == 0 else 0, 80 + i, "idle", t, 1.0, shirt=SUIT, pants=SUIT, helmet=True, patch=True, pack=True,
                   arm_pose=1.5 + 0.3 * math.sin(t * 6))
            for j in range(4):
                f = (t * 3 + j * 0.37) % 1.0
                w.box(surf + V3(0, f * 2, 0) + V3(math.sin(j * 3) * f, 0, math.cos(j * 3) * f), (0.2, 0.2, 0.2), (1.0, 0.8 * (1 - f) + 0.2, 0.3), em=1.0)
        return finish(render(w, cam, top=(0.01, 0.05, 0.09), hor=(0.03, 0.12, 0.2), light=(-0.5, 0.4, -0.7), amb=0.5), 0.5)
    if t < 27.2:
        u = t - 24.2
        sc = ease((u - 0.5) / 2.0) * 60
        cp = V3(0, 14 - sc, -46)
        cam = Camera(cp, V3(0, 12 - sc, 0), 60)
        # ice cutaway block + ocean
        w.box((0, 0, 10), (140, 60, 40), (0.78, 0.9, 0.98))
        for k in range(6):
            w.box((0, 10 - k * 9, -9.9), (140, 4.2, 0.2), (0.62 + 0.04 * k, 0.8 - 0.02 * k, 0.92), em=0.0)
        w.box((0, -62, 10), (140, 70, 40), (0.03, 0.12, 0.25))
        planet(w, V3(-30, 62, 70), 36, "jupiter", rot=t * 0.05)
        shaft = clamp(u / 2.7)
        sy = lerp(26, -34, ease(shaft))
        w.box((0, (26 + sy) / 2, -10.1), (4.0, 26 - sy + 1, 0.2), (0.12, 0.22, 0.36))
        w.box((0, sy, -10.6), (3.2, 2.0, 0.8), (1.0, 0.8, 0.2), em=0.2); w.box((0, sy + 0.8, -11.1), (1.6, 1.0, 0.3), (0.85, 0.95, 1.0))
        w.box((0, sy - 3, -12), (3.0, 5.5, 0.2), (1.0, 0.95, 0.6), em=1.0, alpha=0.3)
        for i in range(30):
            w.box((-60 + (i * 29 + t * (6 + i % 5)) % 120, -35 - (i * 13) % 24, -10.3), (0.5, 0.5, 0.3), (0.2, 1.0, 0.9), em=0.8)
        if u > 1.6:
            fa = ease((u - 1.6) / 1.0)
            w.box((lerp(22, 12, fa), -44 + math.sin(t * 2), -10.4), (3.2, 1.8, 0.4), (0.4, 1.0, 0.95), em=1.0)
        if sc < 40:
            w.box((0, 31.2, -9), (8, 3.5, 6), (0.95, 0.95, 0.98)); w.box((0, 33.8, -9), (3, 2, 3), (0.95, 0.5, 0.2))
        return finish(render(w, cam, top=(0.02, 0.04, 0.12), hor=(0.06, 0.12, 0.25), light=(-0.2, 0.5, -0.7), amb=0.55, fog=(0.02, 0.05, 0.12)), 0.5)
    u = t - 27.2
    cp = V3(lerp(-4, 4, u / 2.8), 3.0, -12)
    cam = Camera(cp, V3(0, 4.5, 14), 66)
    ground(w, -300, 300, -60, 300, (0.78, 0.55, 0.28), 40.0)
    w.box((0, 0.05, 40), (150, 0.1, 70), (0.03, 0.1, 0.14))
    for i in range(14):
        w.box((-120 + i * 18, 4 + hsh(1, i) * 7, 100 + hsh(2, i) * 20), (14, 8 + hsh(3, i) * 14, 12), (0.42, 0.42, 0.36))
    planet(w, V3(90, 62, 230), 14, "titan")
    jump = max(0.0, math.sin(clamp((u - 0.9) / 1.6) * math.pi))
    wx = lerp(-5, 5, ease(u / 2.8)); wy = jump * 7
    person(w, (wx, wy, 2), math.pi * 0.95, 91, "walk" if jump < 0.05 else "idle", t, 1.5, shirt=(0.75, 0.88, 1.0), pants=(0.75, 0.88, 1.0), helmet=True, patch=True, pack=True, look_up=0.1)
    fl = math.sin(t * (4 + 6 * jump))
    for sg in (-1, 1):
        w.box((wx + sg * 3.6, wy + 2.6 + 1.0 * fl, 2.5), (5.4, 0.15, 2.4), (0.6, 0.95, 1.0), rot_z(sg * (0.3 + 0.5 * fl)), em=0.3)
    w.box((wx, 0.02, 2), (2.0 * (1 - jump * 0.3), 0.04, 1.6), (0, 0, 0))
    top = (0.2, 0.32, 0.34); hor = (0.95, 0.62, 0.3)
    return finish(render(w, cam, top=top, hor=hor, light=(-0.4, 0.7, 0.4), amb=0.5, fog=hor, fog_range=(70, 360)), 0.45)


# ============================================================ scene 5: building worlds
def oneill_inside(t):
    u = t - 30.0
    w = World()
    Rc = 34.0
    ang0 = u * 0.12
    cp = V3(0, 0, -30 + 8 * u)
    cam = Camera(cp, V3(0, 0, 60 + 8 * u), 80, roll=ang0)
    L0 = cp[2] - 10; L1 = cp[2] + 340
    for s in range(6):
        a0 = s / 6 * 6.283; a1 = (s + 1) / 6 * 6.283
        land = s % 2 == 0
        for zc in np.arange(math.floor(L0 / 20) * 20, L1, 20):
            p = lambda a, z: (math.cos(a) * Rc, math.sin(a) * Rc, z)
            if land:
                f = hsh(s, int(zc / 20))
                c = (0.32, 0.65, 0.28) if f < 0.5 else (0.78, 0.7, 0.3)
                if abs(f - 0.5) < 0.08: c = (0.25, 0.55, 0.95)
                w.quad([p(a0, zc), p(a1, zc), p(a1, zc + 20), p(a0, zc + 20)], c, ds=True)
                # little houses
                if hsh(s, int(zc / 20), 7) < 0.6:
                    am = (a0 + a1) / 2 + (hsh(s, int(zc / 20), 8) - 0.5) * 0.4
                    base = V3(math.cos(am) * Rc, math.sin(am) * Rc, zc + 8)
                    inward = -base / np.linalg.norm(base[:2].tolist() + [0]) if False else V3(-math.cos(am), -math.sin(am), 0)
                    Rm = frame_from_dir(V3(0, 0, 1), up=inward) if False else None
                    c3 = base + inward * 1.6
                    w.box(c3, (3.2, 3.2, 3.2), (0.97, 0.94, 0.88))
                    w.box(c3 + inward * 2.4, (3.8, 1.6, 3.8), (0.85, 0.3, 0.2))
            else:
                w.quad([p(a0, zc), p(a1, zc), p(a1, zc + 20), p(a0, zc + 20)], (0.65, 0.88, 1.0), em=0.7, ds=True)
    w.box(V3(0, 0, cp[2] + 160), (3, 3, 340), (1.0, 0.95, 0.8), em=1.0)
    img = render(w, cam, top=(0.7, 0.9, 1.0), hor=(1.0, 0.95, 0.85), amb=0.7, light=(0.0, -1.0, 0.1), fog=(1.0, 0.95, 0.85), fog_range=(90, 300))
    return img


def oneill_outside(t):
    u = t - 34.4
    w = World()
    cp = V3(30, 26, -170 + 24 * (1 - ease(u / 2.3)))
    cam = Camera(cp, V3(0, 0, 0), 62)
    space(w, cp, 7)
    planet(w, V3(120, 90, 330), 30, "sun")
    n = 12
    sides = np.zeros((n, 3), np.float32)
    cols = np.array([(0.3, 0.55, 0.34) if i % 4 < 2 else (0.7, 0.9, 1.0) for i in range(n)], np.float32)
    cm = cyl_unit(n)
    Rm = frame_from_dir(V3(1, 0, 0)) @ rot_z(t * 0.9)
    Rm = rot_z(math.pi / 2) @ rot_y(t * 0.9)
    colf = np.concatenate([cols, np.tile(np.array([[0.62, 0.66, 0.74]], np.float32), (len(cm) - n, 1))])
    w.mesh(cm, V3(0, 0, 0), (34, 90, 34), colf, rot_z(math.pi / 2) @ rot_y(t * 0.9), 0.0)
    for k in (-1, 0, 1):
        w.box(V3(0, k * 26, 0), (90, 2.5, 2.5), (1.0, 0.9, 0.55), em=0.4)
        w.box(V3(0, k * 30 * 1.0, 0), (36, 0.4, 40), (1.0, 0.85, 0.45)) if False else None
    return render(w, cam, top=(0.02, 0.02, 0.09), hor=(0.06, 0.05, 0.14), light=(-0.5, 0.6, 0.6), amb=0.3)


def dyson(t):
    u = t - 36.7
    w = World()
    cp = V3(0, lerp(70, 105, u / 2.3), -lerp(110, 190, u / 2.3))
    cam = Camera(cp, V3(0, 0, 0), 54)
    space(w, cp, 8)
    planet(w, V3(0, 0, 0), 16, "sun")
    rng = np.random.default_rng(5); N = 1700
    a = 28 + rng.random(N) * 60; inc = (rng.random(N) - 0.5) * 2.4; node = rng.random(N) * 6.28; ph = rng.random(N) * 6.28
    nu = ph + 1.8 / (a / 30) ** 1.5 * t * 0.7
    x = a * np.cos(nu); y = a * np.sin(nu)
    y2 = y * np.cos(inc); z2 = y * np.sin(inc)
    xr = x * np.cos(node) - y2 * np.sin(node); yr = x * np.sin(node) + y2 * np.cos(node)
    pos = np.stack([xr, z2, yr], 1).astype(np.float32)
    k = rng.random(N) < (ease((u - 0.1) / 2.0) * 0.95 + 0.04)
    cols = np.array([1.0, 0.82, 0.38], np.float32)[None] * (0.7 + 0.3 * rng.random((N, 1)))
    w.cubes(pos[k], 1.3, cols[k], em=0.8)
    return render(w, cam, top=(0.04, 0.03, 0.08), hor=(0.1, 0.06, 0.12), light=(0.0, 0.5, 0.0), amb=0.8)


def s5(t):
    if t < 34.4: return finish(oneill_inside(t), 0.5)
    if t < 36.7: return finish(oneill_outside(t), 0.5)
    return finish(dyson(t), 0.7)


# ============================================================ scene 6: the first star
def sails(t):
    u = t - 39.0
    w = World()
    cp = V3(12, 2, -62)
    cam = Camera(cp, V3(16, 0, 0), 62)
    space(w, cp, 9)
    planet(w, V3(-60, 0, 30), 40, "sun")
    w.cyl((-8, 0, 0), 3.5, 5, (0.92, 0.93, 0.98), 8, rot_z(math.pi / 2))
    w.box((-6, 0, 0), (1, 14, 14), (0.7, 0.74, 0.86))
    w.box((-3, 0, 0), (0.5, 4, 4), (0.5, 1.0, 1.0), em=1.0)
    for i in range(7):
        yy = -18 + i * 6; zz = math.sin(i * 1.7) * 8
        k = ease((u - 0.2 - i * 0.08) / 0.5)
        x = 6 + max(0.0, u - 0.4 - i * 0.08) ** 2.1 * 28
        if k <= 0.01: continue
        w.beam(V3(-3, 0, 0), V3(x, yy, zz), 0.28, (0.6, 1.0, 1.0), em=1.0, alpha=0.9)
        w.box(V3(x, yy, zz), (0.4, 5.0, 5.0), (1.0, 0.95, 0.85), em=0.6)
        w.beam(V3(x, yy, zz), V3(x - 4 - 20 * max(0.0, u - 0.4), yy, zz), 0.3, (0.6, 0.8, 1.0), em=1.0, alpha=0.6)
    return render(w, cam, top=(0.05, 0.03, 0.12), hor=(0.16, 0.08, 0.2), light=(-0.5, 0.5, 0.5), amb=0.45)


def starship(t):
    u = t - 42.0
    w = World()
    cp = V3(lerp(0, -12, u / 3), 14, lerp(-100, -76, u / 3))
    cam = Camera(cp, V3(0, 0, 0), 52)
    space(w, cp, 10)
    w.box(V3(0, 0, 0), (10, 9, 100), (0.8, 0.82, 0.9)); w.box(V3(0, 0, 54), (7, 6, 12), (0.92, 0.93, 0.98))
    w.box(V3(0, 0, -54), (14, 12, 10), (0.5, 0.52, 0.65))
    fl = 0.6 + 0.4 * ease(u / 2)
    w.box(V3(0, 0, -62 - 6 * fl), (8, 7, 14 * fl), (0.7, 0.55, 1.0), em=1.0)
    # habitat ring made of boxes
    for k in range(16):
        a = k / 16 * 6.283 + t * 0.3
        c = V3(math.cos(a) * 24, math.sin(a) * 24, 4)
        w.box(c, (5, 5, 8), (0.88, 0.9, 0.97), rot_z(a))
        wc = c + V3(math.cos(a), math.sin(a), 0) * 2.6
        garden = k % 3 == 0
        w.box(wc, (3, 3, 4), (0.3, 0.9, 0.45) if garden else (1.0, 0.85, 0.5), rot_z(a), em=0.9)
    for sg in (-1, 1):
        w.box(V3(0, sg * 12, 4), (1.2, 24, 1.2), (0.7, 0.74, 0.86))
        w.box(V3(sg * 12, 0, 4), (24, 1.2, 1.2), (0.7, 0.74, 0.86))
    for i in range(3):
        w.cyl(V3(0, 0, 10 + 8 * i - 30), 4.5, 6, (0.93, 0.94, 0.98), 8, rot_x(math.pi / 2))
    star_p = V3(-8, 6.0, 50)
    w.box(star_p, (2.6, 2.6, 0.5), (1.0, 0.56, 0.14), em=1.0)
    return render(w, cam, top=(0.04, 0.02, 0.1), hor=(0.12, 0.06, 0.2), light=(-0.5, 0.6, 0.4), amb=0.38)


def window_room(t):
    u = t - 45.0
    w = World()
    cp = V3(0, 3.0, -1.0 + 0.3 * u)
    cam = Camera(cp, V3(0.4, 4.6, 8), 68)
    starbox(w, V3(0, 3, 0), 11, 240, 500, 1.0)
    sz = lerp(3, 7, ease(u / 3))
    sz *= 6
    SP = V3(2, 125, 330)
    w.box(SP, (sz, sz, sz), (1.0, 0.95, 0.8), em=1.0)
    w.box(SP - V3(0, 0, 1), (sz * 2.6, sz * 0.22, 1), (1.0, 0.85, 0.5), em=0.8)
    w.box(SP - V3(0, 0, 1), (sz * 0.22, sz * 2.6, 1), (1.0, 0.85, 0.5), em=0.8)
    # wall with window cut-out (four panels)
    wall = (0.34, 0.24, 0.34)
    w.box(V3(0, 7.5, 12), (50, 15, 1), wall) if False else None
    w.box(V3(-16, 8, 12), (20, 18, 1), wall); w.box(V3(16, 8, 12), (20, 18, 1), wall)
    w.box(V3(0, 1, 12), (14, 6, 1), wall); w.box(V3(0, 15, 12), (14, 5, 1), wall)
    w.box(V3(0, 4.2, 11.6), (14, 0.7, 1.6), (0.3, 0.2, 0.26))
    w.box(V3(0, -0.3, 4), (50, 0.6, 40), (0.2, 0.13, 0.17))
    person(w, (-2.4, 0, 3.6), 0.35, 95, "idle", t, 1.15, shirt=(0.55, 0.52, 0.7), pants=(0.3, 0.3, 0.4), skin=(0.88, 0.66, 0.52), hair=(0.92, 0.92, 0.96), look_up=0.1, patch=True,
           arm_pose=0.9)
    person(w, (0.8, 0, 5.4), 0.0, 96, "idle", t, 0.85, shirt=SUIT, pants=(0.35, 0.35, 0.5), skin=(0.9, 0.68, 0.56), hair=(0.08, 0.05, 0.04), look_up=0.5, patch=True)
    return render(w, cam, top=(0.04, 0.03, 0.09), hor=(0.1, 0.06, 0.14), light=(0.5, 0.6, 0.4), amb=0.5)


def s6(t):
    if t < 42: return finish(sails(t), 0.6)
    if t < 45: return finish(starship(t), 0.55)
    return finish(window_room(t), 0.6)


# ============================================================ scene 7: the galaxy
def make_gal(n, seed, arms=2, wind=3.0):
    r = np.random.default_rng(seed)
    rr = r.random(n) ** 0.65
    th = r.integers(0, arms, n) * 2 * math.pi / arms + wind * np.log1p(rr * 6) + r.normal(0, 0.2, n) * (1 - 0.55 * rr)
    x = rr * np.cos(th); z = rr * np.sin(th)
    y = r.normal(0, 0.03, n) * (1.3 - rr)
    return np.stack([x, y, z], 1).astype(np.float32), rr.astype(np.float32), r.random(n).astype(np.float32)


GAL = make_gal(2600, 21)
GAL_B = make_gal(900, 33, 3, 2.4)

CULT = [
    dict(sky=((0.15, 0.45, 0.55), (0.95, 0.65, 0.6)), skin=(0.70, 0.50, 0.38), hair=(0.08, 0.08, 0.14), outfit=(0.12, 0.45, 0.55), hat=(0.95, 0.75, 0.3), arch="spires"),
    dict(sky=((0.28, 0.2, 0.55), (0.8, 0.55, 0.8)), skin=(0.94, 0.78, 0.68), hair=(0.55, 0.2, 0.1), outfit=(0.55, 0.22, 0.5), hat=(0.95, 0.92, 0.8), arch="islands"),
    dict(sky=((0.85, 0.4, 0.15), (1.0, 0.8, 0.45)), skin=(0.45, 0.3, 0.24), hair=(0.05, 0.05, 0.06), outfit=(0.22, 0.24, 0.3), hat=(0.2, 0.9, 0.95), arch="blocks"),
    dict(sky=((0.02, 0.05, 0.22), (0.2, 0.3, 0.6)), skin=(0.6, 0.8, 0.72), hair=(0.15, 0.35, 0.35), outfit=(0.75, 0.78, 0.88), hat=(1.0, 0.8, 0.4), arch="ring"),
]


def culture(t, i):
    c = CULT[i]; u = t - (49.6 + 1.6 * i)
    w = World()
    ang = 0.5 * u + i
    cp = V3(math.sin(ang * 0.4) * 2.4, 2.1, 6.8)
    cam = Camera(cp, V3(0, 1.8, 0), 58)
    ground(w, -200, 200, -200, 200, mixc(c["sky"][1], (0.3, 0.3, 0.3), 0.6), 40.0)
    for k in range(10):
        a = k / 10 * 6.283
        r = 26 + hsh(i, k) * 14
        h = 8 + hsh(i, k, 1) * 22
        x, z = math.cos(a) * r, math.sin(a) * r
        if c["arch"] == "islands":
            w.box((x, 6 + hsh(i, k, 2) * 12 + math.sin(t + k), z), (12, 2, 12), (0.45, 0.75, 0.4)); w.box((x, 4 + hsh(i, k, 2) * 12 + math.sin(t + k), z), (7, 3, 7), (0.5, 0.35, 0.3))
        elif c["arch"] == "ring":
            w.box((x, 14 + 6 * math.sin(a), z), (4, 4, 4), (0.8, 0.85, 1.0), em=0.8)
        else:
            w.box((x, h / 2, z), (6, h, 6), (0.8, 0.95, 1.0) if c["arch"] == "spires" else (0.22, 0.2, 0.28), em=0.0)
            if c["arch"] == "blocks":
                w.box((x, h * 0.6, z - 3.05), (3.5, 1, 0.2), (1.0, 0.85, 0.4), em=1.0)
    w.box((-6, 5, 8), (3.5, 3.5, 0.3), (1.0, 0.6, 0.2), em=0.4)
    person(w, (0, 0, 0), math.pi * 0.0, 120 + i, "idle" if i % 2 else "cheer", t, 1.0, shirt=c["outfit"], pants=(0.2, 0.2, 0.28), skin=c["skin"], hair=c["hair"], hat=c["hat"],
           patch=True)
    top, hor = c["sky"]
    return render(w, cam, top=top, hor=hor, light=(-0.4, 0.8, 0.4), amb=0.5, fog=hor, fog_range=(60, 220))


def galaxy_view(t, u, cx_ofs=0.0):
    w = World()
    R_ = lerp(36, 52, ease(u / 8.0))
    ang = 0.2 + u * 0.05
    ca, sa = math.cos(ang), math.sin(ang)
    P = GAL[0] * R_
    X = P[:, 0] * ca - P[:, 2] * sa; Z = P[:, 0] * sa + P[:, 2] * ca
    pos = np.stack([X, P[:, 1] * R_, Z], 1)
    origin = np.array([0.52, 0.12]) * R_
    ox = origin[0] * ca - origin[1] * sa; oz = origin[0] * sa + origin[1] * ca
    d = np.hypot(X - ox, Z - oz)
    wave = ease((u - 0.4) / 8.0) * 1.9 * R_
    inn = d < wave; front = np.abs(d - wave) < 0.05 * R_
    rr = GAL[1]; rnd = GAL[2]
    base = np.array([0.55, 0.45, 1.0], np.float32)[None] * (0.5 + 0.5 * rnd[:, None])
    core = np.array([1.0, 0.92, 0.75], np.float32)[None]
    m = np.clip(1 - rr * 1.7, 0, 1)[:, None]
    cols = base * (1 - m) + core * m
    cols = np.where(inn[:, None], np.array([1.0, 0.78, 0.3], np.float32)[None] * (0.7 + 0.5 * rnd[:, None]), cols)
    cols = np.where(front[:, None], np.array([1.0, 1.0, 0.95], np.float32)[None], cols)
    sz = 0.5 + 1.2 * (1 - rr) + 1.0 * inn
    w.cubes(pos, sz.astype(np.float32), cols, em=1.0)
    w.cubes(np.array([[ox, 0, oz]], np.float32), 3.0, np.array([[1, 1, 1]], np.float32), em=1.0)
    cp = V3(0, 150, -52)
    cam = Camera(cp, V3(0, 0, 0), 60)
    return render(w, cam, top=(0.04, 0.02, 0.12), hor=(0.08, 0.04, 0.18), amb=1.0)


def s7(t):
    u = t - 48.0
    cut = None
    for i in range(4):
        a = 49.6 + 1.6 * i
        if a <= t < a + 1.45: cut = i
    if cut is not None: return finish(culture(t, cut), 0.4)
    return finish(galaxy_view(t, u), 0.8)


# ============================================================ scene 8: the limit
FAR_N = 130
FAR_P = np.array([[hsh(40, i, 1) - 0.5, (hsh(40, i, 2) - 0.5) * 0.5, hsh(40, i, 3) - 0.5] for i in range(FAR_N)], np.float32)
FAR_P = FAR_P / (np.linalg.norm(FAR_P, axis=1, keepdims=True) + 1e-6) * (0.45 + np.array([hsh(41, i) for i in range(FAR_N)])[:, None] ** 0.8 * 1.9)


def s8(t):
    u = t - 57.0
    w = World()
    zoom = lerp(2.4, 0.5, ease((u - 0.2) / 5.5))
    recede = ease((u - 3.5) / 5.0)
    cp = V3(0, 260, -90)
    cam = Camera(cp, V3(0, 0, 0), 64)
    starbox(w, V3(0, 0, 0), 12, 160, 900, 0.6)
    Rg = 40 * zoom
    ang = 0.45
    ca, sa = math.cos(ang), math.sin(ang)
    P = GAL[0] * Rg
    pos = np.stack([P[:, 0] * ca - P[:, 2] * sa, P[:, 1] * Rg, P[:, 0] * sa + P[:, 2] * ca], 1)
    rr = GAL[1]; rnd = GAL[2]
    cols = np.array([1.0, 0.78, 0.35], np.float32)[None] * (0.55 + 0.5 * rnd[:, None]) * (1 - 0.3 * rr[:, None])
    w.cubes(pos, (0.5 + 1.1 * (1 - rr)).astype(np.float32) * max(0.7, zoom), cols, em=1.0)
    # Andromeda
    A = GAL_B[0] * 36 * zoom
    off = np.array([62, 6, -30], np.float32) * zoom
    ap = np.stack([A[:, 0] * 0.9 - A[:, 2] * 0.4, A[:, 1] * 36 * zoom + A[:, 0] * 0.3, A[:, 0] * 0.4 + A[:, 2] * 0.9], 1) + off
    w.cubes(ap, 0.7, np.array([0.7, 0.7, 1.0], np.float32)[None] * (0.5 + 0.5 * GAL_B[2][:, None]), em=1.0)
    # distant galaxies drift away beyond the reachable horizon
    horizon = 0.95
    dist = np.linalg.norm(FAR_P, axis=1)
    outside = dist > horizon
    k = 1 + np.where(outside, recede * (0.9 + 1.4 * np.array([hsh(42, i) for i in range(FAR_N)])), 0.0)
    pos2 = FAR_P * 100 * zoom * k[:, None]
    br = np.where(outside, np.clip(1 - recede * 1.15, 0, 1), 1.0)
    warm = np.where(outside, recede, 0.0)[:, None]
    col = (np.array([0.8, 0.85, 1.0], np.float32)[None] * (1 - warm) + np.array([1.0, 0.25, 0.1], np.float32)[None] * warm) * br[:, None]
    keep = br > 0.03
    w.cubes(pos2[keep], (1.4 * max(0.7, zoom)), col[keep], em=1.0)
    # horizon ring
    if u > 2.2:
        a_ = ease((u - 2.2) / 1.2)
        for i in range(48):
            if i % 2: continue
            th = i / 48 * 6.283
            w.box(V3(math.cos(th), 0, math.sin(th)) * horizon * 100 * zoom, (2.0, 0.6, 2.0), (1.0, 0.8, 0.4) * np.array([a_] * 3, np.float32), em=1.0)
    return finish(render(w, cam, top=(0.03, 0.01, 0.09), hor=(0.09, 0.03, 0.16), amb=1.0), 0.8)


# ============================================================ scene 9
def s9(t):
    u = t - 66.0
    w = World()
    cpos = V3(-2.5, 2.0, 9.0 + 0.2 * u)
    head = V3(0, 1.68, 0)
    cam = Camera(cpos, V3(30, 36, -120) + V3(0, 0, 0), 62)
    space(w, cpos, 1)
    moon_ground(w)
    planet(w, EARTH_POS, 46, "earth", rot=t * 0.06)
    step = ease((u - 0.3) / 1.4)
    walk = math.sin(step * math.pi) * 0.8 if 0.3 < u < 1.7 else 0.0
    pos = V3(0, 0, -2.0 * step)
    astro(w, pos, math.pi * 0.86 + math.pi * 0.14 * 0, t, 1, anim="idle", look_up=0.0) if walk == 0 else person(
        w, pos, math.pi, 1, "walk", u * 0.9, 1.0, shirt=SUIT, pants=SUIT, helmet=True, patch=True, pack=True)
    # patch glow
    gl = 0.5 + 0.5 * math.sin(u * 5)
    w.box(pos + V3(0, 1.45, -0.18), (0.36 + 0.2 * gl, 0.36 + 0.2 * gl, 0.05), (1.0, 0.56, 0.14), em=1.0, alpha=0.7)
    return finish(render(w, cam, light=(-0.5, 0.6, 0.7), amb=0.36))


SCENES = [(0, 4, s1), (4, 11, s2), (11, 21, s3), (21, 30, s4), (30, 39, s5), (39, 48, s6), (48, 57, s7), (57, 66, s8), (66, 70, s9)]


def render3d(t):
    for a, b, fn in SCENES:
        if a <= t < b: return fn(t)
    return SCENES[-1][2](69.99)
