// Set dressing kit — all bevelled / faceted / vertex-coloured.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube, lerp, clamp, col } from '../engine/lowpoly.js';

const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };
const DS = lpMat({ side: THREE.DoubleSide });

export function lapSiding(w, h, c0 = 0x8a8f9c, c1 = 0x5a5f6c, board = 0.2, seed = 1) {
  const g = new THREE.Group(), n = Math.ceil(h / board), R = rng(seed);
  for (let i = 0; i < n; i++) { const t = i / n; put(g, bevelBox(w, board * 0.98, 0.07, 0.012, { top: new THREE.Color(c1).lerp(new THREE.Color(c0), 1 - t).getHex(), bottom: new THREE.Color(c1).lerp(new THREE.Color(c0), 1 - t).multiplyScalar(0.82).getHex(), axis: 'y', seed: seed + i, jitter: 0.06 }), 0, i * board + board / 2, 0); }
  return g;
}
export function palm(h = 8, seed = 1) {
  const g = new THREE.Group(), R = rng(seed), segs = 9; let y = 0, x = 0;
  const lean = (R() - 0.5) * 0.5;
  for (let i = 0; i < segs; i++) { const r0 = 0.2 - i * 0.012, sh = h / segs; const c = new THREE.CylinderGeometry(r0 * 0.9, r0 * (i % 2 ? 1.12 : 1.02), sh, 6); c.translate(0, sh / 2, 0);
    const m = put(g, paint(c, { top: 0x5a4a3a, bottom: 0x3a2e24, jitter: 0.1, seed: seed + i }), x, y, 0); y += sh * 0.98; x += lean * 0.12; }
  const crown = new THREE.Group(); crown.position.set(x, y, 0); g.add(crown);
  put(crown, paint(new THREE.IcosahedronGeometry(0.28, 0), { top: 0x4a3a2a, jitter: 0.1 }), 0, 0, 0);
  const n = 11;
  for (let f = 0; f < n; f++) {
    const a = (f / n) * Math.PI * 2 + R() * 0.3, L = 2.6 + R() * 0.8, seg = 6, pos = [];
    const pts = []; for (let k = 0; k <= seg; k++) { const u = k / seg; pts.push([u * L * Math.cos(0), Math.sin(u * 2.2) * 0.9 - u * u * 1.8 + 0.2, 0, u]); }
    const idx = []; const verts = [];
    for (let k = 0; k <= seg; k++) { const w = 0.4 * Math.sin((1 - pts[k][3]) * Math.PI * 0.55 + 0.25) + 0.02; verts.push(pts[k][0], pts[k][1], w, pts[k][0], pts[k][1] + 0.04, -w); }
    for (let k = 0; k < seg; k++) { const a0 = k * 2; idx.push(a0, a0 + 1, a0 + 2, a0 + 1, a0 + 3, a0 + 2); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3)); geo.setIndex(idx);
    const m = put(crown, paint(geo, { top: 0x2e6a3a, bottom: 0x14301c, axis: 'x', jitter: 0.12, seed: seed + f }), 0, 0, 0, DS); m.rotation.y = a; m.rotation.z = (R() - 0.5) * 0.3;
  }
  return g;
}
export function streetLamp(h = 6.2) {
  const g = new THREE.Group(), glow = [];
  put(g, paint(new THREE.CylinderGeometry(0.07, 0.1, h, 6), { top: 0x3a3f4a, bottom: 0x1a1d24, jitter: 0.05 }), 0, h / 2, 0);
  put(g, bevelBox(1.5, 0.08, 0.1, 0.02, { top: 0x3a3f4a }), 0.7, h, 0);
  put(g, bevelBox(0.6, 0.14, 0.26, 0.04, { top: 0x2a2d36 }), 1.4, h - 0.05, 0);
  const lens = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.03, 0.2), emissiveMat(0xffc880, 6)); lens.position.set(1.4, h - 0.14, 0); g.add(lens); glow.push(lens);
  g.userData.glow = glow; g.userData.lampPos = new THREE.Vector3(1.4, h - 0.16, 0); return g;
}
export function stringLights(p0, p1, { sag = 0.4, count = 12, color = 0xffc070, bulb = 0.045, wire = 0x1a1a1a } = {}) {
  const g = new THREE.Group(), a = new THREE.Vector3(...p0), b = new THREE.Vector3(...p1), glow = [], pts = [];
  for (let i = 0; i <= 14; i++) { const u = i / 14; const p = a.clone().lerp(b, u); p.y -= Math.sin(u * Math.PI) * sag; pts.push(p); }
  g.add(tube(pts, 0.006, 3, false, wire));
  for (let i = 1; i < count; i++) { const u = i / count, p = a.clone().lerp(b, u); p.y -= Math.sin(u * Math.PI) * sag - 0.03;
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(bulb, 0), emissiveMat(color, 7)); m.position.copy(p); m.position.y -= 0.05; g.add(m); glow.push(m); }
  g.userData.glow = glow; return g;
}
function posterTex(seed, pal) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 384; const g = c.getContext('2d'), R = rng(seed);
  g.fillStyle = pal[0]; g.fillRect(0, 0, 256, 384);
  for (let i = 0; i < 9; i++) { g.fillStyle = pal[1 + ((R() * (pal.length - 1)) | 0)]; const x = R() * 256, y = R() * 384, w = 40 + R() * 150, h = 40 + R() * 150; if (R() > 0.5) g.fillRect(x, y, w, h); else { g.beginPath(); g.moveTo(x, y); g.lineTo(x + w, y + R() * h); g.lineTo(x + R() * w, y + h); g.fill(); } }
  g.fillStyle = 'rgba(0,0,0,.22)'; g.fillRect(0, 300, 256, 84); g.fillStyle = 'rgba(255,255,255,.7)'; g.fillRect(20, 330, 150, 10); g.fillRect(20, 350, 100, 8);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
export function poster(w, h, seed = 1, pal = ['#1b1b2a', '#c0392b', '#e8c872', '#2a7a8a', '#eae0d0']) {
  const g = new THREE.Group(); const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: posterTex(seed, pal), roughness: 0.9, flatShading: true })); m.receiveShadow = true; m.position.z = 0.004; g.add(m);
  put(g, bevelBox(w + 0.03, h + 0.03, 0.01, 0.003, { top: 0x1a1a1a }), 0, 0, 0); g.rotation.z = (rng(seed)() - 0.5) * 0.06; return g;
}
export function pegboard(w = 2.4, h = 1.5, seed = 3) {
  const g = new THREE.Group(), R = rng(seed);
  put(g, bevelBox(w, h, 0.03, 0.008, { top: 0xb09a74, bottom: 0x8a7650, jitter: 0.05 }), 0, 0, 0);
  const c = document.createElement('canvas'); c.width = 256; c.height = 160; const x = c.getContext('2d'); x.fillStyle = '#b59d76'; x.fillRect(0, 0, 256, 160); x.fillStyle = 'rgba(40,28,14,.55)';
  for (let i = 0; i < 16; i++) for (let j = 0; j < 10; j++) { x.beginPath(); x.arc(8 + i * 16, 8 + j * 16, 2.2, 0, 7); x.fill(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: t, roughness: 1 })); face.position.z = 0.0165; face.receiveShadow = true; g.add(face);
  const tool = (kind, x0, y0, rot, c0) => { const t = new THREE.Group(); t.position.set(x0, y0, 0.05); t.rotation.z = rot; g.add(t);
    if (kind === 'hammer') { put(t, bevelBox(0.05, 0.4, 0.03, 0.008, { top: 0x7a5230 }), 0, 0, 0); put(t, bevelBox(0.2, 0.08, 0.05, 0.01, { top: 0x8a8f9a, bottom: 0x4a4f5a }), 0, 0.2, 0); }
    else if (kind === 'wrench') { put(t, bevelBox(0.05, 0.38, 0.02, 0.006, { top: 0xaab0ba, bottom: 0x6a707a }), 0, 0, 0); put(t, bevelBox(0.12, 0.09, 0.02, 0.006, { top: 0xaab0ba }), 0, 0.2, 0); }
    else if (kind === 'saw') { const s = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(0.55, 0.05), new THREE.Vector2(0.55, 0.12), new THREE.Vector2(0, 0.14)]); const gg = new THREE.ExtrudeGeometry(s, { depth: 0.008, bevelEnabled: false }); put(t, paint(gg, { top: 0xc8ccd4, bottom: 0x7a7f8a }), -0.25, 0, 0); put(t, bevelBox(0.14, 0.08, 0.03, 0.01, { top: c0 }), -0.31, 0.07, 0.01); }
    else put(t, bevelBox(0.12, 0.12, 0.05, 0.015, { top: c0 }), 0, 0, 0); };
  tool('hammer', -0.8, 0.25, 0.05, 0); tool('wrench', -0.5, 0.3, -0.1, 0); tool('saw', 0.1, 0.4, 0.0, 0xc0392b); tool('wrench', 0.7, 0.3, 0.08, 0); tool('hammer', 0.95, 0.15, -0.06, 0);
  tool('box', -0.7, -0.35, 0, 0xc0392b); tool('box', -0.3, -0.4, 0, 0xe8c872); tool('box', 0.2, -0.38, 0, 0x2a7a8a); tool('box', 0.7, -0.4, 0, 0xc0392b);
  return g;
}
export function cloud(seed = 1, s = 1, tint = 0xffffff, shade = 0xc0a8c8) {
  const g = new THREE.Group(), R = rng(seed);
  for (let i = 0; i < 6; i++) { const r = (0.7 + R() * 0.8) * s, b = new THREE.IcosahedronGeometry(r, 1); b.scale(1.3, 0.7, 1); put(g, paint(b, { top: tint, bottom: shade, jitter: 0.06, seed: seed + i }), (i - 2.5) * s * 0.9 + R() * s * 0.4, R() * s * 0.35, (R() - 0.5) * s * 0.8, lpMat({ roughness: 1, emissive: new THREE.Color(tint).multiplyScalar(0.12) })); }
  g.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } }); return g;
}
export function rainWindow(w, h, seed = 4) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 512; const g = c.getContext('2d'), R = rng(seed);
  g.clearRect(0, 0, 256, 512); g.lineCap = 'round';
  for (let i = 0; i < 110; i++) { const x = R() * 256, y = R() * 512, L = 40 + R() * 160; g.strokeStyle = `rgba(190,215,255,${0.1 + R() * 0.35})`; g.lineWidth = 0.6 + R() * 1.8; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - 0.5) * 6, y + L); g.stroke(); }
  for (let i = 0; i < 70; i++) { g.fillStyle = `rgba(210,230,255,${0.2 + R() * 0.4})`; g.beginPath(); g.arc(R() * 256, R() * 512, 1 + R() * 3, 0, 7); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, opacity: 0.9 }));
  m.userData.update = (tm) => { t.offset.y = -tm * 0.35; }; return m;
}
export function cityBokeh(w, h, seed = 6, palette = [0xff9a50, 0x7fc8ff, 0xff4f7a, 0xffe08a]) {   // out-of-focus city lights seen through a window
  const g = new THREE.Group(), R = rng(seed), glow = [];
  put(g, new THREE.PlaneGeometry(w, h), 0, 0, 0, new THREE.MeshBasicMaterial({ color: 0x0a0e1c, toneMapped: false })).castShadow = false;
  for (let i = 0; i < 70; i++) { const m = new THREE.Mesh(new THREE.CircleGeometry(0.05 + R() * 0.16, 7), emissiveMat(palette[(R() * palette.length) | 0], 1.8 + R() * 2)); m.position.set((R() - 0.5) * w * 0.95, (R() - 0.2) * h * 0.55 - h * 0.1, 0.01); g.add(m); glow.push(m); }
  g.userData.glow = glow; return g;
}
export function crate(w = 0.5, h = 0.4, d = 0.4, c = 0x6a4a2a) { return bevelBox(w, h, d, 0.015, { top: c, bottom: new THREE.Color(c).multiplyScalar(0.7).getHex(), jitter: 0.08, seed: Math.round(w * 100) }); }
