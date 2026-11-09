// Suburban San Diego garage at night. Faces +z. Interior x∈[-3.4,3.4], z∈[-6.5,0].
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube, lerp, clamp, smooth } from '../engine/lowpoly.js';
import { makeRig } from '../engine/pipeline.js';
import { makeShaft } from '../engine/shafts.js';
import { makeSky } from '../engine/sky.js';
import { makeHuman, pose, BAND } from '../kit/human.js';
import { makeGuitar, makeMicStand, makeDrumKit, makeAmpStack } from '../kit/instruments.js';
import { lapSiding, palm, streetLamp, stringLights, poster, pegboard, crate } from '../kit/props.js';
import { textTexture } from '../engine/textures.js';

const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };

export function makeGarage() {
  const group = new THREE.Group(), glow = [], R = rng(17);
  const wallC = [0xb9b4a8, 0x6a6660];

  // ---------- shell ----------
  const L = new THREE.Group(); group.add(L);
  put(L, bevelBox(8.2, 0.12, 7.2, 0.02, { top: 0x6e6c70, bottom: 0x3c3b40, jitter: 0.07, seed: 3 }), 0, -0.06, -3.4);                // slab
  put(L, bevelBox(0.12, 3.6, 7.2, 0.02, { top: 0x7a766e, bottom: 0x4a4640, seed: 4 }), -3.5, 1.8, -3.4); put(L, bevelBox(0.12, 3.6, 7.2, 0.02, { top: 0x7a766e, bottom: 0x4a4640, seed: 5 }), 3.5, 1.8, -3.4);
  put(L, bevelBox(7.2, 3.6, 0.12, 0.02, { top: 0x827e76, bottom: 0x4e4a44, seed: 6 }), 0, 1.8, -6.5);                                  // back wall
  put(L, bevelBox(7.3, 0.1, 7.2, 0.02, { top: 0x3a3630, bottom: 0x2a2622 }), 0, 3.62, -3.4);                                           // ceiling
  for (let i = 0; i < 9; i++) put(L, bevelBox(7.2, 0.18, 0.09, 0.015, { top: 0x5a4a38, bottom: 0x3a2e22, seed: i }), 0, 3.5, -0.4 - i * 0.78);   // rafters
  // facade (front wall with opening 5.0 x 3.0): siding pillars + lintel + gable
  const sid = (w, h, x, y, z, s) => { const g = lapSiding(w, h, 0xc9c3b4, 0x8a8478, 0.2, s); g.position.set(x, y, z); L.add(g); return g; };
  sid(1.5, 3.6, -3.25, 0, 0, 1); sid(1.5, 3.6, 3.25, 0, 0, 2); sid(8.0, 0.8, 0, 3.0, 0, 3);
  const gable = new THREE.Shape([new THREE.Vector2(-4.3, 3.7), new THREE.Vector2(4.3, 3.7), new THREE.Vector2(0, 5.5)]);
  put(L, paint(new THREE.ExtrudeGeometry(gable, { depth: 0.14, bevelEnabled: false }), { top: 0xaaa497, bottom: 0x7a7468, seed: 7 }), 0, 0, -0.07);
  for (const s of [-1, 1]) { const roof = bevelBox(5.6, 0.14, 8.6, 0.02, { top: 0x3a3340, bottom: 0x1e1a24, jitter: 0.1, seed: 8 }); const m = put(L, roof, s * 2.25, 4.65, -3.2); m.rotation.z = -s * 0.38; }
  put(L, bevelBox(9.0, 0.16, 0.16, 0.02, { top: 0xd6d0c4 }), 0, 3.66, 0.1);                                                            // fascia / header
  // sectional door, half open: bottom edge at y=1.95 (two panels visible), rolled into the ceiling track
  const door = new THREE.Group(); L.add(door);
  for (let i = 0; i < 2; i++) { put(door, bevelBox(5.0, 0.5, 0.06, 0.015, { top: 0xe0dccf, bottom: 0xa8a396, seed: 20 + i }), 0, 2.2 + i * 0.52, -0.1); put(door, bevelBox(4.5, 0.3, 0.02, 0.01, { top: 0xcfcabc, bottom: 0x9a9588 }), 0, 2.2 + i * 0.52, -0.065); }
  put(door, bevelBox(0.05, 0.05, 3.0, 0.01, { top: 0x707480 }), -2.55, 3.0, -1.5); put(door, bevelBox(0.05, 0.05, 3.0, 0.01, { top: 0x707480 }), 2.55, 3.0, -1.5);

  // ---------- exterior ----------
  const ex = new THREE.Group(); group.add(ex);
  const gnd = new THREE.Mesh(new THREE.PlaneGeometry(120, 120, 30, 30), lpMat()); const gp = gnd.geometry.attributes.position; for (let i = 0; i < gp.count; i++) gp.setZ(i, (R() - 0.5) * 0.05); gnd.geometry.rotateX(-Math.PI / 2); gnd.geometry = paint(gnd.geometry, { top: 0x1c2a26, bottom: 0x14201e, axis: 'z', seed: 3, jitter: 0.12 }); gnd.position.set(0, -0.14, 0); gnd.receiveShadow = true; ex.add(gnd);
  put(ex, bevelBox(5.8, 0.08, 10.4, 0.02, { top: 0x7a7a82, bottom: 0x484850, axis: 'z', jitter: 0.07, seed: 9 }), 0, -0.04, 5.0);                      // driveway
  put(ex, bevelBox(40, 0.1, 1.6, 0.02, { top: 0x82828a, bottom: 0x56565e, seed: 10 }), 0, -0.04, 11.6);                                               // sidewalk
  put(ex, bevelBox(40, 0.06, 7.5, 0.02, { top: 0x2a2a34, bottom: 0x16161c, seed: 11, jitter: 0.05 }), 0, -0.08, 16.1);                                 // street
  for (let i = -8; i < 9; i++) put(ex, bevelBox(1.4, 0.02, 0.12, 0.005, { top: 0xc8b060 }), i * 2.6, 0.0, 16.1);
  // neighbouring houses (left / right) with a lit window each
  const house = (x, z, w, c0, win) => { const h = new THREE.Group(); h.position.set(x, 0, z); ex.add(h); const s = lapSiding(w, 3.2, c0, 0x4a5066, 0.22, Math.round(x)); h.add(s);
    put(h, bevelBox(w + 0.4, 0.2, 0.5, 0.03, { top: 0x2a2630 }), 0, 3.3, 0.1);
    const gb = new THREE.Shape([new THREE.Vector2(-w / 2 - 0.3, 3.3), new THREE.Vector2(w / 2 + 0.3, 3.3), new THREE.Vector2(0, 4.7)]); put(h, paint(new THREE.ExtrudeGeometry(gb, { depth: 0.1, bevelEnabled: false }), { top: 0x2a2638, bottom: 0x1a1826 }), 0, 0, 0);
    if (win) { const wi = new THREE.Mesh(new THREE.BoxGeometry(1.3, 1.0, 0.05), emissiveMat(win, 2.2)); wi.position.set(w * 0.2, 1.7, 0.05); h.add(wi); glow.push(wi); put(h, bevelBox(1.5, 1.2, 0.04, 0.01, { top: 0x2a2a30 }), w * 0.2, 1.7, 0.02); } return h; };
  house(-9.0, 0.0, 9.0, 0x8c93a8, 0xffcf8a); house(9.6, 0.0, 9.0, 0x9a8f98, null); house(-22, -2, 10, 0x7d8aa0, 0xffe0a8);
  for (const x of [-16, -4.8, 6.2, 17]) house(x, 24, 8, 0x5a6280, null).rotation.y = Math.PI;                                  // across the street
  const palms = [[-8.5, 7.5, 9.5, 2], [7.8, 8.4, 11, 5], [-14, 10, 12, 8], [13, 12, 10.5, 11], [-5.2, 16, 12, 14]];
  palms.forEach(([x, z, h, s]) => { const p = palm(h, s); p.position.set(x, 0, z); p.rotation.y = s; ex.add(p); });
  const lamp = streetLamp(); lamp.position.set(4.6, 0, 10.9); lamp.rotation.y = Math.PI; ex.add(lamp); glow.push(...lamp.userData.glow);
  ex.add(Object.assign(makeShaft([4.6 - 1.4, 6.0, 10.9], [4.0, 0.0, 10.9], { r0: 0.2, r1: 2.2, color: 0xffc880, intensity: 0.28 }), {}));
  const sl = stringLights([-3.9, 3.5, 0.45], [3.9, 3.5, 0.45], { sag: 0.5, count: 16 }); group.add(sl); glow.push(...sl.userData.glow);
  const sl2 = stringLights([-3.9, 3.3, 0.5], [-8.5, 3.1, 0.6], { sag: 0.35, count: 8 }); group.add(sl2); glow.push(...sl2.userData.glow);
  const trash = put(ex, bevelBox(0.7, 1.0, 0.7, 0.06, { top: 0x2a4a3a, bottom: 0x16241e }), 3.6, 0.5, 2.0);

  // ---------- interior dressing ----------
  const I = new THREE.Group(); group.add(I);
  const rug = put(I, paint(new THREE.CylinderGeometry(1.7, 1.7, 0.03, 16), { top: 0x8a2a2a, bottom: 0x4a1414, jitter: 0.1, seed: 4 }), 1.2, 0.015, -4.2);
  const peg = pegboard(2.6, 1.5, 3); peg.position.set(-1.9, 1.8, -6.42); I.add(peg);
  const pals = [['#1b1b2a', '#c0392b', '#e8c872', '#2a7a8a', '#eae0d0'], ['#2a1a1a', '#e8c872', '#8a2a2a', '#d0c0a0'], ['#12202a', '#2a7a8a', '#e87a4a', '#eae0d0']];
  [[1.9, 2.3, 0.8, 1.15], [3.0, 1.9, 0.6, 0.9], [2.45, 0.95, 0.5, 0.7]].forEach(([x, y, w, h], i) => { const p = poster(w, h, 10 + i, pals[i % 3]); p.position.set(x + 0.0, y, -6.42); I.add(p); });
  const side = poster(0.9, 1.3, 31, pals[0]); side.position.set(-3.43, 2.1, -3.2); side.rotation.y = Math.PI / 2; I.add(side);
  put(I, bevelBox(0.7, 0.07, 2.4, 0.015, { top: 0x8a6a44, bottom: 0x5a4028 }), -3.0, 0.92, -4.7);                                               // workbench
  for (const z of [-3.7, -5.7]) put(I, bevelBox(0.08, 0.9, 0.08, 0.01, { top: 0x4a3a2a }), -3.0, 0.45, z);
  [[-3.0, 1.1, -5.2, 0xc0392b], [-3.0, 1.05, -4.5, 0x2a7a8a]].forEach(([x, y, z, c]) => put(I, bevelBox(0.28, 0.22, 0.34, 0.02, { top: c, bottom: new THREE.Color(c).multiplyScalar(0.6).getHex() }), x, y, z));
  [[-2.4, 0.2, -6.0, 0.6, 0.4, 0.5], [-2.9, 0.4, -6.1, 0.55, 0.4, 0.5], [-2.4, 0.6, -6.0, 0.5, 0.35, 0.4]].forEach(([x, y, z, w, h, d], i) => put(I, crate(w, h, d, [0x7a5a36, 0x6a4a2a, 0x8a6a46][i]), x, y, z));
  const couch = new THREE.Group(); couch.position.set(3.0, 0, -1.9); couch.rotation.y = -Math.PI / 2; I.add(couch);
  put(couch, bevelBox(2.0, 0.45, 0.85, 0.08, { top: 0x4a3a4a, bottom: 0x2a2030, seed: 2 }), 0, 0.23, 0); put(couch, bevelBox(2.0, 0.6, 0.22, 0.08, { top: 0x4a3a4a, bottom: 0x2a2030 }), 0, 0.6, -0.4); for (const s of [-1, 1]) put(couch, bevelBox(0.2, 0.55, 0.85, 0.07, { top: 0x54445a }), s * 1.0, 0.4, 0);
  const amp1 = makeAmpStack(); amp1.position.set(-2.55, 0, -5.9); amp1.rotation.y = 0.35; I.add(amp1); const amp2 = makeAmpStack({ glow: 0xff5030 }); amp2.position.set(-0.1, 0, -6.05); amp2.rotation.y = -0.05; amp2.scale.setScalar(0.92); I.add(amp2); glow.push(...amp1.userData.glow, ...amp2.userData.glow);
  const kit = makeDrumKit(); kit.position.set(1.4, 0, -4.4); kit.scale.setScalar(1.12); I.add(kit);
  const mic = makeMicStand(); mic.position.set(-0.85, 0, -2.3); mic.rotation.y = 0.2; I.add(mic);
  const cord = tube([new THREE.Vector3(-2.4, 0.04, -5.6), new THREE.Vector3(-1.2, 0.03, -4.4), new THREE.Vector3(0.2, 0.03, -3.6), new THREE.Vector3(0.9, 0.03, -2.2), new THREE.Vector3(2.0, 0.03, -0.6)], 0.012, 4, false, 0xe8a030); I.add(cord);
  // band-name board (flips BEFORE TODAY -> PIERCE THE VEIL), hung above the kit
  const board = new THREE.Group(); board.position.set(1.4, 2.6, -6.4); I.add(board);
  const faceMat = (txt, bg) => new THREE.MeshStandardMaterial({ map: textTexture(txt, { w: 1024, h: 384, bg, fg: '#f2eadc', size: 200, rough: true }), roughness: 0.85, flatShading: true });
  const flip = new THREE.Group(); board.add(flip); put(flip, bevelBox(2.5, 0.8, 0.05, 0.012, { top: 0x6a5538 }), 0, 0, 0);
  const fA = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.7), faceMat('BEFORE TODAY', '#4a4038')); fA.position.z = 0.03; const fB = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.7), faceMat('PIERCE THE VEIL', '#8a2230')); fB.rotation.x = Math.PI; fB.position.z = -0.03; flip.add(fA, fB); fA.receiveShadow = fB.receiveShadow = true;
  // hanging bulbs
  const bulbs = [];
  [[0.0, 2.75, -2.4], [-1.6, 2.8, -5.0]].forEach(([x, y, z], i) => { const cordT = tube([new THREE.Vector3(x, 3.6, z), new THREE.Vector3(x, y + 0.2, z)], 0.008, 3, false, 0x111111); I.add(cordT);
    const b = new THREE.Mesh(new THREE.IcosahedronGeometry(0.09, 1), emissiveMat(0xffcf90, 9)); b.position.set(x, y, z); I.add(b); glow.push(b); bulbs.push(b);
    put(I, paint(new THREE.CylinderGeometry(0.03, 0.04, 0.1, 6), { top: 0x333333 }), x, y + 0.13, z); });

  // ---------- people ----------
  const figs = {}; const addFig = (id, mode, x, y, z, ry) => { const h = makeHuman({ ...BAND[id] }); h.root.position.set(x, y, z); h.root.rotation.y = ry; I.add(h.root); figs[id] = { h, mode }; return h; };
  const vic = addFig('vic', 'guitar', -0.8, 0, -2.9, 0.12); const g1 = makeGuitar({ body: 0xb3202b }); g1.position.set(-0.02, 0.1, 0.19); g1.rotation.z = 0.5; vic.attach(g1);
  const mike = addFig('mike', 'drum', 1.4, 0.0, -5.3, 0.0);
  put(I, paint(new THREE.CylinderGeometry(0.17, 0.2, 0.06, 10), { top: 0x1a1a20 }), 1.4, 0.5, -5.15);
  mike.root.position.y = 0.0;

  // ---------- lights (key / rim / fill + practicals) ----------
  const rig = makeRig({ key: { type: 'spot', pos: [0, 2.72, -2.35], color: 0xffb468, intensity: 52, angle: 1.05, far: 14 }, rim: { pos: [-3.5, 3.4, -9], color: 0x78a4ff, intensity: 2.6 }, fill: { sky: 0x39508a, ground: 0x1a1218, intensity: 0.5 }, target: new THREE.Vector3(0.2, 0.9, -3.8) });
  group.add(rig);
  const spill = new THREE.SpotLight(0xffa850, 36, 22, 0.75, 0.9, 2); spill.position.set(0, 2.9, -1.2); spill.target.position.set(0, 0, 7); group.add(spill, spill.target);
  const sp2 = new THREE.PointLight(0xffb060, 5, 8, 2); sp2.position.set(0, 3.2, 1.0); group.add(sp2);
  const shaftA = makeShaft([0, 2.7, -2.4], [0.1, 0, -2.5], { r0: 0.08, r1: 0.9, color: 0xffc27a, intensity: 0.38, falloff: 1.2 }); group.add(shaftA);
  const shaftB = makeShaft([0, 2.3, -1.2], [0, 0.05, 6.8], { r0: 1.9, r1: 3.2, color: 0xffa860, intensity: 0.16, falloff: 1.0 }); group.add(shaftB);
  const dust = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xffe3b0, size: 2.4, sizeAttenuation: false, transparent: true, opacity: 0.5, depthWrite: false, toneMapped: false }));
  const DN = 160, dpos = new Float32Array(DN * 3); dust.geometry.setAttribute('position', new THREE.BufferAttribute(dpos, 3)); dust.frustumCulled = false; group.add(dust);
  const sky = makeSky({ top: 0x050a22, mid: 0x14204a, horizon: 0x4a3c66, below: 0x0a0a12, stars: 380, sun: { dir: [-0.42, 0.38, -0.82], color: 0xcfdcff, power: 3.5, size: 22 } });
  group.add(sky); glow.push(sky.userData.disc);
  const dustR = rng(5); const dBase = Array.from({ length: DN }, () => [(dustR() - 0.5) * 2.2, dustR() * 2.6, -1.8 - dustR() * 2.0, dustR() * 6.28, 0.1 + dustR() * 0.2]);

  const set = { id: 'garage', group, glow, sky, figs,
    env: { top: 0x0a1030, mid: 0x1a2656, horizon: 0x4a3c66, ground: 0x0a0a12, sun: { dir: [-0.42, 0.38, -0.82], color: 0xcfdcff, power: 3, size: 4 } },
    fog: { color: 0x121a38, density: 0.016 }, look: { grade: 'amber', bloomI: 1.55, dofScale: 0 },
    // mode: 'band' (2004–06) | 'hook' (dark, single bulb) ; board: 0..1 flip ; keyI: scale of interior key
    update(t, cfg = {}) {
      const mode = cfg.mode || 'band', hook = mode === 'hook';
      figs.vic.h.root.visible = figs.mike.h.root.visible = !hook;
      pose(figs.vic.h, t, 'guitar', { ph: 0.3 }); pose(figs.mike.h, t, 'drum', { ph: 1.1 });
      mike.root.position.y = 0;
      flip.rotation.x = Math.PI * (cfg.board ?? 0); flip.position.y = Math.sin((cfg.board ?? 0) * Math.PI) * 0.12;
      const k = hook ? 0.35 : 1; rig.userData.key.intensity = 52 * k * (cfg.keyI ?? 1); spill.intensity = 36 * (hook ? 0.1 : 1); shaftB.visible = !hook; sp2.intensity = hook ? 0.5 : 5; rig.userData.rim.intensity = hook ? 1.2 : 2.6;
      bulbs[1].visible = !hook; sl.visible = sl2.visible = !hook;
      for (const b of [shaftA, shaftB]) b.userData.setT(t);
      const p = dust.geometry.attributes.position; dBase.forEach((d, i) => p.setXYZ(i, d[0] + Math.sin(t * d[4] + d[3]) * 0.12, d[1] + Math.sin(t * d[4] * 0.7 + d[3]) * 0.1, d[2])); p.needsUpdate = true;
      sky.userData.follow && 0;
    } };
  return set;
}
