// Low-poly helpers: faceting, vertex-colour gradients, bevelled boxes, materials.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
export { THREE, mergeGeometries };

export const col = (h) => new THREE.Color(h);
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };

// triangulate + split vertices so every face is a visible facet
export function facet(geo) { const g = geo.index ? geo.toNonIndexed() : geo; g.computeVertexNormals(); return g; }

// vertex-colour gradient along an axis with per-facet value jitter (never a single flat colour)
export function paint(geo, { top = 0xffffff, bottom, axis = 'y', jitter = 0.07, seed = 1, hue = 0 } = {}) {
  bottom = bottom ?? top; const g = facet(geo), p = g.attributes.position, R = rng(seed);
  g.computeBoundingBox(); const bb = g.boundingBox, a = axis, lo = bb.min[a], hi = bb.max[a], span = Math.max(1e-6, hi - lo);
  const c0 = col(bottom), c1 = col(top), tmp = new THREE.Color(), cols = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i += 3) {
    const t = clamp((((p.getX(i) * (a === 'x') + p.getY(i) * (a === 'y') + p.getZ(i) * (a === 'z')) + ((p.getX(i + 1) * (a === 'x') + p.getY(i + 1) * (a === 'y') + p.getZ(i + 1) * (a === 'z'))) + ((p.getX(i + 2) * (a === 'x') + p.getY(i + 2) * (a === 'y') + p.getZ(i + 2) * (a === 'z')))) / 3 - lo) / span);
    tmp.copy(c0).lerp(c1, t).multiplyScalar(1 + (R() - 0.5) * 2 * jitter);
    if (hue) tmp.offsetHSL((R() - 0.5) * hue, 0, 0);
    for (let k = 0; k < 3; k++) { cols[(i + k) * 3] = tmp.r; cols[(i + k) * 3 + 1] = tmp.g; cols[(i + k) * 3 + 2] = tmp.b; }
  }
  g.setAttribute('color', new THREE.BufferAttribute(cols, 3)); return g;
}
export const lpMat = (o = {}) => new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.82, metalness: 0.02, envMapIntensity: 1, ...o });
export const emissiveMat = (color, intensity = 3) => new THREE.MeshStandardMaterial({ color: 0x000000, emissive: color, emissiveIntensity: intensity, roughness: 1, flatShading: true, toneMapped: false });

export function bevelBox(w, h, d, r = 0.02, opt = {}) { return paint(new RoundedBoxGeometry(w, h, d, 2, Math.min(r, w / 2.01, h / 2.01, d / 2.01)), opt); }
export function mesh(geo, mat, { cast = true, receive = true } = {}) { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; m.receiveShadow = receive; return m; }
export const M = lpMat();           // shared default vertex-colour material
export function at(o, x = 0, y = 0, z = 0) { o.position.set(x, y, z); return o; }
export function tris(obj) { let n = 0; obj.traverse((o) => { if (o.isMesh) n += o.geometry.attributes.position.count / 3; }); return Math.round(n); }
export function tube(points, r = 0.01, seg = 3, closed = false, color = 0x222222) {
  const c = new THREE.CatmullRomCurve3(points); const g = new THREE.TubeGeometry(c, Math.max(4, points.length * 3), r, seg, closed);
  return mesh(paint(g, { top: color, jitter: 0.03 }), M);
}
