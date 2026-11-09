import * as THREE from 'three';
import { createPipeline } from './engine/pipeline.js';
import { smooth } from './engine/lowpoly.js';
import { Director } from './engine/director.js';
import { setHud } from './engine/hud.js';
import { SHOTS, CARDS, DUR, HOLD, camAt, shotAt, cardAt } from './part1.js';
import { makeGarage } from './sets/garage.js';
import { makeStudio } from './sets/studio.js';
import { makeFestival } from './sets/festival.js';
import { makeClub } from './sets/club.js';
import { makePetco } from './sets/petco.js';

const pipe = createPipeline(document.getElementById('c'), +(new URLSearchParams(location.search).get('pr') || 2));
const dir = new Director(pipe);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sets = {};
const reg = (id, make) => { try { sets[id] = dir.register(make()); } catch (e) { console.error('SET FAIL', id, e.stack.split('\n').slice(0, 4).join(' | ')); } };
reg('garage', makeGarage); reg('studio', makeStudio); reg('festival', makeFestival); reg('club', makeClub); reg('petco', makePetco);

// hero style frames: { set, t, cfg, cam, look overrides, hud }
const STILLS = {
  hookB: { set: 'garage', t: 2.0, cfg: { mode: 'hook' }, cam: { pos: V(0.1, 1.2, 1.6), look: V(0, 2.55, -6), fov: 42 }, look: { dofScale: 2.2, focus: 8, focusRange: 3 }, hud: { year: '2004', card: 'From this garage… to this.' } },
  b2: { set: 'garage', t: 3.1, cfg: { mode: 'band', board: 0 }, cam: { pos: V(1.8, 1.5, 9.6), look: V(-0.1, 1.9, -3.2), fov: 36 }, look: { dofScale: 1.4, focus: 14, focusRange: 5 }, hud: { year: '2004–06', card: 'A song title becomes a band.' } },
};
STILLS.b3 = { set: 'studio', t: 4.2, cfg: { mode: 'studio', monument: 0.72, show: {} }, cam: { pos: V(0.6, 1.95, 3.4), look: V(0.1, 1.15, -5.0), fov: 40 }, look: { dofScale: 2.4, focus: 8.4, focusRange: 3.0 }, hud: { year: '2007', card: 'Two brothers. One debut.' } };
STILLS.b4 = { set: 'studio', t: 6.0, cfg: { mode: 'rehearsal', monument: 1, spots: [1, 1, 0.9, 0.9], show: { tony: true, jaime: true } }, cam: { pos: V(0.0, 1.95, 2.8), look: V(0.0, 1.2, -5.2), fov: 44 }, look: { dofScale: 1.4, focus: 8.4, focusRange: 3.5 }, hud: { year: '2007', card: 'Then there were four.' } };
STILLS.hookA = { set: 'petco', t: 1.2, cfg: {}, cam: { pos: V(-2, 9, 54), look: V(0, 22.5, -120), fov: 46 }, look: { dofScale: 0 }, hud: { year: '2026', card: 'From this garage… to this.' } };
STILLS.b5a = { set: 'festival', t: 2.4, cfg: {}, cam: { pos: V(-2.6, 2.5, 28.5), look: V(0.2, 4.0, -2), fov: 38 }, look: { dofScale: 1.8, focus: 30, focusRange: 10 }, hud: { year: '2008', card: 'A full Warped Tour run.' } };
STILLS.b5b = { set: 'club', t: 3.0, cfg: { monument: 1 }, cam: { pos: V(0.7, 2.2, 8.4), look: V(0.0, 2.9, -8), fov: 40 }, look: { dofScale: 1.4, focus: 15, focusRange: 7 }, hud: { year: '2010', card: '#1 on Heatseekers.' } };
window.renderStill = async (name, tOverride) => {
  const s = STILLS[name]; if (!s) throw new Error('unknown still ' + name);
  const set = dir.use(s.set); const t = tOverride ?? s.t;
  set.update(t, s.cfg); dir.camera(s.cam); pipe.setLook({ ...set.look, ...(s.look || {}) });
  if (set.sky) set.sky.userData.follow(pipe.camera);
  setHud(s.hud || {}); pipe.render(Math.round(t * 30), t);
  return { name, tris: 0 };
};
window.renderCustom = async (o) => { const set = dir.use(o.set); const t = o.t ?? 1; set.update(t, o.cfg || {}); const c = o.cam; dir.camera({ pos: V(...c.pos), look: V(...c.look), fov: c.fov ?? 40 }); pipe.setLook({ ...set.look, ...(o.look || {}) });
  if (set.sky) set.sky.userData.follow(pipe.camera); setHud(o.hud || {}); pipe.render(Math.round(t * 30), t); return o.set; };
window.listStills = () => Object.keys(STILLS);
window.ptvReady = true;

// ---------- Part 1 timeline ----------
let curSet = null;
window.renderFrame = (frame) => {
  const t = frame / 30, shot = shotAt(t), u = (t - shot.t0) / (shot.t1 - shot.t0);
  if (curSet !== shot.set) { dir.use(shot.set); curSet = shot.set; }
  const set = dir.sets[shot.set];
  set.update(t, shot.cfg(u, t));
  const c = camAt(shot, t); dir.camera(c);
  const fo = shot.fp ? pipe.camera.position.distanceTo(shot.fp) : 8;
  pipe.setLook({ ...set.look, dofScale: shot.dof || 0, focus: fo, focusRange: Math.max(2, fo * 0.35) });
  if (set.sky) set.sky.userData.follow(pipe.camera);
  const card = cardAt(t); setHud({ year: shot.year, card: card?.text, a: card?.a ?? 0 });
  pipe.render(frame, t, smooth(59.0, 59.6, t) );
  return shot.id;
};
// self-review helper: camera angular speed (deg/s), hold stillness and shot lengths
window.checkCameras = () => {
  const out = []; const prev = new THREE.Vector3(), cur = new THREE.Vector3();
  for (const s of SHOTS) { let maxDeg = 0, holdMove = 0, last = null, lastP = null;
    for (let f = Math.round(s.t0 * 30); f < Math.round(s.t1 * 30); f++) { const t = f / 30, c = camAt(s, t); cur.copy(c.look).sub(c.pos).normalize();
      if (last) { const ang = Math.acos(Math.min(1, last.dot(cur))) * 180 / Math.PI * 30; maxDeg = Math.max(maxDeg, ang); if (t > s.t1 - HOLD + 0.05) holdMove = Math.max(holdMove, c.pos.distanceTo(lastP) * 30); }
      last = cur.clone(); lastP = c.pos.clone(); }
    out.push({ id: s.id, dur: +(s.t1 - s.t0).toFixed(2), maxDegPerSec: +maxDeg.toFixed(1), holdSpeed: +holdMove.toFixed(3) }); }
  return out; };
window.cards = () => CARDS;
