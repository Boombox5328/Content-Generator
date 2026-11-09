// Club stage (2010): packed, sweaty, red + teal light, haze, teal monument rising behind the band.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube, lerp, clamp, smooth } from '../engine/lowpoly.js';
import { makeRig } from '../engine/pipeline.js';
import { makeShaft } from '../engine/shafts.js';
import { makeHuman, pose, BAND } from '../kit/human.js';
import { makeGuitar, makeMicStand, makeDrumKit, makeAmpStack } from '../kit/instruments.js';
import { makeCrowd } from '../kit/crowd.js';
import { makeMonument } from '../kit/monument.js';
const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };

export function makeClub() {
  const group = new THREE.Group(), glow = [], R = rng(41);
  put(group, bevelBox(18, 0.1, 22, 0.02, { top: 0x2a2630, bottom: 0x14121a, axis: 'z', jitter: 0.09, seed: 1 }), 0, -0.05, 0);               // sticky floor
  put(group, bevelBox(0.2, 5.4, 22, 0.02, { top: 0x1a1820, bottom: 0x0c0a10 }), -9, 2.7, 0); put(group, bevelBox(0.2, 5.4, 22, 0.02, { top: 0x1a1820, bottom: 0x0c0a10 }), 9, 2.7, 0);
  put(group, bevelBox(18, 0.2, 22, 0.02, { top: 0x14121a }), 0, 5.4, 0); put(group, bevelBox(18, 5.4, 0.2, 0.02, { top: 0x1c1a24, bottom: 0x0c0a10 }), 0, 2.7, -11);
  for (let i = 0; i < 16; i++) put(group, bevelBox(0.8, 5.0, 0.12, 0.03, { top: 0x2a1418, bottom: 0x0c0608, jitter: 0.12, seed: i }), -7.8 + i * 1.04, 2.6, -10.8);   // curtain folds
  // stage + riser + backline
  put(group, bevelBox(9.5, 1.0, 4.8, 0.03, { top: 0x2c2832, bottom: 0x14121a, seed: 2 }), 0, 0.5, -7.4); put(group, bevelBox(4.0, 0.4, 2.2, 0.02, { top: 0x3a3640 }), 0.0, 1.2, -9.0);
  for (const [x, s] of [[-3.9, 0.3], [3.9, -0.3]]) { const a = makeAmpStack({ glow: x < 0 ? 0xff4a30 : 0x30e0d0 }); a.position.set(x, 1.0, -9.6); a.rotation.y = s; group.add(a); glow.push(...a.userData.glow); }
  const kit = makeDrumKit({ shell: 0x16606a, shell2: 0x08262c }); kit.position.set(0, 1.4, -9.1); kit.scale.setScalar(1.1); group.add(kit);
  // truss with lamp cans (emissive) and mic
  const truss = new THREE.Group(); group.add(truss);
  for (const z of [-5.5, -2.0]) { put(truss, bevelBox(15, 0.18, 0.18, 0.02, { top: 0x6a6f7c }), 0, 4.6, z); for (let i = 0; i < 8; i++) { const x = -6.5 + i * 1.85, col = i % 2 ? 0x1ad6c8 : 0xff2a44; const can = put(truss, paint(new THREE.CylinderGeometry(0.16, 0.2, 0.34, 8), { top: 0x2a2a30 }), x, 4.4, z); const lens = new THREE.Mesh(new THREE.CircleGeometry(0.15, 8), emissiveMat(col, 7)); lens.rotation.x = Math.PI / 2; lens.position.set(x, 4.22, z); truss.add(lens); glow.push(lens); } }
  const figs = {}; const addFig = (id, mode, x, z, ry) => { const h = makeHuman({ ...BAND[id] }); h.root.position.set(x, 1.0, z); h.root.rotation.y = ry; group.add(h.root); figs[id] = { h, mode }; return h; };
  const vic = addFig('vic', 'guitar', -0.4, -6.2, 0.0); const g1 = makeGuitar({ body: 0xb3202b }); g1.position.set(-0.02, 0.1, 0.19); g1.rotation.z = 0.5; vic.attach(g1);
  const tony = addFig('tony', 'guitar', -2.6, -7.0, 0.3); const g2 = makeGuitar({ body: 0x2aa6b8, body2: 0x0d3a44 }); g2.position.set(-0.02, -0.12, 0.19); g2.rotation.z = 0.35; tony.attach(g2);
  const jaime = addFig('jaime', 'guitar', 2.2, -7.0, -0.3); const g3 = makeGuitar({ body: 0x23262e, body2: 0x090a0d, bass: true }); g3.position.set(-0.02, 0.0, 0.19); g3.rotation.z = 0.42; jaime.attach(g3);
  const mikeFig = addFig('mike', 'drum', 0.0, -9.9, 0); mikeFig.root.position.y = 1.4;
  const mic = makeMicStand(); mic.position.set(-0.35, 1.0, -5.0); group.add(mic);
  const mon = makeMonument({ color: 0x18d6c4, height: 5.0, seed: 8, glowI: 4.0 }); mon.group.position.set(0.0, 1.0, -9.9); group.add(mon.group); glow.push(...mon.glow);
  const monLight = new THREE.PointLight(0x18d6c4, 0, 14, 2); monLight.position.set(0, 3.0, -8.5); group.add(monLight);
  // crowd (dense, arms up, some bounce) in front of the stage
  const crowd = makeCrowd({ count: 190, seed: 3, noPhones: true, scale: 1.0, place: (r, i) => ({ x: (r() - 0.5) * 12.5, z: -3.6 + r() * 9.5 + (i % 2) * 0.0, y: 0, yaw: (r() - 0.5) * 0.5 }), palette: [0x1c1c22, 0x2a2f45, 0x6a2a3a, 0x20303a, 0x3a3a52, 0x5a2a2a, 0x2a4a50] }); group.add(crowd.group);
  // lights: red KEY from front-left, teal RIM from behind, dim FILL; sweeping shaft cones
  const rig = makeRig({ key: { type: 'spot', pos: [-6, 4.6, 0.5], color: 0xff3a40, intensity: 520, angle: 0.62, far: 24 }, rim: { pos: [3, 4, -14], color: 0x18d6c4, intensity: 3.8 }, fill: { sky: 0x302040, ground: 0x10080c, intensity: 0.35 }, target: new THREE.Vector3(0, 1.8, -6.5) }); group.add(rig);
  const tealSpot = new THREE.SpotLight(0x18d6c4, 420, 26, 0.6, 0.9, 2); tealSpot.position.set(6, 4.6, 0.5); tealSpot.target.position.set(0, 1.8, -7); group.add(tealSpot, tealSpot.target);
  const shafts = []; [[-6.5, 0xff2a44], [-2.2, 0x1ad6c8], [2.2, 0xff2a44], [6.5, 0x1ad6c8], [-4.4, 0xff2a44], [4.4, 0x1ad6c8]].forEach(([x, c], i) => { const s = makeShaft([x, 4.3, -3.8], [x * 0.6, 0.0, -8.5], { r0: 0.1, r1: 1.4, color: c, intensity: 0.55, falloff: 1.0 }); group.add(s); shafts.push([s, x, i]); });

  return { id: 'club', group, glow, figs, mon,
    env: { top: 0x18101c, mid: 0x2a1a30, horizon: 0x40303a, ground: 0x0a080c }, fog: { color: 0x241420, density: 0.052 }, look: { grade: 'teal', bloomI: 1.9, dofScale: 0 },
    update(t, cfg = {}) {
      Object.entries(figs).forEach(([id, f]) => pose(f.h, t, id === 'mike' ? 'drum' : 'guitar', { ph: id.length * 0.9, tempo: 1.1 })); mikeFig.root.position.y = 1.4; crowd.update(t, 1.2);
      const m = cfg.monument ?? 0; mon.grow(m); mon.update(t); mon.group.visible = m > 0.001; mon.group.position.y = 1.0 - (1 - m) * 1.0; monLight.intensity = 120 * smooth(0.05, 0.8, m);
      shafts.forEach(([s, x, i]) => { s.userData.setT(t); s.rotation.z = Math.sin(t * 0.9 + i) * 0.08; });
    } };
}
