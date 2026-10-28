"""Ava and her descendants: chunky clay-style astronauts with readable faces and the orange-star patch."""
import math
import numpy as np
from gfx import *

ORANGE = col(1.0, 0.56, 0.14)
SUIT = col(0.93, 0.91, 0.88)
TRIM = col(0.52, 0.58, 0.68)
SKIN = col(0.95, 0.72, 0.58)


def soft_ell(X, Y, cx, cy, rx, ry):
    k = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
    return np.clip((1 - k) * min(rx, ry) + 0.5, 0, 1)


def blend(dst, cov, c):
    dst += (np.asarray(c, np.float32) - dst) * cov[..., None]


def face_layer(loc, X, Y, cx, cy, r, expr="smile", blink=0.0, look=(0.0, 0.0), brow=0.0):
    """Eyes, cheeks, mouth drawn in-place onto loc (h,w,3) with coords X,Y."""
    blend(loc, soft_ell(X, Y, cx - 0.52 * r, cy + 0.26 * r, 0.17 * r, 0.11 * r) * 0.38, (1.0, 0.5, 0.45))
    blend(loc, soft_ell(X, Y, cx + 0.52 * r, cy + 0.26 * r, 0.17 * r, 0.11 * r) * 0.38, (1.0, 0.5, 0.45))
    big = 1.22 if expr in ("awe", "wow") else 1.0
    ery = 0.15 * r * big * max(0.08, 1 - 0.92 * blink)
    erx = 0.105 * r * (1.05 if big > 1 else 1.0)
    for sgn in (-1, 1):
        ex = cx + sgn * 0.34 * r; ey = cy - 0.02 * r
        blend(loc, soft_ell(X, Y, ex, ey, erx, ery), (0.09, 0.06, 0.08))
        hx = ex - 0.035 * r + look[0] * 0.035 * r; hy = ey - 0.05 * r + look[1] * 0.03 * r
        blend(loc, soft_ell(X, Y, hx, hy, 0.042 * r, 0.05 * r) * (1 - 0.8 * blink), (1, 1, 1))
        if brow != 0:
            by = ey - 0.26 * r - brow * 0.05 * r
            m = np.clip((0.035 * r - np.abs(Y - by - sgn * (X - ex) * 0.0)) * 3, 0, 1) * np.clip((0.15 * r - np.abs(X - ex)) * 4, 0, 1)
            blend(loc, m * 0.7, (0.2, 0.12, 0.1))
    my = cy + 0.38 * r
    if expr in ("awe", "wow"):
        blend(loc, soft_ell(X, Y, cx, my + 0.03 * r, 0.10 * r, 0.12 * r), (0.35, 0.07, 0.12))
        blend(loc, soft_ell(X, Y, cx, my + 0.09 * r, 0.06 * r, 0.05 * r) * 0.9, (0.9, 0.35, 0.4))
        return
    depth = {"smile": 0.13, "grin": 0.2, "calm": 0.05}.get(expr, 0.12) * r
    mw = (0.30 if expr == "grin" else 0.24) * r
    u = (X - cx) / mw
    yc = my + depth * (1 - u * u) - depth * 0.5
    th = 0.03 * r * (1.6 if expr == "grin" else 1.0)
    m = np.clip((th - np.abs(Y - yc)) * 2.2, 0, 1) * np.clip((1 - np.abs(u)) * 5, 0, 1)
    blend(loc, m * 0.9, (0.35, 0.1, 0.12))
    if expr == "grin":
        fill = np.clip((Y - (yc - th)) * 2, 0, 1) * np.clip((yc + depth * 0.6 - Y) * 2, 0, 1) * np.clip((1 - np.abs(u)) * 5, 0, 1)
        blend(loc, fill * 0.9, (1.0, 0.96, 0.95))


def draw_visor(cv, cx, cy, rx, ry, face=True, skin=SKIN, expr="smile", blink=0.0, look=(0, 0),
               reflect=None, t=0.0, hair=None, sheen=1.0):
    bb = bbox(cx - rx - 2, cy - ry - 2, cx + rx + 2, cy + ry + 2)
    if not bb: return
    xa, xb, ya, yb = bb
    X = XX[ya:yb, xa:xb]; Y = YY[ya:yb, xa:xb]
    k0 = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
    k1 = np.sqrt(((X - cx) / (rx * rx)) ** 2 + ((Y - cy) / (ry * ry)) ** 2) + 1e-6
    cov = np.clip(0.5 - k0 * (k0 - 1) / k1, 0, 1)
    if not cov.any(): return
    f = np.clip((Y - (cy - ry)) / (2 * ry), 0, 1)[..., None]
    loc = col(0.14, 0.22, 0.45) * (1 - f) + col(0.04, 0.07, 0.18) * f
    r_face = rx * 0.7
    fcx = cx + look[0] * rx * 0.08; fcy = cy + 0.06 * ry
    if face:
        kk = soft_ell(X, Y, fcx, fcy, rx * 0.76, ry * 0.9)
        sk = np.asarray(skin, np.float32) * (0.86 + 0.14 * (1 - f))
        blend(loc, kk * 0.97, sk)
        if hair is not None:
            hm = soft_ell(X, Y, fcx, fcy - ry * 0.55, rx * 0.8, ry * 0.5) * (Y < fcy - ry * 0.28)
            blend(loc, hm, hair)
        face_layer(loc, X, Y, fcx, fcy, r_face, expr, blink, look)
    if reflect is not None:
        rr = ry * reflect.get("size", 0.5)
        rcx = cx + rx * reflect.get("dx", -0.3); rcy = cy + ry * reflect.get("dy", -0.2)
        Xn = (X - rcx) / rr; Yn = (Y - rcy) / rr
        c, rrn = sphere_arrays(Xn, Yn, reflect["tex"], light=(0.6, -0.4, 0.7), amb=0.25, atmo=(0.25, 0.45, 1.0))
        cv_ = np.clip((1 - rrn) * rr + 0.5, 0, 1) * reflect.get("alpha", 0.9)
        blend(loc, cv_, c * 1.1)
        g = np.clip(1 - np.sqrt((X - rcx) ** 2 + (Y - rcy) ** 2) / (rr * 1.9), 0, 1) ** 2
        loc += g[..., None] * np.asarray(reflect.get("halo", (0.05, 0.12, 0.3)), np.float32)
    # glass sheen + rim highlights
    diag = ((X - cx) / rx + (Y - cy) / ry)
    loc += (np.clip(1 - np.abs(diag + 0.55) * 2.2, 0, 1) * 0.12 * sheen)[..., None]
    ang = np.arctan2(Y - cy, X - cx)
    cres = np.clip(1 - np.abs(k0 - 0.82) * 14, 0, 1) * np.clip(-np.cos(ang - (-2.2)) * 1.4 - 0.2, 0, 1)
    loc += (cres * 0.55 * sheen)[..., None]
    loc *= (1 - 0.32 * np.clip((k0 - 0.82) / 0.18, 0, 1))[..., None]
    sub = cv[ya:yb, xa:xb]
    sub += (loc - sub) * cov[..., None]


def person(cv, x, y, s, t=0.0, *, helmet=True, flip=False, suit=SUIT, trim=TRIM, skin=SKIN, hair=None, hair_style=None,
           expr="smile", blink=0.0, look=(0.0, 0.0), wave=False, arm_l=0.18, arm_r=0.18, walk=0.0, patch=1.0,
           reflect=None, wings=None, pack=True, lean=0.0, head_k=1.0, glow_patch=0.0, pack_col=(0.74, 0.76, 0.82),
           patch_xy=(-12, -91), patch_r=8.5, patch_col=ORANGE, flare=0.0):
    """(x, y) = feet centre. Returns dict of key anchor points (screen coords)."""
    if s < 0.05:
        return {"patch": (x, y), "head": (x, y), "hand": (x, y), "visor": (x, y)}
    dx = -1.0 if flip else 1.0

    def P(px, py):
        return x + dx * (px + lean * (-py) * 0.12) * s, y + py * s

    suit = np.asarray(suit, np.float32); trim = np.asarray(trim, np.float32)
    # wings (behind everything)
    if wings:
        fl = math.sin(t * wings.get("rate", 5.0))
        wc = np.asarray(wings.get("col", (0.55, 0.85, 1.0)), np.float32)
        for sg in (-1, 1):
            sh = P(sg * 20, -100)
            tip1 = P(sg * (88 + 14 * fl), -128 - 46 * fl)
            tip2 = P(sg * (96 + 10 * fl), -74 - 38 * fl)
            tip3 = P(sg * (62 + 6 * fl), -26 - 24 * fl)
            hp = P(sg * 18, -56)
            poly(cv, [sh, tip1, tip2, tip3, hp], wc * 1.05, wc * 0.65, a=0.9)
            for tp in (tip1, tip2, tip3):
                line(cv, sh[0], sh[1], tp[0], tp[1], 2.2 * s, wc * 0.5, 0.8)
            for tp in (tip1, tip2, tip3):
                circ(cv, tp[0], tp[1], 3.5 * s, wc * 1.2, flat=True)
    # backpack
    if pack and helmet:
        px_, py_ = P(0, -86)
        rrect(cv, px_, py_, 35 * s, 30 * s, 12 * s, pack_col)
    # legs
    for sg in (-1, 1):
        ph = walk * sg
        fx = sg * 12 + ph * 11; lift = max(0.0, ph) * 9
        a = P(sg * 11, -54); b = P(fx, -10 - lift)
        capsule(cv, a[0], a[1], b[0], b[1], 11 * s, suit * 0.97)
        bx, by = P(fx + dx * 0 + sg * 0 + 3 * dx * (1 if not flip else 1), -5 - lift)
        rrect(cv, b[0] + 3 * dx * s, b[1] + 3 * s, 14 * s, 8 * s, 7 * s, trim * 0.8)
    # far arm
    def arm(sg, ang):
        sh = P(sg * 26, -100)
        L = 40
        hx, hy = P(sg * 26 + sg * math.sin(ang) * L, -100 + math.cos(ang) * L)
        capsule(cv, sh[0], sh[1], hx, hy, 10 * s, suit, r1=8.5 * s)
        circ(cv, hx, hy, 10 * s, trim * 1.1)
        return hx, hy
    arm(-1, arm_l)
    # torso
    tx, ty = P(0, -78)
    rrect(cv, tx, ty, 27 * s, 31 * s, 15 * s, suit)
    bx_, by_ = P(5, -86)
    rrect(cv, bx_, by_, 12 * s, 8 * s, 4 * s, trim)
    for i, cc in enumerate(((0.3, 0.9, 0.5), (1.0, 0.5, 0.3))):
        q = P(1 + i * 7, -86)
        circ(cv, q[0], q[1], 2.1 * s, cc, flat=True)
    belt = P(0, -52)
    rrect(cv, belt[0], belt[1], 26 * s, 6.5 * s, 3 * s, trim * 0.9)
    # patch
    pp = P(*patch_xy)
    if patch > 0:
        star(cv, pp[0], pp[1], patch_r * s, np.asarray(patch_col, np.float32), ang=-0.2 * dx, a=patch, gloss=0.25)
    if glow_patch > 0:
        glow(cv, pp[0], pp[1], 34 * s * (0.8 + 0.4 * glow_patch), np.asarray(patch_col, np.float32) * 0.9, glow_patch, 2.0)
    # near arm
    if wave:
        hand = arm(1, 2.55 + 0.28 * math.sin(t * 8.0))
    else:
        hand = arm(1, arm_r)
    # neck + head
    nk = P(0, -108)
    rrect(cv, nk[0], nk[1], 19 * s, 7 * s, 5 * s, trim)
    hc = P(0, -126)
    hr = 30 * s * head_k
    out = {"patch": pp, "head": hc, "hand": hand}
    if helmet:
        circ(cv, hc[0], hc[1], hr, suit * 1.02, gloss=0.35)
        vc = P(2.5 * look[0] + 1, -124)
        draw_visor(cv, vc[0], vc[1], 22 * s * head_k, 19 * s * head_k, True, skin, expr, blink, look, reflect, t, hair=hair)
        out["visor"] = vc
        # little antenna
        ap = P(-16, -150)
        capsule(cv, ap[0], ap[1], ap[0] - dx * 3 * s, ap[1] - 10 * s, 1.6 * s, trim * 0.9, flat=True)
        circ(cv, ap[0] - dx * 3 * s, ap[1] - 11 * s, 2.6 * s, ORANGE, flat=True)
    else:
        hc = P(0, -122)
        hrr = 26 * s * head_k
        hairc = np.asarray(hair if hair is not None else (0.25, 0.15, 0.1), np.float32)
        if hair_style in ("long", "bun"):
            ell(cv, hc[0], hc[1] + 6 * s, hrr * 1.12, hrr * 1.18, hairc * 0.9)
        if hair_style == "bun":
            circ(cv, hc[0] + dx * 2 * s, hc[1] - hrr * 1.12, 10 * s, hairc)
        circ(cv, hc[0], hc[1], hrr, skin)
        bb = bbox(hc[0] - hrr - 3, hc[1] - hrr - 3, hc[0] + hrr + 3, hc[1] + hrr + 3)
        if bb:
            xa, xb, ya, yb = bb
            sub = cv[ya:yb, xa:xb]
            face_layer(sub, XX[ya:yb, xa:xb], YY[ya:yb, xa:xb], hc[0] + look[0] * 0.04 * hrr, hc[1] + 0.12 * hrr, hrr * 0.92, expr, blink, look)
        if hair_style is not None and hair_style != "bald":
            ell(cv, hc[0], hc[1] - hrr * 0.62, hrr * 1.02, hrr * 0.52, hairc)
        out["visor"] = hc
    if flare > 0:
        glow(cv, out["head"][0], out["head"][1], 60 * s, (1.0, 0.8, 0.5), flare, 2.0)
    return out


def bust(cv, x, y, s, *, skin, hair, hair_style, outfit, outfit2, hat=None, patch="chest", faded=0.55, expr="calm", t=0.0, blink=0.0):
    """Upper-body portrait used for the evolved-culture cards. (x,y) = bottom centre."""
    outfit = np.asarray(outfit, np.float32); outfit2 = np.asarray(outfit2, np.float32)
    hairc = np.asarray(hair, np.float32)
    # shoulders
    rrect(cv, x, y - 24 * s, 62 * s, 44 * s, 26 * s, outfit)
    rrect(cv, x, y - 52 * s, 44 * s, 14 * s, 8 * s, outfit2)
    if hat == "hood":
        circ(cv, x, y - 98 * s, 46 * s, outfit2 * 0.9)
    if hair_style == "long":
        ell(cv, x, y - 96 * s, 38 * s, 46 * s, hairc * 0.9)
    capsule(cv, x, y - 56 * s, x, y - 66 * s, 12 * s, np.asarray(skin, np.float32) * 0.9, flat=False)
    hr = 32 * s
    hc = (x, y - 92 * s)
    circ(cv, hc[0], hc[1], hr, skin)
    bb = bbox(hc[0] - hr - 3, hc[1] - hr - 3, hc[0] + hr + 3, hc[1] + hr + 3)
    if bb:
        xa, xb, ya, yb = bb
        sub = cv[ya:yb, xa:xb]
        face_layer(sub, XX[ya:yb, xa:xb], YY[ya:yb, xa:xb], hc[0], hc[1] + 3 * s, hr * 0.92, expr, blink)
    if hair_style in ("cap", "long", "bun"):
        ell(cv, hc[0], hc[1] - hr * 0.62, hr * 1.04, hr * 0.5, hairc)
    if hair_style == "bun":
        circ(cv, hc[0], hc[1] - hr * 1.15, 11 * s, hairc)
    if hair_style == "crest":
        for k in range(-2, 3):
            capsule(cv, hc[0] + k * 9 * s, hc[1] - hr * 0.8, hc[0] + k * 12 * s, hc[1] - hr * (1.5 - 0.1 * abs(k)), 5 * s, hairc)
    if hat == "turban":
        ell(cv, hc[0], hc[1] - hr * 0.7, hr * 1.12, hr * 0.62, outfit2 * 1.05)
        circ(cv, hc[0] + 14 * s, hc[1] - hr * 0.9, 5 * s, ORANGE, flat=True)
    if hat == "halo":
        ring_y = hc[1] - hr - 14 * s
        ell(cv, hc[0], ring_y, 34 * s, 8 * s, np.asarray((1.0, 0.85, 0.45), np.float32), flat=True)
        ell(cv, hc[0], ring_y, 27 * s, 4.5 * s, np.asarray((0.1, 0.06, 0.15), np.float32), flat=True)
    if hat == "visor":
        rrect(cv, hc[0], hc[1] - 4 * s, hr * 1.02, 11 * s, 6 * s, np.asarray((0.2, 0.9, 0.95), np.float32), flat=True, a=0.8)
    if hat == "antenna":
        for sg in (-1, 1):
            capsule(cv, hc[0] + sg * 14 * s, hc[1] - hr * 0.9, hc[0] + sg * 24 * s, hc[1] - hr * 1.7, 2.2 * s, outfit2, flat=True)
            circ(cv, hc[0] + sg * 24 * s, hc[1] - hr * 1.7, 4.5 * s, (1.0, 0.8, 0.4), flat=True)
    # faded patch
    pc = ORANGE * 0.55 + np.asarray(outfit, np.float32) * 0.45
    if patch == "chest":
        star(cv, x - 26 * s, y - 28 * s, 11 * s, pc, a=faded, flat=True)
    elif patch == "brow":
        star(cv, hc[0], hc[1] - hr * 0.28, 5.5 * s, pc, a=min(1, faded + 0.25), flat=True)
    elif patch == "collar":
        star(cv, x, y - 46 * s, 8 * s, pc, a=faded, flat=True)
    elif patch == "shoulder":
        star(cv, x + 38 * s, y - 38 * s, 10 * s, pc, a=faded, flat=True)
