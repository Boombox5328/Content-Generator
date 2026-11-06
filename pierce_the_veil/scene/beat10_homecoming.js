// BEAT 10 · 68–75 s · 2026 HOMECOMING — camera pulls back from the garage, reversing the opening dive.
// The last frame matches frame 1 (same cluster, palette, light phase) so the reel loops.
import { THREE, V, ease, clamp } from './common.js';
import { makeFigure, makeGuitar, animateFigure } from './figures.js';
import { animateHometown, divePose } from './hometown.js';
import { ROAD_LEN, PAL } from './world.js';

let S;
const OFF = V(0, 0, -ROAD_LEN);
export const beat = {
  id: 'homecoming', start: 68, end: 75, accent: '#ffd27a', hometown: 'B', focus: V(14, 0, 10 - ROAD_LEN),
  palette: () => PAL.dusk,
  cards: [{ t0: 70.2, t1: 75.4, text: '20 years. *5 albums.* 1 hometown.', cta: 'Which era got you into PTV?', ctaT: 72.4 }],
  counter: [[68, 2025], [69, 2026], [75, 2026]],
  shots: [
    { t0: 68, t1: 70, cam: (u) => ({ pos: V(5 + 7 * u, 3.6, 24 - ROAD_LEN - 3 * u), look: V(14, 3.4, 8 - ROAD_LEN) }) },
    { t0: 70, t1: 75, cam: (u) => { const d = divePose(1 - u); return { pos: d.pos.clone().add(OFF), look: d.target.clone().add(OFF), roll: d.roll }; } },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = { figs: [] };
    [[7, 0x8a2f28, 'long'], [11, 0x1d1d26, 'swoop'], [17, 0x264653, 'beanie'], [21, 0xf1f1f1, 'spike']].forEach(([x, c, st], i) => {
      const f = makeFigure({ scale: 1.6, shirt: c, hair: { style: st, color: 0x1a1a1a, color2: 0x999999 } }); f.root.position.set(x, 0, 12 - ROAD_LEN); g.add(f.root); S.figs.push(f); });
  },
  update(t, world) {
    animateHometown(world.hometownB, t, 1 + 0.8 * Math.exp(-(((t - 0.7) / 0.28) ** 2)));
    S.figs.forEach((f, i) => animateFigure(f, t, i % 2 ? 'cheer' : 'wave', i * 1.1, 1));
    S.figs.forEach((f) => (f.root.visible = t < 72.8));            // gone before the pull-back reaches frame-1 framing
  },
};
