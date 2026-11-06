// BEAT 2 · 3–10 s · 2004–2006 BEFORE TODAY — two figures; a sign flips BEFORE TODAY -> PIERCE THE VEIL.
import { THREE, V, flat, box, rng, smooth, clamp, orbit, dolly } from './common.js';
import { makeFigure, makeGuitar, makeMicStand, makeDrumKit, setSeated, animateFigure } from './figures.js';
import { makeSign } from './props.js';
import { animateHometown, GARAGE_C } from './hometown.js';
import { PAL } from './world.js';

const FLIP0 = 6.4, FLIP1 = 7.0;
let S;
export const beat = {
  id: 'before_today', start: 3, end: 10, accent: '#ff5a6e', hometown: 'A', focus: V(13, 0, 9),
  palette: () => PAL.garage,
  cards: [{ t0: 6.3, t1: 9.8, text: '2006: A song title becomes a *band.*' }],
  counter: [[3, 2004], [6.0, 2006], [10, 2006]],
  shots: [
    { t0: 3.0, t1: 5.0, cam: (u) => dolly(V(-2, 2.4, 30), V(8, 3.2, 22), V(14, 3.0, 10), V(14, 3.2, 10), u) },
    { t0: 5.0, t1: 6.6, cam: (u) => dolly(V(27, 3, 28), V(20, 6, 24), V(14, 4, 8), V(14, 6.5, 5), u) },
    { t0: 6.6, t1: 8.2, cam: (u) => ({ ...dolly(V(14, 5.5, 30), V(14, 8, 26), V(14, 6.8, 4.9), V(14, 7.2, 4.9), u), fov: 50 }) },
    { t0: 8.2, t1: 10.0, cam: (u) => orbit(V(14, 0, 10), 18, 5, 0.05, 1.0, u, 3.2) },
  ],
  build(world) {
    const g = this.group = new THREE.Group(); world.scene.add(g); S = {};
    const vic = makeFigure({ scale: 1.5, shirt: 0x1d1d26, pants: 0x2b2d42, hair: { style: 'swoop', color: 0x111111 }, shades: false });
    const gt = makeGuitar(0xd62839); gt.position.set(-0.05, 1.15, 0.32); vic.body.add(gt);
    vic.root.position.set(9.5, 0, 11); g.add(vic.root);
    const mic = makeMicStand(); mic.position.set(9.4, 0, 12.4); mic.scale.setScalar(1.2); g.add(mic);
    const kit = makeDrumKit(0xd62839); kit.scale.setScalar(1.5); kit.position.set(19, 0, 9); g.add(kit);
    const mike = makeFigure({ scale: 1.5, shirt: 0xf1f1f1, pants: 0x3a3a4a, hair: { style: 'spike', color: 0x222222 }, shades: true });
    setSeated(mike, true); mike.root.position.set(19, 0.35, 9 - 0.9 * 1.5); g.add(mike.root);
    S.vic = vic; S.mike = mike;
    const sign = makeSign('BEFORE TODAY', 'PIERCE THE VEIL', { w: 8.5, h: 2.7, bgF: '#4a4a5a', bgB: '#d62839' });
    sign.position.set(GARAGE_C.x, 5.7, 4.9); g.add(sign); S.sign = sign;
    // confetti burst on the flip
    const N = 140, R = rng(12), cols = [0xff5a6e, 0xffffff, 0xffd27a, 0x4fd5ff].map((c) => new THREE.Color(c));
    const conf = new THREE.InstancedMesh(new THREE.BoxGeometry(0.35, 0.35, 0.05), new THREE.MeshBasicMaterial(), N); S.conf = conf; conf.frustumCulled = false;
    S.cv = Array.from({ length: N }, (_, i) => { conf.setColorAt(i, cols[(R() * 4) | 0]); return { v: new THREE.Vector3((R() - 0.5) * 12, 6 + R() * 8, 2 + R() * 8), s: new THREE.Vector3(R() * 9, R() * 9, R() * 9) }; });
    g.add(conf);
  },
  update(t, world) {
    animateHometown(world.hometownA, t, 0);
    animateFigure(S.vic, t, 'guitar', 0, 1); animateFigure(S.mike, t, 'drum', 0.5, 1);
    const k = smooth(FLIP0, FLIP1, t); S.sign.userData.flip.rotation.x = Math.PI * k;
    S.sign.userData.flip.scale.setScalar(1 + 0.12 * Math.sin(k * Math.PI));
    const tau = t - FLIP1, m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), p = new THREE.Vector3(), sc = new THREE.Vector3();
    S.cv.forEach((c, i) => { if (tau < 0) { sc.setScalar(0); } else { sc.setScalar(Math.max(0, 1 - tau / 2.4));
      p.set(GARAGE_C.x + c.v.x * tau * 0.5, 8.5 + c.v.y * tau - 6 * tau * tau, 6 + c.v.z * tau * 0.5); }
      q.setFromEuler(e.set(tau * c.s.x, tau * c.s.y, 0)); m.compose(p, q, sc); S.conf.setMatrixAt(i, m); });
    S.conf.instanceMatrix.needsUpdate = true;
  },
};
