import * as THREE from 'three';
import { rng } from './lowpoly.js';
// gradient sky dome + stars + optional moon/sun disc. Follows the camera (call follow(cam)).
export function makeSky({ top = 0x0a0f2a, mid = 0x2a2a5a, horizon = 0x6a4a6a, below = 0x151218, stars = 0, sun = null, radius = 900 } = {}) {
  const g = new THREE.Group();
  const mat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, toneMapped: false,
    uniforms: { top: { value: new THREE.Color(top) }, mid: { value: new THREE.Color(mid) }, hor: { value: new THREE.Color(horizon) }, low: { value: new THREE.Color(below) } },
    vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'uniform vec3 top,mid,hor,low; varying vec3 d; void main(){ float h = d.y; vec3 c = h>0. ? mix(hor, mix(mid, top, smoothstep(.2,.85,h)), smoothstep(0.,.32,h)) : mix(hor, low, smoothstep(0.,.25,-h)); gl_FragColor = vec4(c,1.); }' });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 20), mat); dome.renderOrder = -10; g.add(dome);
  if (stars) { const R = rng(9), v = []; for (let i = 0; i < stars; i++) { const a = R() * 6.283, e = 0.08 + R() * 1.4; v.push(Math.cos(a) * Math.cos(e) * radius * 0.98, Math.sin(e) * radius * 0.98, Math.sin(a) * Math.cos(e) * radius * 0.98); }
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    g.add(new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xdfe8ff, size: 2.2, sizeAttenuation: false, fog: false, toneMapped: false, transparent: true, opacity: 0.8 }))); }
  let disc = null;
  if (sun) { disc = new THREE.Mesh(new THREE.CircleGeometry(sun.size ?? 26, 24), new THREE.MeshBasicMaterial({ color: new THREE.Color(sun.color ?? 0xffe0b0).multiplyScalar(sun.power ?? 4), fog: false, toneMapped: false, depthWrite: false }));
    disc.position.set(...sun.dir).setLength(radius * 0.9); disc.lookAt(0, 0, 0); g.add(disc); g.userData.disc = disc; }
  g.userData.follow = (cam) => g.position.copy(cam.position);
  return g;
}
