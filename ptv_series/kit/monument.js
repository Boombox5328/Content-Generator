// Album "monuments": original abstract faceted sculptures (twisted crystal spire + leaning shards + floating fragments). No album art.
import { THREE, paint, mesh, lpMat, emissiveMat, rng, lerp, clamp, col, M } from '../engine/lowpoly.js';

function twistPrism({ h, r0, r1, sides = 6, rings = 14, twist = 1.1, seed = 1, taperPow = 1.15 }) {
  const R = rng(seed), pos = [], idx = [];
  for (let k = 0; k <= rings; k++) { const u = k / rings, r = lerp(r0, r1, Math.pow(u, taperPow)), a0 = u * twist;
    for (let j = 0; j < sides; j++) { const a = a0 + (j / sides) * Math.PI * 2, rr = r * (0.9 + 0.2 * R()) * (j % 2 ? 0.8 : 1.15); pos.push(Math.cos(a) * rr, u * h, Math.sin(a) * rr); } }
  for (let k = 0; k < rings; k++) for (let j = 0; j < sides; j++) { const a = k * sides + j, b = k * sides + (j + 1) % sides, c = (k + 1) * sides + j, d = (k + 1) * sides + (j + 1) % sides; idx.push(a, c, b, b, c, d); }
  const top = pos.length / 3; pos.push(0, h * 1.04, 0); for (let j = 0; j < sides; j++) idx.push(rings * sides + j, top, rings * sides + (j + 1) % sides);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); return g;
}
export function makeMonument({ color = 0xc01830, height = 8, seed = 1, dark = false, edge = 0xffffff, glowI = 3.0 } = {}) {
  const g = new THREE.Group(), body = new THREE.Group(), R = rng(seed), glow = []; g.add(body);
  const base = new THREE.Color(color), deep = base.clone().multiplyScalar(dark ? 0.06 : 0.22), tip = base.clone().lerp(new THREE.Color(0xffffff), dark ? 0 : 0.35);
  const mat = lpMat({ roughness: dark ? 0.35 : 0.5, metalness: dark ? 0.5 : 0.1, emissive: base.clone().multiplyScalar(dark ? 0.0 : 0.22), emissiveIntensity: 1 });
  const r0 = height * 0.1, shards = [];
  const main = mesh(paint(twistPrism({ h: height, r0, r1: r0 * 0.12, seed, twist: 1.3 }), { top: tip.getHex(), bottom: deep.getHex(), seed, jitter: 0.1 }), mat); body.add(main);
  for (let i = 0; i < 5; i++) { const a = (i / 5) * 6.28 + R(), hh = height * (0.35 + R() * 0.35), s = mesh(paint(twistPrism({ h: hh, r0: r0 * (0.45 + R() * 0.25), r1: r0 * 0.05, sides: 5, rings: 8, seed: seed + i + 1, twist: 0.8 }), { top: tip.getHex(), bottom: deep.getHex(), seed: seed + i, jitter: 0.1 }), mat);
    s.position.set(Math.cos(a) * r0 * 1.1, 0, Math.sin(a) * r0 * 1.1); s.rotation.set(Math.sin(a) * 0.32, a, -Math.cos(a) * 0.32); body.add(s); }
  // emissive inner "core" spire (this is what blooms)
  const core = mesh(twistPrism({ h: height * 0.97, r0: r0 * 0.3, r1: r0 * 0.02, sides: 4, rings: 10, seed: seed + 9, twist: -1.6 }), emissiveMat(base.clone().lerp(new THREE.Color(0xffffff), dark ? 0.0 : 0.25), glowI)); core.castShadow = false; body.add(core); glow.push(core);
  const frag = [];
  for (let i = 0; i < 12; i++) { const f = mesh(paint(new THREE.OctahedronGeometry(height * (0.02 + R() * 0.03), 0), { top: tip.getHex(), bottom: base.getHex(), seed: i }), mat); const e = new THREE.Mesh(new THREE.OctahedronGeometry(height * 0.01, 0), emissiveMat(color, glowI)); f.add(e); glow.push(e);
    frag.push({ f, a: R() * 6.28, r: r0 * (1.6 + R() * 2.2), y: height * (0.1 + R() * 0.9), sp: 0.15 + R() * 0.3 }); g.add(f); }
  const plinth = mesh(paint(new THREE.CylinderGeometry(r0 * 2.2, r0 * 2.7, height * 0.04, 6), { top: 0x2a2630, bottom: 0x121016, seed }), M); plinth.position.y = height * 0.02; g.add(plinth); plinth.name = 'plinth';
  g.userData = { plinth };
  return { group: g, body, glow, height, r0,
    update(t) { frag.forEach((o) => { o.f.position.set(Math.cos(o.a + t * o.sp) * o.r, o.y + Math.sin(t * 1.1 + o.a) * height * 0.015, Math.sin(o.a + t * o.sp) * o.r); o.f.rotation.set(t * o.sp, t * 0.6, 0); }); },
    grow(k) { body.scale.set(1, Math.max(0.001, k), 1); const s = clamp(k * 1.6, 0.001, 1); frag.forEach((o) => (o.f.visible = k > 0.5)); } };
}
