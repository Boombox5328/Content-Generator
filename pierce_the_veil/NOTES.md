# NOTES

## Fact flags (nothing silently changed)
- *Selfish Machines*: sources disagree on June 21 vs 22, 2010. Copy says only "June 2010" (and the film shows no release day).
- **Petco Park, Sept 12, 2026**: confirmed sold out, but no recap confirming the show went ahead as planned. Verify before posting.
- Beat 4 map shows no city names; the route is decorative, not a factual itinerary.
- Beat 9 billboards use only brief facts (Madison Square Garden, Red Rocks, Kia Forum / 3 nights). A fourth generic "SOLD OUT" billboard is decoration.
- "5 albums" on the end card = A Flair for the Dramatic, Selfish Machines, Collide with the Sky, Misadventures, The Jaws of Life.

## Sensitive content
- 2017 is a single neutral card ("2017: The band goes dark."), the drummer figure fades, the riser stays empty. Nothing else is shown or implied.
- Beat 8 uses one generic "new drummer" figure; it does not separately depict the record vs. tour drummers.

## Creative decisions
- Hook counter runs 2026 → 2004 during the dive (so the loop's first/last frame both read 2026), then ticks forward. (Approved.)
- Garage + stadium "hometown" is built at both ends of the road; beat 10 reverses beat 1's dive so the last frame matches frame 1. The 3D scene matches; the end-card text overlays the final frames.
- Figures are faceless blocky silhouettes with generic hair/clothes; instruments only. No logos, no album art (monoliths are abstract). The phone shows a generic play icon.
- Captions render in uppercase with a word-by-word pop and a highlighted keyword.
- Safe zones: nothing above y=220 / below y=1540 / right of x=960 in the HUD (3D billboards are in-world scenery).

## Render
`node render.js --from 0 --to 75 --workers 4 --out out/ptv_history_reel.mp4`
ffmpeg (inside render.js): `-f image2pipe -framerate 30 -vcodec png -i - -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart -an`
