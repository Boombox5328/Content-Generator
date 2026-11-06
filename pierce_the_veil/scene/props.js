// Set dressing: buildings, trees, van, stage, monoliths, signs, billboards, phone, US map.
import { THREE, flat, unlit, box, halo, rng, noise2, smooth, clamp, lerp, textTexture, glowTexture } from './common.js';

// ---------- buildings with window grids ----------
export function windowTexture(base, win, lit = false, seed = 1) {
  const R = rng(seed), c = document.createElement('canvas'); c.width = 128; c.height = 256; const g = c.getContext('2d');
  g.fillStyle = lit ? '#000' : base; g.fillRect(0, 0, 128, 256);
  for (let y = 0; y < 16; y++) for (let x = 0; x < 8; x++) {
    const on = R() > 0.28; g.fillStyle = lit ? (on ? ['#ffd98a', '#9fe8ff', '#ffb3d9'][(R() * 3) | 0] : '#000') : (R() > 0.5 ? win[0] : win[1]);
    g.fillRect(x * 16 + 2, y * 16 + 3, 12, 10);
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}
export function makeBuilding({ w = 20, h = 50, d = 20, color = '#6d86b3', win = ['#9ec5ee', '#c9b8a8'], glow = false, seed = 1 }) {
  const map = windowTexture(color, win, false, seed); map.repeat.set(Math.max(1, Math.round(w / 12)), Math.max(1, Math.round(h / 24)));
  const side = flat(0xffffff, { map });
  if (glow) { const em = windowTexture(color, win, true, seed + 7); em.repeat.copy(map.repeat); side.emissiveMap = em; side.emissive = new THREE.Color(0xffffff); side.emissiveIntensity = 1; }
  const roof = flat(new THREE.Color(color).multiplyScalar(0.7));
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), [side, side, roof, roof, side, side]);
  m.position.y = h / 2; m.castShadow = m.receiveShadow = true; return m;
}

export function makeTree(seed = 1, s = 1) {
  const R = rng(seed), g = new THREE.Group();
  g.add(box(0.7 * s, 4 * s, 0.7 * s, flat(0x6b4a2b), 0, 2 * s, 0));
  const leaf = flat(new THREE.Color().setHSL(0.27 + R() * 0.06, 0.55, 0.38 + R() * 0.1));
  for (const [x, y, z, r] of [[0, 5.4, 0, 3], [1.2, 4.3, 0.6, 2.2], [-1.1, 4.5, -0.5, 2.2]]) {
    const b = new THREE.Mesh(new THREE.IcosahedronGeometry(r * s, 0), leaf); b.position.set(x * s, y * s, z * s); b.rotation.set(R() * 3, R() * 3, 0); b.castShadow = true; g.add(b);
  }
  return g;
}
export function makeLamp() {
  const g = new THREE.Group(), d = flat(0x2c2f3a);
  g.add(box(0.3, 8, 0.3, d, 0, 4, 0), box(2.2, 0.3, 0.3, d, 0.9, 8, 0), box(1, 0.3, 0.7, unlit(0xfff2c0), 1.8, 7.85, 0));
  const h = halo(0xffe7a8, 7); h.position.set(1.8, 7.6, 0); g.add(h); return g;
}

// ---------- tour van ----------
export function makeVan(color = 0x1fb6c1) {
  const g = new THREE.Group(), white = flat(0xf4f4f4), dark = flat(0x1a2230), c = flat(color);
  g.add(box(3, 2.4, 6.4, white, 0, 2.1, 0), box(3.04, 0.7, 6.44, c, 0, 1.55, 0), box(2.8, 1.1, 1.5, flat(0x2b3a4a), 0, 2.8, 2.45), box(3.02, 0.9, 3, dark, 0, 2.7, -0.6));
  g.add(box(2.8, 0.3, 4.2, flat(0x444a58), 0, 3.5, -0.4));
  for (const [x, z] of [[1.55, 2.1], [-1.55, 2.1], [1.55, -2.1], [-1.55, -2.1]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.6, 10), dark); w.rotation.z = Math.PI / 2; w.position.set(x, 0.75, z); w.castShadow = true; g.add(w); }
  g.add(box(2.2, 0.35, 0.3, unlit(0xfff2c0), 0, 1.5, 3.25));
  return g;
}

// ---------- stage with truss, speakers, light rig ----------
export function makeBeamGeo(len = 60, r = 7) {
  const geo = new THREE.CylinderGeometry(0.4, r, len, 8, 1, true); geo.translate(0, -len / 2, 0);
  const p = geo.attributes.position, col = [];
  for (let i = 0; i < p.count; i++) { const v = Math.pow(1 - clamp(-p.getY(i) / len), 2); col.push(v, v, v); }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); return geo;
}
export function makeStage({ w = 44, d = 22, h = 2.2, accent = 0xff4fa3, lights = 5 } = {}) {
  const g = new THREE.Group(), dk = flat(0x232634), truss = flat(0x8a8fa3);
  g.add(box(w, h, d, flat(0x3a3f55), 0, h / 2, 0));
  const riser = box(16, 2, 9, flat(0x2d3046), 0, h + 1, -d / 2 + 6); g.add(riser); g.userData.riserY = h + 2; g.userData.riserZ = -d / 2 + 6;
  const top = h + 21;
  g.add(box(1.2, 21, 1.2, truss, -w / 2 + 1, h + 10.5, -d / 2 + 1), box(1.2, 21, 1.2, truss, w / 2 - 1, h + 10.5, -d / 2 + 1), box(w, 1.2, 1.2, truss, 0, top, -d / 2 + 1));
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w - 8, 14), new THREE.MeshBasicMaterial({ color: accent })); screen.position.set(0, h + 12, -d / 2 + 0.6); g.add(screen);
  for (const sx of [-1, 1]) for (let i = 0; i < 3; i++) { g.add(box(5, 4.5, 4, dk, sx * (w / 2 + 3), h + 2.25 + i * 4.6, -d / 2 + 4)); const cone = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.3, 10), flat(0x555a6e)); cone.rotation.x = Math.PI / 2; cone.position.set(sx * (w / 2 + 3), h + 2.25 + i * 4.6, -d / 2 + 6.1); g.add(cone); }
  const beamMat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
  const geo = makeBeamGeo(60, 6), rigs = [], cols = [0xff4fa3, 0x4fd5ff, 0xffe066, 0xb388ff, 0x7dffb0];
  for (let i = 0; i < lights; i++) {
    const x = lerp(-w / 2 + 5, w / 2 - 5, i / (lights - 1)), mat = beamMat.clone(); mat.color.set(cols[i % 5]).multiplyScalar(0.55);
    const b = new THREE.Mesh(geo, mat); b.position.set(x, top - 0.8, -d / 2 + 3); const hl = halo(cols[i % 5], 9); hl.position.copy(b.position); g.add(b, hl);
    g.add(box(1.4, 1, 1.4, unlit(0xffffff), x, top - 0.2, -d / 2 + 3));
    rigs.push({ b, hl, base: b.position.x, mat, col: new THREE.Color(cols[i % 5]) });
  }
  g.userData.set = (level, t = 0) => { rigs.forEach((r, i) => { r.mat.color.copy(r.col).multiplyScalar(0.55 * level); r.hl.material.color.setScalar(level); r.hl.visible = level > 0.02; r.b.visible = level > 0.02;
    r.b.rotation.set(0.35 + Math.sin(t * 1.3 + i) * 0.25, 0, Math.sin(t * 0.9 + i * 1.7) * 0.35); }); screen.material.color.copy(new THREE.Color(accent)).multiplyScalar(0.12 + 0.88 * level); };
  g.userData.set(1);
  return g;
}

// ---------- abstract album monoliths (no cover art) ----------
export function makeMonolith({ color = 0xd62839, height = 30, seed = 1, dark = false, edge = 0xffffff } = {}) {
  const R = rng(seed), g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const mat = dark ? flat(0x08100c, { roughness: 0.4 }) : flat(color, { emissive: color, emissiveIntensity: 0.3, roughness: 0.45 });
  const lineMat = new THREE.LineBasicMaterial({ color: dark ? color : edge });
  let y = 0; const w0 = height * 0.17, n = 4;
  for (let i = 0; i < n; i++) {
    const hh = height * (i === n - 1 ? 0.3 : 0.24), rb = w0 * (1 - i * 0.15), rt = w0 * (1 - (i + 1) * 0.15) * (i === n - 1 ? 0.15 : 1);
    const geo = new THREE.CylinderGeometry(rt, rb, hh, 5 + (i % 2), 1), m = new THREE.Mesh(geo, mat);
    m.position.set((R() - 0.5) * w0 * 0.3, y + hh / 2, (R() - 0.5) * w0 * 0.3); m.rotation.y = R() * 3; m.castShadow = true; m.receiveShadow = true;
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), lineMat)); body.add(m); y += hh * 0.97;
  }
  const shards = [];
  for (let i = 0; i < 9; i++) { const s = new THREE.Mesh(new THREE.OctahedronGeometry(height * (0.02 + R() * 0.03), 0), dark ? flat(color, { emissive: color, emissiveIntensity: 0.8 }) : flat(color, { emissive: color, emissiveIntensity: 0.5 }));
    s.castShadow = true; shards.push({ s, a: R() * 6.28, r: w0 * (1.8 + R() * 1.6), y: height * (0.15 + R() * 0.8), sp: 0.3 + R() * 0.5 }); g.add(s); }
  const plinth = new THREE.Mesh(new THREE.CylinderGeometry(w0 * 2.3, w0 * 2.7, 1.2, 6), flat(0x222633)); plinth.position.y = 0.6; plinth.receiveShadow = true; g.add(plinth);
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(w0 * 1.9, w0 * 2.0, 0.3, 6), unlit(color)); ring.position.y = 1.3; g.add(ring);
  const gl = halo(color, height * 1.1); gl.position.y = height * 0.5; gl.material.opacity = 0.5; g.add(gl);
  body.position.y = 1.2;
  return { group: g, body, height, glow: gl, shards, w0,
    update(t) { shards.forEach((o) => { o.s.position.set(Math.cos(o.a + t * o.sp) * o.r, o.y + Math.sin(t * 1.3 + o.a) * 1.2, Math.sin(o.a + t * o.sp) * o.r); o.s.rotation.set(t * o.sp, t, 0); }); },
    setGrow(k) { body.scale.set(1, Math.max(0.001, k), 1); gl.visible = k > 0.02; gl.position.y = height * 0.5 * k; shards.forEach((o) => (o.s.visible = k > 0.55)); } };
}

// ---------- sign (flips between two faces) ----------
export function makeSign(frontText, backText, { w = 14, h = 4.4, fg = '#ffffff', bgF = '#3a3a48', bgB = '#d62839' } = {}) {
  const g = new THREE.Group(), flip = new THREE.Group(); g.add(flip);
  const f = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: textTexture(frontText, { w: 1024, h: Math.round(1024 * h / w), bg: bgF, fg, size: 200 }) }));
  f.position.z = 0.2; const b = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: textTexture(backText, { w: 1024, h: Math.round(1024 * h / w), bg: bgB, fg, size: 200 }) }));
  b.rotation.x = Math.PI; b.position.z = -0.2; flip.add(f, b, box(w + 0.6, h + 0.6, 0.3, flat(0x15151c)));
  flip.position.y = h / 2 + 0.5; g.add(box(0.4, 0.5, 0.4, flat(0x333)));
  g.userData.flip = flip; return g;
}
export function makeBillboard(text, color = '#ff4fa3', w = 26, h = 11) {
  const g = new THREE.Group(), dk = flat(0x1a1c28);
  g.add(box(0.8, 14, 0.8, dk, -w / 2 + 2, 7, 0), box(0.8, 14, 0.8, dk, w / 2 - 2, 7, 0));
  const board = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: textTexture(text, { w: 1024, h: Math.round(1024 * h / w), bg: '#0d0b1e', fg: color, size: 190 }) }));
  board.position.set(0, 14 + h / 2 - 2, 0.5); g.add(board, box(w + 1, h + 1, 0.8, flat(color), 0, 14 + h / 2 - 2, 0));
  const hl = halo(color, w * 1.6); hl.position.set(0, 14 + h / 2 - 2, 2); hl.material.opacity = 0.45; g.add(hl); return g;
}
export function makeMilestone(year, color = '#ffd27a') {
  const g = new THREE.Group();
  g.add(box(3.2, 5, 1, flat(0xdfe3ee), 0, 2.5, 0));
  const p = new THREE.Mesh(new THREE.PlaneGeometry(3, 1.5), new THREE.MeshBasicMaterial({ map: textTexture(String(year), { w: 256, h: 128, bg: '#15151c', fg: color, size: 110 }) })); p.position.set(0, 4, 0.52); g.add(p); return g;
}

// ---------- phone + shatter ----------
export function makePhone() {
  const g = new THREE.Group(); g.add(box(3.4, 6.6, 0.4, flat(0x0b0b12)));
  const c = document.createElement('canvas'); c.width = 256; c.height = 512; const x = c.getContext('2d');
  const gr = x.createLinearGradient(0, 0, 256, 512); gr.addColorStop(0, '#ff2d95'); gr.addColorStop(0.5, '#7b2cff'); gr.addColorStop(1, '#18d6ff'); x.fillStyle = gr; x.fillRect(0, 0, 256, 512);
  x.fillStyle = 'rgba(255,255,255,.95)'; x.beginPath(); x.moveTo(90, 190); x.lineTo(90, 322); x.lineTo(190, 256); x.fill();
  x.fillStyle = 'rgba(255,255,255,.7)'; for (let i = 0; i < 9; i++) x.fillRect(30 + i * 24, 470 - ((i * 37) % 70), 14, 20 + ((i * 37) % 70));
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Mesh(new THREE.PlaneGeometry(3.1, 6.2), new THREE.MeshBasicMaterial({ map: t })); s.position.z = 0.21; g.add(s); g.userData.screen = s; return g;
}
export function makeShards(n = 260, seed = 4) {
  const R = rng(seed), mesh = new THREE.InstancedMesh(new THREE.TetrahedronGeometry(0.5, 0), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }), n);
  const cols = [0xff2d95, 0x18d6ff, 0xffffff, 0x7b2cff, 0xffe066].map((c) => new THREE.Color(c)), S = [];
  for (let i = 0; i < n; i++) { const th = R() * 6.28, ph = Math.acos(2 * R() - 1);
    S.push({ v: new THREE.Vector3(Math.sin(ph) * Math.cos(th), Math.sin(ph) * Math.sin(th), Math.cos(ph) * 0.6).multiplyScalar(5 + R() * 9), sz: 0.25 + R() * 0.7, sp: new THREE.Vector3(R() * 6, R() * 6, R() * 6), lane: new THREE.Vector3((R() - 0.5) * 9, 0.6 + R() * 5.5, 0), off: R() * 60 });
    mesh.setColorAt(i, cols[(R() * cols.length) | 0]); }
  mesh.frustumCulled = false; const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), p = new THREE.Vector3(), sc = new THREE.Vector3(), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  // tau = seconds since burst. origin = world pos of phone, roadZ = z of road reference ahead
  mesh.userData.update = (tau, origin, camZ) => {
    for (let i = 0; i < n; i++) { const s = S[i];
      if (tau < 0) { mesh.setMatrixAt(i, zero); continue; }
      const burst = Math.min(tau, 1.1), k = smooth(0.9, 2.2, tau);
      const pb = origin.clone().addScaledVector(s.v, burst * (1 - 0.3 * burst));
      const flow = new THREE.Vector3(s.lane.x, s.lane.y, camZ - 14 - ((s.off + tau * 34) % 90));  // stream running down the road
      p.copy(pb).lerp(flow, k); sc.setScalar(s.sz * (1 - 0.5 * k));
      q.setFromEuler(e.set(tau * s.sp.x, tau * s.sp.y, tau * s.sp.z)); m.compose(p, q, sc); mesh.setMatrixAt(i, m); }
    mesh.instanceMatrix.needsUpdate = true; };
  return mesh;
}

// ---------- faceted US map ----------
const US = [[-124.7,48.4],[-123.1,49],[-95.2,49],[-89.6,48],[-84.8,46.8],[-82.5,45.3],[-82.4,43],[-79,42.8],[-76.5,43.6],[-74.7,45],[-71.5,45],[-69.2,47.4],[-67,45],[-70.2,43.6],[-70.8,42.3],[-70,41.7],[-72,41.2],[-74,40.6],[-74,39.2],[-75.5,38.4],[-76,37],[-75.6,35.2],[-78.5,33.8],[-80.8,32],[-81.3,30.5],[-80,26.8],[-80.4,25.2],[-81.8,26],[-82.8,28],[-83.7,29.9],[-85.3,29.7],[-88,30.4],[-89.4,30],[-89.2,29],[-91.5,29.5],[-93.8,29.7],[-95,29],[-97.2,27.6],[-97.4,25.9],[-99.1,26.4],[-100.9,29.3],[-102.4,29.8],[-103.2,29],[-104.5,29.7],[-106.5,31.8],[-108.2,31.8],[-108.2,31.3],[-111.1,31.3],[-114.8,32.5],[-117.1,32.5],[-118.5,34],[-120.6,34.6],[-121.9,36.6],[-122.5,37.8],[-123.8,39.5],[-124.4,40.4],[-124.1,42],[-124.5,43],[-123.9,46.2]];
export const proj = (lon, lat) => new THREE.Vector3((lon + 96) * 0.79 * 5.2, 0, -(lat - 38) * 5.2);
export function makeUSMap({ top = 0x6fd6b8, side = 0x0f5f6e } = {}) {
  const g = new THREE.Group(), P = US.map(([lo, la]) => proj(lo, la));
  const inside = (x, z) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { if ((P[i].z > z) !== (P[j].z > z) && x < ((P[j].x - P[i].x) * (z - P[i].z)) / (P[j].z - P[i].z) + P[i].x) c = !c; } return c; };
  const hgt = (x, z) => 0.8 + 2.2 * noise2(x * 0.05, z * 0.05) + 3.2 * smooth(-60, -105, x) * noise2(x * 0.09 + 4, z * 0.09) + 2 * smooth(60, 100, x) * noise2(x * 0.08, z * 0.08 + 9) * 0.6;
  const step = 6, pos = [], col = [], R = rng(8), c0 = new THREE.Color(top), tmp = new THREE.Color();
  for (let x = -125; x < 125; x += step) for (let z = -62; z < 72; z += step) {
    const q = [[x, z], [x + step, z], [x, z + step], [x + step, z + step]].map(([a, b]) => new THREE.Vector3(a + (noise2(a * 0.3, b * 0.3) - 0.5) * 2.4, hgt(a, b), b + (noise2(b * 0.3 + 5, a * 0.3) - 0.5) * 2.4));
    for (const tri of [[0, 2, 1], [1, 2, 3]]) { const cx = (q[tri[0]].x + q[tri[1]].x + q[tri[2]].x) / 3, cz = (q[tri[0]].z + q[tri[1]].z + q[tri[2]].z) / 3;
      if (!inside(cx, cz)) continue; tmp.copy(c0).multiplyScalar(0.82 + R() * 0.2).lerp(new THREE.Color(0x9ed8c9), clamp(((q[tri[0]].y + q[tri[1]].y + q[tri[2]].y) / 3 - 2) / 5));
      for (const k of tri) { pos.push(q[k].x, q[k].y, q[k].z); col.push(tmp.r, tmp.g, tmp.b); } }
  }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); geo.computeVertexNormals();
  const top_ = new THREE.Mesh(geo, flat(0xffffff, { vertexColors: true })); top_.receiveShadow = true; g.add(top_);
  const shape = new THREE.Shape(P.map((p) => new THREE.Vector2(p.x, -p.z))); const eg = new THREE.ExtrudeGeometry(shape, { depth: 4, bevelEnabled: false }); eg.rotateX(-Math.PI / 2); eg.translate(0, -4.2, 0);
  const slab = new THREE.Mesh(eg, flat(side)); slab.receiveShadow = true; g.add(slab);
  // route + van path
  const city = [[-117.2, 32.7], [-118.2, 34], [-122.3, 47.6], [-105, 39.7], [-87.6, 41.9], [-74, 40.7], [-84.4, 33.7], [-96.8, 32.8]].map(([lo, la]) => proj(lo, la).setY(2.6));
  const curve = new THREE.CatmullRomCurve3(city, false, 'centripetal', 0.5);
  const pins = new THREE.Group(); city.forEach((c, i) => { const pin = new THREE.Mesh(new THREE.ConeGeometry(1.3, 4, 5), flat(0xff4f5e, { emissive: 0xff2030, emissiveIntensity: 0.4 })); pin.rotation.x = Math.PI; pin.position.set(c.x, 4.4, c.z); pin.castShadow = true; pins.add(pin); }); g.add(pins);
  const N = 420, trail = new THREE.InstancedMesh(new THREE.BoxGeometry(1.1, 0.5, 1.1), unlit(0x18e0d0), N); trail.frustumCulled = false; g.add(trail);
  const m = new THREE.Matrix4(), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  const van = makeVan(0x1fb6c1); van.scale.setScalar(0.9); g.add(van);
  const api = { group: g, curve, pins, van, setProgress(p) {
    p = clamp(p); const pt = curve.getPointAt(p), tg = curve.getTangentAt(Math.min(0.999, p));
    van.position.copy(pt).setY(3.2); van.lookAt(van.position.clone().add(tg)); van.rotation.z = 0;
    for (let i = 0; i < N; i++) { const u = i / N; if (u > p) { trail.setMatrixAt(i, zero); continue; } const q = curve.getPointAt(u); m.makeTranslation(q.x, 2.3, q.z); trail.setMatrixAt(i, m); }
    trail.instanceMatrix.needsUpdate = true; } };
  api.setProgress(0); return api;
}
