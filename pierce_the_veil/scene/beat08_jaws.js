// BEAT 8 · 50–58 s · 2022–2023 THE JAWS OF LIFE — neon-green monolith cracks through the fog; lights snap back on.
import { THREE, V, flat, box, rng, smooth, clamp, orbit, dolly } from './common.js';
import { makeBand } from './figures.js';
import { makeStage, makeMonolith } from './props.js';
import { PAL, mixPal } from './world.js';

const ZS = -1190, ZM = -1232, SNAP = 54.4; let S;
const GREEN = { ...PAL.fog, top: 0x03140c, hor: 0x1f8a52, ground: 0x1d3a2a, hemiSky: 0xa8ffd0, hemiGround: 0x0e2418, sunColor: 0x7aff9a, sunI: 1.6, hemiI: 1.5, fogNear: 30, fogFar: 520, stars: 0.8, road: 0x14181a };
export const beat = {
  id: 'jaws', start: 50, end: 58, accent: '#39ff88', focus: V(0, 4, ZS),
  palette: (u) => { const t = 50 + u * 8; return mixPal(PAL.fog, GREEN, smooth(SNAP - 0.15, SNAP + 0.2, t)); },
  cards: [{ t0: 50.5, t1: 57.8, text: 'Seven years later: *back.*' }],
  counter: [[50, 2022], [51, 2022], [58, 2023]],
  shots: [
    { t0: 50, t1: 52.3, cam: (u) => dolly(V(0, 3, -1120), V(0, 3.4, -1142), V(0, 12, ZM), V(0, 16, ZM), u) },
    { t0: 52.3, t1: 54.4, cam: (u) => dolly(V(-16, 2, ZS + 16), V(-9, 4, ZS + 4), V(0, 18, ZM), V(0, 40, ZM), u) },
    { t0: 54.4, t1: 56.2, cam: (u) => orbit(V(0, 0, ZS), 34, 7, -0.9, 0.5, u, 6) },
    { t0: 56.2, t1: 58, cam: (u) => dolly(V(0, 10, ZS + 62), V(0, 30, ZS + 80), V(0, 24, ZM), V(0, 34, ZM), u) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    S.stage = makeStage({ w: 40, d: 22, accent: 0x39ff88, lights: 5 }); S.stage.position.set(0, 0, ZS); g.add(S.stage);
    S.band = makeBand({ scale: 1.8, kitY: 4.2, kitZ: -5.5, show: { mike: false, newdrummer: true } }); S.band.group.position.set(0, 2.2, ZS + 2); g.add(S.band.group);
    S.mono = makeMonolith({ color: 0x39ff88, height: 78, seed: 23, dark: true, edge: 0x39ff88 }); S.mono.group.position.set(0, 0, ZM); g.add(S.mono.group);
    // glowing ground cracks radiating from the monolith
    const R = rng(4), ng = new THREE.MeshBasicMaterial({ color: 0x39ff88, fog: false }); S.cracks = [];
    for (let i = 0; i < 16; i++) { const a = (i / 16) * 6.283 + R() * 0.2, L = 14 + R() * 30, c = box(L, 0.15, 0.5 + R() * 0.5, ng, 0, 0.12, 0); c.userData = { a, L }; c.castShadow = false; g.add(c); S.cracks.push(c); }
  },
  update(t) {
    const on = smooth(SNAP - 0.1, SNAP + 0.15, t), flash = on * (1 - smooth(SNAP + 0.15, SNAP + 0.7, t));
    S.stage.userData.set(on > 0 ? 0.35 + 0.65 * on + flash * 0.6 : 0.0, t);
    S.band.update(t, 'play', 0.4 + on);
    const grow = smooth(51.6, 54.2, t); S.mono.setGrow(grow); S.mono.update(t);
    S.mono.group.position.set((Math.random() * 0 + Math.sin(t * 90) * 0.25 * (1 - on) * (grow > 0 && grow < 1 ? 1 : 0)), 0, ZM);
    const ck = smooth(50.6, 53.4, t); S.cracks.forEach((c) => { const d = c.userData, L = Math.max(0.01, d.L * ck); c.scale.x = Math.max(0.001, ck); c.position.set(Math.cos(d.a) * (d.L * ck / 2 + 4), 0.12, ZM + Math.sin(d.a) * (d.L * ck / 2 + 4)); c.rotation.y = -d.a; });
  },
};
