"""Tiny flat-shaded software 3D engine for blocky (Roblox-style) scenes. Painter's algorithm over quads, PIL polygons.

World axes: x right, y up, z forward.  Every face is a quad (triangles repeat a vertex), wound CCW seen from outside.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ------------------------------------------------------------------ unit meshes
_P, _M = 0.5, -0.5
CUBE = np.array([
    [(_P, _M, _M), (_P, _P, _M), (_P, _P, _P), (_P, _M, _P)],   # +x
    [(_M, _M, _P), (_M, _P, _P), (_M, _P, _M), (_M, _M, _M)],   # -x
    [(_M, _P, _M), (_M, _P, _P), (_P, _P, _P), (_P, _P, _M)],   # +y
    [(_M, _M, _P), (_M, _M, _M), (_P, _M, _M), (_P, _M, _P)],   # -y
    [(_P, _M, _P), (_P, _P, _P), (_M, _P, _P), (_M, _M, _P)],   # +z
    [(_M, _M, _M), (_M, _P, _M), (_P, _P, _M), (_P, _M, _M)],   # -z
], np.float32)


def rot_x(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)
def rot_y(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
def rot_z(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)
I3 = np.eye(3, dtype=np.float32)


def frame_from_dir(d, up=(0, 1, 0)):
    """Rotation whose local +z points along d."""
    z = np.asarray(d, np.float32); z = z / (np.linalg.norm(z) + 1e-9)
    up = np.asarray(up, np.float32)
    if abs(float(z @ up)) > 0.98: up = np.array([1, 0, 0], np.float32)
    x = np.cross(up, z); x /= np.linalg.norm(x) + 1e-9
    y = np.cross(z, x)
    return np.stack([x, y, z], 1).astype(np.float32)


def cyl_mesh(n, top_scale=1.0):
    """Unit cylinder (radius .5, height 1, centred) as quads: n sides + 2 caps (n even)."""
    a = np.arange(n) / n * 2 * math.pi
    bot = np.stack([np.cos(a) * 0.5, np.full(n, -0.5), np.sin(a) * 0.5], 1)
    top = np.stack([np.cos(a) * 0.5 * top_scale, np.full(n, 0.5), np.sin(a) * 0.5 * top_scale], 1)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([bot[j], top[j], top[i], bot[i]])
    for i in range((n - 2) // 2):
        faces.append([top[0], top[2 * i + 3], top[2 * i + 2], top[2 * i + 1]])
        faces.append([bot[0], bot[2 * i + 1], bot[2 * i + 2], bot[2 * i + 3]])
    return np.array(faces, np.float32)


_CYL = {}
def cyl_unit(n, ts=1.0):
    k = (n, ts)
    if k not in _CYL: _CYL[k] = cyl_mesh(n, ts)
    return _CYL[k]


def sphere_mesh(nu=10, nv=6):
    faces = []
    for j in range(nv):
        v0 = math.pi * j / nv; v1 = math.pi * (j + 1) / nv
        for i in range(nu):
            u0 = 2 * math.pi * i / nu; u1 = 2 * math.pi * (i + 1) / nu
            def pt(u, v): return (math.sin(v) * math.cos(u) * 0.5, math.cos(v) * 0.5, math.sin(v) * math.sin(u) * 0.5)
            faces.append([pt(u1, v0), pt(u1, v1), pt(u0, v1), pt(u0, v0)])
    return np.array(faces, np.float32)


_SPH = {}
def sphere_unit(nu=10, nv=6):
    k = (nu, nv)
    if k not in _SPH: _SPH[k] = sphere_mesh(nu, nv)
    return _SPH[k]


# ------------------------------------------------------------------ world
class World:
    def __init__(self):
        self.V = []; self.C = []; self.E = []; self.A = []; self.DS = []; self.B = []

    def _add(self, v, color, em, alpha, ds):
        n = len(v)
        self.V.append(v)
        c = np.asarray(color, np.float32)
        self.C.append(np.broadcast_to(c, (n, 3)) if c.ndim == 1 else c)
        self.E.append(np.full(n, em, np.float32)); self.A.append(np.full(n, alpha, np.float32)); self.DS.append(np.full(n, ds, bool)); self.B.append(np.zeros(n, np.float32))

    def box(self, c, size, color, R=None, em=0.0, alpha=1.0, faces=None, ds=False):
        v = CUBE * np.asarray(size, np.float32)
        if R is not None: v = v @ R.T
        v = v + np.asarray(c, np.float32)
        if faces is not None: v = v[faces]
        self._add(v, color, em, alpha, ds)

    def mesh(self, unit, c, size, color, R=None, em=0.0, alpha=1.0, ds=False):
        v = unit * np.asarray(size, np.float32)
        if R is not None: v = v @ R.T
        self._add(v + np.asarray(c, np.float32), color, em, alpha, ds)

    def cyl(self, c, r, h, color, n=8, R=None, em=0.0, alpha=1.0, ts=1.0):
        self.mesh(cyl_unit(n, ts), c, (2 * r, h, 2 * r), color, R, em, alpha)

    def sphere(self, c, r, color, em=0.0, alpha=1.0, nu=10, nv=6):
        self.mesh(sphere_unit(nu, nv), c, (2 * r,) * 3, color, None, em, alpha, ds=alpha < 1)

    def quad(self, verts, color, em=0.0, alpha=1.0, ds=False):
        self._add(np.asarray(verts, np.float32)[None], color, em, alpha, ds)

    def beam(self, a, b, w, color, em=1.0, alpha=1.0):
        a = np.asarray(a, np.float32); b = np.asarray(b, np.float32)
        d = b - a; L = float(np.linalg.norm(d))
        if L < 1e-4: return
        self.box((a + b) / 2, (w, w, L), color, frame_from_dir(d), em, alpha)

    def quads(self, V, C, em=0.0, bias=0.6):
        """Bulk add (F,4,3) quads with (F,3) colours (used for windows)."""
        if len(V) == 0: return
        self.V.append(np.asarray(V, np.float32)); self.C.append(np.asarray(C, np.float32))
        n = len(V)
        self.E.append(np.full(n, em, np.float32)); self.A.append(np.ones(n, np.float32)); self.DS.append(np.zeros(n, bool)); self.B.append(np.full(n, bias, np.float32))

    def cubes(self, centers, sizes, colors, em=0.0):
        """Bulk axis-aligned cubes: centers (n,3), sizes (n,) or scalar, colors (n,3)."""
        centers = np.asarray(centers, np.float32); n = len(centers)
        if n == 0: return
        sz = np.broadcast_to(np.asarray(sizes, np.float32), (n,))
        V = CUBE[None] * sz[:, None, None, None] + centers[:, None, None, :]
        C = np.repeat(np.asarray(colors, np.float32)[:, None, :], 6, 1).reshape(-1, 3)
        self.V.append(V.reshape(-1, 4, 3)); self.C.append(C)
        m = n * 6
        self.E.append(np.full(m, em, np.float32)); self.A.append(np.ones(m, np.float32)); self.DS.append(np.zeros(m, bool)); self.B.append(np.zeros(m, np.float32))

    def arrays(self):
        if not self.V: return None
        return (np.concatenate(self.V), np.concatenate(self.C), np.concatenate(self.E), np.concatenate(self.A), np.concatenate(self.DS), np.concatenate(self.B))


# ------------------------------------------------------------------ camera / renderer
class Camera:
    def __init__(self, pos, target, fov=60.0, roll=0.0):
        self.pos = np.asarray(pos, np.float32); self.fov = fov; self.roll = roll
        f = np.asarray(target, np.float32) - self.pos
        f /= np.linalg.norm(f) + 1e-9
        r = np.cross(np.array([0, 1, 0], np.float32), f)
        if np.linalg.norm(r) < 1e-4: r = np.array([1, 0, 0], np.float32)
        r /= np.linalg.norm(r)
        u = np.cross(f, r)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            r, u = r * c + u * s, u * c - r * s
        self.M = np.stack([r, u, f]).astype(np.float32)
        self.f = f
        self.pitch = math.asin(max(-1, min(1, float(f[1]))))


class Renderer:
    def __init__(self, w, h):
        self.w, self.h = w, h

    def background(self, cam, sky_top, sky_hor, gnd_hor, gnd_bot, extra=None):
        w, h = self.w, self.h
        F = 0.5 * h / math.tan(math.radians(cam.fov) / 2)
        yh = h / 2 + F * math.tan(cam.pitch)
        ys = np.arange(h, dtype=np.float32)
        img = np.zeros((h, 3), np.float32)
        t_sky = np.clip((yh - ys) / max(yh, 1), 0, 1)[:, None] ** 0.8
        t_gnd = np.clip((ys - yh) / max(h - yh, 1), 0, 1)[:, None] ** 0.7
        sky = np.asarray(sky_hor, np.float32) * (1 - t_sky) + np.asarray(sky_top, np.float32) * t_sky
        gnd = np.asarray(gnd_hor, np.float32) * (1 - t_gnd) + np.asarray(gnd_bot, np.float32) * t_gnd
        img = np.where((ys < yh)[:, None], sky, gnd)
        im = np.broadcast_to(img[:, None, :], (h, w, 3)).copy()
        return im, yh, F

    def render(self, world, cam, bg_img, light=(0.4, 0.8, 0.45), amb=0.45, fog=(0.5, 0.5, 0.6), fog_range=(40, 260), overlay_fn=None, near=0.25):
        w, h = self.w, self.h
        F = 0.5 * h / math.tan(math.radians(cam.fov) / 2)
        img = Image.fromarray((np.clip(bg_img, 0, 1) * 255).astype(np.uint8))
        arr = world.arrays()
        if arr is None: return img
        V, C, E, A, DS, B = arr
        Pc = (V - cam.pos) @ cam.M.T
        cen = Pc.mean(1)
        n_c = np.cross(Pc[:, 1] - Pc[:, 0], Pc[:, 2] - Pc[:, 0])
        vis = ((n_c * (-cen)).sum(1) > 0) | DS
        anyfront = (Pc[:, :, 2] > near).any(1)
        keep = vis & anyfront & (cen[:, 2] > -50)
        idx = np.where(keep)[0]
        if len(idx) == 0: return img
        V = V[idx]; C = C[idx]; E = E[idx]; A = A[idx]; Pc = Pc[idx]; cen = cen[idx]; DS = DS[idx]; B = B[idx]
        nw = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
        nw /= (np.linalg.norm(nw, axis=1, keepdims=True) + 1e-9)
        nw = np.where(DS[:, None], np.where(((nw * (cam.pos - V.mean(1))).sum(1) < 0)[:, None], -nw, nw), nw)
        L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
        lam = np.clip((nw * L).sum(1), 0, 1)
        sky = np.clip(nw[:, 1], 0, 1) * 0.12
        shade = amb + (1 - amb) * 0.9 * lam + sky
        col = C * shade[:, None]
        col = col * (1 - np.clip(E, 0, 1))[:, None] + C * np.maximum(E, 0)[:, None] * (1.0 + 0.0 * E[:, None])
        dist = np.linalg.norm(cen, axis=1)
        fk = np.clip((dist - fog_range[0]) / (fog_range[1] - fog_range[0]), 0, 1) ** 1.2
        fk = fk * (1 - 0.7 * np.clip(E, 0, 1))
        col = col * (1 - fk[:, None]) + np.asarray(fog, np.float32) * fk[:, None]
        col8 = (np.clip(col, 0, 1.0) * 255).astype(np.uint8)
        # projection (fully in front) vectorized
        front = (Pc[:, :, 2] > near).all(1)
        z = np.maximum(Pc[:, :, 2], near)
        sx = w / 2 + F * Pc[:, :, 0] / z
        sy = h / 2 - F * Pc[:, :, 1] / z
        order = np.argsort(-(cen[:, 2] - B))
        d = ImageDraw.Draw(img)
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
        any_ov = False
        for i in order:
            if front[i]:
                pts = [(sx[i, 0], sy[i, 0]), (sx[i, 1], sy[i, 1]), (sx[i, 2], sy[i, 2]), (sx[i, 3], sy[i, 3])]
            else:
                pts = self._clip(Pc[i], near, F, w, h)
                if len(pts) < 3: continue
            if A[i] >= 0.999:
                d.polygon(pts, fill=tuple(int(v) for v in col8[i]))
            else:
                do.polygon(pts, fill=tuple(int(v) for v in col8[i]) + (int(A[i] * 255),)); any_ov = True
        if any_ov:
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        return img

    @staticmethod
    def _clip(P, near, F, w, h):
        out = []
        n = len(P)
        for i in range(n):
            a = P[i]; b = P[(i + 1) % n]
            ina = a[2] > near; inb = b[2] > near
            if ina: out.append(a)
            if ina != inb:
                t = (near - a[2]) / (b[2] - a[2])
                out.append(a + (b - a) * t)
        return [(w / 2 + F * p[0] / max(p[2], near), h / 2 - F * p[1] / max(p[2], near)) for p in out]


def bloom(img, thr=200, amt=0.55, radius=6):
    """Cheap glow for emissive things."""
    a = np.asarray(img, np.float32)
    br = np.clip(a - thr, 0, 255) * (255.0 / (255 - thr))
    small = Image.fromarray(br.astype(np.uint8)).resize((img.width // 4, img.height // 4), Image.BILINEAR)
    b = small.filter(ImageFilter.GaussianBlur(radius / 2)).resize(img.size, Image.BILINEAR)
    b2 = small.filter(ImageFilter.GaussianBlur(radius * 1.6)).resize(img.size, Image.BILINEAR)
    out = a + (np.asarray(b, np.float32) * 0.7 + np.asarray(b2, np.float32) * 0.9) * amt
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
