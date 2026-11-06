// BEAT 4 · 18–26 s · 2008–2010 THE GRIND — tour van crosses a faceted US map; teal monolith.
import { THREE, V, smooth, clamp, orbit, dolly, ease } from './common.js';
import { makeUSMap, makeMonolith, proj } from './props.js';
import { PAL } from './world.js';

const MAP = V(135, 0.4, -380); let S;
const vanP = (t) => clamp((t - 18.6) / (23.4 - 18.6));
export const beat = {
  id: 'grind', start: 18, end: 26, accent: '#1fe0d0', focus: V(135, 0, -380),
  palette: () => PAL.teal,
  cards: [{ t0: 18.4, t1: 25.8, text: 'Warped Tour → *#1* Heatseekers.' }],
  counter: [[18, 2007], [19, 2008], [26, 2010]],
  shots: [
    { t0: 18, t1: 20.4, cam: (u) => dolly(V(135, 90, -250), V(165, 70, -290), V(135, 0, -380), V(135, 0, -385), u) },
    { t0: 20.4, t1: 23.6, cam: (u, t) => { const p = S.van.position.clone().add(MAP); return { pos: p.clone().add(V(16, 15, 24)), look: p.clone().add(V(0, 2, 0)) }; } },
    { t0: 23.6, t1: 26, cam: (u) => orbit(S.monoPos, 62, 24, 0.2, 1.4, u, 18) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    const map = makeUSMap(); map.group.position.copy(MAP); g.add(map.group); S.map = map; S.van = map.van;
    const end = proj(-96.8, 32.8); S.monoPos = MAP.clone().add(end);
    const mono = makeMonolith({ color: 0x1fb6c1, height: 46, seed: 6, edge: 0xdffffa }); mono.group.position.copy(S.monoPos); g.add(mono.group); S.mono = mono;
  },
  update(t, world) {
    S.map.setProgress(ease(vanP(t)) * 0.98 + (vanP(t) > 0 ? 0.0 : 0)); S.map.van.position.y = 3.2 + Math.abs(Math.sin(t * 14)) * 0.15;
    S.map.pins.children.forEach((p, i) => (p.position.y = 4.4 + Math.sin(t * 3 + i) * 0.4));
    const k = smooth(23.4, 25.2, t); S.mono.setGrow(k); S.mono.update(t);
    world.focus.copy(MAP).add(S.van.position);
  },
};
