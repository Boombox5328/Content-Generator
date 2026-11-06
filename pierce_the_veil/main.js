import { createWorld } from './scene/world.js';
import { renderFrame, FPS, DURATION } from './scene/timeline.js';
const world = createWorld(document.getElementById('c'));
window.renderFrame = (t) => renderFrame(world, t);
window.ptv = { FPS, DURATION };
window.ptvReady = true;
