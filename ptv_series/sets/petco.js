// Petco Park at sunset, stylised low-poly: open-outfield bowl, light towers, stage + crowd, San Diego skyline and bay behind.
// Home plate side is +z, the open outfield faces -z toward downtown.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, lerp, clamp, smooth } from '../engine/lowpoly.js';
import { makeRig } from '../engine/pipeline.js';
import { makeShaft } from '../engine/shafts.js';
import { makeSky } from '../engine/sky.js';
import { makeHuman, pose, BAND } from '../kit/human.js';
import { makeGuitar, makeMicStand, makeDrumKit } from '../kit/instruments.js';
import { makeCrowd } from '../kit/crowd.js';
import { cloud } from '../kit/props.js';
import { windowTexture } from '../kit/windowTex.js';
const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };
const DS = lpMat({ side: THREE.DoubleSide });

// sweep a (radius, height) profile around an arc -> faceted ring segment
function sweep(profile, a0, a1, segs, jitterSeed = 1) {
  const pos = [], idx = [], n = profile.length;
  for (let s = 0; s <= segs; s++) { const a = lerp(a0, a1, s / segs); for (const [r, y] of profile) pos.push(Math.sin(a) * r, y, Math.cos(a) * r); }
  for (let s = 0; s < segs; s++) for (let k = 0; k < n - 1; k++) { const a = s * n + k, b = a + 1, c = a + n, d = c + 1; idx.push(a, b, c, b, d, c, a, c, b, b, c, d); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); return g;
}
function tower(w, h, d, style, seed, c0, c1) {
  const g = new THREE.Group(), R = rng(seed);
  const map = windowTexture(c0, ['#ffcf90', '#9ec8ff'], seed); map.repeat.set(Math.max(1, Math.round(w / 14)), Math.max(1, Math.round(h / 36)));
  const side = lpMat({ map, color: 0xffffff, vertexColors: false, emissive: 0xffffff, emissiveMap: map, emissiveIntensity: 0.2, roughness: 0.55, metalness: 0.2 });
  const roofM = lpMat({ vertexColors: false, color: new THREE.Color(c1) });
  const box = (ww, hh, dd, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(ww, hh, dd), [side, side, roofM, roofM, side, side]); m.position.y = y + hh / 2; m.castShadow = true; m.receiveShadow = true; g.add(m); return m; };
  if (style === 'stepped') { box(w, h * 0.6, d, 0); box(w * 0.75, h * 0.25, d * 0.75, h * 0.6); box(w * 0.5, h * 0.15, d * 0.5, h * 0.85); }
  else if (style === 'spire') { box(w, h * 0.85, d, 0); const c = new THREE.ConeGeometry(Math.min(w, d) * 0.6, h * 0.22, 4); c.rotateY(Math.PI / 4); put(g, paint(c, { top: c1, bottom: c0, seed }), 0, h * 0.85 + h * 0.11, 0); }
  else if (style === 'sail') { const cg = new THREE.CylinderGeometry(w * 0.55, w * 0.55, h, 12, 1, false, 0, Math.PI * 1.1); const m = new THREE.Mesh(cg, [side, roofM, roofM]); m.position.y = h / 2; m.castShadow = true; g.add(m); }
  else box(w, h, d, 0);
  return g;
}

export function makePetco() {
  const group = new THREE.Group(), glow = [], R = rng(55);
  // ---- field ----
  const fg = new THREE.CircleGeometry(58, 28); fg.rotateX(-Math.PI / 2);
  { const p = fg.attributes.position, cols = []; const c0 = new THREE.Color(0x2f7a3a), c1 = new THREE.Color(0x3a9446); const g2 = paint(fg, { top: 0x3a9446, bottom: 0x2f7a3a, axis: 'z', jitter: 0.05, seed: 3 }); const pp = g2.attributes.position, cc = g2.attributes.color;
    for (let i = 0; i < pp.count; i += 3) { const k = Math.floor(((pp.getZ(i) + pp.getZ(i + 1) + pp.getZ(i + 2)) / 3 + 80) / 6) % 2; const c = k ? c0 : c1; for (let j = 0; j < 3; j++) cc.setXYZ(i + j, c.r * (0.94 + R() * 0.1), c.g * (0.94 + R() * 0.1), c.b * (0.94 + R() * 0.1)); } put(group, g2, 0, 0.02, 0); }
  const dirt = put(group, paint(new THREE.CylinderGeometry(21, 21, 0.06, 4), { top: 0x2f7a3a, bottom: 0x2a6a34, jitter: 0.06, seed: 4 }), 0, 0.04, 26); dirt.rotation.y = Math.PI / 4;
  put(group, paint(new THREE.CylinderGeometry(3.2, 3.2, 0.12, 10), { top: 0xc09a68 }), 0, 0.08, 14);
  put(group, bevelBox(70, 0.4, 3, 0.05, { top: 0x2a2a3a }), 0, 0.2, 58);
  // ---- seating bowl: lower, club, upper decks + facade (open toward -z) ----
  const A = 2.45;                                                        // half-angle covered (rad) -> opening ~ 80°
  const stepProfile = (r0, r1, y0, rows, rise, tread) => { const p = []; let r = r0, y = y0; p.push([r, y]); for (let i = 0; i < rows; i++) { y += rise; p.push([r, y]); r += tread; p.push([r, y]); } return p; };
  const seats = paint(sweep(stepProfile(64, 64, 0, 14, 0.9, 1.1), -A, A, 36), { top: 0x2a3a6a, bottom: 0x14203c, axis: 'y', jitter: 0.16, hue: 0.06, seed: 5 }); put(group, seats, 0, 0, 0, DS);
  const club = paint(sweep(stepProfile(84, 84, 16, 12, 0.9, 1.1), -A, A, 36), { top: 0x3a4a7a, bottom: 0x1c2644, axis: 'y', jitter: 0.16, hue: 0.06, seed: 6 }); put(group, club, 0, 0, 0, DS);
  const wall = paint(sweep([[63, 0], [63, 15], [100.5, 36], [100.5, 0]], -A, A, 36), { top: 0xd8c4a0, bottom: 0x8a7658, axis: 'y', jitter: 0.07, seed: 7 }); put(group, wall, 0, 0, 0, DS);
  const roof = paint(sweep([[78, 31], [104, 38], [104, 39], [78, 32.2]], -1.55, 1.55, 24), { top: 0xe6e0d4, bottom: 0xaaa498, axis: 'y', jitter: 0.05, seed: 8 }); put(group, roof, 0, 2, 0, DS);
  for (let i = 0; i < 26; i++) { const a = lerp(-A, A, i / 25); put(group, bevelBox(2.4, 22, 1.6, 0.1, { top: 0xb8a47c, bottom: 0x7a6648, seed: i }), Math.sin(a) * 101, 11, Math.cos(a) * 101).rotation.y = a; }   // facade piers
  // brick warehouse (left-field corner)
  const wh = put(group, bevelBox(28, 26, 12, 0.2, { top: 0xb06a50, bottom: 0x6a3a2c, jitter: 0.1, seed: 9 }), -70, 13, -52); wh.rotation.y = 0.55;
  // ---- light towers (emissive lamp banks) ----
  const lampMat = emissiveMat(0xfff0cc, 4.5), TW = [-2.2, -1.5, 1.5, 2.2];
  for (const a of TW) { const tg = new THREE.Group(); tg.position.set(Math.sin(a) * 106, 0, Math.cos(a) * 106); tg.rotation.y = a + Math.PI; group.add(tg);
    put(tg, paint(new THREE.CylinderGeometry(0.7, 1.0, 64, 6), { top: 0x6a6f7c, bottom: 0x3a3e48 }), 0, 32, 0); put(tg, bevelBox(11, 8, 1.2, 0.2, { top: 0x2a2d36 }), 0, 66, 1.0);
    for (let r = 0; r < 3; r++) for (let c = 0; c < 5; c++) { const l = new THREE.Mesh(new THREE.CircleGeometry(0.7, 6), lampMat); l.position.set(-4 + c * 2, 63.5 + r * 2.4, 1.65); tg.add(l); glow.push(l); } }
  // ---- stage + crowd on the field (the finale's "sold-out" show; present in the hook, tiny and warm) ----
  const stage = new THREE.Group(); stage.position.set(0, 0, -26); group.add(stage);
  put(stage, bevelBox(34, 3.0, 14, 0.2, { top: 0x2a2630, bottom: 0x14121a }), 0, 1.5, 0); put(stage, bevelBox(30, 0.4, 12, 0.1, { top: 0x4a4650 }), 0, 3.1, 0);
  const ledTex = (() => { const c = document.createElement('canvas'); c.width = 512; c.height = 216; const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, 216); gr.addColorStop(0, '#ff3d9a'); gr.addColorStop(0.55, '#ff7a5a'); gr.addColorStop(1, '#ffc05a'); g.fillStyle = gr; g.fillRect(0, 0, 512, 216);
    g.fillStyle = 'rgba(255,255,255,.14)'; for (let i = 0; i < 9; i++) { g.beginPath(); g.moveTo(i * 70, 216); g.lineTo(i * 70 + 90, 0); g.lineTo(i * 70 + 120, 0); g.lineTo(i * 70 + 30, 216); g.fill(); }
    g.fillStyle = 'rgba(20,10,40,.45)'; g.fillRect(150, 90, 212, 12); g.fillRect(190, 112, 132, 8); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const led = new THREE.Mesh(new THREE.PlaneGeometry(26, 11), new THREE.MeshBasicMaterial({ map: ledTex, color: new THREE.Color(0.95, 0.9, 0.9), toneMapped: false })); led.position.set(0, 10, -6); stage.add(led);
  for (const x of [-15, 15]) put(stage, bevelBox(1.0, 18, 1.0, 0.1, { top: 0x6a6f7c }), x, 12, -6);
  put(stage, bevelBox(32, 1.2, 1.2, 0.1, { top: 0x6a6f7c }), 0, 20.5, -6);
  const figs = {}; const addFig = (id, mode, x, z) => { const h = makeHuman({ ...BAND[id], scale: 1.0 }); h.root.position.set(x, 3.3, z); stage.add(h.root); figs[id] = { h, mode }; return h; };
  addFig('vic', 'guitar', -0.5, 2.5); addFig('tony', 'guitar', -5, 1.5); addFig('jaime', 'guitar', 4.5, 1.5);
  const crowd = makeCrowd({ count: 420, seed: 2, scale: 1.1, place: (r, i) => ({ x: (r() - 0.5) * 78, z: -10 + r() * 52, y: 0, yaw: Math.PI + (r() - 0.5) * 0.3 }), palette: [0x2a2f45, 0x6a2a3a, 0x3a5a6a, 0xd0c8b8, 0x1c1c22, 0x9a5a3a, 0xc0392b, 0x2a7a8a, 0xe8a850] }); group.add(crowd.group);
  // ---- downtown skyline (stylised), bay, boats, hills ----
  const sky = new THREE.Group(); group.add(sky);
  const cols = [['#8a90b8', 0x9aa4c8], ['#a89aa8', 0xb8a8b0], ['#7a8ab0', 0x8a9ac0], ['#b0a090', 0xc8b8a0]];
  const spec = [[-150, -250, 26, 70, 'box'], [-122, -262, 22, 96, 'stepped'], [-92, -240, 30, 62, 'box'], [-60, -270, 24, 120, 'spire'], [-28, -250, 22, 84, 'stepped'], [-14, -330, 26, 150, 'sail'], [38, -255, 22, 98, 'box'], [66, -272, 28, 124, 'stepped'],
    [96, -250, 24, 76, 'box'], [124, -268, 22, 104, 'spire'], [-40, -230, 18, 54, 'box'], [24, -225, 20, 66, 'stepped'], [86, -228, 18, 48, 'box'], [-110, -222, 18, 44, 'box'], [150, -238, 26, 62, 'box'], [-176, -236, 20, 52, 'box']];
  spec.forEach(([x, z, w, h, st], i) => { const c = cols[i % 4]; h *= 0.66; const t = tower(w, h, w * 0.85, st, i + 1, c[0], c[1]); t.position.set(x, 0, z); sky.add(t); });
  const bay = new THREE.Mesh(new THREE.PlaneGeometry(2200, 1200, 40, 24), new THREE.MeshStandardMaterial({ color: 0x1a2a52, roughness: 0.22, metalness: 0.15, flatShading: true })); bay.rotation.x = -Math.PI / 2; bay.position.set(0, -0.5, -700); bay.receiveShadow = true; group.add(bay);
  { const p = bay.geometry.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, (R() - 0.5) * 0.9); bay.geometry.computeVertexNormals(); }
  put(group, paint(new THREE.PlaneGeometry(2400, 160), { top: 0x2a3a2a, jitter: 0.1 }), 0, -0.6, -110).rotation.x = -Math.PI / 2;
  const glitter = new THREE.Mesh(new THREE.PlaneGeometry(90, 520), new THREE.MeshBasicMaterial({ map: (() => { const c = document.createElement('canvas'); c.width = 128; c.height = 512; const g = c.getContext('2d'); for (let i = 0; i < 900; i++) { const y = Math.pow(R(), 1.7) * 512, w = (1 - y / 512) * 54 + 8, x = 64 + (R() - 0.5) * w * 2; g.fillStyle = `rgba(255,${190 + (R() * 50) | 0},${120 + (R() * 60) | 0},${0.15 + R() * 0.7})`; g.fillRect(x, y, 2 + R() * 8, 1 + R() * 2); } const t = new THREE.CanvasTexture(c); return t; })(), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, opacity: 0.8 }));
  glitter.rotation.x = -Math.PI / 2; glitter.position.set(12, 0.3, -400); group.add(glitter);
  const boat = (x, z, s) => { const b = new THREE.Group(); b.position.set(x, 0, z); b.scale.setScalar(s); put(b, bevelBox(3.2, 0.7, 1.1, 0.12, { top: 0xe8e2d4, bottom: 0x6a6a78 }), 0, 0.3, 0); const sl = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(2.2, 0), new THREE.Vector2(0, 5)]); put(b, paint(new THREE.ShapeGeometry(sl), { top: 0xffe8d0, bottom: 0xe8a888, seed: 2 }), -0.4, 0.7, 0, DS); put(b, paint(new THREE.CylinderGeometry(0.04, 0.04, 5, 4), { top: 0xdddddd }), -0.4, 3.2, 0); group.add(b); };
  [[-30, -170, 1.6], [24, -190, 1.9], [60, -215, 1.5], [-70, -200, 1.4], [110, -180, 1.7], [-12, -230, 1.2]].forEach(([x, z, s]) => boat(x, z, s));
  for (const [x, z, s, sd] of [[320, -520, 120, 1], [470, -540, 150, 2], [200, -560, 90, 3]]) { const h = paint(new THREE.IcosahedronGeometry(s, 1), { top: 0x4a3a58, bottom: 0x2a2038, jitter: 0.1, seed: sd }); h.scale(1, 0.4, 1); put(group, h, x, 0, z, lpMat({ vertexColors: true, roughness: 1 })); }
  // ---- sky + clouds ----
  const sunDir = [0.03, 0.28, -1];
  const skyDome = makeSky({ top: 0x1b1c52, mid: 0x7a3c8a, horizon: 0xffa868, below: 0xe0906a, sun: { dir: sunDir, color: 0xffd890, power: 6, size: 44 }, radius: 1400 }); group.add(skyDome); glow.push(skyDome.userData.disc);
  const cl = new THREE.Group(); group.add(cl);
  [[-300, 120, -900, 70, 1], [180, 170, -950, 90, 2], [420, 100, -820, 60, 3], [-520, 190, -880, 80, 4], [-760, 260, -1000, 100, 5], [-420, 90, -820, 50, 6], [600, 230, -900, 80, 7]].forEach(([x, y, z, s, sd]) => { const c = cloud(sd, s, 0xffb888, 0x8a4a88); c.position.set(x, y, z); cl.add(c); });
  // ---- lights ----
  const rig = makeRig({ key: { pos: [-60, 40, -90], color: 0xffa860, intensity: 3.6, extent: 120, far: 320 }, rim: { pos: [90, 60, -120], color: 0x7aa0ff, intensity: 2.4 }, fill: { sky: 0x8a70b0, ground: 0x5a3a40, intensity: 0.65 }, target: new THREE.Vector3(0, 8, -10) }); group.add(rig);
  const rays = [[-40, 0xffc888, 0.07], [10, 0xffd8a0, 0.09], [60, 0xffc080, 0.06]].map(([x, c, i]) => { const s = makeShaft([x * 0.2, 60, -700], [x * 2.2, 0, 60], { r0: 30, r1: 120, color: c, intensity: i, falloff: 0.5 }); group.add(s); return s; });
  return { id: 'petco', group, glow, figs, sky: skyDome,
    env: { top: 0x1b1c52, mid: 0x7a3c8a, horizon: 0xffa868, ground: 0x5a3a40, sun: { dir: sunDir, color: 0xffd890, power: 5, size: 6 } }, fog: { color: 0xd88a8a, density: 0.0011 }, look: { grade: 'magenta', bloomI: 1.35, dofScale: 0 },
    update(t, cfg = {}) { Object.entries(figs).forEach(([id, f]) => pose(f.h, t, 'guitar', { ph: id.length })); crowd.update(t, 0.8); rays.forEach((r) => r.userData.setT(t)); } };
}
