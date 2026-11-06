// BEAT 3 · 10–18 s · 2007 A FLAIR FOR THE DRAMATIC — red monolith rises; two figures become four.
import { THREE, V, flat, box, smooth, clamp, orbit, dolly } from './common.js';
import { makeBand } from './figures.js';
import { makeMonolith, makeMilestone } from './props.js';
import { PAL } from './world.js';

const Z = -190; let S;
export const beat = {
  id: 'flair', start: 10, end: 18, accent: '#ff5a6e', focus: V(12, 0, Z),
  palette: () => PAL.red,
  cards: [{ t0: 10.5, t1: 14.1, text: 'Two *brothers.*' }, { t0: 14.1, t1: 17.9, text: 'Then *four.*' }],
  counter: [[10, 2006], [10.5, 2007], [18, 2007]],
  shots: [
    { t0: 10, t1: 12.5, cam: (u) => dolly(V(5, 2.2, Z + 42), V(7, 4, Z + 22), V(-24, 8, Z - 15), V(-24, 24, Z - 15), u) },
    { t0: 12.5, t1: 15, cam: (u) => orbit(V(12, 0, Z), 17, 4.5, -0.9, 0.35, u, 3.2) },
    { t0: 15, t1: 18, cam: (u) => dolly(V(12, 5, Z + 26), V(34, 17, Z + 40), V(12, 4, Z - 4), V(-4, 16, Z - 12), u) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    g.add(box(34, 0.6, 24, flat(0x3a2f45), 12, 0.3, Z - 2));
    const band = makeBand({ scale: 1.6, kitY: 0.6, kitZ: -6.5, show: { tony: false, jaime: false, newdrummer: false } });
    band.group.position.set(12, 0.6, Z + 2); g.add(band.group); S.band = band;
    const mono = makeMonolith({ color: 0xd62839, height: 36, seed: 3 }); mono.group.position.set(-24, 0, Z - 15); g.add(mono.group); S.mono = mono;
    const ms = makeMilestone(2007, '#ff7a8a'); ms.position.set(8, 0, Z + 36); g.add(ms);
  },
  update(t) {
    const k = smooth(10.4, 13.4, t); S.mono.setGrow(k); S.mono.update(t); S.mono.group.position.y = (1 - k) * -1;
    const join = (n, t0) => { const f = S.band.figs[n], a = clamp((t - t0) / 0.45); f.root.visible = a > 0; f.root.scale.setScalar(f.S * (a < 1 ? (0.4 + 0.6 * a + Math.sin(a * Math.PI) * 0.3) : 1)); };
    join('tony', 14.1); join('jaime', 14.5);
    S.band.update(t, 'play', 1);
  },
};
