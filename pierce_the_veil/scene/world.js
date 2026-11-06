import { THREE, flat, unlit, rng, noise2, smooth, lerp, clamp, mixHex } from './common.js';
import { buildHometown, CLUSTER_C } from './hometown.js';
import { ROAD_LEN, SITES } from './layout.js';
export { ROAD_LEN };
export const W = 1080, H = 1920;

// ---------- era palettes (sky/fog/ground/lights) ----------
const P = (o) => ({ fogNear: 120, fogFar: 900, hemiI: 1.6, sunI: 2.4, sunDir: [-0.5, 0.9, 0.6], stars: 0, road: 0x2c2f3c, ...o });
export const PAL = {
  dusk:  P({ top: 0x2a1b6e, hor: 0xff9a62, ground: 0x6a5a98, hemiSky: 0xb6a2ff, hemiGround: 0x3a2a5a, sunColor: 0xffc08a, sunI: 1.7, stars: 0.6, hemiI: 1.5, fogFar: 1000 }),
  garage:P({ top: 0x4b94e8, hor: 0xffe2b8, ground: 0x93c26e, hemiSky: 0xcfe6ff, hemiGround: 0x7a8a5a, sunColor: 0xfff0d0, sunI: 3.2, sunDir: [-0.6, 0.7, 0.7] }),
  red:   P({ top: 0x2b0f3a, hor: 0xe8454f, ground: 0x8a4a5e, hemiSky: 0xffb0b0, hemiGround: 0x4a2a3a, sunColor: 0xff8a70, sunI: 2.0, sunDir: [0.6, 0.45, 0.7], stars: 0.3 }),
  teal:  P({ top: 0x2f9ab8, hor: 0xd8fbf2, ground: 0xe9d9a8, hemiSky: 0xe6fff8, hemiGround: 0xbfa97a, sunColor: 0xffffff, sunI: 3.4, sunDir: [-0.4, 1, 0.5] }),
  sky:   P({ top: 0x3a9cf2, hor: 0xffffff, ground: 0xd5e6f6, hemiSky: 0xffffff, hemiGround: 0x9ab8d8, sunColor: 0xffffff, sunI: 3.6, sunDir: [-0.5, 1, 0.4] }),
  sunset:P({ top: 0x6a3590, hor: 0xffa23c, ground: 0xd9955f, hemiSky: 0xffd0a0, hemiGround: 0x7a4a3a, sunColor: 0xffb060, sunI: 2.8, sunDir: [0.7, 0.35, 0.5] }),
  grey:  P({ top: 0x1b2230, hor: 0x5d6678, ground: 0x3e4656, hemiSky: 0x8a96aa, hemiGround: 0x2a303c, sunColor: 0x9aa6bb, sunI: 0.6, hemiI: 1.0, fogNear: 12, fogFar: 170, road: 0x20232c }),
  fog:   P({ top: 0x050c09, hor: 0x1b3b2a, ground: 0x16261d, hemiSky: 0x6aa88a, hemiGround: 0x0c1a12, sunColor: 0x7aff9a, sunI: 0.5, hemiI: 0.9, fogNear: 6, fogFar: 120, stars: 0.2, road: 0x15181a }),
  neon:  P({ top: 0x0e0832, hor: 0xff4fd8, ground: 0x2c2257, hemiSky: 0xb99cff, hemiGround: 0x20163f, sunColor: 0xff9ae8, sunI: 1.4, hemiI: 1.5, stars: 0.9, fogFar: 700 }),
};
export function mixPal(a, b, k) {
  const o = {}; for (const key in a) { const x = a[key], y = b[key];
    if (key === 'sunDir') o[key] = x.map((v, i) => lerp(v, y[i], k));
    else if (['top', 'hor', 'ground', 'hemiSky', 'hemiGround', 'sunColor', 'road'].includes(key)) o[key] = mixHex(x, y, k).getHex();
    else o[key] = lerp(x, y, k); } return o;
}

export function terrainHeight(x, z) {
  let keepFlat = 1;
  for (const k in SITES) { const s = SITES[k]; keepFlat = Math.min(keepFlat, smooth(s.r * 0.6, s.r, Math.hypot(x - s.x, z - s.z))); }
  const road = smooth(14, 60, Math.abs(x));
  let h = 9 * noise2(x * 0.011, z * 0.011) + 3 * noise2(x * 0.045, z * 0.045);
  h += 55 * smooth(130, 360, Math.abs(x)) * noise2(x * 0.007 + 9, z * 0.007);
  return h * road * keepFlat;
}

export function createWorld(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene(); scene.fog = new THREE.Fog(0xffffff, 100, 900); scene.background = new THREE.Color(0x000000);
  const camera = new THREE.PerspectiveCamera(55, W / H, 0.1, 4000);
  const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 1.5); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffffff, 2.5); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -48, right: 48, top: 48, bottom: -48, near: 1, far: 320 }); sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.06;
  scene.add(sun, sun.target);

  // gradient sky shader (smooth, like the reference style)
  const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() }, sunDir: { value: new THREE.Vector3(0, 1, 0) }, sunCol: { value: new THREE.Color() } },
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'uniform vec3 top; uniform vec3 hor; uniform vec3 sunDir; uniform vec3 sunCol; varying vec3 vD; void main(){ float h = clamp(vD.y,0.,1.); vec3 c = mix(hor, top, pow(h,0.55)); float s = max(dot(normalize(vD), normalize(sunDir)),0.); c += sunCol*(pow(s,900.)*1.4 + pow(s,12.)*0.22); gl_FragColor = vec4(c,1.);\n#include <colorspace_fragment>\n}' });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 24, 16), skyMat); sky.renderOrder = -10; scene.add(sky);
  const R = rng(5), sv = [];
  for (let i = 0; i < 420; i++) { const a = R() * 6.283, e = 0.12 + R() * 1.4; sv.push(Math.cos(a) * Math.cos(e) * 1400, Math.sin(e) * 1400, Math.sin(a) * Math.cos(e) * 1400); }
  const sgeo = new THREE.BufferGeometry(); sgeo.setAttribute('position', new THREE.Float32BufferAttribute(sv, 3));
  const starsMat = new THREE.PointsMaterial({ color: 0xffffff, size: 2.6, sizeAttenuation: false, fog: false, depthWrite: false, transparent: true });
  const stars = new THREE.Points(sgeo, starsMat); scene.add(stars);

  // terrain: per-face brightness jitter (vertex colours), tinted per era via material.color
  const tl = ROAD_LEN + 600;
  let tg = new THREE.PlaneGeometry(1000, tl, 100, Math.round(tl / 9)); tg.rotateX(-Math.PI / 2); tg.translate(0, 0, -ROAD_LEN / 2);
  const tp = tg.attributes.position;
  for (let i = 0; i < tp.count; i++) { const x = tp.getX(i) + (noise2(i * 0.37, 3) - 0.5) * 5, z = tp.getZ(i); tp.setXYZ(i, tp.getX(i), terrainHeight(x, z) - 0.2, tp.getZ(i)); }
  tg = tg.toNonIndexed(); tg.computeVertexNormals();
  const tpos = tg.attributes.position, tcol = [], rr = rng(21);
  for (let i = 0; i < tpos.count; i += 3) { const h = (tpos.getY(i) + tpos.getY(i + 1) + tpos.getY(i + 2)) / 3, v = 0.86 + rr() * 0.16 + Math.min(0.2, h / 160); for (let j = 0; j < 3; j++) tcol.push(v, v, v); }
  tg.setAttribute('color', new THREE.Float32BufferAttribute(tcol, 3));
  const groundMat = flat(0xffffff, { vertexColors: true }); const terrain = new THREE.Mesh(tg, groundMat); terrain.receiveShadow = true; scene.add(terrain);

  // road
  const roadMat = flat(0x2c2f3c);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(12, ROAD_LEN + 260), roadMat); road.rotation.x = -Math.PI / 2; road.position.set(0, 0.04, -ROAD_LEN / 2); road.receiveShadow = true; scene.add(road);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.PlaneGeometry(0.5, ROAD_LEN + 260), unlit(0xf0eefc)); e.rotation.x = -Math.PI / 2; e.position.set(s * 5.4, 0.06, -ROAD_LEN / 2); scene.add(e); }
  const nd = Math.floor(ROAD_LEN / 8), dm = new THREE.InstancedMesh(new THREE.BoxGeometry(0.5, 0.05, 3.4), unlit(0xffd27a), nd), mm = new THREE.Matrix4();
  for (let i = 0; i < nd; i++) { mm.makeTranslation(0, 0.08, 10 - i * 8); dm.setMatrixAt(i, mm); } scene.add(dm);

  // trees (lowpoly canopies), instanced
  const NT = 1100, trees = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(3.2, 0), flat(0xffffff), NT), trunks = new THREE.InstancedMesh(new THREE.BoxGeometry(0.8, 4, 0.8), flat(0x6b4a2b), NT);
  const rt = rng(99), q = new THREE.Quaternion(), e = new THREE.Euler(); let n = 0;
  const tcs = [0x3fae5a, 0x2e9a63, 0x56c06a, 0x7ac05a].map((c) => new THREE.Color(c));
  while (n < NT) {
    const x = (rt() < 0.5 ? -1 : 1) * (22 + rt() * 280), z = 60 - rt() * (ROAD_LEN + 120);
    if (Object.values(SITES).some((s) => Math.hypot(x - s.x, z - s.z) < s.r * 0.75)) continue;
    const s = 0.8 + rt() * 1.4, y = terrainHeight(x, z);
    q.setFromEuler(e.set(rt() * 3, rt() * 3, 0)); mm.compose(new THREE.Vector3(x, y + 5.5 * s, z), q, new THREE.Vector3(s, s * 1.1, s)); trees.setMatrixAt(n, mm);
    trees.setColorAt(n, tcs[(rt() * 4) | 0].clone().multiplyScalar(0.8 + rt() * 0.3));
    mm.compose(new THREE.Vector3(x, y + 2 * s, z), new THREE.Quaternion(), new THREE.Vector3(s, s, s)); trunks.setMatrixAt(n, mm); n++;
  }
  trees.castShadow = false; scene.add(trees, trunks);

  const hometownA = buildHometown(), hometownB = buildHometown(); hometownB.position.z = -ROAD_LEN; scene.add(hometownA, hometownB);
  const world = { renderer, scene, camera, sky, stars, hemi, sun, groundMat, roadMat, hometownA, hometownB, focus: new THREE.Vector3(), W, H };

  world.applyPalette = (p) => {
    skyMat.uniforms.top.value.set(p.top); skyMat.uniforms.hor.value.set(p.hor); skyMat.uniforms.sunCol.value.set(p.sunColor).multiplyScalar(0.8);
    const sd = new THREE.Vector3(...p.sunDir).normalize(); skyMat.uniforms.sunDir.value.copy(sd);
    scene.fog.color.set(p.hor); scene.fog.near = p.fogNear; scene.fog.far = p.fogFar;
    groundMat.color.set(p.ground); roadMat.color.set(p.road);
    hemi.color.set(p.hemiSky); hemi.groundColor.set(p.hemiGround); hemi.intensity = p.hemiI;
    sun.color.set(p.sunColor); sun.intensity = p.sunI; starsMat.opacity = p.stars; stars.visible = p.stars > 0.01;
    sun.position.copy(world.focus).addScaledVector(sd, 140); sun.target.position.copy(world.focus); sun.target.updateMatrixWorld();
  };
  return world;
}

export function render(world) {
  world.sky.position.copy(world.camera.position); world.stars.position.copy(world.camera.position);
  world.renderer.render(world.scene, world.camera);
}
