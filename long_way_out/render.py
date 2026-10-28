"""Compose scenes, post-process (bloom/grade), draw HUD + text at 1080x1920, encode with ffmpeg."""
import math, sys, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import spec
from spec import W, H, SCALE, smooth
import gfx
import scenes1 as S1
import scenes2 as S2

OW, OH = W * SCALE, H * SCALE
SCENE_FN = [S1.scene1, S1.scene2, S1.scene3, S1.scene4, S2.scene5, S2.scene6, S2.scene7, S2.scene8, S1.scene9]

FD = "/usr/share/fonts/opentype/inter/"
def F(name, size): return ImageFont.truetype(FD + name, size)
F_LAB = F("Inter-SemiBold.otf", 21); F_VAL = F("Inter-Bold.otf", 44); F_VAL_S = F("Inter-Bold.otf", 36)
F_TAG = F("Inter-SemiBold.otf", 19); F_TXT = F("Inter-SemiBold.otf", 40); F_BIG = F("Inter-ExtraBold.otf", 66)
F_END = F("Inter-ExtraBold.otf", 70); F_END2 = F("Inter-Medium.otf", 40); F_KARD = F("Inter-Bold.otf", 34)

# colour grade per scene (gain rgb) - Earth blue -> Mars orange -> icy cyan -> gold -> violet
GRADE = [(0.98, 1.0, 1.06), (0.98, 1.0, 1.05), (1.08, 0.98, 0.92), (0.90, 1.02, 1.10), (1.08, 1.02, 0.90), (1.0, 0.94, 1.10), (0.98, 0.92, 1.12), (0.98, 0.92, 1.14), (0.98, 1.0, 1.06)]
ACCENT = [(120, 190, 255), (150, 200, 255), (255, 150, 90), (120, 230, 240), (255, 200, 90), (255, 200, 120), (190, 150, 255), (190, 150, 255), (255, 160, 60)]


def grade_gain(t):
    i = spec.scene_of(t)
    a, b = spec.SCENES[i]
    g = np.array(GRADE[i], np.float32)
    if i + 1 < len(GRADE) and t > b - 0.6:
        g = g + (np.array(GRADE[i + 1], np.float32) - g) * smooth((t - (b - 0.6)) / 0.6) * 0.5
    return g


def compose(t):
    cv = np.zeros((H, W, 3), np.float32)
    i = spec.scene_of(t)
    SCENE_FN[i](cv, t)
    cv = np.nan_to_num(cv, nan=0.0, posinf=1.0, neginf=0.0)
    gfx.vignette(cv, 0.32)
    gfx.bloom(cv, 0.70, 0.45)
    cv *= grade_gain(t)
    # era-transition punch: zoom-in settle + white flash
    a, b = spec.SCENES[i]
    u = t - a
    if i > 0 and u < 0.4:
        f = 1 - smooth(u / 0.4)
        cv += f * 0.28
        z = 1 + 0.07 * f
        img = Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8))
        w2, h2 = W / z, H / z
        img = img.resize((W, H), Image.BICUBIC, box=((W - w2) / 2, (H - h2) / 2, (W + w2) / 2, (H + h2) / 2))
        cv = np.asarray(img, np.float32) / 255.0
    if t >= 69.5:
        cv *= max(0.0, 1 - (t - 69.5) / 0.5)
    rng = np.random.default_rng(int(t * 1000) % 100000)
    q = np.clip(cv, 0, 1) * 255 + rng.random((H, W, 1), dtype=np.float32) - 0.5
    return Image.fromarray(np.clip(q, 0, 255).astype(np.uint8)).resize((OW, OH), Image.BICUBIC)


# ---------------------------------------------------------------- HUD
def tw(d, s, font): return d.textlength(s, font=font)


def star_icon(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=fill)


def spaced(d, xy, s, font, fill, sp=2.0, anchor="l"):
    w = sum(tw(d, ch, font) + sp for ch in s) - sp
    x, y = xy
    if anchor == "r": x -= w
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill)
        x += tw(d, ch, font) + sp
    return w


def glass(layer, box, rad, alpha=110):
    x0, y0, x1, y1 = box
    base = layer.crop((int(x0), int(y0), int(x1), int(y1))).filter(ImageFilter.GaussianBlur(0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle(box, rad, fill=(8, 10, 28, alpha), outline=(255, 255, 255, 52), width=2)


def hud(img, t):
    layer = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    i = spec.scene_of(t)
    acc = ACCENT[i]
    vis = 1.0
    if t < 0.6: vis = smooth(t / 0.6)
    if t > 68.0: vis = 1 - smooth((t - 68.0) / 0.5)
    A = lambda v: int(v * vis)
    # years pill
    ys = spec.years_text(t)
    vw = tw(d, ys, F_VAL)
    w1 = max(250, vw + 64)
    box = (44, 150, 44 + w1, 270)
    d.rounded_rectangle(box, 30, fill=(8, 10, 28, A(120)), outline=(255, 255, 255, A(56)), width=2)
    star_icon(d, 44 + 38, 150 + 36, 12, (255, 143, 36, A(255)))
    spaced(d, (44 + 62, 150 + 25), "YEARS FROM NOW", F_LAB, (255, 255, 255, A(170)), 2.0)
    d.text((44 + 32, 150 + 54), ys, font=F_VAL, fill=(255, 255, 255, A(255)))
    # distance pill
    ds = spec.dist_text(t)
    font = F_VAL if tw(d, ds, F_VAL) < 360 else F_VAL_S
    dvw = tw(d, ds, font)
    w2 = max(300, dvw + 64)
    x1 = OW - 44
    box2 = (x1 - w2, 150, x1, 270)
    d.rounded_rectangle(box2, 30, fill=(8, 10, 28, A(120)), outline=(255, 255, 255, A(56)), width=2)
    spaced(d, (x1 - 32, 150 + 25), "DISTANCE FROM EARTH", F_LAB, (255, 255, 255, A(170)), 2.0, anchor="r")
    d.text((x1 - 32 - dvw, 150 + 57 if font is F_VAL else 150 + 62), ds, font=font, fill=(255, 255, 255, A(255)))
    # era tag
    era = spec.ERA[i]
    if era and t > 4.2:
        ek = smooth((t - spec.SCENES[i][0] - 0.1) / 0.4)
        e_w = sum(tw(d, ch, F_TAG) + 3 for ch in era) + 56
        d.rounded_rectangle((44, 288, 44 + e_w, 288 + 48), 24, fill=(acc[0], acc[1], acc[2], A(46 * ek)), outline=(acc[0], acc[1], acc[2], A(130 * ek)), width=2)
        d.ellipse((44 + 18, 288 + 18, 44 + 30, 288 + 30), fill=(acc[0], acc[1], acc[2], A(255 * ek)))
        spaced(d, (44 + 40, 288 + 13), era, F_TAG, (255, 255, 255, A(230 * ek)), 3.0)
    # texts
    for (t0, t1, kind, text) in spec.TEXTS:
        if not (t0 <= t < t1): continue
        k = smooth((t - t0) / 0.35) * (1 - smooth((t - (t1 - 0.3)) / 0.3))
        if k <= 0.01: continue
        rise = (1 - smooth((t - t0) / 0.45)) * 26
        if kind == "label":
            lines = wrap(d, text, F_TXT, 800)
            lh = 54
            wmax = max(tw(d, l, F_TXT) for l in lines)
            bw = wmax + 96; bh = lh * len(lines) + 40
            cx = OW / 2; y0 = 1350 + rise
            box = (cx - bw / 2, y0, cx + bw / 2, y0 + bh)
            d.rounded_rectangle(box, 36, fill=(8, 10, 28, int(150 * k)), outline=(255, 255, 255, int(60 * k)), width=2)
            d.rounded_rectangle((box[0] + 22, y0 + 22, box[0] + 30, y0 + bh - 22), 4, fill=(acc[0], acc[1], acc[2], int(255 * k)))
            for j, l in enumerate(lines):
                d.text((box[0] + 52, y0 + 20 + j * lh), l, font=F_TXT, fill=(255, 255, 255, int(255 * k)))
        elif kind == "big":
            lines = wrap(d, text, F_BIG, 900)
            lh = 84
            y0 = 1080 + rise - (len(lines) - 1) * lh / 2
            for j, l in enumerate(lines):
                x = OW / 2 - tw(d, l, F_BIG) / 2
                for off, a in ((6, 60), (3, 90)):
                    d.text((x, y0 + j * lh + off), l, font=F_BIG, fill=(0, 0, 20, int(a * k)))
                d.text((x, y0 + j * lh), l, font=F_BIG, fill=(255, 255, 255, int(255 * k)))
        elif kind == "kard":
            kard(d, text, k, t - t0, acc)
    # end card
    if t >= spec.END_CARD[0]:
        k = smooth((t - spec.END_CARD[0]) / 0.5)
        ch = spec.CHANNEL
        w = tw(d, ch, F_END)
        d.text((OW / 2 - w / 2, 1368), ch, font=F_END, fill=(255, 255, 255, int(255 * k)))
        s2 = spec.END_CARD[2]
        w = tw(d, s2, F_END2)
        d.text((OW / 2 - w / 2, 1460), s2, font=F_END2, fill=(255, 190, 110, int(255 * k)))
        star_icon(d, OW / 2, 1340, 20, (255, 143, 36, int(255 * k)))
    img = img.convert("RGBA")
    img.alpha_composite(layer)
    return img.convert("RGB")


def wrap(d, text, font, maxw):
    words = text.split(" "); lines = []; cur = ""
    for w_ in words:
        tr = (cur + " " + w_).strip()
        if tw(d, tr, font) <= maxw: cur = tr
        else: lines.append(cur); cur = w_
    lines.append(cur)
    return lines


def kard(d, text, k, u, acc):
    y0 = 1140
    bw, bh = 760, 120
    x0 = OW / 2 - bw / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 36, fill=(8, 10, 28, int(150 * k)), outline=(255, 215, 130, int(140 * k)), width=2)
    prog = smooth((u - 0.6) / 1.4)
    # node I -> node II
    n1 = (x0 + 90, y0 + 60); n2 = (x0 + bw - 90, y0 + 60)
    d.line((n1[0] + 40, n1[1], n2[0] - 40, n2[1]), fill=(255, 255, 255, int(70 * k)), width=6)
    d.line((n1[0] + 40, n1[1], n1[0] + 40 + (n2[0] - n1[0] - 80) * prog, n2[1]), fill=(255, 200, 90, int(255 * k)), width=6)
    for n, lab, on in ((n1, "I", True), (n2, "II", prog > 0.97)):
        d.ellipse((n[0] - 42, n[1] - 42, n[0] + 42, n[1] + 42), fill=(255, 190, 70, int((255 if on else 90) * k)) if on else (30, 30, 60, int(220 * k)),
                  outline=(255, 215, 130, int(255 * k)), width=4)
        w = tw(d, lab, F_KARD)
        d.text((n[0] - w / 2, n[1] - 22), lab, font=F_KARD, fill=((20, 12, 0, int(255 * k)) if on else (255, 255, 255, int(255 * k))))
    mid = "TYPE"
    w = tw(d, mid, F_TAG)
    d.text((OW / 2 - w / 2, y0 + 44), "CIVILIZATION", font=F_TAG, fill=(255, 255, 255, int(200 * k)),) if False else None
    spaced(d, (OW / 2 - 70, y0 + 46), "CIVILIZATION", F_TAG, (255, 255, 255, int(220 * k)), 3.0)


def draw_frame(i):
    t = i / spec.FPS
    return hud(compose(t), t)


def render(out, audio, t0=0.0):
    n = int(spec.DUR * spec.FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(spec.FPS), "-i", "-",
           "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(spec.FPS),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import multiprocessing as mp
    with mp.Pool(os.cpu_count()) as pool:
        for k, img in enumerate(pool.imap(draw_frame, range(n), chunksize=3)):
            p.stdin.write(img.tobytes())
            if k % 150 == 0: print("frame", k, "/", n, flush=True)
    p.stdin.close(); p.wait()
    print("done", out)


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for tt in map(float, sys.argv[3:]):
            draw_frame(int(round(tt * spec.FPS))).resize((OW // 2, OH // 2), Image.LANCZOS).save(f"{out}/t{tt:06.2f}.png")
    else:
        render(sys.argv[1], sys.argv[2])
