// DOM overlay (captured by the screenshot). Safe zone is enforced by the CSS in index.html:
// nothing above y=220, below y=1540, or right of x=960.
import { clamp } from './common.js';
const year = document.getElementById('year'), card = document.getElementById('card'), txt = document.getElementById('txt'), cta = document.getElementById('cta');
let key = '', words = [];
export function setYear(v, accent) {
  year.textContent = String(Math.round(v)); const f = Math.abs(v - Math.round(v));
  year.style.transform = `scale(${1 + 0.08 * (1 - clamp(f * 2.5))})`; document.documentElement.style.setProperty('--accent', accent);
}
export function setCard(c, t) {
  if (!c) { card.style.opacity = 0; return; }
  const k = c.text + '|' + (c.cta || '');
  if (k !== key) {
    key = k; txt.textContent = ''; words = [];
    c.text.split(/\s+/).forEach((raw) => { const hl = raw.startsWith('*') || raw.includes('*'); const span = document.createElement('span'); span.className = 'w' + (hl ? ' hl' : ''); span.textContent = raw.replace(/\*/g, ''); txt.appendChild(span); txt.appendChild(document.createTextNode(' ')); words.push(span); });
    cta.textContent = c.cta || '';
  }
  const out = clamp((c.t1 - t) / 0.25); card.style.opacity = out;
  const n = words.length, per = Math.min(0.16, (c.t1 - c.t0 - 0.9) / Math.max(1, n));
  words.forEach((w, i) => { const a = clamp((t - (c.t0 + i * per)) / 0.18), back = 1 + Math.sin(a * Math.PI) * 0.18; w.style.opacity = a; w.style.transform = `scale(${(0.6 + 0.4 * a) * back}) translateY(${(1 - a) * 24}px)`; });
  cta.style.opacity = c.cta ? clamp((t - (c.ctaT ?? c.t0 + 1.5)) / 0.3) : 0;
}
