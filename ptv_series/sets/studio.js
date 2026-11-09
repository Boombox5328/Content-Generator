// Seattle studio (2007): control room with glowing desk (foreground), live room beyond the glass, rainy window, monument.
// Also serves as the dark rehearsal room (cfg.mode = 'rehearsal') with four spotlights lit one by one.
import { THREE, paint, bevelBox, mesh, M, lpMat, emissiveMat, rng, tube, lerp, clamp, smooth } from '../engine/lowpoly.js';
import { makeRig } from '../engine/pipeline.js';
import { makeShaft } from '../engine/shafts.js';
import { makeHuman, pose, BAND } from '../kit/human.js';
import { makeGuitar, makeMicStand, makeDrumKit, makeAmpStack } from '../kit/instruments.js';
import { rainWindow, cityBokeh, crate } from '../kit/props.js';
import { makeMonument } from '../kit/monument.js';

const put = (p, geo, x = 0, y = 0, z = 0, mat = M) => { const m = mesh(geo, mat); m.position.set(x, y, z); p.add(m); return m; };

export function makeStudio() {
  const group = new THREE.Group(), glow = [], R = rng(23);
  // ---------- live room (z from -0.4 to -9, x ±4.2, h 3.6) ----------
  const live = new THREE.Group(); group.add(live);
  put(live, bevelBox(8.6, 0.1, 9.4, 0.02, { top: 0x7a5a3a, bottom: 0x4a3420, axis: 'z', jitter: 0.09, seed: 2 }), 0, -0.05, -4.7);                  // wood floor
  for (let i = 0; i < 14; i++) put(live, bevelBox(8.5, 0.005, 0.02, 0.002, { top: 0x2a1c10 }), 0, 0.001, -0.5 - i * 0.65);                                    // plank seams
  put(live, bevelBox(0.15, 3.8, 9.4, 0.02, { top: 0x3a3440, bottom: 0x1e1a24 }), -4.3, 1.9, -4.7); put(live, bevelBox(0.15, 3.8, 9.4, 0.02, { top: 0x3a3440, bottom: 0x1e1a24 }), 4.3, 1.9, -4.7);
  put(live, bevelBox(8.6, 3.8, 0.15, 0.02, { top: 0x2e2a38, bottom: 0x18141e }), 0, 1.9, -9.4); put(live, bevelBox(8.7, 0.12, 9.5, 0.02, { top: 0x2a2630 }), 0, 3.84, -4.7);
  // acoustic foam pyramids on side walls
  for (const sx of [-1, 1]) for (let r = 0; r < 4; r++) for (let c = 0; c < 9; c++) { const p = put(live, paint(new THREE.ConeGeometry(0.2, 0.22, 4), { top: 0x6a6070, bottom: 0x2a2630, seed: r * 9 + c, jitter: 0.12 }), sx * 4.1, 0.7 + r * 0.55, -0.9 - c * 0.92); p.rotation.set(0, Math.PI / 4, sx * Math.PI / 2 * -1); }
  // rainy window on the back wall with city bokeh behind it
  const win = new THREE.Group(); win.position.set(0, 2.0, -9.3); live.add(win);
  const bok = cityBokeh(5.2, 2.2, 6, [0xff9a50, 0x7fc8ff, 0xff4f7a, 0xffe08a]); bok.position.z = -0.12; win.add(bok); glow.push(...bok.userData.glow);
  const rain = rainWindow(5.2, 2.2, 4); rain.position.z = 0.02; win.add(rain);
  put(win, bevelBox(5.5, 0.14, 0.18, 0.02, { top: 0x2a2630 }), 0, 1.16, 0.02); put(win, bevelBox(5.5, 0.14, 0.18, 0.02, { top: 0x2a2630 }), 0, -1.16, 0.02);
  for (const x of [-2.7, 0, 2.7]) put(win, bevelBox(0.14, 2.4, 0.18, 0.02, { top: 0x2a2630 }), x, 0, 0.02);
  // gear in live room
  const amp = makeAmpStack({ glow: 0xff5030 }); amp.position.set(-2.8, 0, -7.9); amp.rotation.y = 0.3; live.add(amp); glow.push(...amp.userData.glow);
  const amp2 = makeAmpStack(); amp2.position.set(2.9, 0, -7.9); amp2.rotation.y = -0.3; live.add(amp2); glow.push(...amp2.userData.glow);
  const kit = makeDrumKit({ shell: 0x2a5a6a, shell2: 0x0e2028 }); kit.position.set(1.6, 0, -6.0); kit.scale.setScalar(1.12); live.add(kit);
  put(live, paint(new THREE.CylinderGeometry(0.18, 0.2, 0.06, 10), { top: 0x1a1a20 }), 1.6, 0.5, -6.85);
  const mic = makeMicStand(); mic.position.set(-0.7, 0, -3.5); mic.rotation.y = 0.15; live.add(mic);
  put(live, paint(new THREE.CylinderGeometry(1.4, 1.4, 0.03, 16), { top: 0x6a3030, bottom: 0x3a1818, jitter: 0.1, seed: 9 }), 1.6, 0.015, -6.0);
  const figs = {}; const addFig = (id, mode, x, z, ry, extra) => { const h = makeHuman({ ...BAND[id] }); h.root.position.set(x, 0, z); h.root.rotation.y = ry; live.add(h.root); figs[id] = { h, mode }; return h; };
  const vic = addFig('vic', 'guitar', -0.7, -4.0, 0.1); const g1 = makeGuitar({ body: 0xb3202b }); g1.position.set(-0.02, 0.1, 0.19); g1.rotation.z = 0.5; vic.attach(g1);
  addFig('mike', 'drum', 1.6, -6.9, 0);
  const tony = addFig('tony', 'guitar', -2.0, -4.5, 0.3); const g2 = makeGuitar({ body: 0x2aa6b8, body2: 0x0d3a44 }); g2.position.set(-0.02, -0.12, 0.19); g2.rotation.z = 0.35; tony.attach(g2);
  const jaime = addFig('jaime', 'guitar', 1.3, -4.3, -0.3); const g3 = makeGuitar({ body: 0x23262e, body2: 0x090a0d, bass: true }); g3.position.set(-0.02, 0.0, 0.19); g3.rotation.z = 0.42; jaime.attach(g3);
  // ---------- control room (z > 0) ----------
  const ctl = new THREE.Group(); group.add(ctl);
  put(ctl, bevelBox(8.6, 0.1, 6, 0.02, { top: 0x3a3440, bottom: 0x1c1822, seed: 3 }), 0, -0.05, 3.0);
  put(ctl, bevelBox(8.6, 0.12, 6, 0.02, { top: 0x201c28 }), 0, 3.5, 3.0);
  put(ctl, bevelBox(0.15, 3.6, 6, 0.02, { top: 0x2e2a38 }), -4.3, 1.8, 3.0); put(ctl, bevelBox(0.15, 3.6, 6, 0.02, { top: 0x2e2a38 }), 4.3, 1.8, 3.0);
  put(ctl, bevelBox(8.6, 3.6, 0.15, 0.02, { top: 0x2a2632 }), 0, 1.8, 6.0);
  // glass window wall with frame
  const frame = (w, h, x, y, z) => put(ctl, bevelBox(w, h, 0.18, 0.02, { top: 0x1e1a24 }), x, y, z);
  frame(8.6, 0.6, 0, 3.3, -0.4); frame(8.6, 0.9, 0, 0.45, -0.4); frame(0.22, 3.6, -4.3, 1.8, -0.4); frame(0.22, 3.6, 4.3, 1.8, -0.4);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(8.2, 2.1), new THREE.MeshBasicMaterial({ color: 0x9ab8ff, transparent: true, opacity: 0.03, depthWrite: false })); glass.position.set(0, 1.95, -0.3); ctl.add(glass);
  // mixing desk (angled meter bridge, channel strips with glowing faders/meters)
  const desk = new THREE.Group(); desk.position.set(0, 0, 1.1); ctl.add(desk);
  put(desk, bevelBox(4.2, 0.78, 1.1, 0.04, { top: 0x2a2630, bottom: 0x14101a, seed: 5 }), 0, 0.39, 0);
  const top = put(desk, bevelBox(4.3, 0.1, 1.0, 0.03, { top: 0x3a3440, bottom: 0x24202c }), 0, 0.82, 0.02); top.rotation.x = -0.12;
  const br = put(desk, bevelBox(4.3, 0.55, 0.14, 0.03, { top: 0x2a2630 }), 0, 1.15, -0.46); br.rotation.x = 0.3;
  const chans = 24, fMat = emissiveMat(0xffb040, 3.2), gMat = emissiveMat(0x40ff90, 3.0), rMat = emissiveMat(0xff4a30, 3.2);
  for (let i = 0; i < chans; i++) { const x = -2.0 + (i / (chans - 1)) * 4.0;
    put(desk, bevelBox(0.11, 0.015, 0.5, 0.004, { top: 0x14101a }), x, 0.885, 0.04).rotation.x = -0.12;
    const f = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.03, 0.08), fMat); f.position.set(x, 0.915, 0.04 + ((i * 37) % 10 - 5) * 0.04); f.rotation.x = -0.12; desk.add(f); glow.push(f);
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.02 + ((i * 53) % 9) * 0.012, 0.012), (i % 7 === 3) ? rMat : gMat); m.position.set(x, 1.22 + 0.04, -0.47 + 0.05); m.rotation.x = 0.3; desk.add(m); glow.push(m);
    for (let k = 0; k < 3; k++) { const kn = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.02, 6), new THREE.MeshStandardMaterial({ color: 0xaaaab4, flatShading: true, roughness: 0.4, metalness: 0.5 })); kn.position.set(x, 0.9, -0.25 - k * 0.07); desk.add(kn); } }
  put(ctl, bevelBox(0.5, 1.3, 0.4, 0.03, { top: 0x1e1a24 }), -3.3, 0.65, 1.2); put(ctl, bevelBox(0.5, 1.3, 0.4, 0.03, { top: 0x1e1a24 }), 3.3, 0.65, 1.2);   // racks
  for (const x of [-3.3, 3.3]) for (let k = 0; k < 7; k++) { const l = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.02, 0.01), k % 2 ? gMat : fMat); l.position.set(x, 0.2 + k * 0.17, 1.42); ctl.add(l); glow.push(l); }
  for (const x of [-2.6, 2.6]) { put(ctl, bevelBox(0.5, 0.78, 0.45, 0.05, { top: 0x2a2630 }), x, 1.55, 0.7).rotation.y = x < 0 ? 0.3 : -0.3; put(ctl, paint(new THREE.CylinderGeometry(0.17, 0.17, 0.03, 10), { top: 0x3a3a44 }), x + (x < 0 ? 0.05 : -0.05), 1.55, 0.95).rotation.x = Math.PI / 2; }
  const lamp = new THREE.Group(); lamp.position.set(-1.9, 0.85, 1.0); ctl.add(lamp); put(lamp, paint(new THREE.CylinderGeometry(0.06, 0.08, 0.04, 8), { top: 0x2a2a30 }), 0, 0.02, 0); put(lamp, paint(new THREE.CylinderGeometry(0.012, 0.012, 0.5, 5), { top: 0x2a2a30 }), 0, 0.27, 0);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.16, 8, 1, true), new THREE.MeshStandardMaterial({ color: 0xffd9a0, emissive: 0xffa040, emissiveIntensity: 2.2, side: THREE.DoubleSide, flatShading: true })); shade.position.set(0, 0.6, 0.05); shade.rotation.x = 0.4; lamp.add(shade); glow.push(shade);
  put(ctl, paint(new THREE.CylinderGeometry(0.05, 0.04, 0.09, 8), { top: 0xe8e4dc }), 1.7, 0.9, 1.0);                                                  // coffee mug

  // ---------- monument (deep red) ----------
  const mon = makeMonument({ color: 0xd01830, height: 3.4, seed: 5, glowI: 3.4 }); mon.group.position.set(0.2, 0, -6.9); live.add(mon.group); glow.push(...mon.glow);
  const crackMat = emissiveMat(0xff3050, 4); const cracks = []; for (let i = 0; i < 9; i++) { const c = new THREE.Mesh(new THREE.BoxGeometry(1, 0.012, 0.05 + R() * 0.04), crackMat); c.userData = { a: (i / 9) * 6.283 + R() * 0.4, L: 0.8 + R() * 1.4 }; live.add(c); cracks.push(c); glow.push(c); }
  const monLight = new THREE.PointLight(0xff2a40, 0, 12, 2); monLight.position.set(0.2, 1.8, -6.5); live.add(monLight);

  // ---------- lights ----------
  const rig = makeRig({ key: { type: 'spot', pos: [-2.2, 3.5, -1.4], color: 0xffb468, intensity: 120, angle: 0.9, far: 16 }, rim: { pos: [0.5, 3.2, -11], color: 0x7fb4ff, intensity: 3.4 }, fill: { sky: 0x405080, ground: 0x1a1218, intensity: 0.5 }, target: new THREE.Vector3(0, 1.0, -4.5) });
  group.add(rig);
  const spots = [[-2.0, -4.5], [-0.5, -3.9], [1.3, -4.3], [1.6, -6.7]].map(([x, z], i) => { const s = new THREE.SpotLight(0xfff0d8, 0, 14, 0.38, 0.8, 2); s.position.set(x + 0.4, 3.6, z + 2.2); s.target.position.set(x, 1.0, z); if (i < 2) { s.castShadow = true; s.shadow.mapSize.set(2048, 2048); s.shadow.bias = -0.0004; }
    live.add(s, s.target); const sh = makeShaft([x + 0.4, 3.6, z + 2.2], [x, 0.0, z], { r0: 0.1, r1: 1.0, color: 0xfff0d8, intensity: 0.0, falloff: 1.1 }); live.add(sh); return { s, sh }; });
  const rimWin = new THREE.SpotLight(0x6aa4ff, 120, 20, 0.9, 1, 2); rimWin.position.set(0, 2.4, -9.0); rimWin.target.position.set(0, 1.2, -3); live.add(rimWin, rimWin.target);
  const shaftWin = makeShaft([0, 2.5, -9.1], [0, 0.0, -3.0], { r0: 1.2, r1: 3.4, color: 0x6a9cff, intensity: 0.14, falloff: 0.9 }); live.add(shaftWin);
  const dust = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xcfe0ff, size: 2.2, sizeAttenuation: false, transparent: true, opacity: 0.45, depthWrite: false, toneMapped: false }));
  const DN = 140, dBase = Array.from({ length: DN }, () => [(R() - 0.5) * 7, R() * 3.2, -1.5 - R() * 7, R() * 6.28, 0.1 + R() * 0.2]); dust.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(DN * 3), 3)); dust.frustumCulled = false; live.add(dust);

  const ctlFill = new THREE.PointLight(0xff9a50, 7, 10, 2); ctlFill.position.set(0, 2.6, 2.4); group.add(ctlFill); const ctlBlue = new THREE.PointLight(0x5a7aff, 4, 9, 2); ctlBlue.position.set(0, 1.2, 4.6); group.add(ctlBlue);
  const set = { id: 'studio', group, glow, figs, mon,
    env: { top: 0x10182e, mid: 0x20284a, horizon: 0x3a3a60, ground: 0x0a0810 }, fog: { color: 0x120e1c, density: 0.026 }, look: { grade: 'amber', bloomI: 1.7, dofScale: 0 },
    // mode: 'studio' | 'rehearsal' ; monument: 0..1 grow ; spots:[a,b,c,d] 0..1 ; show:{tony,jaime}
    update(t, cfg = {}) {
      const mode = cfg.mode || 'studio', reh = mode === 'rehearsal', sh = cfg.show || {};
      figs.tony.h.root.visible = reh ? (cfg.spots?.[2] ?? 0) > 0.01 || sh.tony : !!sh.tony; figs.jaime.h.root.visible = reh ? (cfg.spots?.[3] ?? 0) > 0.01 || sh.jaime : !!sh.jaime;
      Object.entries(figs).forEach(([id, f]) => pose(f.h, t, f.mode, { ph: id.length * 0.9 }));
      figs.vic.h.root.position.set(-0.5, 0, -3.9);
      rig.userData.key.intensity = reh ? 0 : 120; rig.userData.rim.intensity = reh ? 1.0 : 3.4; rimWin.intensity = reh ? 20 : 120; shaftWin.visible = !reh;
      const sp = cfg.spots || [0, 0, 0, 0];
      spots.forEach((o, i) => { o.s.intensity = 380 * sp[i]; o.sh.material.uniforms.intensity.value = 0.55 * sp[i]; o.sh.userData.setT(t); o.sh.visible = sp[i] > 0.01; });
      const m = cfg.monument ?? 0; mon.grow(m); mon.update(t); mon.group.visible = m > 0.001; mon.group.position.y = (1 - m) * -0.6; monLight.intensity = 90 * smooth(0.05, 0.8, m) * (reh ? 0.5 : 1);
      cracks.forEach((c) => { const d = c.userData, k = smooth(0.0, 0.5, m), L = d.L * k + 0.001; c.scale.x = L; c.position.set(0.2 + Math.cos(d.a) * (L / 2 + 0.3), 0.012, -6.9 + Math.sin(d.a) * (L / 2 + 0.3)); c.rotation.y = -d.a; c.visible = m > 0.01; });
      ctlFill.intensity = reh ? 4 : 7; rain.userData.update(t); shaftWin.userData.setT(t);
      const p = dust.geometry.attributes.position; dBase.forEach((d, i) => p.setXYZ(i, d[0] + Math.sin(t * d[4] + d[3]) * 0.15, d[1] + Math.sin(t * d[4] * 0.7 + d[3]) * 0.1, d[2])); p.needsUpdate = true;
    } };
  return set;
}
