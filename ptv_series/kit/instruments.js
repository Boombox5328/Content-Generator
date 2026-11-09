// Guitars, bass, mic stand, drum kit, amp stack, drum riser — bevelled, faceted, vertex-coloured.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube } from '../engine/lowpoly.js';

const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };
const METAL = lpMat({ metalness: 0.75, roughness: 0.35 });

function bodyShape() {
  const top = [[-0.21, 0.0], [-0.2, 0.085], [-0.145, 0.145], [-0.07, 0.155], [-0.03, 0.105], [0.02, 0.095], [0.075, 0.165], [0.135, 0.175], [0.175, 0.105], [0.185, 0.0]];
  const pts = [...top.map(([x, y]) => new THREE.Vector2(x, y)), ...top.slice().reverse().slice(1, -1).map(([x, y]) => new THREE.Vector2(x, -y))];
  return new THREE.Shape(pts);
}
export function makeGuitar({ body = 0xb3202b, body2 = 0x4a0d12, bass = false, neckLen } = {}) {
  const g = new THREE.Group(), L = neckLen ?? (bass ? 0.78 : 0.64);
  const bg = new THREE.ExtrudeGeometry(bodyShape(), { depth: 0.045, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.009, bevelSegments: 1 }); bg.translate(0, 0, -0.022);
  put(g, paint(bg, { top: body, bottom: body2, axis: 'x', seed: 4, jitter: 0.06 }), 0, 0, 0);
  put(g, bevelBox(L, 0.042, 0.032, 0.008, { top: 0x5a3a22, jitter: 0.05 }), 0.19 + L / 2, 0, 0.0);
  put(g, bevelBox(L - 0.02, 0.036, 0.008, 0.002, { top: 0x120d0a, jitter: 0.03 }), 0.2 + L / 2, 0, 0.02);
  const hs = new THREE.Shape([new THREE.Vector2(0, -0.026), new THREE.Vector2(0.17, -0.034), new THREE.Vector2(0.18, 0.03), new THREE.Vector2(0, 0.024)]);
  const hg = new THREE.ExtrudeGeometry(hs, { depth: 0.026, bevelEnabled: false }); hg.translate(0, 0, -0.013); put(g, paint(hg, { top: 0x3a2616, jitter: 0.05 }), 0.19 + L, 0, 0);
  for (const x of bass ? [0.02, 0.1] : [0.0, 0.065, 0.12]) put(g, bevelBox(0.03, bass ? 0.07 : 0.055, 0.018, 0.004, { top: 0x1a1a1e }), x, 0, 0.032);
  put(g, bevelBox(0.03, 0.09, 0.016, 0.004, { top: 0xc8ccd4 }), -0.1, 0, 0.032, METAL);
  g.userData.tip = new THREE.Vector3(0.19 + L + 0.18, 0, 0);
  return g;
}
export function makeMicStand() {
  const g = new THREE.Group(), d = lpMat({ metalness: 0.5, roughness: 0.4 });
  put(g, paint(new THREE.CylinderGeometry(0.21, 0.24, 0.03, 8), { top: 0x1b1b1f, jitter: 0.04 }), 0, 0.015, 0);
  put(g, paint(new THREE.CylinderGeometry(0.012, 0.012, 1.48, 6), { top: 0x2a2a30, jitter: 0.03 }), 0, 0.77, 0, d);
  put(g, paint(new THREE.CylinderGeometry(0.01, 0.01, 0.3, 6), { top: 0x2a2a30 }), 0.0, 1.5, 0.12, d).rotation.x = Math.PI / 2 - 0.4;
  put(g, paint(new THREE.IcosahedronGeometry(0.045, 1), { top: 0x8a8f9a, bottom: 0x2a2c32, jitter: 0.08 }), 0, 1.57, 0.25, d);
  return g;
}
export function makeDrumKit({ shell = 0x8a1620, shell2 = 0x3a0a10 } = {}) {
  const g = new THREE.Group(), gold = lpMat({ metalness: 0.7, roughness: 0.32 });
  const drum = (r, h, x, y, z, rx = 0, rz = 0, seg = 14) => { const d = new THREE.Group(); d.position.set(x, y, z); d.rotation.set(rx, 0, rz); g.add(d);
    put(d, paint(new THREE.CylinderGeometry(r, r, h, seg), { top: shell, bottom: shell2, axis: 'x', jitter: 0.07, seed: Math.round(x * 10) }), 0, 0, 0);
    put(d, paint(new THREE.CylinderGeometry(r * 1.02, r * 1.02, 0.012, seg), { top: 0xe9e2d2, jitter: 0.03 }), 0, h / 2, 0);
    put(d, paint(new THREE.CylinderGeometry(r * 1.04, r * 1.04, 0.012, seg), { top: 0xb0b6c0 }), 0, -h / 2, 0, gold); return d; };
  drum(0.29, 0.38, 0, 0.3, 0.1, Math.PI / 2);                 // kick (head toward +z)
  drum(0.17, 0.15, -0.2, 0.72, 0.28, 0.25); drum(0.19, 0.17, 0.2, 0.72, 0.28, 0.25);
  drum(0.24, 0.22, 0.66, 0.42, 0.2); drum(0.18, 0.12, -0.04, 0.5, 0.58);                   // floor tom + snare
  const cym = (r, x, y, z, tilt) => { const c = new THREE.Group(); c.position.set(x, y, z); c.rotation.set(tilt, 0, 0.1); g.add(c);
    put(c, paint(new THREE.CylinderGeometry(r, r * 0.92, 0.012, 14), { top: 0xf2c758, bottom: 0xb48a2c, jitter: 0.06 }), 0, 0, 0, gold);
    put(c, paint(new THREE.ConeGeometry(0.05, 0.03, 8), { top: 0xffe08a }), 0, 0.012, 0, gold);
    put(g, paint(new THREE.CylinderGeometry(0.008, 0.008, y, 5), { top: 0x2a2a30 }), x, y / 2, z, gold); };
  cym(0.2, -0.45, 1.02, 0.15, -0.15); cym(0.24, 0.45, 1.1, 0.05, -0.2); cym(0.19, -0.75, 0.72, 0.55, 0);
  put(g, paint(new THREE.CylinderGeometry(0.2, 0.2, 0.012, 14), { top: 0xe9c44a }), -0.75, 0.72, 0.55, gold);
  put(g, paint(new THREE.CylinderGeometry(0.2, 0.2, 0.012, 14), { top: 0xe9c44a }), 0.75, 0.9, 0.35, gold);
  put(g, paint(new THREE.CylinderGeometry(0.15, 0.17, 0.05, 10), { top: 0x1a1a20 }), 0.0, 0.5, -0.45);       // stool
  return g;
}
export function makeAmpStack({ tolex = 0x17171c, trim = 0xb0b4bc, glow = 0xff7a30 } = {}) {
  const g = new THREE.Group(); const grille = lpMat({ roughness: 0.9 });
  for (const y of [0.36, 1.1]) { put(g, bevelBox(0.78, 0.7, 0.42, 0.03, { top: tolex, bottom: 0x0a0a0d, jitter: 0.05 }), 0, y, 0);
    put(g, paint(new THREE.BoxGeometry(0.62, 0.52, 0.02), { top: 0x2a2a2f, bottom: 0x111115, jitter: 0.1 }), 0, y, 0.215, grille);
    for (const dx of [-0.2, 0.2]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.012, 10), lpMat()); c.visible = false; } }
  put(g, bevelBox(0.78, 0.22, 0.34, 0.03, { top: 0x202026, bottom: 0x0a0a0d }), 0, 1.57, 0);
  for (let i = 0; i < 5; i++) put(g, paint(new THREE.CylinderGeometry(0.022, 0.022, 0.03, 6), { top: trim }), -0.28 + i * 0.14, 1.6, 0.18, lpMat({ metalness: 0.6 })).rotation.x = Math.PI / 2;
  const led = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.02, 0.01), emissiveMat(glow, 4)); led.position.set(0.3, 1.52, 0.175); g.add(led); g.userData.glow = [led];
  return g;
}
export function makeRiser(w = 3.2, d = 2.4, h = 0.35) {
  const g = new THREE.Group(); put(g, bevelBox(w, h, d, 0.02, { top: 0x4a4a54, bottom: 0x1e1e24, jitter: 0.06 }), 0, h / 2, 0);
  put(g, bevelBox(w + 0.04, 0.03, d + 0.04, 0.01, { top: 0x2a2a30 }), 0, h + 0.012, 0); return g;
}
