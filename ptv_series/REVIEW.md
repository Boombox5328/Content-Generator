# REVIEW — Part 1 (self-review loop)

Method: draft render at 1× (`out/part1_draft.mp4`), contact sheet at 1 fps (`out/contact_part1.png`), programmatic camera/hold check (`node check_cams.js`), then fixes, then final 2× render.

## Round 1 (draft) — findings
| Check | Result |
|---|---|
| Faceted triangles visible | PASS (all sets; characters 830–940 tris) |
| Rim light separating subject | PASS in garage/studio/club/festival; WEAK on the dark studio figures in 3a |
| Ambient occlusion at contacts | PASS (floors under kits/amps/crowd) |
| Bloom only on lights | PASS (selective bloom list = emissive meshes only) |
| Each set reads without text | PASS (Petco skyline, garage, studio with rain window, festival, club) |
| Text off the subject, readable, ≥3.5 s | PASS: every card 3.5–4.0 s, lower third on gradient panel, ≤6 words |
| Year tag matches the beat | PASS: 2026, 2004, 2004–06, 2007, 2008, 2010 (from the same shot table) |
| Shot under 3.5 s | FAIL (intentional): 1a/1b are 2 s each (hook match cut, see NOTES.md #1). All other shots 3.5–5 s |
| Move with no hold | PASS: hold-speed 0 for the last 1 s of every shot (`out/camcheck.json`) |
| Rotation ≤ 15°/s | PASS after fix: 2b was 18.9°/s → 12.9°/s. Max now 12.9°/s |

## Failures found and fixed for the final render
1. **2c sign cropped** ("ERCE THE VE") → wider FOV 52 and pulled back.
2. **Studio too dark / figures murky (3a/3b)** → key 70→120 cd, added warm + blue control-room fills.
3. **Lower third nearly black in 4a/4b** (desk + window frame) → control-room fill light lifts desk and floor.
4. **Club crowd/floor a black mass (5b)** → lighter floor, teal front fill, red front fill.

## Not fixed / open (please decide)
- Hook shots (2 s) break the 3.5 s minimum by necessity.
- Ensemble shots fill 25–35 % of the frame, not 40 %.
- Final-render re-check: contact sheet of `out/ptv_part1_garage_years.mp4` is listed below once rendered.

## Round 2 (final 2× render, `out/ptv_part1_garage_years.mp4`) — contact sheet re-checked
| Check | Result |
|---|---|
| 2c sign cropped | FIXED — "BEFORE TODAY" → "PIERCE THE VEIL" fully readable |
| Studio too dark (3a/3b) | IMPROVED — figures and rain window read; still moody by design |
| Club black mass (5b) | IMPROVED — crowd now rim-lit teal/red, stage and monument visible |
| Faceted / rim / AO / bloom-on-lights / each set reads / card timing / year tags / holds / ≤15°/s | PASS (unchanged from round 1) |
| **4a/4b lower third (desk + window frame) still mostly black** | **OPEN** — the control-room fill did not lift it enough. Fix = move/raise the camera or drop the desk from these two shots (≈3.7 h re-render, so not done without your OK). |
| Hook shots 2 s (< 3.5 s) | OPEN by design (NOTES.md #1) |
| Ensemble shots 25–35 % of frame | OPEN (NOTES.md #6) |
