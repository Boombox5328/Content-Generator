import * as THREE from 'three';
import { rng } from '../engine/lowpoly.js';
// building window-grid texture (lit windows at dusk)
export function windowTexture(base, wins, seed = 1) {
  const R = rng(seed), c = document.createElement('canvas'); c.width = 128; c.height = 256; const g = c.getContext('2d');
  g.fillStyle = base; g.fillRect(0, 0, 128, 256);
  for (let y = 0; y < 12; y++) for (let x = 0; x < 6; x++) { const on = R() > 0.4; g.fillStyle = on ? wins[(R() * wins.length) | 0] : 'rgba(30,36,60,.9)'; g.fillRect(x * 21.3 + 4, y * 21.3 + 5, 13.3, 11); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}
