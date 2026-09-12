// Scroll choreography for the intro, services and milestones sections.
import { FrameSequence } from './frames.js';

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (p, a, b) => { const t = clamp((p - a) / (b - a)); return t * t * (3 - 2 * t); };

export async function initSections() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  gsap.registerPlugin(ST);

  // ---------- intro ----------
  gsap.from('.intro-copy', { autoAlpha: 0, y: 34, duration: .9, scrollTrigger: { trigger: '.home-intro', start: 'top 78%' } });
  gsap.from('.intro-copy2', { autoAlpha: 0, y: 34, duration: .9, delay: .1, scrollTrigger: { trigger: '.home-intro', start: 'top 78%' } });
  gsap.from('.intro-btn', { autoAlpha: 0, y: 24, duration: .8, delay: .2, scrollTrigger: { trigger: '.home-intro', start: 'top 78%' } });
  gsap.from('.intro-img', { autoAlpha: 0, y: 40, duration: 1, scrollTrigger: { trigger: '.home-intro', start: 'top 60%' } });
  gsap.from('.intro-h2', { autoAlpha: 0, y: 46, duration: 1, scrollTrigger: { trigger: '.home-intro', start: 'top 60%' } });
  gsap.from('.intro-stats', { autoAlpha: 0, y: 40, duration: 1, scrollTrigger: { trigger: '.intro-stats', start: 'top 92%' } });

  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    const state = { v: 0 };
    ST.create({ trigger: el, start: 'top 88%', once: true, onEnter: () => {
      gsap.to(state, { v: target, duration: 1.8, ease: 'power2.out', onUpdate: () => {
        el.textContent = (target >= 1000) ? Math.round(state.v).toLocaleString('en-US') : state.v.toFixed(decimals);
      }});
    }});
  });

  // ---------- services ----------
  const svcEl = document.querySelector('.home-service');
  if (!svcEl) return;

  let seqs = [];
  try { seqs = await fetch('data/frames-sequences.json').then(r => r.json()); } catch (e) { console.warn('no frame data', e); }
  let crane = null, truck = null;
  if (seqs.length >= 4) {
    crane = new FrameSequence({ canvas: document.getElementById('craneCanvas'), frames: seqs[0] });
    truck = new FrameSequence({ canvas: document.getElementById('truckCanvas'), frames: seqs[3] });
  }

  // crane sequence: live window = first-screen top + 100vh -> + 450vh (viewport-relative,
  // recomputed on refresh so it works at any window size)
  if (crane) {
    const svcTop = () => svcEl.getBoundingClientRect().top + scrollY;
    ST.create({
      trigger: svcEl, scrub: true,
      start: () => svcTop() + innerHeight,
      end: () => svcTop() + innerHeight * 4.5,
      onUpdate: self => crane.setProgress(self.progress)
    });
  }

  const cards = document.querySelector('.service-cards');
  const dark = document.querySelector('.service-dark');
  const containers = document.querySelectorAll('.svc-containers img');

  const cardStart = () => window.innerWidth * 0.95;
  const cardEnd = () => -Math.max(0, cards.scrollWidth - window.innerWidth * 0.3);

  const onUpdate = (p) => {
    if (truck) truck.setProgress(smooth(p, 0.06, 0.46));
    if (cards) gsap.set(cards, { x: cardStart() + (cardEnd() - cardStart()) * smooth(p, 0.12, 0.88) });
    if (dark) gsap.set(dark, { opacity: 0.94 * smooth(p, 0.07, 0.15) * (1 - 0.5 * smooth(p, 0.94, 1)) });
    // containers stay grounded at their live-measured spots (were floating early); gentle exit drift only
    containers.forEach((im, i) => gsap.set(im, { x: -smooth(p, 0.55, 1) * (10 + i * 5) * 4 }));
  };
  onUpdate(0);
  ST.create({ trigger: svcEl, start: 'top top', end: 'bottom bottom', onUpdate: (self) => onUpdate(self.progress) });

  // ---------- milestones removed (replaced by the ported service tail, see js/tail.js) ----------
}
