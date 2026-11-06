import { createWorld } from './scene/world.js';
import { renderFrame, initBeats, beatsTxt, FPS, DURATION } from './scene/timeline.js';
const world = createWorld(document.getElementById('c'));
initBeats(world);
window.renderFrame = (t) => renderFrame(world, t);
window.beatsTxt = beatsTxt; window.ptv = { FPS, DURATION };
window.ptvReady = true;
