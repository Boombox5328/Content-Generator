// Instanced low-poly crowd: 3 body variants (arms up / fist pump / phone raised), randomised colours + bounce timing.
import { THREE, paint, lpMat, emissiveMat, rng, mergeGeometries, clamp } from '../engine/lowpoly.js';

function part(geo, color, tx = 0, ty = 0, tz = 0, rx = 0, ry = 0, rz = 0, jit = 0.05) { const g = paint(geo, { top: color, jitter: jit }); const m = new THREE.Matrix4().compose(new THREE.Vector3(tx, ty, tz), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(1, 1, 1)); g.applyMatrix4(m); return g; }
function body(variant) {
  const cloth = [], skin = [];
  cloth.push(part(new THREE.CylinderGeometry(0.19, 0.15, 0.52, 6), 0xffffff, 0, 1.2, 0)); cloth.push(part(new THREE.CylinderGeometry(0.095, 0.075, 0.82, 5), 0x555555, 0.09, 0.42, 0)); cloth.push(part(new THREE.CylinderGeometry(0.095, 0.075, 0.82, 5), 0x555555, -0.09, 0.42, 0));
  skin.push(part(new THREE.IcosahedronGeometry(0.145, 0), 0xffffff, 0, 1.64, 0));
  const arm = (sx, up, bend) => { const L = 0.62; const ang = up ? Math.PI * 0.86 : 0.12; const rz = -sx * ang * 1; const x = sx * 0.21;
    const a = new THREE.CylinderGeometry(0.05, 0.04, L, 5); a.translate(0, L / 2, 0); const m = new THREE.Matrix4().compose(new THREE.Vector3(x, 1.4, 0), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, rz + Math.PI)), new THREE.Vector3(1, 1, 1));
    const g1 = paint(a, { top: 0xffffff, jitter: 0.05 }); g1.applyMatrix4(m); cloth.push(g1);
    const tip = new THREE.Vector3(0, L, 0).applyMatrix4(m); skin.push(part(new THREE.IcosahedronGeometry(0.06, 0), 0xffffff, tip.x, tip.y, tip.z)); return tip; };
  let phone = null;
  if (variant === 0) { arm(1, true); arm(-1, true); } else if (variant === 1) { arm(1, true); arm(-1, false); } else { const t = arm(1, true); arm(-1, false); phone = t; }
  const strip = (arr) => mergeGeometries(arr.map((g) => g.toNonIndexed ? (g.index ? g.toNonIndexed() : g) : g));
  return { cloth: strip(cloth), skin: strip(skin), phone };
}
export function makeCrowd({ count = 200, place, palette, scale = 1, phoneColor = 0xdfe9ff, phoneFrac = 0.4, seed = 1, noPhones = false }) {
  const R = rng(seed), group = new THREE.Group(), glow = [];
  const pal = (palette || [0x2a2f45, 0x6a2a3a, 0x3a5a6a, 0x8a8a92, 0x1c1c22, 0x7a5a3a, 0x3a3a52, 0xb0a090]).map((c) => new THREE.Color(c));
  const skins = [0xd9ac8a, 0xc08a68, 0x9a6a48, 0x6e472c, 0xe6bfa0].map((c) => new THREE.Color(c));
  const V = [0, 1, 2].map((v) => ({ ...body(v), items: [] }));
  for (let i = 0; i < count; i++) { const p = place(R, i); V[Math.min(noPhones ? 1 : 2, Math.floor(R() * (noPhones ? 2 : 3)))].items.push({ ...p, ph: R() * 6.28, sp: 0.8 + R() * 0.7, sc: scale * (0.92 + R() * 0.2), cl: pal[(R() * pal.length) | 0], sk: skins[(R() * skins.length) | 0] }); }
  const mats = { cloth: lpMat({ roughness: 0.9 }), skin: lpMat({ roughness: 0.8 }) };
  const rigs = V.map((v) => { const n = Math.max(1, v.items.length), a = new THREE.InstancedMesh(v.cloth, mats.cloth, n), b = new THREE.InstancedMesh(v.skin, mats.skin, n);
    a.castShadow = b.castShadow = true; a.receiveShadow = b.receiveShadow = true; a.frustumCulled = b.frustumCulled = false;
    v.items.forEach((it, i) => { a.setColorAt(i, it.cl); b.setColorAt(i, it.sk); }); group.add(a, b);
    let ph = null; if (v.phone) { ph = new THREE.InstancedMesh(new THREE.BoxGeometry(0.1, 0.18, 0.012), emissiveMat(phoneColor, 4), n); ph.frustumCulled = false; group.add(ph); glow.push(ph); }
    return { a, b, ph, v }; });
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pp = new THREE.Vector3(), ss = new THREE.Vector3(), mp = new THREE.Matrix4(), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  function update(t, energy = 1, visible = 1) {
    rigs.forEach(({ a, b, ph, v }) => { v.items.forEach((it, i) => {
      const hide = (it.appear ?? 0) > t || visible <= 0;
      const jump = Math.abs(Math.sin(t * 5.2 * it.sp + it.ph)) * 0.16 * energy;
      pp.set(it.x, (it.y ?? 0) + jump, it.z); q.setFromEuler(e.set(Math.sin(t * 2.6 * it.sp + it.ph) * 0.05 * energy, it.yaw ?? 0, Math.sin(t * 3.1 * it.sp + it.ph) * 0.07 * energy)); ss.setScalar(it.sc);
      m.compose(pp, q, ss); if (hide) { a.setMatrixAt(i, zero); b.setMatrixAt(i, zero); if (ph) ph.setMatrixAt(i, zero); } else { a.setMatrixAt(i, m); b.setMatrixAt(i, m); if (ph) { const t3 = v.phone; mp.makeTranslation(t3.x, t3.y + 0.09, t3.z + 0.05); ph.setMatrixAt(i, m.clone().multiply(mp)); } } });
      a.instanceMatrix.needsUpdate = b.instanceMatrix.needsUpdate = true; if (ph) ph.instanceMatrix.needsUpdate = true; });
  }
  update(0); return { group, update, glow };
}
