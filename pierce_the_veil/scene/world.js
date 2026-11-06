import { THREE, flat, unlit, rng, noise2, smooth, lerp, clamp } from './common.js';
import { buildHometown, CLUSTER_C } from './hometown.js';

export const W = 1080, H = 1920;
export const ROAD_LEN = 1800;           // road runs from z=0 to z=-ROAD_LEN
export const FOG_COLOR = 0x2a1740;

export function terrainHeight(x, z) {
  const d0 = Math.hypot(x - CLUSTER_C.x, z - CLUSTER_C.z);
  const d1 = Math.hypot(x - CLUSTER_C.x, z - (CLUSTER_C.z - ROAD_LEN));
  const keepFlat = Math.min(smooth(95, 150, d0), smooth(95, 150, d1));
  const road = smooth(14, 60, Math.abs(x));
  let h = 9 * noise2(x * 0.011, z * 0.011) + 3 * noise2(x * 0.045, z * 0.045);
  h += 55 * smooth(130, 360, Math.abs(x)) * noise2(x * 0.007 + 9, z * 0.007);
  return h * road * keepFlat;
}

export function createWorld(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(FOG_COLOR);
  scene.fog = new THREE.Fog(FOG_COLOR, 90, 760);
  const camera = new THREE.PerspectiveCamera(55, W / H, 0.1, 4000);

  const hemi = new THREE.HemisphereLight(0x9a86e8, 0x1d1536, 1.5); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xb7c0ff, 1.7); sun.position.set(-60, 120, 80); scene.add(sun);

  // ---- sky: faceted gradient dome + stars ----
  const sg = new THREE.IcosahedronGeometry(1500, 2); const sp = sg.attributes.position, sc = [];
  const cTop = new THREE.Color(0x0a0720), cMid = new THREE.Color(0x3a1c5e), cHor = new THREE.Color(0xff7a6b), tmp = new THREE.Color();
  for (let i = 0; i < sp.count; i += 3) {
    const y = (sp.getY(i) + sp.getY(i + 1) + sp.getY(i + 2)) / 3 / 1500;
    const k = clamp(y * 1.4 + 0.08);
    tmp.copy(cHor).lerp(cMid, smooth(0, 0.35, k)).lerp(cTop, smooth(0.3, 1, k));
    for (let j = 0; j < 3; j++) sc.push(tmp.r, tmp.g, tmp.b);
  }
  sg.setAttribute('color', new THREE.Float32BufferAttribute(sc, 3));
  const sky = new THREE.Mesh(sg, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false }));
  sky.renderOrder = -10; scene.add(sky);
  const R = rng(5), sv = [];
  for (let i = 0; i < 420; i++) { const a = R() * 6.283, e = 0.12 + R() * 1.4; sv.push(Math.cos(a) * Math.cos(e) * 1400, Math.sin(e) * 1400, Math.sin(a) * Math.cos(e) * 1400); }
  const sgeo = new THREE.BufferGeometry(); sgeo.setAttribute('position', new THREE.Float32BufferAttribute(sv, 3));
  const stars = new THREE.Points(sgeo, new THREE.PointsMaterial({ color: 0xffffff, size: 2.4, sizeAttenuation: false, fog: false, depthWrite: false }));
  scene.add(stars);

  // ---- terrain (non-indexed => true per-face flat colours) ----
  const tl = ROAD_LEN + 500;
  let tg = new THREE.PlaneGeometry(1000, tl, 100, Math.round(tl / 9)); tg.rotateX(-Math.PI / 2); tg.translate(0, 0, -ROAD_LEN / 2);
  const tp = tg.attributes.position;
  for (let i = 0; i < tp.count; i++) { const x = tp.getX(i) + (noise2(i * 0.37, 3) - 0.5) * 5, z = tp.getZ(i); tp.setXYZ(i, tp.getX(i), terrainHeight(x, z) - 0.2, tp.getZ(i)); }
  tg = tg.toNonIndexed(); tg.computeVertexNormals();
  const tpos = tg.attributes.position, tcol = [], base = new THREE.Color(0x2c2a5e), hill = new THREE.Color(0x5b3f86), rr = rng(21);
  for (let i = 0; i < tpos.count; i += 3) {
    const h = (tpos.getY(i) + tpos.getY(i + 1) + tpos.getY(i + 2)) / 3;
    tmp.copy(base).lerp(hill, smooth(0, 40, h)).multiplyScalar(0.88 + rr() * 0.24);
    for (let j = 0; j < 3; j++) tcol.push(tmp.r, tmp.g, tmp.b);
  }
  tg.setAttribute('color', new THREE.Float32BufferAttribute(tcol, 3));
  scene.add(new THREE.Mesh(tg, flat(0xffffff, { vertexColors: true })));

  // ---- the road: the spine of the whole piece ----
  const road = new THREE.Mesh(new THREE.PlaneGeometry(12, ROAD_LEN + 200), flat(0x23222f));
  road.rotation.x = -Math.PI / 2; road.position.set(0, 0.04, -ROAD_LEN / 2); scene.add(road);
  for (const s of [-1, 1]) {
    const edge = new THREE.Mesh(new THREE.PlaneGeometry(0.5, ROAD_LEN + 200), unlit(0xe8e4ff));
    edge.rotation.x = -Math.PI / 2; edge.position.set(s * 5.4, 0.06, -ROAD_LEN / 2); scene.add(edge);
  }
  const dashes = Math.floor(ROAD_LEN / 8);
  const dm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.5, 0.05, 3.4), unlit(0xffd27a), dashes);
  const mm = new THREE.Matrix4();
  for (let i = 0; i < dashes; i++) { mm.makeTranslation(0, 0.08, 10 - i * 8); dm.setMatrixAt(i, mm); }
  scene.add(dm);

  // ---- trees ----
  const NT = 900, trees = new THREE.InstancedMesh(new THREE.ConeGeometry(2.4, 8, 5), flat(0xffffff), NT);
  const rt = rng(99), tcs = [0x1f5b6a, 0x2a7a6f, 0x3b4f9a, 0x5a3f9a].map((c) => new THREE.Color(c));
  const q = new THREE.Quaternion(); let n = 0;
  while (n < NT) {
    const x = (rt() < 0.5 ? -1 : 1) * (24 + rt() * 260), z = 60 - rt() * (ROAD_LEN + 120);
    if (Math.hypot(x - CLUSTER_C.x, z - CLUSTER_C.z) < 125 || Math.hypot(x - CLUSTER_C.x, z - (CLUSTER_C.z - ROAD_LEN)) < 125) continue;
    const s = 0.7 + rt() * 1.3, y = terrainHeight(x, z);
    mm.compose(new THREE.Vector3(x, y + 4 * s, z), q, new THREE.Vector3(s, s * (0.9 + rt() * 0.6), s));
    trees.setMatrixAt(n, mm); trees.setColorAt(n, tcs[(rt() * 4) | 0].clone().multiplyScalar(0.8 + rt() * 0.4)); n++;
  }
  scene.add(trees);

  // ---- hometown clusters (start + end of the road) ----
  const hometownA = buildHometown(), hometownB = buildHometown();
  hometownB.position.z = -ROAD_LEN; scene.add(hometownA, hometownB);

  return { renderer, scene, camera, sky, stars, hemi, sun, hometownA, hometownB, tmp, W, H };
}

export function render(world) {
  world.sky.position.copy(world.camera.position); world.stars.position.copy(world.camera.position);
  world.renderer.render(world.scene, world.camera);
}
