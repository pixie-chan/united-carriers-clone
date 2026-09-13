// Rebuild entry: Lenis smooth scroll, loader sequence, dot globe, hero reveal.
import { initGlobe } from './globe.js';
import { initCursor } from './cursor.js';
import { initSections } from './sections.js';
import { initTail } from './tail.js';
import { initChrome } from './chrome.js';
import { initWhy } from './why.js';
import { initTesti } from './testi.js';
import { initPartners } from './partners.js';
import { initInsights } from './insights.js';
import { initFaq } from './faq.js';
import { initFooter } from './footer.js';

const gsap = window.gsap;
const Lenis = window.Lenis;
document.documentElement.classList.add('is-loading');

function tick(lenis) {
  requestAnimationFrame(time => { lenis.raf(time); tick(lenis); });
}

function drawLoaderMap() {
  const canvas = document.getElementById('loaderMap');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  fetch('data/globe-points.json').then(r => r.json()).then(cloud => {
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    const r = 1.35;
    for (const [x, y, z] of cloud.points) {
      // recover lon/lat from the sphere vector
      const lat = 90 - Math.acos(Math.max(-1, Math.min(1, y))) * 180 / Math.PI;
      const lon = Math.atan2(z, -x) * 180 / Math.PI - 180;
      if (lon < -180 || lon > 180) continue;
      const px = (lon + 180) / 360 * W;
      const py = (90 - lat) / 180 * H;
      // halftone thinning: alternate rows
      const row = Math.round(py / 26);
      if ((row + Math.round(px / 26)) % 2 === 0) continue;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }
    // active blue nodes (SE Asia / Australasia)
    const nodes = [[13.0, 122.0], [-2.2, 118.0], [-7.2, 110.2], [-6.5, 145.0]];
    const t0 = performance.now();
    (function pulse() {
      const t = (performance.now() - t0) / 1000;
      nodes.forEach(([lat, lon], i) => {
        const px = (lon + 180) / 360 * W;
        const py = (90 - lat) / 180 * H;
        const s = 1 + 0.5 * Math.sin(t * 2 + i);
        ctx.fillStyle = '#2b4bff';
        ctx.beginPath();
        ctx.arc(px, py, 4.6 * s, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(43,75,255,0.25)';
        ctx.beginPath();
        ctx.arc(px, py, 12 * s, 0, Math.PI * 2);
        ctx.fill();
      });
      requestAnimationFrame(pulse);
    })();
  });
}

function loaderTickers() {
  const countries = document.getElementById('loaderCountries');
  const services = document.getElementById('loaderServices');
  if (countries) gsap.to(countries, { yPercent: -45, duration: 9, ease: 'none', repeat: -1 });
  if (services) gsap.to(services, { yPercent: -52, duration: 10, ease: 'none', repeat: -1 });
  gsap.to('.loader-spinner', { rotation: 360, duration: 1.4, ease: 'none', repeat: -1, transformOrigin: '50% 50%' });
  const count = document.getElementById('loaderCount');
  const state = { v: 0 };
  gsap.to(state, {
    v: 100, duration: 2.7, ease: 'power1.inOut',
    onUpdate: () => { if (count) count.textContent = String(Math.round(state.v)).padStart(2, '0'); }
  });
}

async function boot() {
  const lenis = new Lenis({ duration: 1.15, smoothWheel: true });
  window.__lenis = lenis;
  tick(lenis);
  document.documentElement.classList.add('lenis');
  if (window.ScrollTrigger) lenis.on('scroll', window.ScrollTrigger.update);
  initCursor();
  initChrome();
  loaderTickers();
  drawLoaderMap();

  let globe = null;
  try {
    globe = await initGlobe(document.getElementById('globe'), {
      labelContainer: document.querySelector('.home-hero-globe'),
      labelCountries: ['UK', 'GERMANY', 'SPAIN', 'ITALY', 'TURKEY', 'ISRAEL', 'EGYPT', 'QATAR', 'SAUDI ARABIA', 'KENYA', 'SOUTH AFRICA']
    });
  } catch (e) {
    console.warn('globe failed', e);
  }
  initSections().catch(e => console.warn('sections failed', e));
  try { initTail(); } catch (e) { console.warn('tail failed', e); }
  try { initWhy(); } catch (e) { console.warn('why failed', e); }
  try { initTesti(); } catch (e) { console.warn('testi failed', e); }
  try { initPartners(); } catch (e) { console.warn('partners failed', e); }
  try { initInsights(); } catch (e) { console.warn('insights failed', e); }
  try { initFaq(); } catch (e) { console.warn('faq failed', e); }
  try { initFooter(); } catch (e) { console.warn('footer failed', e); }
  runLoader(globe);
}

function runLoader(globe) {
  const loader = document.getElementById('loader');
  const tl = gsap.timeline({ delay: 2.95 });
  tl.add(() => { document.documentElement.classList.remove('is-loading'); })
    .to(loader, {
      yPercent: -100, duration: 1.05, ease: 'power3.inOut',
      onComplete: () => loader.remove()
    })
    .from('.hero-h1 .line > span', { yPercent: 118, duration: .95, stagger: .09, ease: 'power3.out' }, '-=.75')
    .from('.hero-label', { autoAlpha: 0, y: 10, duration: .5 }, '<')
    .from('.hero-desc', { autoAlpha: 0, y: 10, duration: .5 }, '<.12')
    .from('.hero-ctas .btn', { autoAlpha: 0, y: 10, duration: .5, stagger: .07 }, '<.1')
    .from('.home-hero-globe', { autoAlpha: 0, scale: .95, duration: 1.2, ease: 'power2.out' }, '<-.35')
    .from('.header, .topbar', { autoAlpha: 0, duration: .6 }, '<');

  if (globe) {
    const phi = { v: 3.8 };
    gsap.ticker.add(() => {
      phi.v += 0.0015 * gsap.ticker.deltaRatio();
      globe.setPhi(phi.v);
      globe.update();
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
