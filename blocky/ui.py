"""Caption / HUD overlay in the 'what-if' reel style: serif title, italic narration captions, small-caps stat readout."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FS = "/usr/share/fonts/truetype/liberation/"
FI = "/usr/share/fonts/opentype/inter/"
def font(path, size): return ImageFont.truetype(path, size)

F_TITLE = font(FS + "LiberationSerif-Regular.ttf", 96)
F_CAP = font(FS + "LiberationSerif-Italic.ttf", 58)
F_VAL = font(FS + "LiberationSerif-Regular.ttf", 104)
F_VAL_S = font(FS + "LiberationSerif-Regular.ttf", 76)
F_LAB = font(FI + "Inter-SemiBold.otf", 27)
F_SUB = font(FI + "Inter-SemiBold.otf", 23)
F_END = font(FS + "LiberationSerif-Regular.ttf", 84)
F_END2 = font(FI + "Inter-SemiBold.otf", 34)
F_TAG = font(FI + "Inter-Medium.otf", 21)


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def tw(d, s, f, sp=0.0): return sum(d.textlength(c, font=f) + sp for c in s) - sp if sp else d.textlength(s, font=f)


def spaced(d, xy, s, f, fill, sp=4.0):
    x, y = xy
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + sp


def shadow_layer(size, draw_fn, blur=7, alpha=210):
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay), (0, 0, 0, alpha))
    return lay.filter(ImageFilter.GaussianBlur(blur))


def wrap(d, text, f, maxw):
    words = text.split(" "); lines = []; cur = ""
    for w in words:
        tr = (cur + " " + w).strip()
        if d.textlength(tr, font=f) <= maxw: cur = tr
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines


def overlay(img, t, spec):
    """spec: dict(title=[(t0,t1,text)], caps=[(t0,t1,text)], stat=fn(t)->(label,value,sub)|None, end=(t0,channel,tagline), tag=str)"""
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)

    def put(fn):
        fn(sd, (0, 0, 0, 220)); fn(d, (255, 255, 255, 255))

    # title (top third), centred, 2+ lines
    for (t0, t1, text) in spec.get("title", []):
        if t0 <= t < t1:
            k = smooth((t - t0) / 0.6) * (1 - smooth((t - (t1 - 0.5)) / 0.5))
            lines = wrap(d, text, F_TITLE, W - 150)
            y0 = H * 0.285 - len(lines) * 56 + (1 - smooth((t - t0) / 0.8)) * 24
            for j, l in enumerate(lines):
                x = W / 2 - d.textlength(l, font=F_TITLE) / 2
                a = int(255 * k)
                sd.text((x, y0 + j * 112), l, font=F_TITLE, fill=(0, 0, 0, int(220 * k)))
                d.text((x, y0 + j * 112), l, font=F_TITLE, fill=(255, 255, 255, a))
    # narration captions: word-by-word reveal
    for (t0, t1, text) in spec.get("caps", []):
        if t0 <= t < t1:
            lines = wrap(d, text, F_CAP, W - 150)
            words = text.split(" ")
            n = len(words)
            reveal = min(0.55 + 0.05 * n, (t1 - t0) * 0.55)
            out = 1 - smooth((t - (t1 - 0.35)) / 0.35)
            wi = 0
            y0 = H * 0.585 - (len(lines) - 1) * 36
            for j, l in enumerate(lines):
                lw = d.textlength(l, font=F_CAP)
                x = W / 2 - lw / 2
                for wd in l.split(" "):
                    k = smooth((t - t0 - reveal * wi / max(1, n)) / 0.25) * out
                    ww = d.textlength(wd + " ", font=F_CAP)
                    if k > 0.01:
                        sd.text((x, y0 + j * 72), wd, font=F_CAP, fill=(0, 0, 0, int(230 * k)))
                        d.text((x, y0 + j * 72), wd, font=F_CAP, fill=(255, 255, 255, int(255 * k)))
                    x += ww; wi += 1
    # stat block
    st = spec["stat"](t) if spec.get("stat") else None
    if st:
        label, value, sub = st
        x0 = 56; y0 = H * 0.425
        fv = F_VAL if d.textlength(value, font=F_VAL) < W - 160 else F_VAL_S
        for dr, fill in ((sd, (0, 0, 0, 220)), (d, (255, 255, 255, 235))):
            spaced(dr, (x0, y0), label, F_LAB, fill, 5.0)
            dr.text((x0, y0 + 30), value, font=fv, fill=(255, 255, 255, 255) if fill[0] else (0, 0, 0, 220))
            if sub: spaced(dr, (x0, y0 + 30 + (112 if fv is F_VAL else 86)), sub, F_SUB, fill, 3.0)
    # end card
    e = spec.get("end")
    if e and t >= e[0]:
        k = smooth((t - e[0]) / 0.6)
        ch, tag = e[1], e[2]
        for dr, fl in ((sd, (0, 0, 0, int(220 * k))), (d, (255, 255, 255, int(255 * k)))):
            dr.text((W / 2 - d.textlength(ch, font=F_END) / 2, H * 0.70), ch, font=F_END, fill=fl)
            dr.text((W / 2 - d.textlength(tag, font=F_END2) / 2, H * 0.70 + 104), tag, font=F_END2, fill=(fl[0], fl[1], fl[2], fl[3]) if fl[0] == 0 else (255, 200, 120, fl[3]))
    # tiny disclaimer
    if spec.get("tag"):
        d.text((56, H - 86), spec["tag"], font=F_TAG, fill=(255, 255, 255, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    base = img.convert("RGBA")
    base.alpha_composite(sh)
    base.alpha_composite(lay)
    return base.convert("RGB")
