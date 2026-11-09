// Volumetric-looking light shafts: additive cone with axial fade, soft edges and slow noise. Deterministic via uniform time.
import * as THREE from 'three';
const vs = 'varying vec3 vN; varying vec3 vV; varying float vA; varying vec2 vUv; void main(){ vUv=uv; vA = uv.y; vec4 mv = modelViewMatrix*vec4(position,1.); vV = normalize(-mv.xyz); vN = normalize(normalMatrix*normal); gl_Position = projectionMatrix*mv; }';
const fs = 'uniform vec3 color; uniform float intensity; uniform float t; uniform float near; varying vec3 vN; varying vec3 vV; varying float vA; varying vec2 vUv; float h(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }\n void main(){ float edge = pow(abs(dot(normalize(vN), normalize(vV))), 1.6); float ax = smoothstep(0.0,0.12,vA) * pow(1.0 - vA, near); float n = 0.78 + 0.22*sin(vUv.x*40.0 + t*0.6 + vA*9.0); gl_FragColor = vec4(color * intensity * edge * ax * n, 1.0); }';
export function makeShaft(from, to, { r0 = 0.05, r1 = 1.2, color = 0xffd9a0, intensity = 0.6, falloff = 1.4 } = {}) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), len = a.distanceTo(b);
  const g = new THREE.CylinderGeometry(r1, r0, len, 20, 1, true); g.translate(0, -len / 2 + len / 2 * 0, 0);
  const m = new THREE.Mesh(g, new THREE.ShaderMaterial({ vertexShader: vs, fragmentShader: fs, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false, toneMapped: false,
    uniforms: { color: { value: new THREE.Color(color) }, intensity: { value: intensity }, t: { value: 0 }, near: { value: falloff } } }));
  m.position.copy(a).add(b).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize()); // +y axis runs from `from` (narrow end r0) to `to` (wide end r1)
  m.userData.setT = (t) => (m.material.uniforms.t.value = t); m.renderOrder = 5; m.frustumCulled = false; return m;
}
