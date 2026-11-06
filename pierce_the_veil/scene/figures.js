// Faceless blocky band figures (silhouette + instrument), plus an instanced crowd.
import { THREE, flat, unlit, box, rng, clamp } from './common.js';

function addHair(head, style, color, color2) {
  const m = flat(color), g = new THREE.Group(); head.add(g);
  const add = (w, h, d, x, y, z, mat = m, rz = 0) => { const b = box(w, h, d, mat, x, y, z); b.rotation.z = rz; g.add(b); return b; };
  if (style === 'swoop') { add(0.64, 0.16, 0.64, 0, 0.62, 0); add(0.64, 0.5, 0.14, 0, 0.36, -0.25); add(0.14, 0.34, 0.5, 0.3, 0.45, 0); add(0.14, 0.34, 0.5, -0.3, 0.45, 0); add(0.7, 0.14, 0.3, 0.06, 0.6, 0.27, m, 0.28); }
  else if (style === 'long') { add(0.64, 0.16, 0.64, 0, 0.62, 0); add(0.66, 0.95, 0.14, 0, 0.12, -0.27); add(0.12, 0.7, 0.44, 0.31, 0.28, -0.05); add(0.12, 0.7, 0.44, -0.31, 0.28, -0.05); }
  else if (style === 'spike') { add(0.62, 0.14, 0.62, 0, 0.6, 0); [[-.2, -.1], [0, .1], [.2, -.05], [-.1, .2], [.12, -.22]].forEach(([x, z], i) => add(0.14, 0.34, 0.14, x, 0.8, z, m, (i - 2) * 0.12)); }
  else if (style === 'beanie') { add(0.68, 0.34, 0.68, 0, 0.68, 0); add(0.7, 0.1, 0.7, 0, 0.52, 0, flat(color2 || 0x222222)); }
  else if (style === 'cap') { add(0.64, 0.16, 0.64, 0, 0.62, 0); add(0.5, 0.05, 0.42, 0, 0.56, 0.46, flat(color2 || color)); }
  return g;
}

export function makeFigure(o = {}) {
  const S = o.scale ?? 1.3;
  const skin = flat(o.skin ?? 0xd9a27a), shirt = flat(o.shirt ?? 0x2a9d8f), pants = flat(o.pants ?? 0x2b2d42), shoe = flat(o.shoes ?? 0x15151c);
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const mkLeg = (x) => { const l = new THREE.Group(); l.position.set(x, 0.9, 0); l.add(box(0.3, 0.9, 0.32, pants, 0, -0.45, 0), box(0.32, 0.16, 0.44, shoe, 0, -0.86, 0.06)); root.add(l); return l; };
  const legL = mkLeg(0.18), legR = mkLeg(-0.18);
  body.add(box(0.74, 0.9, 0.42, shirt, 0, 1.35, 0));
  const head = new THREE.Group(); head.position.set(0, 1.8, 0); head.add(box(0.58, 0.58, 0.58, skin, 0, 0.31, 0)); body.add(head);
  if (o.shades) head.add(box(0.6, 0.1, 0.05, flat(0x050505), 0, 0.38, 0.3));
  if (o.hair !== false) addHair(head, o.hair?.style ?? 'swoop', o.hair?.color ?? 0x1b1b1b, o.hair?.color2);
  const mkArm = (x) => { const a = new THREE.Group(); a.position.set(x, 1.72, 0); a.add(box(0.25, 0.62, 0.27, shirt, 0, -0.31, 0), box(0.24, 0.24, 0.26, skin, 0, -0.74, 0)); body.add(a); return a; };
  const armL = mkArm(0.5), armR = mkArm(-0.5);
  root.scale.setScalar(S);
  const f = { root, body, head, armL, armR, legL, legR, S, mats: [skin, shirt, pants, shoe], seated: false };
  f.setOpacity = (a) => root.traverse((n) => { if (n.material) { const ms = Array.isArray(n.material) ? n.material : [n.material];
    ms.forEach((m) => { m.transparent = a < 0.999; m.opacity = a; m.depthWrite = a > 0.98; }); n.castShadow = a > 0.5; } });
  return f;
}

export function makeGuitar(color = 0xd62839, bass = false) {
  const g = new THREE.Group(), m = flat(color), wood = flat(0x6b4226), dark = flat(0x1a1a1a);
  const b = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.14, 8), m); b.rotation.x = Math.PI / 2; b.scale.set(1, 1, 1.2); b.castShadow = true; g.add(b);
  const L = bass ? 1.75 : 1.4;
  g.add(box(L, 0.09, 0.07, wood, 0.4 + L / 2, 0, 0.06), box(0.3, 0.17, 0.06, dark, 0.45 + L, 0, 0.06), box(0.22, 0.3, 0.03, flat(0xf3f3f3), 0.05, 0.05, 0.1));
  g.rotation.z = 0.55; return g;
}
export function makeMicStand() {
  const g = new THREE.Group(), d = flat(0x222222);
  g.add(box(0.7, 0.06, 0.7, d, 0, 0.03, 0), box(0.06, 2.3, 0.06, d, 0, 1.2, 0), box(0.2, 0.28, 0.2, flat(0xbbbbbb), 0, 2.45, 0.05)); return g;
}
export function makeDrumKit(color = 0xd62839) {
  const g = new THREE.Group(), sh = flat(color), white = flat(0xf0f0f0), gold = flat(0xe6b422, { metalness: 0.4, roughness: 0.5 });
  const cyl = (r, h, mat, x, y, z, rx = 0) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 10), mat); m.position.set(x, y, z); m.rotation.x = rx; m.castShadow = true; g.add(m); return m; };
  cyl(0.62, 0.6, sh, 0, 0.7, 0.7, Math.PI / 2);          // kick
  cyl(0.64, 0.05, white, 0, 0.7, 1.02, Math.PI / 2);
  cyl(0.34, 0.26, white, -0.35, 1.45, 0.55); cyl(0.3, 0.26, white, 0.35, 1.45, 0.55);   // toms
  cyl(0.38, 0.24, white, 0.05, 1.0, 0.1);  // snare
  cyl(0.46, 0.5, sh, -1.0, 0.85, 0.25);    // floor tom
  [[-1.1, 1.9, 0.5], [1.15, 1.8, 0.4], [0.9, 1.35, 0.2]].forEach(([x, y, z], i) => { cyl(i === 2 ? 0.34 : 0.5, 0.04, gold, x, y, z); g.add(box(0.04, y, 0.04, flat(0x333333), x, y / 2, z)); });
  g.add(box(0.7, 0.14, 0.7, flat(0x1d1d24), 0, 0.7, -0.95));
  return g;
}

export function setSeated(f, on) { f.seated = on; f.legL.position.y = f.legR.position.y = on ? 0.55 : 0.9; f.body.position.y = on ? -0.35 : 0; }

export function animateFigure(f, t, mode = 'idle', ph = 0, amp = 1) {
  const s = Math.sin, b = t * 5 + ph;
  f.armL.rotation.set(0, 0, 0); f.armR.rotation.set(0, 0, 0); f.legL.rotation.set(0, 0, 0); f.legR.rotation.set(0, 0, 0); f.head.rotation.set(0, 0, 0);
  const by = f.seated ? -0.35 : 0; f.body.position.y = by; f.body.rotation.set(0, 0, 0);
  if (mode === 'idle') { f.body.position.y = by + s(t * 2 + ph) * 0.015; f.armL.rotation.z = 0.08; f.armR.rotation.z = -0.08; f.head.rotation.y = s(t * 0.8 + ph) * 0.25; }
  else if (mode === 'guitar') {
    f.body.position.y = by + Math.abs(s(b)) * 0.06 * amp; f.head.rotation.x = 0.15 + s(b) * 0.2 * amp; f.head.rotation.z = s(b * 0.5) * 0.12;
    f.armL.rotation.set(-1.05, 0, -0.5); f.armR.rotation.set(-0.85 + s(b * 2) * 0.3 * amp, 0, 0.12);
    f.legL.rotation.z = -0.14; f.legR.rotation.z = 0.14; f.body.rotation.x = 0.05;
  } else if (mode === 'sing') {
    f.head.rotation.x = -0.2 + s(b) * 0.12; f.armR.rotation.set(-1.75, 0, 0.3); f.armL.rotation.set(-0.25 + s(b * 0.5) * 0.3, 0, 0.55 + s(b) * 0.2);
    f.body.position.y = by + Math.abs(s(b * 0.5)) * 0.04;
  } else if (mode === 'drum') {
    f.legL.rotation.x = f.legR.rotation.x = -1.3; f.legL.rotation.z = 0.1; f.legR.rotation.z = -0.1;
    const d = t * 9 + ph; f.armL.rotation.set(-1.25 + s(d) * 0.55 * amp, 0, -0.3); f.armR.rotation.set(-1.25 + s(d + Math.PI) * 0.55 * amp, 0, 0.3);
    f.head.rotation.x = 0.1 + s(d * 0.5) * 0.18; f.body.position.y = by + Math.abs(s(d * 0.5)) * 0.04;
  } else if (mode === 'walk') {
    const w = t * 8 + ph; f.legL.rotation.x = s(w) * 0.7; f.legR.rotation.x = -s(w) * 0.7; f.armL.rotation.x = -s(w) * 0.6; f.armR.rotation.x = s(w) * 0.6;
    f.body.position.y = by + Math.abs(s(w)) * 0.07;
  } else if (mode === 'cheer') {
    f.armL.rotation.z = 2.7 + s(b) * 0.3; f.armR.rotation.z = -2.7 - s(b + 1) * 0.3; f.body.position.y = by + Math.abs(s(b * 0.8)) * 0.3; f.head.rotation.x = -0.2;
  } else if (mode === 'wave') {
    f.armR.rotation.z = -2.5; f.armR.rotation.x = s(b * 1.5) * 0.4; f.armL.rotation.z = 0.08; f.body.position.y = by + s(t * 2) * 0.015;
  } else if (mode === 'stand') { f.armL.rotation.z = 0.06; f.armR.rotation.z = -0.06; f.head.rotation.x = 0.35; }
}

// ---------- instanced crowd ----------
export function makeCrowd({ count, seed = 1, place, appear, palette, scale = 1.25, y = 0 }) {
  const R = rng(seed), group = new THREE.Group();
  const geo = { legs: new THREE.BoxGeometry(0.62, 0.9, 0.34), torso: new THREE.BoxGeometry(0.74, 0.9, 0.42), head: new THREE.BoxGeometry(0.58, 0.58, 0.58), arm: new THREE.BoxGeometry(0.22, 0.8, 0.24) };
  const mk = (g) => { const m = new THREE.InstancedMesh(g, flat(0xffffff), count); m.castShadow = true; m.frustumCulled = false; group.add(m); return m; };
  const M = { legs: mk(geo.legs), torso: mk(geo.torso), head: mk(geo.head), armL: mk(geo.arm), armR: mk(geo.arm) };
  const skins = [0xf1c27d, 0xd9a27a, 0xa9744f, 0x7a4b2a, 0xffdbac].map((c) => new THREE.Color(c));
  const pal = (palette || [0xe63946, 0x1d3557, 0xf1faee, 0xffd166, 0x06d6a0, 0x8338ec, 0xff9f1c, 0x222222]).map((c) => new THREE.Color(c));
  const P = [];
  for (let i = 0; i < count; i++) {
    const p = place(R, i), sh = pal[(R() * pal.length) | 0], sk = skins[(R() * skins.length) | 0];
    P.push({ x: p.x, z: p.z, y: p.y ?? y, yaw: p.yaw ?? 0, ph: R() * 6.28, sp: 0.8 + R() * 0.6, sc: scale * (0.9 + R() * 0.25), at: appear ? appear(i, R) : -1, cheer: 0.5 + R() * 0.5 });
    M.legs.setColorAt(i, new THREE.Color(0x1f2430).lerp(sh, R() * 0.3)); M.torso.setColorAt(i, sh); M.head.setColorAt(i, sk); M.armL.setColorAt(i, sh); M.armR.setColorAt(i, sh);
  }
  const m0 = new THREE.Matrix4(), mm = new THREE.Matrix4(), tr = new THREE.Matrix4(), rz = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), one = new THREE.Vector3(1, 1, 1), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  const set = (mesh, i, base, lx, ly, lz) => { tr.makeTranslation(lx, ly, lz); mm.multiplyMatrices(base, tr); mesh.setMatrixAt(i, mm); };
  function update(t, energy = 1) {
    for (let i = 0; i < count; i++) {
      const p = P[i], age = t - p.at;
      if (p.at >= 0 && age < 0) { for (const k in M) M[k].setMatrixAt(i, zero); continue; }
      const pop = p.at >= 0 ? Math.min(1, age / 0.35) : 1, sc = p.sc * (pop < 1 ? 1 + Math.sin(pop * Math.PI) * 0.25 : 1) * pop;
      const jump = Math.abs(Math.sin(t * 5 * p.sp + p.ph)) * 0.35 * energy * p.cheer;
      q.setFromEuler(e.set(0, p.yaw, 0)); m0.compose(new THREE.Vector3(p.x, p.y + jump * p.sc, p.z), q, new THREE.Vector3(sc, sc, sc));
      set(M.legs, i, m0, 0, 0.45, 0); set(M.torso, i, m0, 0, 1.35, 0); set(M.head, i, m0, 0, 2.1, 0);
      const ang = 2.4 + Math.sin(t * 6 * p.sp + p.ph) * 0.35 * energy;
      for (const [k, sx, sg] of [['armL', 0.5, 1], ['armR', -0.5, -1]]) {
        rz.makeRotationZ(sg * ang); tr.makeTranslation(sx, 1.72, 0); mm.multiplyMatrices(m0, tr).multiply(rz); tr.makeTranslation(0, 0.4, 0); mm.multiply(tr); M[k].setMatrixAt(i, mm);
      }
    }
    for (const k in M) { M[k].instanceMatrix.needsUpdate = true; }
  }
  update(0); return { group, update };
}

// A band on a flat deck facing +z. Front line at z=0, kit behind. `show` toggles members.
export function makeBand({ scale = 1.6, kitY = 0, kitZ = -7, show = {} } = {}) {
  const g = new THREE.Group(), sk = scale / 1.5, F = {};
  const mk = (name, o, pos, guitar) => { const f = makeFigure({ scale, ...o }); f.root.position.set(...pos); if (guitar) { guitar.position.set(-0.05, 1.15, 0.32); f.body.add(guitar); } g.add(f.root); f.root.visible = show[name] !== false; F[name] = f; return f; };
  mk('vic', { shirt: 0x1d1d26, pants: 0x2b2d42, hair: { style: 'swoop', color: 0x111111 } }, [0, 0, 1.5 * sk], makeGuitar(0xd62839));
  mk('tony', { shirt: 0x8a2f28, pants: 0x1b1b22, hair: { style: 'long', color: 0x2a1a10 } }, [-6.5 * sk, 0, 0], makeGuitar(0x1fb6c1));
  mk('jaime', { shirt: 0x264653, pants: 0x22222a, hair: { style: 'beanie', color: 0x222222, color2: 0x999999 } }, [6.5 * sk, 0, 0], makeGuitar(0x222a35, true));
  const mic = makeMicStand(); mic.position.set(0.1 * sk, 0, 3.2 * sk); mic.scale.setScalar(scale / 1.25); g.add(mic);
  const kit = makeDrumKit(0xd62839); kit.scale.setScalar(scale); kit.position.set(0, kitY, kitZ * sk); g.add(kit);
  const seatY = kitY + 0.77 * scale - 0.55 * scale, seatZ = kitZ * sk - 0.9 * scale;
  const mike = mk('mike', { shirt: 0xf1f1f1, pants: 0x3a3a4a, hair: { style: 'spike', color: 0x222222 }, shades: true }, [0, seatY, seatZ]); setSeated(mike, true);
  const nd = mk('newdrummer', { shirt: 0x2bd96b, pants: 0x1a1d24, hair: { style: 'cap', color: 0x111111, color2: 0x2bd96b } }, [0, seatY, seatZ]); setSeated(nd, true); nd.root.visible = !!show.newdrummer;
  const update = (t, mode = 'play', energy = 1) => {
    const m = mode === 'play';
    animateFigure(F.vic, t, m ? 'guitar' : 'stand', 0, energy); animateFigure(F.tony, t, m ? 'guitar' : 'stand', 1.3, energy); animateFigure(F.jaime, t, m ? 'guitar' : 'stand', 2.1, energy);
    animateFigure(F.mike, t, m ? 'drum' : 'stand', 0.4, energy); animateFigure(F.newdrummer, t, m ? 'drum' : 'stand', 0.4, energy);
    if (!m) { F.mike.legL.rotation.x = F.mike.legR.rotation.x = F.newdrummer.legL.rotation.x = F.newdrummer.legR.rotation.x = -1.3; }
  };
  return { group: g, figs: F, kit, mic, update };
}
