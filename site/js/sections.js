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

  // ---------- services: replaced by the full port, see js/service.js + js/tail.js ----------
}
