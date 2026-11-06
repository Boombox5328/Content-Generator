// Master timeline: beats in order; shots (camera cuts) come from each beat.
import { THREE } from './common.js';
import { beat as b01 } from './beat01_hook.js';
import { beat as b02 } from './beat02_before_today.js';
import { beat as b03 } from './beat03_flair.js';
import { beat as b04 } from './beat04_grind.js';
import { beat as b05 } from './beat05_breakout.js';
import { beat as b06 } from './beat06_misadventures.js';
import { beat as b07 } from './beat07_silence.js';
import { beat as b08 } from './beat08_jaws.js';
import { beat as b09 } from './beat09_sofarsofake.js';
import { beat as b10 } from './beat10_homecoming.js';
import { setYear, setCard } from './hud.js';
import { render, mixPal, PAL } from './world.js';

export const FPS = 30, DURATION = 75;
export const BEATS = [b01, b02, b03, b04, b05, b06, b07, b08, b09, b10];

export function initBeats(world) { BEATS.forEach((b) => b.build && b.build(world)); }

function counterAt(t) {
  const k = BEATS.flatMap((b) => b.counter || []).sort((a, b) => a[0] - b[0]);
  if (t <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) if (t <= k[i][0]) { const [t0, y0] = k[i - 1], [t1, y1] = k[i]; return y0 + ((y1 - y0) * (t - t0)) / (t1 - t0); }
  return k[k.length - 1][1];
}
export function beatsTxt() {
  const L = ['# cut / beat-marker list (seconds)  — every line is a hard cut (new shot) in the silent MP4', '# time  beat  shot'];
  BEATS.forEach((b) => b.shots.forEach((s, i) => L.push(`${s.t0.toFixed(2)}  ${b.id}${i === 0 ? '  [BEAT START]' : ''}  shot ${i + 1}`)));
  L.push(`${DURATION.toFixed(2)}  END`); return L.join('\n');
}

export function renderFrame(world, t) {
  const beat = BEATS.find((b) => t >= b.start && t < b.end) || BEATS[BEATS.length - 1];
  BEATS.forEach((b) => { if (b.group) b.group.visible = b === beat; });
  world.hometownA.visible = beat.hometown === 'A'; world.hometownB.visible = beat.hometown === 'B';
  const shot = beat.shots.find((s) => t >= s.t0 && t < s.t1) || beat.shots[beat.shots.length - 1];
  const u = Math.min(1, Math.max(0, (t - shot.t0) / (shot.t1 - shot.t0)));
  beat.update(t, world);
  world.focus.copy(beat.focus);
  world.applyPalette(beat.palette((t - beat.start) / (beat.end - beat.start)));
  const c = shot.cam(u, t);
  world.camera.position.copy(c.pos); world.camera.lookAt(c.look); if (c.roll) world.camera.rotateZ(c.roll);
  const fov = c.fov || 55; if (world.camera.fov !== fov) { world.camera.fov = fov; world.camera.updateProjectionMatrix(); }
  setYear(counterAt(t), beat.accent); setCard(BEATS.flatMap((b) => b.cards).find((x) => t >= x.t0 && t <= x.t1), t);
  render(world);
}
