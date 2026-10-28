# Content-Generator

## The Last Light — 16-bit pixel-art reel (heat death of the universe)

1080×1920, 24 fps, 64 s. Everything is procedural: no assets.

```
last_light/build.sh      # -> out/the_last_light.mp4
```

| file | what |
|---|---|
| `last_light/spec.py` | timings, counter/zoom keyframes, VO copy, channel name |
| `last_light/render.py` | 270×480 pixel canvas → ordered-dither + limited palette → ffmpeg upscales 4× |
| `last_light/audio.py` | chiptune score that slows, drops pitch and loses instruments (drums → arps → lead → bass → one drone → 2 s silence), SFX, espeak-ng voice-over |
| `last_light/captions.md` | caption hook, engagement prompt, accuracy note, VO script |

Requires `python3` + `numpy` + `pillow`, `ffmpeg`, `espeak-ng`.
Set your channel name via `CHANNEL` in `spec.py`.
