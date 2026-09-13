// Why/ocean section: own three.js water + the ship dolly, cloud reveal and list choreography
// (ported from the original's values; resting states live in CSS, animations added here).
import * as THREE from '../vendor/three.module.min.js';

// cubic-bezier easing helper (mirrors the live's cinematicSilk / cinematicSmooth eases)
function bezierEase(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sampleX = t => ((ax * t + bx) * t + cx) * t;
  const sampleY = t => ((ay * t + by) * t + cy) * t;
  const solve = x => {
    let t = x;
    for (let i = 0; i < 8; i++) {
      const d = sampleX(t) - x;
      if (Math.abs(d) < 1e-4) break;
      const dd = (3 * ax * t + 2 * bx) * t + cx;
      if (Math.abs(dd) < 1e-6) break;
      t -= d / dd;
    }
    return t;
  };
  return x => sampleY(solve(x));
}
const silk = bezierEase(.45, .05, .55, .95);
const csmooth = bezierEase(.25, .1, .25, 1);

const VERT = `
varying vec3 vWorld;
varying vec2 vUv;
void main() {
  vUv = uv;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorld = wp.xyz;
  gl_Position = projectionMatrix * viewMatrix * wp;
}`;

const FRAG = `
precision highp float;
varying vec3 vWorld;
varying vec2 vUv;
uniform sampler2D uNormal;
uniform sampler2D uEnv;
uniform sampler2D uOverlay;
uniform float uTime;
uniform float uPattern;
uniform float uWake;
uniform float uOverlayScale;
uniform vec2 uResolution;
uniform vec2 uShipUv;
uniform float uShipScale;
uniform float uShipTop;
uniform float uShipHalfW;
uniform float uShipHalfLen;
uniform vec3 uSun;

vec3 sampleN(vec2 uv, vec2 drift, float s) {
  vec3 n = texture2D(uNormal, uv * s + drift).rgb;
  return n * 2.0 - 1.0;
}
float lum(vec3 c) { return dot(c, vec3(.3, .59, .11)); }
vec3 clipColor(vec3 c) {
  float l = lum(c);
  float n = min(min(c.r, c.g), c.b);
  float x = max(max(c.r, c.g), c.b);
  if (n < 0.0) c = l + (c - l) * l / (l - n);
  if (x > 1.0) c = l + (c - l) * (1.0 - l) / (x - l);
  return c;
}
vec3 setLum(vec3 c, float l) { return clipColor(c + (l - lum(c))); }
float sat(vec3 c) { return max(max(c.r, c.g), c.b) - min(min(c.r, c.g), c.b); }
vec3 setSat(vec3 c, float s) {
  float mn = min(min(c.r, c.g), c.b);
  float mx = max(max(c.r, c.g), c.b);
  if (mx > mn) return (c - mn) / (mx - mn) * s;
  return vec3(0.0);
}
vec3 satBlend(vec3 base, vec3 top) {
  return setLum(setSat(base, sat(top) * 1.0), lum(base));
}

void main() {
  float t = uTime;
  vec3 n1 = sampleN(vUv, vec2(t * .0065, t * .0085), 14.0 * uPattern);
  vec3 n2 = sampleN(vUv, vec2(-t * .011, t * .0040), 24.0 * uPattern);
  vec3 n3 = sampleN(vUv, vec2(t * .002, -t * .0030), 40.0 * uPattern);
  vec3 n = normalize(vec3(n1.xy * .5 + n2.xy * .3 + n3.xy * .12, 1.0));

  vec3 V = vec3(0., 1., 0.);
  float fres = pow(1.0 - max(dot(n, V), 0.0), 3.0);
  vec3 R = reflect(vec3(0., -1., 0.), n);
  vec2 euv = vec2(atan(R.z, R.x) / 6.28318 + .5, acos(clamp(R.y, -1.0, 1.0)) / 3.14159);
  vec3 env = texture2D(uEnv, euv).rgb;

  // screen-space uv (wake anchoring + view-angle gradient)
  vec2 suv = vec2(gl_FragCoord.x / uResolution.x, gl_FragCoord.y / uResolution.y);

  vec3 deep = vec3(0.0, 0.086, 0.245);
  vec3 col = deep + vec3(.003, .022, .042) * (n1.x + n1.y + n2.x * .5);
  col += env * vec3(.30, .85, 1.0) * 0.5 * (0.03 + 0.13 * fres);
  float spec = pow(max(dot(reflect(-uSun, n), V), 0.0), 90.0);
  col += vec3(1.0, .98, .92) * spec * .65;

  // view-angle gradient: grazing (top) reads brighter, near (bottom) deeper
  // (live's per-pixel fresnel; our V is constant, so fake the vertical term)
  float vshade = clamp((suv.y - 0.5) * 2.0, -1.0, 1.0);
  col *= 1.0 + 0.10 * vshade;

  // the sea settles and darkens as the dolly pulls the camera back (live's late-phase look)
  col *= 1.0 - 0.16 * smoothstep(0.45, 0.10, uShipScale);

  // ---- wakes (screen space, anchored to the ship's DOM box; stern at the TOP of the box) ----
  float dx = abs(suv.x - uShipUv.x);
  float sc = uShipScale;
  float foam = 0.0;
  if (sc > 0.02 && uWake > 0.01) {
    float halfW = max(uShipHalfW, 0.008);           // ship half width, uv units
    float halfL = max(uShipHalfLen, 0.02);
    float sternY = uShipTop;                        // stern edge (top of the ship box)
    float bowY = sternY - 2.0 * halfL;              // bow edge (bottom of the ship box)

    // breakup fields (churn + speckle) shared by all foam: keeps everything streaky, never a solid band
    vec2 spuv = suv * vec2(96.0, 70.0);
    vec2 warp1 = texture2D(uNormal, spuv * .31 + vec2(t * .02)).xy * 2.0 - 1.0;
    vec2 warp2 = texture2D(uNormal, spuv * .73 - vec2(t * .03, t * .02)).zx * 2.0 - 1.0;
    float sp = texture2D(uNormal, spuv + warp1 * 2.4 + warp2 * 1.2 + vec2(t * .05, -t * .04)).b;
    float sp2 = texture2D(uNormal, spuv * 1.9 + warp2 * 2.0).b;
    float speckle = mix(.10, 1.45, smoothstep(.45, .72, sp * .65 + sp2 * .35));
    float churn = .55 + .45 * (sin(t * 2.2 + dx * 520.0 + suv.y * 380.0) * sin(t * 1.7 - suv.y * 210.0 + dx * 330.0) * .5 + .5);
    float breakup = speckle * churn;
    float scGate = smoothstep(0.008, 0.05, halfW); // foam fades out as the ship shrinks

    // 1) bow wave: foam flaring outward + down from the bow (bottom end)
    float dyB = bowY - suv.y;
    if (dyB > -0.01 && dyB < halfL * 1.4 + 0.14) {
      float arm = halfW + dyB * 0.5;
      float armLine = exp(-pow((dx - arm) / (0.007 + 0.05 * dyB + halfW * 0.10), 2.0));
      float wash = smoothstep(arm, halfW * 0.15, dx) * 0.5;
      float fade = exp(-max(dyB, 0.0) / (0.45 * halfL + 0.09));
      foam += (armLine * 0.95 + wash) * fade * breakup;
    }

    // 2) hull side foam: narrow broken streaks hugging the hull edges, fading toward the bow
    float dyIn = sternY - suv.y;
    if (dyIn > -0.02 && dyIn < 2.0 * halfL + 0.05) {
      float edgeD = abs(dx - halfW * 1.02);
      float w0 = max(0.0035, halfW * 0.075);
      float side = exp(-pow(edgeD / w0, 2.0));
      float fade = exp(-max(dyIn, 0.0) / (0.95 * halfL));
      foam += side * fade * (0.12 + 0.60 * breakup);
    }

    // 3) faint stern trail, above the stern (trailing wake)
    float dyA = suv.y - sternY;
    if (dyA > -0.01 && dyA < 0.9 * halfL + 0.1) {
      float trail = exp(-pow(dx / (halfW * 0.45), 2.0));
      float fade = exp(-max(dyA, 0.0) / (0.30 * halfL + 0.06));
      foam += trail * fade * 0.15 * breakup;
    }

    // 4) broad churned-water wash: wide soft bright field spreading laterally
    //    from the hull (live's appearance: streaks near the hull, soft wash far out)
    {
      float wmidY = sternY - halfL;                   // mid-hull, uv
      float ex = dx / 0.17;
      float ey = (suv.y - wmidY) / 0.34;
      float wr = sqrt(ex * ex + ey * ey);
      float soft = .45 + .85 * smoothstep(.30, .80, sp2 * .6 + sp * .4);
      float wash = exp(-wr * 1.35) * soft;
      float wrGate = smoothstep(0.004, 0.02, halfW);
      float washTaper = smoothstep(0.04, 0.12, halfW);   // field calms as the ship shrinks
      col += vec3(.055, .105, .21) * min(wash * wrGate * washTaper, 1.2);
    }

    foam *= scGate;
  }
  col = mix(col, vec3(.94, .97, 1.0), clamp(foam * 1.45, 0.0, .88));

  // ---- photo overlay composite (saturation blend of the brightened overlay) ----
  vec2 ouv = (suv - .5) / max(uOverlayScale, .2) + .5;
  vec3 ov = texture2D(uOverlay, clamp(ouv, 0.0, 1.0)).rgb;
  ov = clamp(ov * 1.8, 0.0, 1.0);
  ov = clamp(mix(vec3(lum(ov)), ov, 1.2), 0.0, 1.0);
  // large-scale luminance mottling from a second, offset overlay sample
  vec3 ov2 = texture2D(uOverlay, clamp((suv - .5) / max(uOverlayScale * 1.6, .2) + .53, 0.0, 1.0)).rgb;
  col *= .88 + .22 * clamp(lum(ov2) * 1.5, 0.0, 1.0);
  col = satBlend(col, ov);

  // radial blue glows (subtle)
  vec2 g1 = suv - vec2(.5, .55);
  col += vec3(.0, .45, 1.0) * .06 * exp(-dot(g1, g1) * 3.2);
  vec2 g2 = suv - vec2(.22, .3);
  col += vec3(.0, .45, 1.0) * .035 * exp(-dot(g2, g2) * 6.0);

  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

export function initWhy() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-why-wrap');
  if (!wrap) return;
  const canvas = document.getElementById('oceanCanvas');
  const shipWrap = wrap.querySelector('.home-why-ship');
  const shipImg = wrap.querySelector('.home-why-ship-img');
  if (!canvas || !shipImg) return;

  // ---------- ocean scene ----------
  const W = 1440, H = 900;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(W, H, false);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, W / H, .1, 400);
  camera.up.set(0, 0, -1);
  camera.position.set(0, 10, 0);
  camera.lookAt(0, 0, 0);

  const loader = new THREE.TextureLoader();
  const texN = loader.load('assets/img/water-normal.webp');
  texN.wrapS = texN.wrapT = THREE.RepeatWrapping;
  texN.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const texE = loader.load('assets/img/ocean-envmap.webp');
  const texO = loader.load('assets/img/ocean-overlay.webp');
  texE.colorSpace = THREE.NoColorSpace;
  texO.colorSpace = THREE.NoColorSpace;
  texO.anisotropy = renderer.capabilities.getMaxAnisotropy();

  const uniforms = {
    uNormal: { value: texN }, uEnv: { value: texE }, uOverlay: { value: texO },
    uTime: { value: 0 }, uPattern: { value: 1 }, uWake: { value: .4 },
    uOverlayScale: { value: .62 }, uResolution: { value: new THREE.Vector2(W, H) },
    uShipUv: { value: new THREE.Vector2(.5, .5) }, uShipScale: { value: 1 },
    uShipTop: { value: .75 }, uShipHalfW: { value: .05 }, uShipHalfLen: { value: .3 },
    uSun: { value: new THREE.Vector3(-.3, .8, -.4).normalize() }
  };
  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry(90, 90, 1, 1),
    new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms })
  );
  plane.rotation.x = -Math.PI / 2;
  scene.add(plane);

  gsap.ticker.add(() => {
    const wr = wrap.getBoundingClientRect();
    if (wr.bottom < -100 || wr.top > innerHeight + 100) return;   // off-screen: skip
    uniforms.uTime.value += gsap.ticker.deltaRatio(60) / 60;
    if (shipImg) {
      const r = shipImg.getBoundingClientRect();
      if (r.width > 1) {
        uniforms.uShipUv.value.set((r.left + r.width / 2) / innerWidth, 1 - (r.top + r.height / 2) / innerHeight);
        uniforms.uShipTop.value = 1 - r.top / innerHeight;            // stern edge (top of box)
        uniforms.uShipHalfW.value = (r.width / 2) / innerWidth;
        uniforms.uShipHalfLen.value = (r.height / 2) / innerHeight;
      }
    }
    uniforms.uShipScale.value = Math.max(st.shipScale * wrapScale, .001);
    renderer.render(scene, camera);
  });

  // ---------- ship dolly (scrub 15960 -> 20822, as live) ----------
  const st = { shipScale: 1 };
  const d = { scale: 1, fov: 35, overlayScale: .62 };
  const applyCam = () => {
    const e = d.scale * st.shipScale;
    camera.fov = d.fov;
    camera.updateProjectionMatrix();
    uniforms.uShipScale.value = Math.max(st.shipScale, .001);
    uniforms.uOverlayScale.value = d.overlayScale;
    const zoom = 8 / Math.max(e, .01);
    // feature scale grows gently as the camera pulls back
    uniforms.uPattern.value = 1 + .9 * (Math.log(zoom / 8) / Math.log(97.6 / 8));
  };
  // ship dolly window: fitted to the live's curve, expressed viewport-relative (recomputed on refresh)
  const wrapTop = () => wrap.getBoundingClientRect().top + scrollY;
  const tlShip = gsap.timeline({
    scrollTrigger: {
      trigger: wrap, scrub: true,
      start: () => wrapTop() + innerHeight * 0.267,
      end: () => wrapTop() + innerHeight * 5.267
    }
  });
  tlShip.fromTo(shipImg, { scale: 1 }, { scale: .082, ease: silk, duration: 1.05 }, 0)
    .to(st, { shipScale: .082, ease: silk, duration: 1.05, onUpdate: applyCam }, 0)
    .to(d, { scale: .082, fov: 50, overlayScale: 1, ease: silk, duration: 1.05, onUpdate: applyCam }, 0);

  // ---------- ship bob (infinite yoyo) ----------
  const inners = wrap.querySelectorAll('.home-why-ship-img-inner');
  if (inners.length) {
    const base = inners[0];
    const t = { xPercent: 0, yPercent: 0, wakeForce: 0 };
    const fn = () => {
      const px = (base.offsetWidth || 1) * t.xPercent / 100;
      const py = (base.offsetHeight || 1) * t.yPercent / 100;
      inners.forEach(el => gsap.set(el, {
        xPercent: px / (el.offsetWidth || 1) * 100,
        yPercent: py / (el.offsetHeight || 1) * 100,
        force3D: true
      }));
      uniforms.uWake.value = .4 + .045 * t.wakeForce;
    };
    gsap.timeline({ repeat: -1, yoyo: true, defaults: { ease: 'sine.inOut' } })
      .to(t, { xPercent: .6, yPercent: -1.2, wakeForce: 0, duration: 2.4, onUpdate: fn })
      .to(t, { xPercent: -.45, yPercent: 2, wakeForce: .6, duration: 2.7, onUpdate: fn });
  }

  // ---------- cloud decor + overlap fly-in (scrub) ----------
  const q1 = sel => wrap.querySelector(sel);
  let wrapScale = 1;   // tracked from the ship wrapper; wake scaling combines it with st.shipScale
  gsap.set(q1('.home-why-cloud-overlap-bg'), { autoAlpha: 0 });
  gsap.set(q1('.home-why-cloud-overlap'), { autoAlpha: 0 });
  wrap.querySelectorAll('.home-why-cloud-overlap-item').forEach(el => gsap.set(el, { opacity: 0 }));
  gsap.set(q1('.home-why-cloud-overlap-item.cloud-1'), { scale: 8 });
  ['.cloud-2', '.cloud-3', '.cloud-5', '.cloud-7'].forEach(c =>
    gsap.set(q1('.home-why-cloud-overlap-item' + c), { scale: 5 }));
  gsap.set(q1('.home-why-cloud-overlap-item.cloud-4'), { scale: 2 });
  gsap.set(q1('.home-why-cloud-overlap-item.cloud-6'), { scale: 4 });
  gsap.set(q1('.home-why-cloud-decor-item.cloud-1'), { x: '-50vw', y: 0, scale: .8, opacity: .3, filter: 'blur(2px)' });
  gsap.set(q1('.home-why-cloud-decor-item.cloud-2'), { x: '100vw', y: 150, scale: .8, opacity: 1, filter: 'blur(2px)' });
  gsap.set(q1('.home-why-cloud-decor-item.cloud-3'), { opacity: 0, x: '-5vw', scale: .7, filter: 'blur(2px)' });

  const secEl = wrap.querySelector('.home-why');
  const sectionBottom200 = () => secEl.getBoundingClientRect().bottom + scrollY;   // absolute bottom
  const holdTail = { v: 0 };
  const tlCloud = gsap.timeline({
    scrollTrigger: {
      trigger: wrap.querySelector('.home-why-stick'),
      start: () => wrapTop() + innerHeight * 4,        // stick top + 400vh, dynamic
      end: () => sectionBottom200() + innerHeight,
      scrub: true
    }
  });
  // Positions are absolute (timeline seconds) calibrated against the live at 1440x900:
  // left mist fades out ~19150-19600 (t 3.2), cloud sheet ramps 19350-20150 (t 4.2-8.9),
  // items follow c2 -> c7 -> c1 -> c3 -> c5 -> c4 -> c6 each stretched ~4-5s.
  tlCloud.to(q1('.home-why-cloud-decor-item.cloud-3'), { x: 0, scale: 1, opacity: .3, filter: 'blur(0px)', ease: silk, duration: 2.4 }, 0)
    .to(q1('.home-why-cloud-decor-item.cloud-1'), { x: '20vw', y: 30, scale: .6, opacity: 0, ease: silk, duration: 2.4 }, 0)
    .to(q1('.home-why-cloud-decor-item.cloud-2'), { x: '50vw', y: 120, scale: .6, opacity: 0, ease: silk, duration: 2.4 }, 0)
    .to(q1('.home-why-cloud-decor-item.cloud-3'), { x: '-5vw', scale: 2, opacity: 0, filter: 'blur(2px)', ease: silk, duration: 2.6 }, 3.2)
    .to(q1('.home-why-main'), { autoAlpha: .9, ease: silk, duration: 2.4 }, 6.2)
    .to(shipWrap, { scale: .9, duration: 2.8, ease: silk, onUpdate: () => { wrapScale = gsap.getProperty(shipWrap, 'scaleY') || 1; } }, 6.3)
    .to(q1('.home-why-cloud-overlap-bg'), { autoAlpha: 1, ease: csmooth, duration: 5.0 }, 5.6)
    .to(q1('.home-why-cloud-overlap'), { autoAlpha: 1, ease: csmooth, duration: 5.0 }, 5.6)
    .to(q1('.home-why-cloud-overlap-item.cloud-2'), { scale: 1, opacity: 1, ease: csmooth, duration: 5.2 }, 5.9)
    .to(q1('.home-why-cloud-overlap-item.cloud-7'), { scale: 1, opacity: 1, ease: csmooth, duration: 4.2 }, 7.1)
    .to(q1('.home-why-cloud-overlap-item.cloud-1'), { scale: 1, opacity: 1, ease: csmooth, duration: 5.0 }, 7.5)
    .to(q1('.home-why-cloud-overlap-item.cloud-3'), { scale: 1, opacity: 1, ease: csmooth, duration: 4.6 }, 8.25)
    .to(q1('.home-why-cloud-overlap-item.cloud-5'), { scale: 1, opacity: 1, ease: csmooth, duration: 4.4 }, 9.4)
    .to(q1('.home-why-cloud-overlap-item.cloud-4'), { scale: 1, opacity: 1, ease: csmooth, duration: 4.2 }, 10.1)
    .to(q1('.home-why-cloud-overlap-item.cloud-6'), { scale: 1, opacity: 1, ease: csmooth, duration: 4.0 }, 10.7)
    .to(holdTail, { v: 1, duration: 9.1 }, 14.9);   // padding so the reveal pacing lands right

  // ---------- text wrap reveal ----------
  const textWrap = q1('.home-why-text-wrap');
  if (textWrap) {
    gsap.set(textWrap, { scale: .9, filter: 'blur(2px)', autoAlpha: .7 });
    gsap.to(textWrap, {
      scale: 1, filter: 'blur(0px)', autoAlpha: 1, ease: 'none', duration: 1,
      scrollTrigger: { trigger: textWrap, start: 'top bottom', end: 'top center', scrub: 1 }
    });
  }

  // ---------- main list items reveal ----------
  const items = wrap.querySelectorAll('.home-why-main-item');
  items.forEach((item, r) => {
    const s = r % 2 === 0;
    const last = r === items.length - 1;
    const tl = gsap.timeline({
      scrollTrigger: { trigger: item, start: 'top bottom', end: 'top center-=20%', scrub: true }
    });
    tl.fromTo(item.querySelector('.home-why-main-item-ic'), { x: last ? 0 : (s ? -100 : 100), y: 100 }, { x: 0, y: 0, ease: csmooth, duration: 1 }, 0)
      .fromTo(item.querySelector('.home-why-main-item-title'), { x: last ? 0 : (s ? -150 : 150), y: 150 }, { x: 0, y: 0, ease: csmooth, duration: 1 }, 0)
      .fromTo(item.querySelector('.home-why-main-item-desc'), { x: last ? 0 : (s ? -200 : 200), y: 200 }, { x: 0, y: 0, ease: csmooth, duration: 1 }, 0);
  });

  applyCam();
}
