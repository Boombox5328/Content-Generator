// PART 1 — "THE GARAGE YEARS" — beat table = shots + cards + year tags (single source of truth).
import * as THREE from 'three';
import { smooth } from './engine/lowpoly.js';
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sm5 = (u) => { u = Math.min(1, Math.max(0, u)); return u * u * u * (u * (u * 6 - 15) + 10); };   // ease in/out
export const HOLD = 1.0;
export const DUR = 60;

// camera helpers: p = eased progress (0..1), already reaches 1 before the final HOLD seconds
const mv = (a, b) => (p) => ({ pos: a.pos.clone().lerp(b.pos, p), look: a.look.clone().lerp(b.look, p), fov: a.fov + (b.fov - a.fov) * p });
const C = (pos, look, fov) => ({ pos: V(...pos), look: V(...look), fov });

export const SHOTS = [
  // ---- HOOK (2 s shots: 1 s move + 1 s hold; match cut sun -> bulb) ----
  { id: '1a', t0: 0, t1: 2, set: 'petco', year: '2026', cam: mv(C([-2, 13, 60], [0, 25, -120], 46), C([-2, 9, 54], [0, 22.5, -120], 46)), cfg: () => ({}), fp: null, dof: 0 },
  { id: '1b', t0: 2, t1: 4, set: 'garage', year: '2004', cam: mv(C([0.1, 1.2, 2.5], [0, 2.55, -6], 42), C([0.1, 1.2, 1.6], [0, 2.55, -6], 42)), cfg: () => ({ mode: 'hook' }), fp: V(0, 2.5, -2.4), dof: 2.0, fr: 3 },
  // ---- 2004–06 garage ----
  { id: '2a', t0: 4, t1: 7.7, set: 'garage', year: '2004–06', cam: mv(C([3.6, 1.7, 15.2], [-0.1, 1.9, -3.2], 38), C([1.8, 1.5, 9.6], [-0.1, 1.9, -3.2], 36)), cfg: () => ({ mode: 'band' }), fp: V(-0.8, 1.4, -2.9), dof: 1.3, fr: 10 },
  { id: '2b', t0: 7.7, t1: 11.4, set: 'garage', year: '2004–06', cam: mv(C([-1.2, 1.45, -0.3], [0.1, 1.25, -4.2], 44), C([0.3, 1.5, -0.35], [0.3, 1.3, -4.4], 44)), cfg: () => ({ mode: 'band' }), fp: V(-0.2, 1.4, -3.5), dof: 1.6, fr: 2.5 },
  { id: '2c', t0: 11.4, t1: 15, set: 'garage', year: '2004–06', cam: mv(C([2.8, 1.5, -1.4], [1.4, 2.25, -6.4], 40), C([1.6, 1.9, -2.4], [1.4, 2.6, -6.4], 40)), cfg: (u) => ({ mode: 'band', board: smooth(0.22, 0.5, u) }), fp: V(1.4, 2.6, -6.4), dof: 1.2, fr: 4 },
  // ---- 2007 studio ----
  { id: '3a', t0: 15, t1: 18.7, set: 'studio', year: '2007', cam: mv(C([1.5, 2.1, 4.4], [0.1, 1.15, -5.0], 40), C([0.6, 1.95, 3.4], [0.1, 1.15, -5.0], 40)), cfg: () => ({ mode: 'studio', monument: 0 }), fp: V(-0.5, 1.3, -4.0), dof: 2.4 },
  { id: '3b', t0: 18.7, t1: 22.4, set: 'studio', year: '2007', cam: mv(C([-2.5, 1.4, -0.8], [-0.5, 1.35, -4.0], 46), C([-1.3, 1.55, -0.9], [-0.3, 1.35, -4.0], 46)), cfg: () => ({ mode: 'studio', monument: 0.04 }), fp: V(-0.5, 1.4, -3.9), dof: 1.6 },
  { id: '3c', t0: 22.4, t1: 26, set: 'studio', year: '2007', cam: mv(C([0.3, 1.0, -1.1], [0.2, 1.0, -6.5], 50), C([0.3, 2.4, -0.9], [0.2, 2.1, -6.8], 50)), cfg: (u) => ({ mode: 'studio', monument: 0.04 + 0.9 * smooth(0.05, 0.8, u) }), fp: V(0.2, 1.6, -6.9), dof: 1.6 },
  // ---- 2007 rehearsal (four lit one by one) ----
  { id: '4a', t0: 26, t1: 30.5, set: 'studio', year: '2007', cam: mv(C([0.0, 1.8, 1.8], [0, 1.2, -5.2], 44), C([0.0, 1.95, 2.8], [0, 1.2, -5.2], 44)), cfg: (u, t) => ({ mode: 'rehearsal', monument: 1, show: { tony: true, jaime: true }, spots: [smooth(28.4, 29.0, t), smooth(26.2, 26.8, t), smooth(29.6, 30.2, t), smooth(26.2, 26.8, t)] }), fp: V(0, 1.2, -4.5), dof: 1.2 },
  { id: '4b', t0: 30.5, t1: 35, set: 'studio', year: '2007', cam: mv(C([-1.2, 1.9, 3.1], [0, 1.2, -5.0], 44), C([1.0, 1.95, 3.0], [0, 1.2, -5.0], 44)), cfg: () => ({ mode: 'rehearsal', monument: 1, show: { tony: true, jaime: true }, spots: [1, 1, 1, 1] }), fp: V(0, 1.2, -4.5), dof: 1.2 },
  // ---- 2008 Warped Tour ----
  { id: '5a1', t0: 35, t1: 38.5, set: 'festival', year: '2008', cam: mv(C([-10, 10, 36], [0, 3, -2], 38), C([-3.5, 3.6, 31], [0, 4, -2], 38)), cfg: () => ({}), fp: V(0, 3, -1), dof: 1.2 },
  { id: '5a2', t0: 38.5, t1: 42, set: 'festival', year: '2008', cam: mv(C([-2.6, 2.5, 30], [0.2, 4.0, -2], 38), C([-1.4, 2.4, 25], [0.2, 4.0, -2], 38)), cfg: () => ({}), fp: V(0, 3, -1), dof: 1.8 },
  { id: '5a3', t0: 42, t1: 45.5, set: 'festival', year: '2008', cam: mv(C([-6.5, 1.6, 28], [0, 3.4, -2], 36), C([-3.4, 1.8, 27], [0, 3.4, -2], 36)), cfg: () => ({}), fp: V(0, 3, -1), dof: 1.8 },
  // ---- 2010 club ----
  { id: '5b1', t0: 45.5, t1: 50.5, set: 'club', year: '2010', cam: mv(C([3.6, 2.6, 12.6], [0, 2.9, -8], 40), C([0.7, 2.2, 8.4], [0, 2.9, -8], 40)), cfg: () => ({ monument: 0 }), fp: V(0, 2.5, -6), dof: 1.4 },
  { id: '5b2', t0: 50.5, t1: 55.5, set: 'club', year: '2010', cam: mv(C([-4.5, 2.2, 8.8], [0, 3.0, -8.5], 40), C([1.2, 2.4, 8.2], [0, 3.0, -8.5], 40)), cfg: (u) => ({ monument: smooth(0.08, 0.6, u) }), fp: V(0, 2.8, -8.5), dof: 1.4 },
  // ---- end card: back to Petco at dusk, then black ----
  { id: 'END', t0: 55.5, t1: 60, set: 'petco', year: null, cam: mv(C([-2, 9, 54], [0, 22.5, -120], 46), C([-2, 15, 57], [0, 24.5, -120], 46)), cfg: () => ({}), fp: null, dof: 0 },
];
// ONE card per beat: appears 1 s into the beat, holds >= 3.5 s (hook: 0.5 s, see NOTES), <= 6 words
export const CARDS = [
  { t0: 0.5, t1: 4.0, text: 'From this garage… to this.' },
  { t0: 5.0, t1: 9.0, text: 'A song title becomes a band.' },
  { t0: 16.0, t1: 20.0, text: 'Two brothers. One debut.' },
  { t0: 27.0, t1: 31.0, text: 'Then there were four.' },
  { t0: 36.0, t1: 40.0, text: 'A full Warped Tour run.' },
  { t0: 46.5, t1: 50.5, text: '#1 on Heatseekers.' },
  { t0: 56.0, t1: 59.5, text: 'Part 2: the peak… and the silence.' },
];
export const camAt = (shot, t) => { const dur = shot.t1 - shot.t0; const p = sm5((t - shot.t0) / (dur - HOLD)); return shot.cam(p); };
export const shotAt = (t) => SHOTS.find((s) => t >= s.t0 && t < s.t1) || SHOTS[SHOTS.length - 1];
export const cardAt = (t) => { const c = CARDS.find((c) => t >= c.t0 && t <= c.t1); if (!c) return null; return { ...c, a: Math.min(1, (t - c.t0) / 0.25, (c.t1 - t) / 0.25) }; };
