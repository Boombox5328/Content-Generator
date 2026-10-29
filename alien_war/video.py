import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
import numpy as np
from PIL import Image
import spec, scenes
from ui import overlay, smooth

OVER = dict(title=spec.TITLE, caps=spec.CAPS, stat=spec.stat, end=spec.END, tag=spec.TAG)
CUTS = [7, 15, 24, 33, 42, 52]


def frame(i):
    t = i / spec.FPS
    img = scenes.render3d(t)
    # quick dip-to-white punch on each cut
    for c in CUTS:
        if 0 <= t - c < 0.35:
            k = 1 - smooth((t - c) / 0.35)
            img = Image.blend(img, Image.new("RGB", img.size, (255, 255, 255)), 0.45 * k)
    if t < 0.4: img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, smooth(t / 0.4))
    if t > spec.DUR - 0.6: img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, smooth((spec.DUR - t) / 0.6))
    return overlay(img, t, OVER)
