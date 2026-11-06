// DOM overlay (captured by the screenshot). Safe zone is enforced by the CSS in index.html.
import { clamp } from './common.js';
const year = document.getElementById('year'), card = document.getElementById('card'),
  txt = document.getElementById('txt'), cta = document.getElementById('cta');
let last = '';
export function setYear(v, accent) {
  const y = Math.round(v); year.textContent = String(y);
  const f = Math.abs(v - Math.round(v)); // tiny "tick" pop as the number changes
  year.style.transform = `scale(${1 + 0.07 * (1 - clamp(f * 2.5))})`;
  document.documentElement.style.setProperty('--accent', accent);
}
export function setCard(c, t) {
  if (!c) { card.style.opacity = 0; return; }
  const a = clamp((t - c.t0) / 0.25) * clamp((c.t1 - t) / 0.25);
  const key = c.text + (c.cta || '');
  if (key !== last) { txt.textContent = c.text; cta.textContent = c.cta || ''; last = key; }
  card.style.opacity = a; card.style.transform = `translateY(${(1 - a) * 28}px)`;
}
