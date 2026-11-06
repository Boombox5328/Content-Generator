// BEAT 5 · 26–36 s · 2011–2012 BREAKOUT — sky-blue monolith launches upward; the crowd grows.
import { THREE, V, flat, rng, smooth, clamp, orbit, dolly } from './common.js';
import { makeBand, makeCrowd } from './figures.js';
import { makeStage, makeMonolith, makeBeamGeo } from './props.js';
import { PAL } from './world.js';

const Z0 = -640; let S;
const LAUNCH = 30.2;
export const beat = {
  id: 'breakout', start: 26, end: 36, accent: '#2fa4ff', focus: V(0, 0, Z0 + 30),
  palette: () => PAL.sky,
  cards: [{ t0: 26.4, t1: 31.8, text: '*#12* on the Billboard 200.' }],
  counter: [[26, 2010], [27, 2011], [33, 2012], [36, 2012]],
  shots: [
    { t0: 26, t1: 28.6, cam: (u) => dolly(V(-26, 3.5, Z0 + 92), V(-12, 6, Z0 + 76), V(0, 8, Z0), V(0, 10, Z0 - 5), u) },
    { t0: 28.6, t1: 31, cam: (u) => orbit(V(0, 2, Z0 + 18), 36, 9, 1.0, 0.1, u, 7) },
    { t0: 31, t1: 33.6, cam: (u, t) => ({ pos: V(10, 6 + 22 * u, Z0 + 55 - 10 * u), look: V(0, 20 + S.mono.group.position.y * 0.7, Z0 - 28) }) },
    { t0: 33.6, t1: 36, cam: (u) => dolly(V(-30, 40, Z0 + 95), V(24, 60, Z0 + 70), V(0, 30, Z0 + 10), V(0, 70, Z0 - 30), u) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    const stage = makeStage({ w: 46, d: 22, accent: 0x4fb4ff, lights: 5 }); stage.position.set(0, 0, Z0); g.add(stage); S.stage = stage;
    const band = makeBand({ scale: 1.9, kitY: 4.2, kitZ: -5, show: { newdrummer: false } }); band.group.position.set(0, 2.2, Z0 + 2); g.add(band.group); S.band = band;
    const mono = makeMonolith({ color: 0x4fb4ff, height: 52, seed: 9, edge: 0xffffff }); mono.group.position.set(0, 0, Z0 - 34); g.add(mono.group); S.mono = mono;
    S.crowd = makeCrowd({ count: 420, seed: 31, scale: 1.6, y: 0, place: (R, i) => ({ x: (R() - 0.5) * 70, z: Z0 + 18 + R() * 48, yaw: Math.PI + (R() - 0.5) * 0.4 }),
      appear: (i, R) => 26.4 + Math.pow(i / 420, 0.8) * 5.5 });
    g.add(S.crowd.group);
    const tg = makeBeamGeo(120, 7), tm = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false, color: new THREE.Color(0x9fd8ff).multiplyScalar(0.8) });
    S.trail = new THREE.Mesh(tg, tm); S.trail.rotation.x = 0; g.add(S.trail);
  },
  update(t, world) {
    S.stage.userData.set(0.55 + 0.45 * Math.sin(t * 2) ** 2, t);
    S.band.update(t, 'play', 1.2); S.crowd.update(t, 0.6 + 0.4 * smooth(26, 33, t));
    const grow = smooth(27, 29.6, t), tau = Math.max(0, t - LAUNCH);
    S.mono.setGrow(grow); S.mono.update(t);
    S.mono.group.position.y = 0.5 * 26 * tau * tau * 0.55;                      // accelerating launch
    S.trail.visible = tau > 0; S.trail.position.set(0, S.mono.group.position.y + 4, Z0 - 34); S.trail.scale.set(1.4, Math.min(1, tau / 1.2) * 1.2, 1.4);
    S.mono.group.position.x = 0; if (tau > 0) S.mono.group.rotation.y = tau * 0.6;
    S.mono.group.visible = S.mono.group.position.y < 900;
  },
};
