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

## The Long Way Out — stylized 3D-look reel (humanity's expansion into space)

1080×1920, 30 fps, 70 s, built the same way: everything procedural, no assets.
Soft clay-shaded characters (signed-distance shapes lit with a key + rim light), a recurring astronaut family
with an orange-star patch, a "years from now" counter and a "distance from Earth" readout (km → AU → light-years).

```
long_way_out/build.sh    # -> out/the_long_way_out.mp4
```

| file | what |
|---|---|
| `long_way_out/spec.py` | scene timings, on-screen text, counter keyframes, VO copy, channel name |
| `long_way_out/gfx.py` | clay-shaded primitives, planets, starfield, bloom |
| `long_way_out/chars.py` | Ava + descendants, culture portraits |
| `long_way_out/scenes1.py`, `scenes2.py` | the 9 scenes |
| `long_way_out/render.py` | post (bloom, grade, transition punch), HUD/text at full res, parallel encode |
| `long_way_out/audio.py` | piano motif → orchestral swell, era whooshes, espeak voice-over |
| `long_way_out/captions.md` | caption hook, engagement prompt, disclaimer, VO script |

Requires `python3` + `numpy` + `pillow`, `ffmpeg`, `espeak-ng`, Inter font (`/usr/share/fonts/opentype/inter`).

## Blocky 3D reels (no narration, timed captions)

A tiny flat-shaded software 3D engine (`blocky/`) renders Roblox-style block worlds; captions are timed to the on-screen events
(serif title, italic word-by-word captions, small-caps stat readout). Audio is synthesized music + sound effects only, no TTS.

```
alien_war/build.sh              # -> out/what_if_aliens.mp4          (fictional: "What if aliens declared war on Earth?")
long_way_out_blocky/build.sh    # -> out/the_long_way_out_blocky.mp4 (blocky re-do of The Long Way Out)
```

`blocky/engine.py` (3D), `props.py` (people, buildings, ships, explosions), `ui.py` (captions/HUD), `audio.py` (synth + mixer), `runner.py` (parallel encode).
