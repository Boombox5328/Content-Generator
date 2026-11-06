// BEAT 1 · 0–3 s · HOOK — stadium lights blaze, camera dives down to a tiny garage.
import { THREE, clamp } from './common.js';
import { animateHometown, divePose } from './hometown.js';

export const beat = {
  id: 'hook', start: 0, end: 3, accent: '#ffd27a',
  cards: [{ t0: 0.35, t1: 2.95, text: 'Garage → sold-out\nstadium. 20 years.' }],
  // the counter rewinds to where it all began while we dive in (it then ticks forward for the rest of the film)
  counter: [[0, 2026], [0.9, 2026], [3, 2004]],
  update(t, world) {
    const u = t / 3;
    const flare = 1 + 0.8 * Math.exp(-(((t - 0.7) / 0.28) ** 2));   // lights "blaze"
    animateHometown(world.hometownA, t, flare);
    const { pos, target, roll } = divePose(u);
    world.camera.position.copy(pos);
    world.camera.lookAt(target);
    world.camera.rotateZ(roll);
  },
};
