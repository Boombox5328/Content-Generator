// BEAT 1 · 0–3 s · HOOK — stadium lights blaze, camera dives down to a tiny garage.
import { THREE, V } from './common.js';
import { animateHometown, divePose } from './hometown.js';
import { PAL } from './world.js';

export const beat = {
  id: 'hook', start: 0, end: 3, accent: '#ffd27a', hometown: 'A', focus: V(14, 0, 0),
  palette: () => PAL.dusk,
  cards: [{ t0: 0.35, t1: 2.95, text: 'Garage → *sold-out* stadium. 20 years.' }],
  counter: [[0, 2026], [0.9, 2026], [3, 2004]],   // rewinds while we dive in (so the loop's first/last frames both read 2026)
  shots: [{ t0: 0, t1: 3, cam: (u) => { const d = divePose(u); return { pos: d.pos, look: d.target, roll: d.roll }; } }],
  update(t, world) { animateHometown(world.hometownA, t, 1 + 0.8 * Math.exp(-(((t - 0.7) / 0.28) ** 2))); },
};
