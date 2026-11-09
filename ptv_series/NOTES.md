# NOTES — PTV series (Parts 1–3)

## Status
Step 3 of the workflow: shared pipeline + character/prop kit are built, and **one full-quality 1080×1920 style frame per Part 1 beat** is rendered in `out/` (`still_hookA/hookB/b2/b3/b4/b5a/b5b.png`, contact sheet `out/STYLE_FRAMES_part1.png`).
**Waiting for approval before animating Part 1.** Nothing else (timeline, camera moves, transitions, MP4s, REVIEW.md, Parts 2–3 sets) is built yet.
The earlier blocky v1 reel in `../pierce_the_veil/` is superseded and left untouched.

## Pipeline (how each requirement is met)
- Three.js 0.160 + pmndrs `postprocessing` + `n8ao`. Deterministic: every frame is `render(t)`; nothing runs on a real-time clock.
- Tone mapping: **ACES Filmic**, applied by `ToneMappingEffect` inside the composer (the composer bypasses `renderer.toneMapping`). sRGB output. PCFSoft shadows, **4096** shadow map on the key light.
- IBL: gradient-sky environment per set → PMREM → `scene.environment`.
- Lighting: every set has a warm KEY (shadow-casting), cool RIM from behind the subject, dim FILL (+ emissive practicals). `engine/pipeline.js: makeRig`.
- Post: N8AO ambient occlusion → SelectiveBloom (only emissive "glow" meshes registered by the set) → DOF (hero shots only) → per-era grade + film grain 0.03 + vignette (+ heat haze for the Warped Tour grade).
- Atmosphere: exponential fog per set, low-poly cloud meshes, light shafts (custom additive cone shader `engine/shafts.js`, not pmndrs GodRaysEffect, so each lamp/window/stage light gets its own controllable shaft).
- Anti-aliasing: render at 2160×3840 (DPR 2), downscale with ffmpeg lanczos (`render.js`).
- Style frames take ~10 s each on CPU (SwiftShader); a 60 s part at 30 fps is ~1800 frames ≈ 5 h single-process, so Part 1 will be rendered with parallel workers.

## Characters (`kit/human.js`)
Procedural jointed humanoids, ~6 heads (1.8 m), faceted with vertex-colour gradients, **830–940 triangles** each (spec 600–1500). Faceless (no features); silhouettes: Vic long dark hair + guitar + centre mic; Tony messy spikes + low-slung lead guitar, stage left; Jaime snapback + bass, stage right; Mike behind the kit. Animations: idle weight-shift, strum + head-bob, sing, drum, headbang, cheer. Crowd = 3 instanced variants (arms up / fist pump / phone raised) with random colours and bounce timing.
CC0 packs (Quaternius/Kenney) were **not used**: no asset access in this environment, so everything is procedural to the spec.

## Brief conflicts I had to resolve (please confirm)
1. **Hook is 4 s, but shots must be ≥ 3.5 s and a card must appear 1 s in and hold ≥ 3.5 s.** Impossible together with a match cut. Plan: hook = 2 shots of 2 s (match cut), card appears at 0.5 s and holds to 4.0 s (3.5 s). Same for Parts 2 and 3 hooks (single 4 s shot there, card 0.5–4.0).
2. **"Every move eases, then HOLDS ≥ 1 s"** → in the 2 s hook shots that means 1 s move + 1 s hold.
3. **Year tag "changes only on a beat cut" but the hook has two eras** (Petco 2026 → garage 2004). The tag table has two hook rows, 2026 then 2004, both changing on a cut. Tags come from the beat table row: `2026 · 2004 · 2004–06 · 2007 · 2007 · 2008 · 2010`.
4. **Part 1 beat 5 spans 2008–2010 and has two different sets**, so I split it into two beats (Warped Tour 2008, club 2010) of ~10 s each. Beat 5 only had one card in the brief ("#1 on Heatseekers."), so I **added a card for the 2008 half: "A full Warped Tour run."** (uses only a given fact; the brief's "Vans" brand is dropped from on-screen copy).
5. **"Door half open"** – the door bottom edge sits at 2.0 m so standing figures remain visible under it.
6. **Subject ≥ 40 % of frame on hero shots**: ensemble/venue shots (garage, club, festival) can't reach 40 % in portrait with the text-safe lower third; subjects there are ~25–35 %. Tell me if you want tighter framing (it crops sets).
7. Part 2/3 run time is "about 60 s" in the brief but the beat durations (4 + 4×12 …) land at ~52–57 s; I'll pad to ~60 s with holds on the end cards unless you prefer otherwise.

## Fact flags (nothing changed silently)
- *Selfish Machines*: sources disagree on June 21 vs 22, 2010 → copy only says "2010" / "#1 on Heatseekers".
- **Petco Park, Sept 12, 2026**: sold out is confirmed, but I found no recap that the show happened as planned. Verify before posting.
- Part 2 card "December 2017: a step away." and the covered-kit visual are the only mention of 2017; nothing else depicted.
- Part 3 drummer is a backlit, unspecified silhouette (per brief); no named drummer is depicted.
- The garage's band-name board shows "BEFORE TODAY" / "PIERCE THE VEIL" as in-world lettering (not a logo). Posters and monuments are original abstract art; no album art.
