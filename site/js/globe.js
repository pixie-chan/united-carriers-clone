// Dot globe, reimplementation of the original's three.js globe.
// Land dots rasterized offline (same algorithm), airport pins, status-active flight arcs,
// fresnel rim (amber top / blue bottom) + projected country labels.
import * as THREE from '../vendor/three.module.min.js';

const DEG = Math.PI / 180;

export function llToVec(lat, lon, r = 1) {
  const phi = (90 - lat) * DEG;
  const th = (lon + 180) * DEG;
  return new THREE.Vector3(
    -Math.sin(phi) * Math.cos(th),
    Math.cos(phi),
    Math.sin(phi) * Math.sin(th)
  ).multiplyScalar(r);
}

export async function initGlobe(canvas, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(61, 1, 0.1, 50);
  camera.position.set(0, 0, opts.cameraZ || 2.23);

  const root = new THREE.Group();
  root.rotation.y = 3.8;
  scene.add(root);

  // dark body so back-side dots are hidden
  root.add(new THREE.Mesh(
    new THREE.SphereGeometry(0.992, 64, 64),
    new THREE.MeshBasicMaterial({ color: 0x060606 })
  ));

  // fresnel rim: amber up top, blue at the bottom (signature of the original)
  const rim = new THREE.Mesh(
    new THREE.SphereGeometry(1.02, 64, 64),
    new THREE.ShaderMaterial({
      transparent: true, blending: THREE.AdditiveBlending, side: THREE.BackSide, depthWrite: false,
      uniforms: {
        uTop: { value: new THREE.Color(0xff6a00) },
        uBot: { value: new THREE.Color(0x3560ff) }
      },
      vertexShader: `varying vec3 vN; varying vec3 vP;
        void main() {
          vN = normalize(normalMatrix * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vP = mv.xyz;
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `varying vec3 vN; varying vec3 vP;
        uniform vec3 uTop; uniform vec3 uBot;
        void main() {
          vec3 v = normalize(-vP);
          float f = pow(1.0 - abs(dot(vN, v)), 2.2);
          float g = smoothstep(-0.35, 0.5, vN.y);
          vec3 c = mix(uBot, uTop, g);
          gl_FragColor = vec4(c, f * 0.85);
        }`
    })
  );
  root.add(rim);

  // land dots
  const cloud = await fetch('data/globe-points.json').then(r => r.json());
  const n = cloud.points.length;
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = cloud.points[i][0];
    pos[i * 3 + 1] = cloud.points[i][1];
    pos[i * 3 + 2] = cloud.points[i][2];
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const dots = new THREE.Points(geo, new THREE.PointsMaterial({
    color: 0xffffff, size: 0.0068, sizeAttenuation: true,
    transparent: true, opacity: 1.0, depthWrite: false
  }));
  dots.scale.setScalar(0.996); // keeps the limb dot ring inside the body silhouette (spill fix)
  root.add(dots);

  // flight arcs (only status:true ones draw, like the original's active network)
  const arcs = [];
  try {
    const flights = await fetch('data/FlightsCollection.json').then(r => r.json());
    const group = new THREE.Group();
    root.add(group);
    flights.flights.filter(f => f.status).forEach((f, idx) => {
      const a = llToVec(f.startLat, f.startLng).normalize();
      const b = llToVec(f.endLat, f.endLng).normalize();
      const theta = Math.acos(Math.max(-1, Math.min(1, a.dot(b))));
      const s = Math.max(Math.sin(theta), 1e-5);
      const alt = Math.min(f.arcAlt || 0.3, 0.3);
      const N = 64;
      const pts = [];
      for (let i = 0; i <= N; i++) {
        const t = i / N;
        // true great-circle slerp: keeps the arc hugging the globe (linear lerp + normalize
        // made long flights dive/spike and float off the sphere)
        const v = a.clone().multiplyScalar(Math.sin((1 - t) * theta) / s)
          .add(b.clone().multiplyScalar(Math.sin(t * theta) / s));
        v.normalize().multiplyScalar(1 + Math.sin(Math.PI * t) * alt * 0.22);
        pts.push(v);
      }
      const g = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({ color: 0xff5a00, transparent: true, opacity: 0.25, linewidth: 1 });
      const line = new THREE.Line(g, mat);
      group.add(line);
      arcs.push({ line, offset: idx * 0.17 });
    });
  } catch (e) { /* arcs optional */ }

  // airport pins + country labels
  const labelEls = [];
  try {
    const ap = await fetch('data/AirportsCollection.json').then(r => r.json());
    const pinGeo = new THREE.BufferGeometry();
    const pp = [];
    ap.airports.forEach(a => {
      const lat = parseFloat(a.lat), lon = parseFloat(a.lng);
      if (isNaN(lat) || isNaN(lon)) return;
      const v = llToVec(lat, lon, 1.001);
      pp.push(v.x, v.y, v.z);
    });
    pinGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pp), 3));
    root.add(new THREE.Points(pinGeo, new THREE.PointsMaterial({
      color: 0xffffff, size: 0.009, sizeAttenuation: true, transparent: true, opacity: 0.95
    })));

    const wanted = opts.labelCountries || [];
    if (wanted.length && opts.labelContainer) {
      wanted.forEach(name => {
        const air = ap.airports.find(a => (a.country || '').toUpperCase() === name.toUpperCase());
        if (!air) return;
        const lat = parseFloat(air.lat), lon = parseFloat(air.lng);
        if (isNaN(lat) || isNaN(lon)) return;
        const el = document.createElement('div');
        el.className = 'globe-label';
        el.innerHTML = '<span class="globe-label-dot"></span><span class="globe-label-text">' + name + '</span>';
        el.style.opacity = '0';
        opts.labelContainer.appendChild(el);
        labelEls.push({ el, vec: llToVec(lat, lon, 1.01) });
      });
    }
  } catch (e) { /* pins optional */ }

  const resize = () => {
    const w = canvas.clientWidth || 900;
    const h = canvas.clientHeight || 900;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  resize();
  window.addEventListener('resize', resize);

  const tmp = new THREE.Vector3();
  let t0 = performance.now();

  function update() {
    const t = (performance.now() - t0) / 1000;
    for (const a of arcs) {
      const total = a.line.geometry.attributes.position.count;
      const phase = (t * 0.16 + a.offset) % 1.9;
      const draw = Math.max(0, Math.min(1, phase));
      a.line.geometry.setDrawRange(0, Math.floor(draw * total));
      a.line.material.opacity = 0.08 + 0.5 * Math.min(1, draw * 1.5);
    }
    if (labelEls.length) {
      const w = canvas.clientWidth, h = canvas.clientHeight;
      for (const L of labelEls) {
        tmp.copy(L.vec).applyAxisAngle(new THREE.Vector3(0, 1, 0), root.rotation.y);
        if (tmp.z < 0.08) { L.el.style.opacity = '0'; continue; }
        const p = tmp.clone().project(camera);
        const x = (p.x * 0.5 + 0.5) * w;
        const y = (-p.y * 0.5 + 0.5) * h;
        L.el.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
        L.el.style.opacity = '1';
      }
    }
    renderer.render(scene, camera);
  }
  function setPhi(phi) { root.rotation.y = phi; }

  return { update, setPhi, renderer, camera, root };
}
