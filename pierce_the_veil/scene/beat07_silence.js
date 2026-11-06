// BEAT 7 · 43–50 s · 2017–2022 SILENCE — neutral: lights dim, one figure fades out, empty drum riser, fog thickens.
import { THREE, V, smooth, clamp, orbit, dolly } from './common.js';
import { makeBand } from './figures.js';
import { makeStage } from './props.js';
import { PAL, mixPal } from './world.js';

const Z0 = -1050; let S;
const THICK = { ...PAL.grey, fogNear: 4, fogFar: 85, sunI: 0.3, hemiI: 0.7 };
export const beat = {
  id: 'silence', start: 43, end: 50, accent: '#9fb0c8', focus: V(0, 2, Z0),
  palette: (u) => mixPal(PAL.grey, THICK, smooth(0.1, 0.9, u)),
  cards: [{ t0: 43.4, t1: 49.8, text: '2017: The band *goes dark.*' }],
  counter: [[43, 2016], [43.6, 2017], [50, 2022]],
  shots: [
    { t0: 43, t1: 45.5, cam: (u) => dolly(V(-12, 6, Z0 + 58), V(-5, 5.5, Z0 + 44), V(0, 7, Z0), V(0, 7, Z0), u) },
    { t0: 45.5, t1: 47.6, cam: (u) => dolly(V(9, 7, Z0 + 24), V(4, 6.5, Z0 + 18), V(0, 5, Z0 - 5), V(0, 5.2, Z0 - 5), u) },
    { t0: 47.6, t1: 50, cam: (u) => dolly(V(0, 5.5, Z0 + 20), V(0, 16, Z0 + 52), V(0, 5, Z0 - 5), V(0, 4, Z0 - 5), u) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    S.stage = makeStage({ w: 44, d: 22, accent: 0x4a5670, lights: 5 }); S.stage.position.set(0, 0, Z0); g.add(S.stage);
    S.band = makeBand({ scale: 1.8, kitY: 4.2, kitZ: -5.5, show: { newdrummer: false } }); S.band.group.position.set(0, 2.2, Z0 + 2); g.add(S.band.group);
  },
  update(t) {
    const dim = 1 - smooth(43.5, 49, t); const flick = t > 44 && t < 47 ? 1 - 0.35 * (Math.sin(t * 40) > 0.6 ? 1 : 0) : 1;
    S.stage.userData.set(Math.max(0, dim * flick) * 0.8 + 0.0, t);
    S.band.update(t, t < 44.3 ? 'play' : 'idle', 0.6);
    S.band.figs.mike.setOpacity(1 - smooth(45.6, 47.2, t)); S.band.figs.mike.root.visible = t < 47.3;   // the drum riser stays, empty
    S.band.figs.vic.head.rotation.x = 0.5; S.band.figs.tony.head.rotation.x = 0.5; S.band.figs.jaime.head.rotation.x = 0.5;
  },
};
