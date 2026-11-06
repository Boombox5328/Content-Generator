import * as THREE from 'three';
export { THREE };

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const smoother = (x) => { const t = clamp(x); return t * t * t * (t * (t * 6 - 15) + 10); };

// flat-shaded, low-poly material (flatShading: true is mandatory in this project)
export function flat(color, opts = {}) {
  return new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: 0.92, metalness: 0, ...opts });
}
export function unlit(color, opts = {}) { return new THREE.MeshBasicMaterial({ color, ...opts }); }

let _glow;
export function glowTexture() {
  if (_glow) return _glow;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,.55)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  _glow = new THREE.CanvasTexture(c); return _glow;
}
export function halo(color, size) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glowTexture(), color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false }));
  s.scale.set(size, size, 1); return s;
}

// smooth value noise
const _r = rng(1337); const _tab = Array.from({ length: 256 * 256 }, () => _r());
const _h = (x, y) => _tab[((y & 255) << 8) | (x & 255)];
export function noise2(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(_h(xi, yi), _h(xi + 1, yi), u), lerp(_h(xi, yi + 1), _h(xi + 1, yi + 1), u), v);
}

export const mixHex = (a, b, k) => new THREE.Color(a).lerp(new THREE.Color(b), k);
export function box(w, h, d, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; return m;
}
// canvas text -> texture (signs, billboards)
export function textTexture(text, { w = 1024, h = 256, bg = '#ffffff', fg = '#111111', size = 150 } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  const lines = text.split('\n'); let fs = size;
  const font = (s) => `900 ${s}px Inter, "DejaVu Sans", sans-serif`;
  g.font = font(fs);
  while (fs > 20 && (Math.max(...lines.map((l) => g.measureText(l).width)) > w * 0.9 || fs * lines.length * 1.05 > h * 0.9)) { fs -= 4; g.font = font(fs); }
  g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
  lines.forEach((l, i) => g.fillText(l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * fs * 1.05));
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
// camera-shot helpers: each returns {pos, look}
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const mix3 = (a, b, k) => a.clone().lerp(b, k);
export const ease = (u) => { u = clamp(u); return 0.25 * u + 0.75 * (u * u * (3 - 2 * u)); }; // never fully stops
export function orbit(c, r, h, a0, a1, u, lookY = 0) {
  const a = lerp(a0, a1, u); return { pos: V(c.x + Math.sin(a) * r, c.y + h, c.z + Math.cos(a) * r), look: V(c.x, c.y + lookY, c.z) };
}
export function dolly(p0, p1, l0, l1, u) { const k = ease(u); return { pos: mix3(p0, p1, k), look: mix3(l0, l1, k) }; }
