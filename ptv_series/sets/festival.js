// Warped Tour lot (2008): dusty festival ground at golden hour, small stage, tents, vans, crowd, heat haze.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube, lerp, clamp, smooth } from '../engine/lowpoly.js';
import { makeRig } from '../engine/pipeline.js';
import { makeShaft } from '../engine/shafts.js';
import { makeSky } from '../engine/sky.js';
import { makeHuman, pose, BAND } from '../kit/human.js';
import { makeGuitar, makeMicStand, makeDrumKit, makeAmpStack } from '../kit/instruments.js';
import { makeCrowd } from '../kit/crowd.js';
import { cloud, crate } from '../kit/props.js';

const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };
const DS = lpMat({ side: THREE.DoubleSide });

function tent(w, d, h, c0, c1, seed) {
  const g = new THREE.Group(); const R = rng(seed);
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) put(g, paint(new THREE.CylinderGeometry(0.04, 0.04, h, 5), { top: 0xb0b4bc, bottom: 0x70747c }), x * (w / 2 - 0.1), h / 2, z * (d / 2 - 0.1));
  const roof = new THREE.ConeGeometry(Math.hypot(w, d) / 2 * 0.98, h * 0.55, 4, 4); roof.rotateY(Math.PI / 4); roof.scale(w / Math.hypot(w, d) * 1.414, 1, d / Math.hypot(w, d) * 1.414); roof.translate(0, h + h * 0.27, 0);
  const rg = paint(roof, { top: c0, bottom: c1, jitter: 0.05, seed });
  { const p = rg.attributes.position, c = rg.attributes.color; for (let i = 0; i < p.count; i += 3) { const k = Math.floor(((Math.atan2(p.getZ(i) + p.getZ(i + 1) + p.getZ(i + 2), p.getX(i) + p.getX(i + 1) + p.getX(i + 2)) + Math.PI) / (Math.PI * 2)) * 16); const alt = k % 2; for (let j = 0; j < 3; j++) { const col = new THREE.Color(alt ? c1 : c0); c.setXYZ(i + j, col.r * (0.9 + R() * 0.15), col.g * (0.9 + R() * 0.15), col.b * (0.9 + R() * 0.15)); } } }
  put(g, rg, 0, 0, 0, DS);
  put(g, bevelBox(w - 0.2, 0.9, 0.1, 0.02, { top: 0xe8e0d0, bottom: 0xb8b0a0 }), 0, h * 0.5, -d / 2 + 0.2);
  put(g, bevelBox(w - 0.4, 0.8, 0.5, 0.03, { top: 0x6a4a2a }), 0, 0.4, -d / 2 + 0.7);                                     // table
  return g;
}
function van(c = 0xe8e2d4, stripe = 0xc0392b) {
  const g = new THREE.Group(), body = new THREE.Shape([[0, 0.35], [0.2, 1.7], [1.3, 1.95], [3.0, 1.95], [3.4, 1.0], [3.5, 0.35]].map(([x, y]) => new THREE.Vector2(x, y)));
  const bg = new THREE.ExtrudeGeometry(body, { depth: 1.9, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.08, bevelSegments: 1 }); bg.translate(-1.75, 0, -0.95);
  put(g, paint(bg, { top: c, bottom: new THREE.Color(c).multiplyScalar(0.55).getHex(), jitter: 0.04, seed: 3 }), 0, 0, 0);
  put(g, bevelBox(3.4, 0.28, 2.06, 0.03, { top: stripe }), 0, 0.85, 0);
  put(g, bevelBox(0.05, 0.7, 1.5, 0.01, { top: 0x1a2230 }), 1.2, 1.4, 0.0); put(g, bevelBox(1.0, 0.6, 1.95, 0.02, { top: 0x1a2230 }), -0.2, 1.4, 0);
  for (const [x, z] of [[-1.15, 0.95], [-1.15, -0.95], [1.1, 0.95], [1.1, -0.95]]) { const w = put(g, paint(new THREE.CylinderGeometry(0.38, 0.38, 0.3, 10), { top: 0x15151a }), x, 0.38, z); w.rotation.x = Math.PI / 2; put(g, paint(new THREE.CylinderGeometry(0.2, 0.2, 0.32, 8), { top: 0xb8bcc4 }), x, 0.38, z).rotation.x = Math.PI / 2; }
  put(g, bevelBox(2.6, 0.08, 1.7, 0.02, { top: 0x2a2a30 }), 0, 2.0, 0);
  return g;
}

export function makeFestival() {
  const group = new THREE.Group(), glow = [], R = rng(31);
  // ground: dusty faceted lot
  const gg = new THREE.PlaneGeometry(400, 400, 80, 80); gg.rotateX(-Math.PI / 2); const gp = gg.attributes.position;
  for (let i = 0; i < gp.count; i++) { const x = gp.getX(i), z = gp.getZ(i); gp.setY(i, (Math.sin(x * 0.11) * Math.cos(z * 0.09) * 0.35 + (R() - 0.5) * 0.12) * smooth(6, 30, Math.hypot(x, z))); }
  const ground = mesh(paint(gg, { top: 0xd9b27a, bottom: 0xb88a56, axis: 'z', jitter: 0.07, seed: 4 }), M); group.add(ground);
  // stage (small, low) facing +z at the origin
  const st = new THREE.Group(); group.add(st);
  put(st, bevelBox(9, 1.0, 5.5, 0.04, { top: 0x3a3a44, bottom: 0x1c1c24, seed: 2 }), 0, 0.5, -1.0);
  put(st, bevelBox(9.6, 0.12, 6.0, 0.03, { top: 0x5a5a66 }), 0, 1.03, -1.0);
  for (const x of [-4.6, 4.6]) put(st, bevelBox(0.25, 5.6, 0.25, 0.03, { top: 0x8a8f9c, bottom: 0x4a4f5c }), x, 3.6, -3.4);
  put(st, bevelBox(9.8, 0.3, 0.3, 0.03, { top: 0x8a8f9c }), 0, 6.3, -3.4); put(st, bevelBox(9.6, 0.1, 5.8, 0.03, { top: 0x2a2a34 }), 0, 6.5, -1.0);
  const banner = new THREE.Group(); banner.position.set(0, 3.7, -3.7); st.add(banner);                                    // abstract backdrop (colour blocks, no logos)
  [[-3, 0x2a7a8a, 2.8], [-0.6, 0xe8a850, 2.0], [1.5, 0xc0392b, 2.2], [3.5, 0x3a3a6a, 1.6]].forEach(([x, c, w], i) => put(banner, bevelBox(w, 3.2 + (i % 2) * 0.5, 0.08, 0.02, { top: c, bottom: new THREE.Color(c).multiplyScalar(0.55).getHex(), seed: i }), x, (i % 2) * 0.1, 0));
  for (const x of [-5.2, 5.2]) { put(st, bevelBox(1.2, 2.4, 1.2, 0.05, { top: 0x2a2a30, bottom: 0x121216 }), x, 1.2 + 1.0, -2.3); }
  const amp = makeAmpStack({ glow: 0xff7a30 }); amp.position.set(-3.4, 1.06, -3.0); st.add(amp); glow.push(...amp.userData.glow);
  const amp2 = makeAmpStack(); amp2.position.set(3.6, 1.06, -3.0); amp2.rotation.y = -0.2; st.add(amp2); glow.push(...amp2.userData.glow);
  const kit = makeDrumKit({ shell: 0xd8d2c4, shell2: 0x8a8478 }); kit.position.set(0.0, 1.09, -3.1); kit.scale.setScalar(1.1); st.add(kit);
  const figs = {}; const addFig = (id, mode, x, z, ry) => { const h = makeHuman({ ...BAND[id] }); h.root.position.set(x, 1.09, z); h.root.rotation.y = ry; st.add(h.root); figs[id] = { h, mode }; return h; };
  const vic = addFig('vic', 'guitar', -0.5, -0.1, 0.0); const g1 = makeGuitar({ body: 0xb3202b }); g1.position.set(-0.02, 0.1, 0.19); g1.rotation.z = 0.5; vic.attach(g1);
  const tony = addFig('tony', 'guitar', -2.3, -0.9, 0.3); const g2 = makeGuitar({ body: 0x2aa6b8, body2: 0x0d3a44 }); g2.position.set(-0.02, -0.12, 0.19); g2.rotation.z = 0.35; tony.attach(g2);
  const jaime = addFig('jaime', 'guitar', 2.0, -0.9, -0.3); const g3 = makeGuitar({ body: 0x23262e, body2: 0x090a0d, bass: true }); g3.position.set(-0.02, 0.0, 0.19); g3.rotation.z = 0.42; jaime.attach(g3);
  addFig('mike', 'drum', 0.0, -3.9, 0);
  const mic = makeMicStand(); mic.position.set(-0.45, 1.09, 0.7); st.add(mic);
  // lot dressing: tents, vans, barriers, pennants, crates
  const tents = [[-14, -6, 0xd9503a, 0xf2e6d0], [-20, 4, 0x2a7a8a, 0xf2e6d0], [15, -8, 0xe8a850, 0xf2e6d0], [20, 2, 0xc0392b, 0xe8e0d0], [-9, -16, 0x3a3a6a, 0xe8e0d0], [10, -18, 0xd9503a, 0xf2e6d0]];
  tents.forEach(([x, z, c0, c1], i) => { const t = tent(4.2, 4.2, 2.6, c0, c1, i + 3); t.position.set(x, 0, z); t.rotation.y = (R() - 0.5) * 0.5; group.add(t); });
  [[-17, -14, 0.4, 0xe8e2d4, 0xc0392b], [18, -16, -0.5, 0x2a7a8a, 0xe8e2d4], [-26, -3, 1.2, 0xd8c8a8, 0x2a7a8a]].forEach(([x, z, ry, c, s]) => { const v = van(c, s); v.position.set(x, 0, z); v.rotation.y = ry; group.add(v); });
  for (let i = 0; i < 14; i++) put(group, bevelBox(1.8, 1.0, 0.1, 0.02, { top: 0x8a8f9c, bottom: 0x50555f, seed: i }), -12.6 + i * 1.9, 0.5, 9.2);                       // crowd barrier
  const pen = tube([new THREE.Vector3(-14, 7.5, -8), new THREE.Vector3(-5, 6.2, -6), new THREE.Vector3(5, 6.2, -6), new THREE.Vector3(14, 7.5, -8)], 0.012, 3, false, 0x1a1a1a); group.add(pen);
  for (let i = 0; i < 24; i++) { const u = i / 23, x = lerp(-14, 14, u), y = 7.5 - Math.sin(u * Math.PI) * 1.2 - 0.2; const f = mesh(new THREE.ConeGeometry(0.2, 0.5, 3), lpMat({ side: THREE.DoubleSide })); f.geometry = paint(f.geometry, { top: [0xd9503a, 0xe8a850, 0x2a7a8a, 0xf2e6d0][i % 4], jitter: 0.05 }); f.position.set(x, y - 0.1, lerp(-8, -8, u) + Math.sin(u * 6.28) * 1.0); f.rotation.x = Math.PI; group.add(f); }
  for (let i = 0; i < 18; i++) put(group, crate(0.6 + R() * 0.4, 0.5 + R() * 0.3, 0.6, [0x7a5a36, 0x6a4a2a, 0x8a6a46][i % 3]), (R() - 0.5) * 60, 0.3, -24 + R() * 10);
  const crowd = makeCrowd({ count: 260, seed: 12, scale: 1.0, noPhones: true, place: (r, i) => { const x = (r() - 0.5) * 20, z = 10.5 + Math.pow(r(), 0.8) * 13; return { x, z, y: 0, yaw: Math.PI + (r() - 0.5) * 0.4 }; }, palette: [0x2a2f45, 0x6a2a3a, 0x3a5a6a, 0xd0c8b8, 0x1c1c22, 0x9a5a3a, 0xc0392b, 0x2a7a8a, 0xe8a850] });
  group.add(crowd.group);
  // sky: golden hour, low sun behind the stage, clouds
  const sunDir = [0.1, 0.17, -0.98];
  const sky = makeSky({ top: 0x3a68a8, mid: 0x9a86a0, horizon: 0xffc070, below: 0xd0a070, sun: { dir: sunDir, color: 0xffe0a0, power: 4.5, size: 30 } }); group.add(sky); glow.push(sky.userData.disc);
  const cl = new THREE.Group(); group.add(cl); [[-80, 60, -280, 18, 1], [60, 80, -300, 22, 2], [150, 50, -250, 14, 3], [-170, 70, -240, 16, 4], [20, 120, -320, 24, 5]].forEach(([x, y, z, s, sd]) => { const c = cloud(sd, s, 0xffe6c8, 0xe08a70); c.position.set(x, y, z); cl.add(c); });
  // lights: warm low KEY from camera-left, cool RIM from behind/above, dim FILL
  const rig = makeRig({ key: { pos: [-22, 18, 24], color: 0xffbe78, intensity: 3.2, extent: 14, far: 90 }, rim: { pos: [6, 14, -30], color: 0x8ab4ff, intensity: 2.6 }, fill: { sky: 0xb0c0e0, ground: 0xb08850, intensity: 0.7 }, target: new THREE.Vector3(0, 1.5, 2) }); group.add(rig);
  const sunShaft = makeShaft([0.0, 5.0, -80], [0.0, 0.0, 12], { r0: 18, r1: 22, color: 0xffd090, intensity: 0.09, falloff: 0.6 }); group.add(sunShaft);
  const dust = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xffe0a8, size: 2.0, sizeAttenuation: false, transparent: true, opacity: 0.5, depthWrite: false, toneMapped: false }));
  const DN = 500, dBase = Array.from({ length: DN }, () => [(R() - 0.5) * 40, 0.3 + R() * 7, -8 + R() * 36, R() * 6.28, 0.2 + R() * 0.5]); dust.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(DN * 3), 3)); dust.frustumCulled = false; group.add(dust);

  return { id: 'festival', group, glow, figs, sky,
    env: { top: 0x3a68a8, mid: 0x9a86a0, horizon: 0xffc070, ground: 0xb88a56, sun: { dir: sunDir, color: 0xffe0a0, power: 4, size: 6 } }, fog: { color: 0xe8b884, density: 0.0085 }, look: { grade: 'gold', bloomI: 1.2, dofScale: 0 },
    update(t, cfg = {}) {
      Object.entries(figs).forEach(([id, f]) => pose(f.h, t, f.mode, { ph: id.length * 0.9 })); crowd.update(t, 0.9); sunShaft.userData.setT(t);
      const p = dust.geometry.attributes.position; dBase.forEach((d, i) => p.setXYZ(i, d[0] + Math.sin(t * d[4] + d[3]) * 0.4 + t * 0.3 % 4, d[1] + Math.sin(t * d[4] * 0.7 + d[3]) * 0.2, d[2])); p.needsUpdate = true;
    } };
}
