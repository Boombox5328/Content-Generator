// Per-era colour grade + film grain + optional heat haze, as one custom postprocessing effect.
import { Effect, BlendFunction } from 'postprocessing';
import * as THREE from 'three';
const frag = /* glsl */ `
uniform vec3 gShadow; uniform vec3 gHigh; uniform float gSat; uniform float gContrast; uniform float gExposure;
uniform float gGrain; uniform float gSeed; uniform float gHaze; uniform float gTime; uniform float gFade;
float h21(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
void mainUv(inout vec2 uv){ uv.x += sin(uv.y*260.0 + gTime*4.0)*0.0011*gHaze*smoothstep(0.0,0.5,uv.y)*(1.0-smoothstep(0.5,0.9,uv.y)); uv.y += sin(uv.x*180.0+gTime*3.0)*0.0006*gHaze; }
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor){
  vec3 c = inputColor.rgb * gExposure;
  float l = dot(c, vec3(0.2126,0.7152,0.0722));
  c = mix(vec3(l), c, gSat);
  c = (c - 0.18) * gContrast + 0.18;
  float w = smoothstep(0.0, 0.9, l);
  c += mix(gShadow, gHigh, w) * 0.18;
  c = max(c, 0.0);
  c += (h21(uv*vec2(1080.0,1920.0) + gSeed) - 0.5) * gGrain * (0.6 + 0.4*(1.0-w));   // film grain
  outputColor = vec4(c * (1.0 - gFade), inputColor.a);
}`;
export class GradeEffect extends Effect {
  constructor() {
    super('GradeEffect', frag, { blendFunction: BlendFunction.NORMAL, uniforms: new Map([
      ['gShadow', new THREE.Uniform(new THREE.Vector3())], ['gHigh', new THREE.Uniform(new THREE.Vector3())],
      ['gSat', new THREE.Uniform(1)], ['gContrast', new THREE.Uniform(1)], ['gExposure', new THREE.Uniform(1)],
      ['gGrain', new THREE.Uniform(0.03)], ['gSeed', new THREE.Uniform(0)], ['gHaze', new THREE.Uniform(0)], ['gTime', new THREE.Uniform(0)], ['gFade', new THREE.Uniform(0)]]) });
  }
  set(g) { const u = this.uniforms; const v = (k, x) => u.get(k).value = x;
    u.get('gShadow').value.set(...g.shadow); u.get('gHigh').value.set(...g.high); v('gSat', g.sat); v('gContrast', g.contrast); v('gExposure', g.exposure ?? 1); v('gHaze', g.haze ?? 0); }
  setFrame(frame, t, fade = 0) { this.uniforms.get('gSeed').value = frame * 0.7131; this.uniforms.get('gTime').value = t; this.uniforms.get('gFade').value = fade; }
}
// shadow/high tints are linear RGB offsets
export const GRADES = {
  amber:   { shadow: [0.10, 0.02, -0.04], high: [0.16, 0.07, -0.05], sat: 1.12, contrast: 1.12, exposure: 1.0 },
  gold:    { shadow: [0.02, 0.05, 0.07],  high: [0.14, 0.09, -0.04], sat: 1.15, contrast: 1.1,  exposure: 1.0, haze: 1 },
  teal:    { shadow: [-0.04, 0.06, 0.10], high: [0.10, 0.04, -0.02], sat: 1.2,  contrast: 1.15, exposure: 1.0 },
  icy:     { shadow: [-0.03, 0.03, 0.10], high: [0.02, 0.06, 0.12],  sat: 1.05, contrast: 1.08, exposure: 1.05 },
  sunset:  { shadow: [0.06, -0.01, 0.06], high: [0.18, 0.08, -0.05], sat: 1.2,  contrast: 1.12, exposure: 1.0 },
  grey:    { shadow: [-0.02, 0.01, 0.05], high: [0.01, 0.03, 0.06],  sat: 0.5,  contrast: 1.05, exposure: 0.95 },
  neon:    { shadow: [-0.04, 0.05, 0.0],  high: [-0.02, 0.14, 0.04], sat: 1.25, contrast: 1.2,  exposure: 1.0 },
  magenta: { shadow: [0.07, -0.02, 0.09], high: [0.16, 0.08, 0.02],  sat: 1.25, contrast: 1.12, exposure: 1.0 },
};
