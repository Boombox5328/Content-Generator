import * as THREE from 'three';
import { rng } from './lowpoly.js';
// canvas text -> texture. rough:true gives a hand-painted, slightly wobbly look (for in-world signs).
export function textTexture(text, { w = 1024, h = 256, bg = '#222', fg = '#fff', size = 160, rough = false, font = 'Inter' } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'), R = rng(text.length * 7 + 1);
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  if (rough) { for (let i = 0; i < 400; i++) { g.fillStyle = `rgba(0,0,0,${R() * 0.07})`; g.fillRect(R() * w, R() * h, 30 + R() * 80, 2 + R() * 4); } }
  const lines = text.split('\n'); let fs = size; const f = (s) => `900 ${s}px ${font}, "DejaVu Sans", sans-serif`; g.font = f(fs);
  while (fs > 20 && (Math.max(...lines.map((l) => g.measureText(l).width)) > w * 0.88 || fs * lines.length * 1.05 > h * 0.86)) { fs -= 4; g.font = f(fs); }
  g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
  lines.forEach((l, i) => { const y = h / 2 + (i - (lines.length - 1) / 2) * fs * 1.05; if (rough) { let x = w / 2 - g.measureText(l).width / 2; for (const ch of l) { const cw = g.measureText(ch).width; g.save(); g.translate(x + cw / 2, y + (R() - 0.5) * 6); g.rotate((R() - 0.5) * 0.05); g.textAlign = 'center'; g.fillText(ch, 0, 0); g.restore(); x += cw; } } else g.fillText(l, w / 2, y); });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
