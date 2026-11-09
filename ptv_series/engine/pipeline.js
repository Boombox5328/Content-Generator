// Render pipeline: ACES tone mapping, sRGB, PCFSoft shadows, gradient-sky IBL, N8AO, selective bloom, DOF, grade/grain/vignette.
import * as THREE from 'three';
import { EffectComposer, RenderPass, EffectPass, SelectiveBloomEffect, DepthOfFieldEffect, VignetteEffect, ToneMappingEffect, ToneMappingMode, BlendFunction } from 'postprocessing';
import { N8AOPostPass } from 'n8ao';
import { GradeEffect, GRADES } from './effects.js';

export const W = 1080, H = 1920;

export function createPipeline(canvas, pixelRatio = 2) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: true, stencil: false });
  renderer.setPixelRatio(pixelRatio); renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.NoToneMapping;   // ACES is applied in the effect chain (ToneMappingEffect)
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(36, W / H, 0.05, 2000);
  const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType });
  const pw = W * pixelRatio, ph = H * pixelRatio;
  const ao = new N8AOPostPass(scene, camera, pw, ph);
  if (!new URLSearchParams(location.search).get('aodef')) Object.assign(ao.configuration, { aoRadius: 1.6, distanceFalloff: 1.0, intensity: 3.2, aoSamples: 16, denoiseSamples: 8, denoiseRadius: 10, halfRes: true, gammaCorrection: false });
  composer.addPass(new RenderPass(scene, camera)); composer.addPass(ao);
  const bloom = new SelectiveBloomEffect(scene, camera, { mipmapBlur: true, intensity: 1.6, radius: 0.72, luminanceThreshold: 0.0, luminanceSmoothing: 0.2 });
  bloom.inverted = false; composer.addPass(new EffectPass(camera, bloom));
  const dof = new DepthOfFieldEffect(camera, { worldFocusDistance: 6, worldFocusRange: 2.5, bokehScale: 0, resolutionScale: 0.5 });
  const dofPass = new EffectPass(camera, dof); composer.addPass(dofPass);
  const grade = new GradeEffect(), tone = new ToneMappingEffect({ mode: ToneMappingMode.ACES_FILMIC }), vig = new VignetteEffect({ offset: 0.28, darkness: 0.6 });
  composer.addPass(new EffectPass(camera, grade, tone, vig));
  composer.setSize(W, H, false);

  const api = { dofPass, renderer, scene, camera, composer, ao, bloom, dof, grade, glow: [] };
  api.setGlow = (objs) => { api.glow = objs; bloom.selection.set(objs); };
  api.setLook = ({ grade: g = 'amber', bloomI = 1.6, dofScale = 0, focus = 6, focusRange = 2.5, ao: a = {} }) => {
    grade.set(GRADES[g] || g); bloom.intensity = bloomI; dofPass.enabled = dofScale > 0; dof.bokehScale = Math.max(0.01, dofScale * pixelRatio); dof.circleOfConfusionMaterial.worldFocusDistance = focus; dof.circleOfConfusionMaterial.worldFocusRange = focusRange;
    Object.assign(ao.configuration, { aoRadius: 1.6, intensity: 3.2, ...a });
  };
  api.render = (frame, t, fade = 0) => { grade.setFrame(frame, t, fade); composer.render(1 / 30); };
  return api;
}

// ---- gradient-sky environment (IBL): surfaces pick up the sky colour ----
export function makeEnvironment(renderer, { top = 0x1a2040, mid = 0x5a4a7a, horizon = 0xffa070, ground = 0x201820, sun = null }) {
  const s = new THREE.Scene();
  const mat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
    uniforms: { top: { value: new THREE.Color(top) }, mid: { value: new THREE.Color(mid) }, hor: { value: new THREE.Color(horizon) }, gnd: { value: new THREE.Color(ground) } },
    vertexShader: 'varying vec3 d; void main(){ d = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'uniform vec3 top,mid,hor,gnd; varying vec3 d; void main(){ float h=d.y; vec3 c = h>0. ? mix(hor, mix(mid, top, smoothstep(.25,.9,h)), smoothstep(0.,.45,h)) : mix(hor, gnd, smoothstep(0.,.35,-h)); gl_FragColor=vec4(c,1.); }' });
  s.add(new THREE.Mesh(new THREE.SphereGeometry(50, 24, 16), mat));
  if (sun) { const m = new THREE.Mesh(new THREE.SphereGeometry(sun.size || 5, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(sun.color).multiplyScalar(sun.power || 6) })); m.position.set(...sun.dir).setLength(45); s.add(m); }
  const pm = new THREE.PMREMGenerator(renderer); const rt = pm.fromScene(s, 0.02); pm.dispose(); mat.dispose();
  return rt.texture;
}
// ---- three-light rig: warm KEY (4096 shadow), cool RIM from behind, dim FILL ----
export function makeRig({ key = {}, rim = {}, fill = {}, target = new THREE.Vector3() }) {
  const g = new THREE.Group();
  const k = key.type === 'spot' ? new THREE.SpotLight(key.color ?? 0xffc890, key.intensity ?? 400, 0, key.angle ?? 0.6, 0.85, 2) : new THREE.DirectionalLight(key.color ?? 0xffc890, key.intensity ?? 3);
  k.position.set(...(key.pos ?? [4, 6, 5])); k.target.position.copy(target); k.castShadow = true; k.shadow.mapSize.set(4096, 4096);
  if (key.type !== 'spot') { const s = key.extent ?? 8; Object.assign(k.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 0.5, far: key.far ?? 80 }); }
  else { k.shadow.camera.near = 0.5; k.shadow.camera.far = key.far ?? 60; }
  k.shadow.bias = key.bias ?? -0.0003; k.shadow.normalBias = key.normalBias ?? 0.03; k.shadow.radius = 3;
  const r = new THREE.DirectionalLight(rim.color ?? 0x7fa8ff, rim.intensity ?? 2.4); r.position.set(...(rim.pos ?? [-3, 4, -6])); r.target.position.copy(target);
  const f = new THREE.HemisphereLight(fill.sky ?? 0x6070a0, fill.ground ?? 0x201818, fill.intensity ?? 0.35);
  g.add(k, k.target, r, r.target, f); g.userData = { key: k, rim: r, fill: f }; return g;
}
