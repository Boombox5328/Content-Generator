// Low-poly jointed humanoid, ~6 heads tall (1.8 m), faceless, readable by silhouette.
import { THREE, paint, bevelBox, mesh, M, col, rng, lerp, tris, clamp } from '../engine/lowpoly.js';

const limb = (rt, rb, len, seg, hs, top, bottom, seed) => { const g = new THREE.CylinderGeometry(rt, rb, len, seg, hs); g.translate(0, -len / 2, 0); return paint(g, { top, bottom, seed }); };
const ball = (r, d, sx, sy, sz, c, seed, jit = 0.05) => { const g = new THREE.IcosahedronGeometry(r, d); g.scale(sx, sy, sz); return paint(g, { top: c, bottom: c, jitter: jit, seed }); };
const grp = (parent, x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; };
const put = (parent, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); parent.add(m); return m; };

function addHair(head, style, c, c2, seed) {
  const R = rng(seed), cap = (r, th, y = 0.155, z = -0.012) => { const g = new THREE.SphereGeometry(r, 8, 5, 0, Math.PI * 2, 0, th); g.scale(1, 1.02, 1.05); return g; };
  if (style === 'long') {                                    // Vic: long dark hair
    put(head, paint(cap(0.158, Math.PI * 0.6), { top: c, bottom: c2 ?? c, seed, jitter: 0.12 }), 0, 0.15, -0.01);
    for (let i = 0; i < 7; i++) { const a = -1.25 + (i / 6) * 2.5 + Math.PI, s = new THREE.CylinderGeometry(0.05, 0.016, 0.34 + R() * 0.1, 4); s.translate(0, -0.18, 0);
      const m = put(head, paint(s, { top: c, bottom: c2 ?? c, seed: seed + i, jitter: 0.15 }), Math.sin(a) * 0.125, 0.14, Math.cos(a) * 0.125 - 0.01); m.rotation.set(Math.cos(a) * -0.22, 0, Math.sin(a) * 0.22); }
  } else if (style === 'messy') {                            // Tony: spiky messy
    put(head, paint(cap(0.156, Math.PI * 0.5), { top: c, bottom: c2 ?? c, seed, jitter: 0.1 }), 0, 0.15, -0.012);
    for (let i = 0; i < 9; i++) { const a = R() * 6.28, e = 0.15 + R() * 0.7, cn = new THREE.ConeGeometry(0.04, 0.12 + R() * 0.06, 4); cn.translate(0, 0.07, 0);
      const m = put(head, paint(cn, { top: c, bottom: c2 ?? c, seed: seed + i }), Math.cos(a) * 0.1 * Math.sin(e + 0.5), 0.27 + Math.cos(e) * 0.02, Math.sin(a) * 0.1 * Math.sin(e + 0.5) - 0.01); m.rotation.set(Math.sin(a) * 0.9, 0, -Math.cos(a) * 0.9); }
  } else if (style === 'snapback') {                         // Jaime: cap with brim
    put(head, paint(cap(0.164, Math.PI * 0.56), { top: c, bottom: c2 ?? c, seed, jitter: 0.06 }), 0, 0.155, -0.005);
    const b = new THREE.BoxGeometry(0.2, 0.02, 0.15); const p = b.attributes.position; for (let i = 0; i < p.count; i++) if (p.getZ(i) > 0) p.setX(i, p.getX(i) * 1.25);
    put(head, paint(b, { top: c2 ?? c, jitter: 0.05, seed }), 0, 0.225, 0.19).rotation.x = 0.12;
  } else if (style === 'short') {                            // drummer: short cropped
    put(head, paint(cap(0.152, Math.PI * 0.5), { top: c, bottom: c2 ?? c, seed, jitter: 0.1 }), 0, 0.15, -0.012);
  }
}

// spec: { skin, shirt:[top,bottom], pants:[top,bottom], shoes, hair:{style,color,color2}, accent, seed, scale }
export function makeHuman(spec = {}) {
  const S = spec.seed ?? 1, skin = spec.skin ?? 0xd6a07a, sh = spec.shirt ?? [0x2a2f45, 0x151826], pn = spec.pants ?? [0x23252e, 0x12131a], shoes = spec.shoes ?? 0x15151a, acc = spec.accent ?? 0x8a8f9c;
  const root = new THREE.Group(), j = {};
  j.hips = grp(root, 0, 0.9, 0);
  const pel = new THREE.CylinderGeometry(0.165, 0.15, 0.2, 8, 1); pel.scale(1.2, 1, 0.8); put(j.hips, paint(pel, { top: pn[0], bottom: pn[1], seed: S }), 0, 0, 0);
  j.spine = grp(j.hips, 0, 0.08, 0);
  const ch = new THREE.CylinderGeometry(0.19, 0.135, 0.5, 8, 3); ch.translate(0, 0.25, 0); { const p = ch.attributes.position; for (let i = 0; i < p.count; i++) { const y = p.getY(i); if (y > 0.38) p.setX(i, p.getX(i) * 1.14); if (y > 0.12 && y < 0.3) p.setZ(i, p.getZ(i) * 1.08); } ch.scale(1.22, 1, 0.86); }
  put(j.spine, paint(ch, { top: sh[0], bottom: sh[1], seed: S + 1, jitter: 0.08 }), 0, 0, 0);
  put(j.spine, paint(new THREE.CylinderGeometry(0.162, 0.162, 0.045, 8), { top: acc, jitter: 0.04, seed: S }), 0, 0.0, 0).scale.set(1.2, 1, 0.78);   // belt
  j.neck = grp(j.spine, 0, 0.5, 0); put(j.neck, paint(new THREE.CylinderGeometry(0.05, 0.056, 0.1, 6), { top: skin, jitter: 0.04, seed: S }), 0, 0.04, 0);
  j.head = grp(j.neck, 0, 0.08, 0);
  const hd = new THREE.IcosahedronGeometry(0.15, 1); hd.scale(0.94, 1.1, 1.03); put(j.head, paint(hd, { top: skin, bottom: new THREE.Color(skin).multiplyScalar(0.82).getHex(), jitter: 0.04, seed: S + 2 }), 0, 0.15, 0);
  addHair(j.head, spec.hair?.style ?? 'short', spec.hair?.color ?? 0x2a1c14, spec.hair?.color2, S + 5);
  for (const [k, sx] of [['L', 1], ['R', -1]]) {
    j['sh' + k] = grp(j.spine, sx * 0.235, 0.45, 0);
    put(j['sh' + k], ball(0.068, 0, 1, 1, 1, sh[0], S + 6), 0, 0, 0);
    put(j['sh' + k], limb(0.058, 0.047, 0.27, 6, 2, sh[0], sh[1], S + 7), 0, 0, 0);
    j['el' + k] = grp(j['sh' + k], 0, -0.27, 0); put(j['el' + k], ball(0.045, 0, 1, 1, 1, skin, S + 8), 0, 0, 0);
    put(j['el' + k], limb(0.046, 0.036, 0.25, 6, 2, skin, skin, S + 9), 0, 0, 0);
    j['hd' + k] = grp(j['el' + k], 0, -0.25, 0); put(j['hd' + k], ball(0.046, 0, 0.9, 1.3, 0.6, skin, S + 10), 0, -0.05, 0);
    j['hp' + k] = grp(j.hips, sx * 0.095, -0.02, 0);
    put(j['hp' + k], limb(0.1, 0.071, 0.42, 7, 2, pn[0], pn[1], S + 11), 0, 0, 0);
    j['kn' + k] = grp(j['hp' + k], 0, -0.42, 0); put(j['kn' + k], ball(0.058, 0, 1, 1, 1, pn[1], S + 12), 0, 0, 0);
    put(j['kn' + k], limb(0.07, 0.052, 0.42, 7, 2, pn[1], pn[1], S + 13), 0, 0, 0);
    j['an' + k] = grp(j['kn' + k], 0, -0.42, 0);
    put(j['an' + k], paint(new THREE.BoxGeometry(0.115, 0.085, 0.3), { top: shoes, bottom: 0x050506, jitter: 0.05, seed: S }), 0, -0.04, 0.07);
  }
  root.scale.setScalar(spec.scale ?? 1);
  const fig = { root, j, spec, tris: tris(root) };
  fig.attach = (obj, joint = 'spine') => { j[joint].add(obj); return obj; };
  return fig;
}

// ------------ poses (deterministic functions of t) ------------
function reset(j) { for (const k in j) { j[k].rotation.set(0, 0, 0); } j.hips.position.set(0, 0.9, 0); j.spine.position.set(0, 0.08, 0); }
export function pose(fig, t, mode = 'idle', o = {}) {
  const j = fig.j, ph = o.ph ?? 0, tempo = o.tempo ?? 1, s = Math.sin, w = t * 2.1 * tempo + ph;
  reset(j); const side = s(t * 1.1 + ph);
  j.hips.position.x = side * 0.015; j.hips.rotation.z = side * 0.03; j.spine.rotation.z = -side * 0.04; j.head.rotation.y = s(t * 0.55 + ph) * 0.18;
  if (mode === 'idle') { j.shL.rotation.z = 0.1; j.shR.rotation.z = -0.1; j.elL.rotation.x = j.elR.rotation.x = -0.2; j.knL.rotation.x = 0.04 + side * 0.04; j.knR.rotation.x = 0.04 - side * 0.04; }
  else if (mode === 'guitar') {                              // strumming + head bob
    const b = s(w * 2), strum = s(t * 15 * tempo + ph);
    j.hips.position.y = 0.9 - 0.03 + Math.abs(b) * 0.02; j.hpL.rotation.z = -0.13; j.hpR.rotation.z = 0.13; j.knL.rotation.x = j.knR.rotation.x = 0.28;
    j.hpL.rotation.x = j.hpR.rotation.x = -0.14; j.spine.rotation.x = 0.1 + b * 0.04; j.head.rotation.x = 0.18 + b * 0.16;
    j.shR.rotation.set(-0.55 + strum * 0.08, 0, -0.15); j.elR.rotation.x = -1.15 + strum * 0.35;
    j.shL.rotation.set(-0.95, 0, 0.5); j.elL.rotation.x = -0.75;
  } else if (mode === 'sing') {
    const b = s(w * 2);
    j.hpL.rotation.z = -0.1; j.hpR.rotation.z = 0.1; j.knL.rotation.x = j.knR.rotation.x = 0.12; j.spine.rotation.x = -0.05 + b * 0.03; j.head.rotation.x = -0.28 + b * 0.05;
    j.shR.rotation.set(-1.45, 0, -0.1); j.elR.rotation.x = -1.55; j.shL.rotation.set(-0.2, 0, 0.5 + s(w) * 0.25); j.elL.rotation.x = -0.4;
  } else if (mode === 'drum') {                              // seated behind the kit
    const d = t * 9 * tempo + ph;
    j.hips.position.y = 0.55; j.hpL.rotation.x = j.hpR.rotation.x = -1.42; j.knL.rotation.x = j.knR.rotation.x = 1.35; j.hpL.rotation.z = -0.2; j.hpR.rotation.z = 0.2;
    j.spine.rotation.x = 0.1; j.head.rotation.x = 0.12 + s(d * 0.5) * 0.1;
    j.shL.rotation.set(-0.85 + s(d) * 0.35, 0, 0.25); j.elL.rotation.x = -1.0 + s(d) * 0.3; j.shR.rotation.set(-0.85 + s(d + Math.PI) * 0.35, 0, -0.25); j.elR.rotation.x = -1.0 + s(d + Math.PI) * 0.3;
  } else if (mode === 'headbang') {
    const b = s(w * 2.2); j.spine.rotation.x = 0.2 + b * 0.12; j.head.rotation.x = 0.3 + b * 0.35; j.hpL.rotation.z = -0.15; j.hpR.rotation.z = 0.15; j.knL.rotation.x = j.knR.rotation.x = 0.3;
    j.shL.rotation.set(-0.95, 0, 0.5); j.elL.rotation.x = -0.75; j.shR.rotation.set(-0.6, 0, -0.15); j.elR.rotation.x = -1.2;
  } else if (mode === 'cheer') {
    const b = s(w * 1.6); j.hips.position.y = 0.9 + Math.abs(b) * 0.06; j.shL.rotation.z = 2.7 + b * 0.25; j.shR.rotation.z = -2.7 - b * 0.25; j.head.rotation.x = -0.2;
  } else if (mode === 'sit') { j.hips.position.y = 0.55; j.hpL.rotation.x = j.hpR.rotation.x = -1.42; j.knL.rotation.x = j.knR.rotation.x = 1.35; j.shL.rotation.set(-0.5, 0, 0.1); j.shR.rotation.set(-0.5, 0, -0.1); j.elL.rotation.x = j.elR.rotation.x = -1.0; j.head.rotation.x = 0.25; }
}
export const BAND = {
  vic:   { seed: 11, skin: 0xc79a7c, shirt: [0x2b2630, 0x14111a], pants: [0x1e2028, 0x101118], accent: 0x9c2a2a, hair: { style: 'long', color: 0x1a1620, color2: 0x08070a } },
  tony:  { seed: 23, skin: 0xb98a68, shirt: [0x8a3a30, 0x4a1e1c], pants: [0x2a2f3a, 0x15181f], accent: 0xb89a5a, hair: { style: 'messy', color: 0x3a2418, color2: 0x1c120c } },
  jaime: { seed: 37, skin: 0xa9754f, shirt: [0x2f5d6e, 0x15303a], pants: [0x2a2a30, 0x15151a], accent: 0xd0c8a0, hair: { style: 'snapback', color: 0x2a3a52, color2: 0xcfd6e4 } },
  mike:  { seed: 51, skin: 0xd2a584, shirt: [0xd8d4cc, 0x8a8680], pants: [0x2c303c, 0x16181f], accent: 0x555555, hair: { style: 'short', color: 0x2a1c12, color2: 0x120c08 } },
};
