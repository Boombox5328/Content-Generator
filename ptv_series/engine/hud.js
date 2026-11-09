// DOM overlay: year tag (top-left) + one text card in the lower third on a soft dark gradient. Safe zone enforced by CSS.
const $ = (id) => document.getElementById(id);
export function setHud({ year = null, card = null, cta = null, a = 1 } = {}) {
  const y = $('year'), c = $('card'), p = $('panel'), t = $('cta');
  y.textContent = year ?? ''; y.style.opacity = year ? 1 : 0;
  c.textContent = card ?? ''; c.style.opacity = card ? a : 0; p.style.opacity = card ? a : 0;
  t.textContent = cta ?? ''; t.style.opacity = cta ? a : 0;
}
