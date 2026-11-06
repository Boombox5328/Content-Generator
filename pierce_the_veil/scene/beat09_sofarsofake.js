// BEAT 9 · 58–68 s · 2025 SO FAR SO FAKE — phone shatters into a particle stream; venue billboards fly past on the road.
import { THREE, V, flat, box, unlit, smooth, clamp, orbit, dolly, rng } from './common.js';
import { makePhone, makeShards, makeBillboard } from './props.js';
import { PAL } from './world.js';

const Z0 = -1340, BURST = 60.0; let S;
const camZ = (t) => Z0 - 5 - Math.max(0, t - 60.6) * 17;
export const beat = {
  id: 'sofarsofake', start: 58, end: 68, accent: '#ff4fd8', focus: V(0, 4, Z0 - 40),
  palette: () => PAL.neon,
  cards: [{ t0: 58.4, t1: 67.7, text: 'A 2023 song. A 2025 *smash.*' }],
  counter: [[58, 2023], [60, 2025], [68, 2025]],
  shots: [
    { t0: 58, t1: 60.6, cam: (u) => dolly(V(-9, 4.5, Z0 + 20), V(-3, 7, Z0 + 11), V(0, 7, Z0), V(0, 7, Z0), u) },
    { t0: 60.6, t1: 64.2, cam: (u, t) => ({ pos: V(Math.sin(u * 2) * 3, 4.5 + u * 1.5, camZ(t)), look: V(Math.sin(u * 2) * -4, 5, camZ(t) - 40) }) },
    { t0: 64.2, t1: 68, cam: (u, t) => ({ pos: V(-14 + u * 28, 11 - u * 4, camZ(t)), look: V(0, 6, camZ(t) - 30), roll: Math.sin(u * 3.14) * 0.12 }) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    S.phone = makePhone(); S.phone.scale.setScalar(2.6); S.phone.position.set(0, 7, Z0); g.add(S.phone);
    S.shards = makeShards(280, 4); g.add(S.shards);
    const bills = [['MADISON SQUARE\nGARDEN', '#4fd5ff', -22, -1392], ['RED ROCKS', '#ff5a6e', 22, -1432], ['KIA FORUM\n3 NIGHTS', '#ffe066', -22, -1472], ['SOLD OUT', '#7dffb0', 22, -1510]];
    bills.forEach(([txt, c, x, z]) => { const b = makeBillboard(txt, c); b.position.set(x, 0, z); b.rotation.y = x < 0 ? 0.5 : -0.5; g.add(b); });
    const ar = new THREE.MeshBasicMaterial({ color: 0xff4fd8, fog: false }), ar2 = new THREE.MeshBasicMaterial({ color: 0x4fd5ff, fog: false });
    for (let i = 0; i < 16; i++) { const z = -1350 - i * 12, m = i % 2 ? ar : ar2; const a = new THREE.Group(); a.add(box(0.5, 9, 0.5, m, -8, 4.5, 0), box(0.5, 9, 0.5, m, 8, 4.5, 0), box(16.5, 0.5, 0.5, m, 0, 9, 0)); a.position.z = z; g.add(a); }
  },
  update(t, world) {
    const tau = t - BURST; S.phone.visible = tau < 0; S.phone.rotation.y = Math.sin(t * 1.6) * 0.5; S.phone.position.y = 7 + Math.sin(t * 2.2) * 0.4;
    S.shards.userData.update(tau, V(0, 7, Z0), camZ(t) - 4);
    world.focus.set(0, 4, camZ(t) - 30);
  },
};
