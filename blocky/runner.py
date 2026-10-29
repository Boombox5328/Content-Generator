"""Parallel frame renderer + ffmpeg encode shared by the blocky videos."""
import os, sys, subprocess
import numpy as np
from PIL import Image
import multiprocessing as mp

_FRAME = None


def _work(i):
    return _FRAME(i).tobytes()


def render_video(frame_fn, n, fps, out, audio, size=(1080, 1920)):
    global _FRAME
    _FRAME = frame_fn
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-",
           "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.Pool(os.cpu_count()) as pool:
        for k, b in enumerate(pool.imap(_work, range(n), chunksize=3)):
            p.stdin.write(b)
            if k % 150 == 0: print("frame", k, "/", n, flush=True)
    p.stdin.close(); p.wait()
    print("done", out)


def preview(frame_fn, fps, out_dir, times, scale=0.5):
    os.makedirs(out_dir, exist_ok=True)
    for t in times:
        im = frame_fn(int(round(t * fps)))
        im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS).save(f"{out_dir}/t{t:06.2f}.png")
