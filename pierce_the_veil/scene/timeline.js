// Master timeline. Add each new beat module to BEATS in order; cards/counter keyframes are merged here.
import { beat as b01 } from './beat01_hook.js';
import { setYear, setCard } from './hud.js';
import { render } from './world.js';

export const FPS = 30, DURATION = 75;
export const BEATS = [b01];          // beats 2–10 are added as they are built

function counterAt(t) {
  const k = BEATS.flatMap((b) => b.counter || []).sort((a, b) => a[0] - b[0]);
  if (t <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) if (t <= k[i][0]) {
    const [t0, y0] = k[i - 1], [t1, y1] = k[i]; return y0 + ((y1 - y0) * (t - t0)) / (t1 - t0);
  }
  return k[k.length - 1][1];
}

export function renderFrame(world, t) {
  const beat = BEATS.find((b) => t >= b.start && t < b.end) || BEATS[BEATS.length - 1];
  beat.update(t, world);
  setYear(counterAt(t), beat.accent);
  setCard(BEATS.flatMap((b) => b.cards).find((c) => t >= c.t0 && t <= c.t1), t);
  render(world);
}
