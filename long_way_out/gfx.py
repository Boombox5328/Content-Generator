"""Soft 'clay' drawing primitives: signed-distance shapes get pillow-shaded with a light + rim light."""
import math
import types
import numpy as np
from PIL import Image, ImageDraw
from spec import W, H, smooth

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def lerp(a, b, f): return a + (b - a) * f
def col(r, g, b): return np.array([r, g, b], np.float32)
def clamp01(x): return min(1.0, max(0.0, x))
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_io(x): return smooth(x)
def mix(a, b, f): return np.asarray(a, np.float32) * (1 - f) + np.asarray(b, np.float32) * f


def _unit(v):
    v = np.asarray(v, np.float32); return v / np.linalg.norm(v)


ST = types.SimpleNamespace(light=_unit((-0.45, -0.55, 0.70)), amb=0.46, rim_dir=(0.8, -0.3),
                           rim_col=col(0.5, 0.7, 1.0), rim_amt=0.55)


def set_light(light=(-0.45, -0.55, 0.70), amb=0.46, rim_dir=(0.8, -0.3), rim_col=(0.5, 0.7, 1.0), rim_amt=0.55):
    ST.light = _unit(light); ST.amb = amb; ST.rim_dir = rim_dir
    ST.rim_col = np.asarray(rim_col, np.float32); ST.rim_amt = rim_amt


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


# ---------------- core painter ----------------
def bbox(x0, y0, x1, y1):
    xa, xb = max(0, int(math.floor(x0))), min(W, int(math.ceil(x1)))
    ya, yb = max(0, int(math.floor(y0))), min(H, int(math.ceil(y1)))
    if xb <= xa or yb <= ya: return None
    return xa, xb, ya, yb


def paint(cv, bb, d, color, bevel=6.0, a=1.0, flat=False, rim=True, gloss=0.0, light=None, amb=None, mask=None):
    xa, xb, ya, yb = bb
    if d.shape[0] < 3 or d.shape[1] < 3: return
    cov = np.clip(0.5 - d, 0.0, 1.0)
    if mask is not None: cov = cov * mask
    if a != 1.0: cov = cov * a
    if not cov.any(): return
    c = np.asarray(color, np.float32)
    if flat:
        col_ = c
    else:
        gy, gx = np.gradient(d)
        t = np.clip(-d / max(bevel, 1e-3), 0, 1)
        k = 1.0 - t
        nx = gx * k; ny = gy * k; nz = 0.30 + 0.70 * t
        inv = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz)
        L = ST.light if light is None else _unit(light)
        am = ST.amb if amb is None else amb
        dif = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) * inv, 0, 1)
        shade = am + (1.12 - am) * dif
        col_ = c * shade[..., None]
        if rim and ST.rim_amt > 0:
            rd = ST.rim_dir
            r = np.clip((nx * rd[0] + ny * rd[1]) * inv * 1.6, 0, 1) * (1 - nz * inv) ** 0.7
            col_ = col_ + (r ** 1.2 * ST.rim_amt)[..., None] * ST.rim_col
        if gloss > 0:
            Hv = _unit(L + np.array([0, 0, 1], np.float32))
            sp = np.clip((nx * Hv[0] + ny * Hv[1] + nz * Hv[2]) * inv, 0, 1) ** 36
            col_ = col_ + (sp * gloss)[..., None]
    sub = cv[ya:yb, xa:xb]
    sub += (col_ - sub) * cov[..., None]


def circ(cv, cx, cy, r, color, **kw):
    bb = bbox(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    d = np.sqrt((XX[ya:yb, xa:xb] - cx) ** 2 + (YY[ya:yb, xa:xb] - cy) ** 2) - r
    kw.setdefault("bevel", r * 0.65)
    paint(cv, bb, d, color, **kw)


def ell(cv, cx, cy, rx, ry, color, ang=0.0, clip_y=None, **kw):
    R = max(rx, ry)
    bb = bbox(cx - R - 2, cy - R - 2, cx + R + 2, cy + R + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb] - cx; Y = YY[ya:yb, xa:xb] - cy
    if ang:
        c, s = math.cos(ang), math.sin(ang); X, Y = X * c + Y * s, -X * s + Y * c
    k0 = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
    k1 = np.sqrt((X / (rx * rx)) ** 2 + (Y / (ry * ry)) ** 2) + 1e-6
    d = k0 * (k0 - 1) / k1
    kw.setdefault("bevel", min(rx, ry) * 0.65)
    if clip_y is not None:
        kw["mask"] = np.clip(clip_y - YY[ya:yb, xa:xb] + 0.5, 0, 1)
    paint(cv, bb, d, color, **kw)


def ring(cv, cx, cy, rx, ry, w, color, a=1.0, ang=0.0, arc=None):
    """Elliptical outline of width w."""
    R = max(rx, ry) + w
    bb = bbox(cx - R - 2, cy - R - 2, cx + R + 2, cy + R + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb] - cx; Y = YY[ya:yb, xa:xb] - cy
    if ang:
        c, s = math.cos(ang), math.sin(ang); X, Y = X * c + Y * s, -X * s + Y * c
    k0 = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
    k1 = np.sqrt((X / (rx * rx)) ** 2 + (Y / (ry * ry)) ** 2) + 1e-6
    d = k0 * (k0 - 1) / k1
    cov = np.clip(w / 2 - np.abs(d) + 0.5, 0, 1) * a
    if arc is not None:
        cov = cov * np.clip(arc(np.arctan2(Y, X)), 0, 1)
    sub = cv[ya:yb, xa:xb]
    sub += (np.asarray(color, np.float32) - sub) * cov[..., None]


def rrect(cv, cx, cy, hw, hh, rad, color, ang=0.0, **kw):
    R = math.hypot(hw, hh)
    bb = bbox(cx - R - 2, cy - R - 2, cx + R + 2, cy + R + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb] - cx; Y = YY[ya:yb, xa:xb] - cy
    if ang:
        c, s = math.cos(ang), math.sin(ang); X, Y = X * c + Y * s, -X * s + Y * c
    rad = min(rad, hw, hh)
    qx = np.abs(X) - (hw - rad); qy = np.abs(Y) - (hh - rad)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad
    kw.setdefault("bevel", min(hw, hh) * 0.7)
    paint(cv, bb, d, color, **kw)


def capsule(cv, x0, y0, x1, y1, r0, color, r1=None, **kw):
    r1 = r0 if r1 is None else r1
    R = max(r0, r1) + 2
    bb = bbox(min(x0, x1) - R, min(y0, y1) - R, max(x0, x1) + R, max(y0, y1) + R)
    if not bb: return
    xa, xb, ya, yb = bb
    px = XX[ya:yb, xa:xb] - x0; py = YY[ya:yb, xa:xb] - y0
    bx, by = x1 - x0, y1 - y0
    h = np.clip((px * bx + py * by) / (bx * bx + by * by + 1e-9), 0, 1)
    d = np.hypot(px - bx * h, py - by * h) - (r0 + (r1 - r0) * h)
    kw.setdefault("bevel", min(r0, r1) * 0.9)
    paint(cv, bb, d, color, **kw)


def star_sd(X, Y, r, rf=0.5):
    """iq's 5-point star SDF; X,Y relative to the centre, y down."""
    k1x, k1y = 0.809016994375, -0.587785252292
    k2x, k2y = -k1x, k1y
    px = np.abs(X); py = -Y
    dk = np.maximum(k1x * px + k1y * py, 0.0) * 2.0
    px = px - dk * k1x; py = py - dk * k1y
    dk = np.maximum(k2x * px + k2y * py, 0.0) * 2.0
    px = px - dk * k2x; py = py - dk * k2y
    px = np.abs(px); py = py - r
    bax, bay = rf * (-k1y) - 0.0, rf * k1x - 1.0
    h = np.clip((px * bax + py * bay) / (bax * bax + bay * bay), 0, r)
    return np.hypot(px - bax * h, py - bay * h) * np.sign(py * bax - px * bay)


def star(cv, cx, cy, r, color, ang=0.0, rf=0.5, **kw):
    bb = bbox(cx - r * 1.3, cy - r * 1.3, cx + r * 1.3, cy + r * 1.3)
    if not bb: return
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb] - cx; Y = YY[ya:yb, xa:xb] - cy
    if ang:
        c, s = math.cos(ang), math.sin(ang); X, Y = X * c + Y * s, -X * s + Y * c
    d = star_sd(X, Y, r, rf)
    kw.setdefault("bevel", r * 0.35)
    paint(cv, bb, d, color, **kw)


def poly(cv, pts, c0, c1=None, a=1.0, ss=3):
    """Anti-aliased filled polygon; optional vertical gradient c0 (top) -> c1 (bottom)."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bb = bbox(min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    m = Image.new("L", ((xb - xa) * ss, (yb - ya) * ss), 0)
    ImageDraw.Draw(m).polygon([((x - xa) * ss, (y - ya) * ss) for x, y in pts], fill=255)
    cov = np.asarray(m.resize((xb - xa, yb - ya), Image.BOX), np.float32) / 255.0 * a
    c0 = np.asarray(c0, np.float32)
    if c1 is None: cc = c0
    else:
        f = np.linspace(0, 1, yb - ya, dtype=np.float32)[:, None, None]
        cc = c0 * (1 - f) + np.asarray(c1, np.float32) * f
    sub = cv[ya:yb, xa:xb]
    sub += (cc - sub) * cov[..., None]


def line(cv, x0, y0, x1, y1, w, color, a=1.0):
    """Flat anti-aliased line."""
    R = w + 2
    bb = bbox(min(x0, x1) - R, min(y0, y1) - R, max(x0, x1) + R, max(y0, y1) + R)
    if not bb: return
    xa, xb, ya, yb = bb
    px = XX[ya:yb, xa:xb] - x0; py = YY[ya:yb, xa:xb] - y0
    bx, by = x1 - x0, y1 - y0
    h = np.clip((px * bx + py * by) / (bx * bx + by * by + 1e-9), 0, 1)
    d = np.hypot(px - bx * h, py - by * h) - w / 2
    cov = np.clip(0.5 - d, 0, 1) * a
    sub = cv[ya:yb, xa:xb]
    sub += (np.asarray(color, np.float32) - sub) * cov[..., None]


def glow(cv, cx, cy, r, color, amt=1.0, power=2.0, ry=None):
    ry = r if ry is None else ry
    bb = bbox(cx - r, cy - ry, cx + r, cy + ry)
    if not bb: return
    xa, xb, ya, yb = bb
    d = np.sqrt(((XX[ya:yb, xa:xb] - cx) / r) ** 2 + ((YY[ya:yb, xa:xb] - cy) / ry) ** 2)
    g = np.clip(1 - d, 0, 1) ** power * amt
    cv[ya:yb, xa:xb] += g[..., None] * np.asarray(color, np.float32)


def beam(cv, x0, y0, x1, y1, w0, w1, color, amt=1.0, power=1.5):
    """Soft additive light beam (tapering) from (x0,y0) to (x1,y1)."""
    R = max(w0, w1) + 2
    bb = bbox(min(x0, x1) - R, min(y0, y1) - R, max(x0, x1) + R, max(y0, y1) + R)
    if not bb: return
    xa, xb, ya, yb = bb
    px = XX[ya:yb, xa:xb] - x0; py = YY[ya:yb, xa:xb] - y0
    bx, by = x1 - x0, y1 - y0
    L2 = bx * bx + by * by + 1e-9
    h = np.clip((px * bx + py * by) / L2, 0, 1)
    dd = np.hypot(px - bx * h, py - by * h)
    w = w0 + (w1 - w0) * h
    g = np.clip(1 - dd / w, 0, 1) ** power * (1 - 0.35 * h) * amt
    cv[ya:yb, xa:xb] += g[..., None] * np.asarray(color, np.float32)


def vgrad(cv, y0, y1, c0, c1, x0=0, x1=W):
    y0 = max(0, int(y0)); y1 = min(H, int(y1))
    if y1 <= y0: return
    f = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    cv[y0:y1, x0:x1] = np.asarray(c0, np.float32) * (1 - f) + np.asarray(c1, np.float32) * f


def fill_bg(cv, c_top, c_bot, y0=0, y1=H):
    vgrad(cv, y0, y1, c_top, c_bot)


# ---------------- stars ----------------
_sr = np.random.default_rng(42)
N_ST = 420
ST_X = _sr.random(N_ST) * W; ST_Y = _sr.random(N_ST) * H
ST_P = _sr.random(N_ST) * 6.28; ST_R = 0.5 + _sr.random(N_ST) * 2.0; ST_K = _sr.random(N_ST)


def starfield(cv, t, off=(0, 0), n=300, bright=1.0, tint=(0.85, 0.9, 1.0), ymax=H, depth=1.0, warm=0.12):
    n = min(n, N_ST)
    x = (ST_X[:n] + off[0] * depth * (0.4 + ST_K[:n])) % W
    y = (ST_Y[:n] + off[1] * depth * (0.4 + ST_K[:n])) % H
    ok = y < ymax
    tw = 0.55 + 0.45 * np.sin(t * ST_R[:n] + ST_P[:n])
    b = (0.25 + 0.75 * ST_K[:n]) * tw * bright
    tn = np.asarray(tint, np.float32)
    c = tn[None, :] * b[:, None]
    wm = ST_K[:n] > (1 - warm)
    c[wm] = np.array([1.0, 0.85, 0.6], np.float32)[None, :] * b[wm, None]
    px = x.astype(int); py = y.astype(int)
    px = np.clip(px, 0, W - 1); py = np.clip(py, 0, H - 1)
    for dx, dy, wgt in ((0, 0, 1.0), (1, 0, 0.35), (0, 1, 0.35)):
        qx = np.clip(px + dx, 0, W - 1); qy = np.clip(py + dy, 0, H - 1)
        big = ST_K[:n] > 0.55
        m = ok & (big | (wgt == 1.0))
        cv[qy[m], qx[m]] = np.maximum(cv[qy[m], qx[m]], c[m] * wgt)
    bigs = np.where(ok & (ST_K[:n] > 0.965))[0]
    for i in bigs:
        glow(cv, x[i], y[i], 6 + 4 * tw[i], c[i] * 0.5, 1.0, 2.2)
        line(cv, x[i] - 5, y[i], x[i] + 5, y[i], 1, c[i], 0.35); line(cv, x[i], y[i] - 5, x[i], y[i] + 5, 1, c[i], 0.35)


# ---------------- spheres / planets ----------------
def sphere_arrays(X, Y, texfun, light=(-0.55, -0.45, 0.70), amb=0.10, rot=0.0, atmo=None, spec=0.0):
    """X,Y: normalized coords (-1..1). Returns (rgb, edge_cov)."""
    d2 = X * X + Y * Y
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    L = _unit(light)
    lam = np.clip(X * L[0] + Y * L[1] + nz * L[2], 0, 1)
    lon = np.arctan2(X, nz) + rot
    lat = np.arcsin(np.clip(Y, -1, 1))
    c = texfun(lon, lat)
    shade = amb + (1 - amb) * lam ** 0.85
    c = c * shade[..., None]
    if atmo is not None:
        rimv = np.clip((d2 - 0.55) / 0.45, 0, 1) ** 2.2 * (0.25 + 0.75 * np.clip(lam * 1.6, 0, 1))
        c = c + rimv[..., None] * np.asarray(atmo, np.float32)
    if spec > 0:
        Hv = _unit(L + np.array([0, 0, 1], np.float32))
        sp = np.clip(X * Hv[0] + Y * Hv[1] + nz * Hv[2], 0, 1) ** 40
        c = c + (sp * spec)[..., None]
    return c, np.sqrt(d2)


def sphere(cv, cx, cy, r, texfun, light=(-0.55, -0.45, 0.70), amb=0.10, rot=0.0, atmo=None, spec=0.0, halo=None):
    if halo is not None:
        glow(cv, cx, cy, r * 1.45, halo, 0.55, 2.4)
    bb = bbox(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    X = (XX[ya:yb, xa:xb] - cx) / r; Y = (YY[ya:yb, xa:xb] - cy) / r
    c, rr = sphere_arrays(X, Y, texfun, light, amb, rot, atmo, spec)
    cov = np.clip((1 - rr) * r + 0.5, 0, 1)
    sub = cv[ya:yb, xa:xb]
    sub += (c - sub) * cov[..., None]


def earth_tex(t=0.0):
    def f(lon, lat):
        u = (lon / (2 * math.pi)) % 1.0; v = lat / math.pi + 0.5
        land = tex(NZ_A, u, v)
        cl = tex(NZ_B, u * 2 + t * 0.004, v * 1.3)
        ocean = np.stack([0.05 + 0.04 * np.cos(lat), 0.22 + 0.14 * np.cos(lat), 0.62 + 0.14 * np.cos(lat)], -1)
        dry = np.clip((0.55 - np.abs(lat) / 1.57) * 1.2, 0, 1)
        green = np.stack([0.20 + 0.28 * dry, 0.52 - 0.05 * dry, 0.20 + 0 * dry], -1)
        m = np.clip((land - 0.505) * 22, 0, 1)[..., None]
        c = ocean * (1 - m) + green * m
        ice = np.clip((np.abs(lat) - 1.25) * 6, 0, 1)[..., None]
        c = c * (1 - ice) + np.array([0.92, 0.95, 1.0], np.float32) * ice
        cm = np.clip((cl - 0.52) * 4.5, 0, 0.85)[..., None]
        return c * (1 - cm) + np.array([0.97, 0.98, 1.0], np.float32) * cm
    return f


def mars_tex(t=0.0):
    def f(lon, lat):
        u = (lon / (2 * math.pi)) % 1.0; v = lat / math.pi + 0.5
        n = tex(NZ_A, u, v); n2 = tex(NZ_C, u * 2, v * 2)
        base = np.stack([0.80 + 0.12 * n, 0.38 + 0.12 * n, 0.20 + 0.06 * n], -1)
        dark = np.clip((n2 - 0.55) * 3, 0, 0.7)[..., None]
        c = base * (1 - dark) + np.array([0.38, 0.18, 0.14], np.float32) * dark
        ice = np.clip((np.abs(lat) - 1.38) * 8, 0, 1)[..., None]
        return c * (1 - ice) + np.array([0.96, 0.92, 0.9], np.float32) * ice
    return f


def jupiter_tex(t=0.0):
    def f(lon, lat):
        u = (lon / (2 * math.pi)) % 1.0
        n = tex(NZ_A, u * 2 + t * 0.003, lat / 3.0 + 0.5)
        band = np.sin(lat * 9 + n * 3.0) * 0.5 + 0.5
        a = np.array([0.93, 0.80, 0.62], np.float32); b = np.array([0.66, 0.40, 0.26], np.float32)
        return a * (1 - band[..., None]) + b * band[..., None]
    return f


def flat_tex(c):
    c = np.asarray(c, np.float32)
    return lambda lon, lat: np.broadcast_to(c, lon.shape + (3,)).copy()


def rock_tex(base, seed_off=0.0):
    base = np.asarray(base, np.float32)
    def f(lon, lat):
        u = (lon / (2 * math.pi)) % 1.0; v = lat / math.pi + 0.5
        n = tex(NZ_A, u * 2 + seed_off, v * 2); n2 = tex(NZ_C, u * 5, v * 5)
        k = 0.75 + 0.5 * n + 0.18 * (n2 - 0.5)
        return base * k[..., None]
    return f


# ---------------- misc ----------------
def haze(cv, y0, y1, color, amt=0.5, t=0.0, scale=1.0):
    """Horizontal band of drifting noise haze."""
    y0 = max(0, int(y0)); y1 = min(H, int(y1))
    if y1 <= y0: return
    Y = YY[y0:y1]; X = XX[y0:y1]
    n = tex(NZ_B, X / 380.0 * scale + t * 0.01, Y / 380.0 * scale)
    fall = np.sin(np.linspace(0, math.pi, y1 - y0, dtype=np.float32))[:, None]
    g = np.clip((n - 0.3) * 1.6, 0, 1) * fall * amt
    cv[y0:y1] += g[..., None] * np.asarray(color, np.float32)


def vignette(cv, amt=0.35):
    cx, cy = W / 2, H / 2
    d = np.sqrt(((XX - cx) / (W * 0.75)) ** 2 + ((YY - cy) / (H * 0.62)) ** 2)
    cv *= (1 - amt * np.clip(d - 0.45, 0, 1) ** 1.6)[..., None]


def bloom(cv, thr=0.72, amt=0.5):
    br = np.clip(cv - thr, 0, 1)
    img = Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8))
    from PIL import ImageFilter
    small = img.resize((W // 4, H // 4), Image.BILINEAR)
    b1 = small.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    b2 = small.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    add = (np.asarray(b1, np.float32) * 0.6 + np.asarray(b2, np.float32) * 0.7) / 255.0
    cv += add * amt * 2.0
