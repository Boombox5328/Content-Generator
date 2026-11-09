// Scene manager: one THREE.Scene, one camera, several "sets" toggled per shot. Applies env/fog/look per set.
import * as THREE from 'three';
import { makeEnvironment } from './pipeline.js';

export class Director {
  constructor(pipe) { this.p = pipe; this.sets = {}; this.envCache = {}; this.current = null; }
  register(set) { this.sets[set.id] = set; set.group.visible = false; this.p.scene.add(set.group); return set; }
  use(id) {
    const set = this.sets[id]; if (!set) throw new Error('no set ' + id);
    for (const k in this.sets) this.sets[k].group.visible = k === id;
    const sc = this.p.scene;
    if (!this.envCache[id]) this.envCache[id] = makeEnvironment(this.p.renderer, set.env);
    sc.environment = this.envCache[id];
    sc.fog = new THREE.FogExp2(set.fog.color, set.fog.density);
    sc.background = new THREE.Color(set.fog.color);
    this.p.setGlow(set.glow || []); this.p.setLook(set.look || {});
    this.current = set; return set;
  }
  camera(c) { const cam = this.p.camera; cam.position.copy(c.pos); cam.fov = c.fov ?? 36; cam.near = c.near ?? 0.05; cam.far = c.far ?? 2000; cam.updateProjectionMatrix(); cam.lookAt(c.look); if (c.roll) cam.rotateZ(c.roll); cam.updateMatrixWorld(); }
}
