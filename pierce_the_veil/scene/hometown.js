// The "hometown" cluster: garage + stadium. Built twice (road start / road end) so that the
// closing pull-back can reproduce frame 1 exactly and the reel loops.
import { THREE, flat, unlit, halo, glowTexture, rng, lerp, clamp } from './common.js';

export const STADIUM_C = new THREE.Vector3(-70, 0, -60);
export const GARAGE_C = new THREE.Vector3(14, 0, -4);
export const CLUSTER_C = new THREE.Vector3(-30, 0, -30); // used for terrain flattening

export function buildHometown() {
  const g = new THREE.Group();
  const R = rng(77);
  const fx = { beams: [], halos: [], crowd: null, beamMat: null, field: null, door: null, garageLight: null, fieldLight: null };

  // ---------- stadium ----------
  const st = new THREE.Group(); st.position.copy(STADIUM_C); g.add(st);
  const prof = [[22, 0.4], [24, 3], [34, 10], [41, 15.5], [43, 18], [48, 17], [48.5, 0]]
    .map(([r, y]) => new THREE.Vector2(r, y));
  const bowl = new THREE.Mesh(new THREE.LatheGeometry(prof, 20), flat(0x5b4a8c, { side: THREE.DoubleSide }));
  st.add(bowl);
  const field = new THREE.Mesh(new THREE.CircleGeometry(22.4, 20), flat(0x2f9a63, { emissive: 0x12602f, emissiveIntensity: 1 }));
  field.rotation.x = -Math.PI / 2; field.position.y = 0.3; st.add(field); fx.field = field;
  const ring = new THREE.Mesh(new THREE.RingGeometry(5, 5.7, 20), unlit(0xdfffee));
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.4; st.add(ring);
  // stage at one end with a glowing back-wall
  const stage = new THREE.Mesh(new THREE.BoxGeometry(15, 3, 8), flat(0x2b2150)); stage.position.set(0, 1.8, -13); st.add(stage);
  const wall = new THREE.Mesh(new THREE.BoxGeometry(15, 9, 0.6), unlit(0xff4fa3)); wall.position.set(0, 7.8, -17); st.add(wall);

  // crowd (instanced boxes on the stands)
  const N = 1100;
  const crowd = new THREE.InstancedMesh(new THREE.BoxGeometry(1.1, 1.5, 0.8), unlit(0xffffff), N);
  const pal = [0xff4d6d, 0xffd166, 0x06d6a0, 0x4cc9f0, 0xf4f4f8, 0xb388ff].map((c) => new THREE.Color(c));
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), sc = new THREE.Vector3(1, 1, 1);
  for (let i = 0; i < N; i++) {
    const a = R() * Math.PI * 2, r = 24.6 + R() * 15.5;
    const y = r < 34 ? lerp(3, 10, (r - 24) / 10) : lerp(10, 15.5, (r - 34) / 7);
    e.set(0, -a + Math.PI / 2, 0); q.setFromEuler(e);
    m.compose(new THREE.Vector3(Math.cos(a) * r, y + 0.9, Math.sin(a) * r), q, sc);
    crowd.setMatrixAt(i, m);
    crowd.setColorAt(i, pal[(R() * pal.length) | 0].clone().multiplyScalar(0.45 + R() * 0.55));
  }
  st.add(crowd); fx.crowd = crowd;

  // floodlight towers + additive beams
  const beamLen = 170, beamGeo = new THREE.CylinderGeometry(0.6, 9, beamLen, 8, 1, true);
  beamGeo.translate(0, -beamLen / 2, 0);
  const pos = beamGeo.attributes.position, col = [];
  for (let i = 0; i < pos.count; i++) { const k = clamp(-pos.getY(i) / beamLen); const v = Math.pow(1 - k, 2.2); col.push(v, v * 0.93, v * 0.75); }
  beamGeo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  fx.beamMat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending,
    depthWrite: false, side: THREE.DoubleSide, fog: false });
  const poleMat = flat(0x2a2547), lampMat = unlit(0xfff3d0);
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2 + Math.PI / 8, tx = Math.cos(a) * 55, tz = Math.sin(a) * 55;
    const tower = new THREE.Group(); tower.position.set(tx, 0, tz); st.add(tower);
    const pole = new THREE.Mesh(new THREE.BoxGeometry(1.6, 40, 1.6), poleMat); pole.position.y = 20; tower.add(pole);
    const head = new THREE.Mesh(new THREE.BoxGeometry(11, 5.5, 1.6), lampMat);
    head.position.y = 42; head.lookAt(new THREE.Vector3(-tx, 42, -tz)); tower.add(head);
    const h = halo(0xfff0c8, 52); h.position.set(-Math.cos(a) * 1.5, 42, -Math.sin(a) * 1.5); tower.add(h); fx.halos.push(h);
    for (const side of [-1, 1]) {
      const beam = new THREE.Mesh(beamGeo, fx.beamMat);
      const tang = new THREE.Vector3(-Math.sin(a), 0, Math.cos(a));
      beam.position.set(0, 42, 0).addScaledVector(tang, side * 3);
      const inward = new THREE.Vector3(-Math.cos(a), 0, -Math.sin(a));
      const dir = inward.clone().multiplyScalar(0.28 + 0.1 * side).add(new THREE.Vector3(0, 1, 0)).addScaledVector(tang, side * 0.18).normalize();
      const base = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir);
      fx.beams.push({ mesh: beam, base, axis: tang.clone().cross(dir).normalize(), phase: k * 0.8 + side });
      beam.quaternion.copy(base); tower.add(beam);
    }
  }

  // ---------- garage ----------
  const ga = new THREE.Group(); ga.position.copy(GARAGE_C); g.add(ga);
  const wallMat = flat(0xd9c7a8), roofMat = flat(0x8a3b4d), trim = flat(0x3b3358);
  const box = (w, h, d, x, y, z, mat) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); b.position.set(x, y, z); ga.add(b); return b; };
  box(9, 5.2, 0.4, 0, 2.6, -3.8, wallMat);           // back
  box(0.4, 5.2, 8, -4.3, 2.6, 0, wallMat);           // left
  box(0.4, 5.2, 8, 4.3, 2.6, 0, wallMat);            // right
  box(1.5, 5.2, 0.4, -3.75, 2.6, 3.8, wallMat);      // front pillars
  box(1.5, 5.2, 0.4, 3.75, 2.6, 3.8, wallMat);
  box(9, 1.6, 0.4, 0, 4.4, 3.8, wallMat);            // lintel
  box(9.6, 0.25, 8.6, 0, 0.05, 0, trim);             // slab
  const inner = box(6, 3.6, 0.1, 0, 1.9, -3.5, unlit(0xff9a3c)); fx.door = inner;
  const floor = box(7.6, 0.1, 7, 0, 0.2, 0, unlit(0xc9742c));
  const shape = new THREE.Shape(); shape.moveTo(-5.1, 0); shape.lineTo(5.1, 0); shape.lineTo(0, 2.9); shape.closePath();
  const roofGeo = new THREE.ExtrudeGeometry(shape, { depth: 8.8, bevelEnabled: false }); roofGeo.translate(0, 0, -4.4);
  const roof = new THREE.Mesh(roofGeo, roofMat); roof.position.y = 5.2; ga.add(roof);
  // drum kit silhouette + amps (gear only, no people)
  const drumMat = flat(0xe9e4f5, { emissive: 0x6a3b12, emissiveIntensity: 0.8 });
  for (const [x, z, r] of [[-1.3, -1.2, 0.75], [0.2, -2, 0.8], [1.7, -1.2, 0.7]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.6, 8), drumMat); d.position.set(x, 1.2, z); ga.add(d);
  }
  const kick = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 1.0, 8), flat(0xb3263e, { emissive: 0x4a0a14 }));
  kick.rotation.x = Math.PI / 2; kick.position.set(0.2, 0.9, -0.4); ga.add(kick);
  box(1.3, 1.8, 1, -2.6, 1.1, 5.6, flat(0x23202e)); box(1.3, 1.2, 1, 2.9, 0.8, 5.2, flat(0x23202e));
  const spill = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshBasicMaterial({
    map: glowTexture(), color: 0xffa24a, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  spill.rotation.x = -Math.PI / 2; spill.position.set(0, 0.35, 8); ga.add(spill);
  const bulb = halo(0xffc27a, 9); bulb.position.set(0, 4.6, 4.6); ga.add(bulb);

  fx.garageLight = new THREE.PointLight(0xffa24a, 900, 55, 2); fx.garageLight.position.set(0, 3, 7); ga.add(fx.garageLight);
  fx.fieldLight = new THREE.PointLight(0xfff0c8, 14000, 220, 2); fx.fieldLight.position.set(0, 60, 0); st.add(fx.fieldLight);

  g.userData.fx = fx;
  return g;
}

// Lights: `boost` multiplies brightness (flare pulses). `t` drives the beam sweep, period 3 s
// (3 divides 75, so the sweep phase at the last frame equals frame 1 => seamless loop).
export function animateHometown(g, t, boost = 1) {
  const fx = g.userData.fx;
  fx.beamMat.color.setScalar(0.075 * boost);
  fx.halos.forEach((h) => h.material.color.setScalar(clamp(0.8 * boost, 0, 2)));
  fx.fieldLight.intensity = 14000 * boost;
  const w = (t * Math.PI * 2) / 3;
  const qs = new THREE.Quaternion();
  for (const b of fx.beams) {
    qs.setFromAxisAngle(b.axis, 0.2 * Math.sin(w + b.phase));
    b.mesh.quaternion.copy(qs).multiply(b.base);
  }
  fx.garageLight.intensity = 900 * (0.92 + 0.08 * Math.sin(w * 4));
}

// Camera dive in hometown-local coordinates; u: 0 = wide on the stadium, 1 = at the garage door.
const P = new THREE.CatmullRomCurve3([[95, 125, 105], [62, 78, 75], [40, 42, 58], [26, 17, 40], [15, 4.5, 22]]
  .map((a) => new THREE.Vector3(...a)), false, 'centripetal');
const T = new THREE.CatmullRomCurve3([[-70, 18, -60], [-45, 16, -45], [-5, 10, -20], [10, 4, -5], [14, 1.8, 0]]
  .map((a) => new THREE.Vector3(...a)), false, 'centripetal');
export function divePose(u) {
  u = clamp(u);
  const s = 0.35 * u + 0.65 * (u * u * (3 - 2 * u)); // never stops: min speed 0.35 at both ends
  return { pos: P.getPoint(s), target: T.getPoint(s), roll: 0.1 * Math.sin(s * Math.PI) };
}
