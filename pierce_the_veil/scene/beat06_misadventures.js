// BEAT 6 · 36–43 s · 2016 MISADVENTURES — orange monolith, the tallest yet (shown against the earlier three).
import { THREE, V, flat, box, rng, smooth, clamp, orbit, dolly } from './common.js';
import { makeBand, makeCrowd } from './figures.js';
import { makeMonolith, makeStage } from './props.js';
import { PAL } from './world.js';

const Z = -850; let S;
export const beat = {
  id: 'misadventures', start: 36, end: 43, accent: '#ff9a2e', focus: V(40, 0, Z - 10),
  palette: () => PAL.sunset,
  cards: [{ t0: 36.5, t1: 42.6, text: '*#4.* Career high.' }],
  counter: [[36, 2012], [38.2, 2016], [43, 2016]],
  shots: [
    { t0: 36, t1: 38.6, cam: (u) => dolly(V(5, 3, Z + 100), V(10, 5, Z + 55), V(40, 22, Z + 10), V(42, 30, Z - 10), u) },
    { t0: 38.6, t1: 41, cam: (u) => dolly(V(22, 6, Z + 16), V(26, 80, Z + 10), V(40, 8, Z - 10), V(40, 92, Z - 10), u) },
    { t0: 41, t1: 43, cam: (u) => dolly(V(-14, 40, Z + 50), V(-30, 70, Z + 90), V(40, 40, Z - 10), V(40, 40, Z - 10), u) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = { monos: [] };
    const defs = [[0xd62839, 32, 1, Z + 70], [0x1fb6c1, 44, 2, Z + 42], [0x4fb4ff, 60, 3, Z + 14]];
    defs.forEach(([c, h, sd, z]) => { const m = makeMonolith({ color: c, height: h, seed: sd }); m.group.position.set(40, 0, z); g.add(m.group); S.monos.push(m); });
    const orange = makeMonolith({ color: 0xff8a1f, height: 96, seed: 16, edge: 0xfff1d0 }); orange.group.position.set(40, 0, Z - 18); g.add(orange.group); S.orange = orange;
    const band = makeBand({ scale: 1.7, kitY: 0.6, kitZ: -6, show: { newdrummer: false } }); band.group.position.set(14, 0.6, Z + 2); g.add(band.group); band.group.rotation.y = 0.3; S.band = band;
    g.add(box(34, 0.6, 22, flat(0x4a3040), 14, 0.3, Z - 2));
    S.crowd = makeCrowd({ count: 160, seed: 5, scale: 1.5, place: (R) => ({ x: -6 + (R() - 0.5) * 34, z: Z + 24 + R() * 22, yaw: Math.PI + 0.3 }) }); g.add(S.crowd.group);
    // rising embers
    const N = 120, R = rng(2); S.em = new THREE.InstancedMesh(new THREE.BoxGeometry(0.4, 0.4, 0.4), new THREE.MeshBasicMaterial({ color: 0xffc060, fog: false }), N); S.em.frustumCulled = false; g.add(S.em);
    S.ev = Array.from({ length: N }, () => ({ x: 40 + (R() - 0.5) * 30, z: Z - 18 + (R() - 0.5) * 30, s: 4 + R() * 9, o: R() * 100 }));
  },
  update(t) {
    S.monos.forEach((m, i) => { m.setGrow(1); m.update(t + i); });
    S.orange.setGrow(smooth(36.4, 39.4, t)); S.orange.update(t);
    S.band.update(t, 'play', 1.1); S.crowd.update(t, 0.8);
    const m = new THREE.Matrix4(), sc = new THREE.Vector3(1, 1, 1), q = new THREE.Quaternion();
    S.ev.forEach((e, i) => { m.compose(new THREE.Vector3(e.x, ((t * e.s + e.o) % 70), e.z), q, sc); S.em.setMatrixAt(i, m); }); S.em.instanceMatrix.needsUpdate = true;
  },
};
