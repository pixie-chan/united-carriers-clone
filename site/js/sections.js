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
    // The live's screen-1 canvas plays sequences 0->1->2 back-to-back as ONE chain
    // (seq0 end / seq1 start are pixel-continuous; verified against the live mirror).
    // 353 frames total: 159 + 97 + 97.
    const chain = [...seqs[0], ...seqs[1], ...seqs[2]];
    crane = new FrameSequence({ canvas: document.getElementById('craneCanvas'), frames: chain });
    truck = new FrameSequence({ canvas: document.getElementById('truckCanvas'), frames: seqs[3] });
  }

  // crane chain windows, measured against the live at 1920x1080 (offsets in viewport heights
  // from the section top): seq0 [1.00, 2.26], seq1 [2.26, 3.79], seq2 [3.79, 4.53], then hold.
  const W = [[1.00, 2.26], [2.26, 3.79], [3.79, 4.53]];
  const LENS = [seqs[0]?.length || 159, seqs[1]?.length || 97, seqs[2]?.length || 97];
  const TOTAL = LENS[0] + LENS[1] + LENS[2];
  const frameIndexForF = (f) => {
    if (f <= W[0][0]) return 0;
    if (f >= W[2][1]) return TOTAL - 1;
    let idx = 0;
    for (let s = 0; s < 3; s++) {
      const [a, b] = W[s];
      if (f >= b) { idx += LENS[s]; continue; }
      const local = clamp((f - a) / (b - a));
      return Math.round(idx + local * (LENS[s] - 1));
    }
    return Math.round(idx);
  };
  if (crane) {
    const svcTop = () => svcEl.getBoundingClientRect().top + scrollY;
    ST.create({
      trigger: svcEl, scrub: true,
      start: () => svcTop() + innerHeight * W[0][0],
      end: () => svcTop() + innerHeight * W[2][1],
      onUpdate: self => {
        const f = W[0][0] + self.progress * (W[2][1] - W[0][0]);
        crane.setProgress(frameIndexForF(f) / (TOTAL - 1));
      }
    });
  }

  const cards = document.querySelector('.service-cards');
  const dark = document.querySelector('.service-dark');
  const head = document.querySelector('.service-head');
  const cta = document.querySelector('.svc-cta');
  const containers = document.querySelectorAll('.svc-containers img');

  const cardStart = () => window.innerWidth * 0.95;
  const cardEnd = () => -Math.max(0, cards.scrollWidth - window.innerWidth * 0.3);

  // p = progress over the whole section (top top -> bottom bottom)
  const onUpdate = (p) => {
    if (truck) truck.setProgress(smooth(p, 0.06, 0.46));
    // dark panel rises from the bottom and rests covering the bottom 60% (live: y980->432 over ~4.3..6.0vh)
    // NOTE: y in px, not yPercent - the pre-JS CSS state is translateY(100%), which GSAP decomposes
    // into its y cache (1080px); yPercent would stack on top of it and never reveal the element.
    if (dark) gsap.set(dark, { y: (0.4 + 0.6 * (1 - smooth(p, 0.3075, 0.4326))) * innerHeight });
    // dark-screen heading + pill button appear with the dark (live: readable ~6.3vh onward)
    const a = smooth(p, 0.442, 0.468);
    // heading strip slides in from the right, settles left, then exits left as the cards roll in
    // (live filmstrip: right side ~6.5vh, rest ~7.0vh, out by ~7.7vh)
    const hx = (1 - smooth(p, 0.458, 0.502)) * innerWidth * 0.5 - smooth(p, 0.504, 0.550) * innerWidth * 0.75;
    if (head) gsap.set(head, { autoAlpha: a, x: hx, y: (1 - a) * 26 });
    if (cta) gsap.set(cta, { autoAlpha: a });
    if (cards) gsap.set(cards, { x: cardStart() + (cardEnd() - cardStart()) * smooth(p, 0.520, 0.740) });
    // machine scene slides right as the loading animation ends (live: +400px at 1920 between ~3.1 and ~4.55vh)
    const slide = smooth(p, 0.222, 0.325) * (400 * window.innerWidth / 1920);
    gsap.set('#craneCanvas', { x: slide });
    containers.forEach(im => gsap.set(im, { x: slide }));
  };
  onUpdate(0);
  ST.create({ trigger: svcEl, start: 'top top', end: 'bottom bottom', onUpdate: (self) => onUpdate(self.progress) });

  // ---------- milestones removed (replaced by the ported service tail, see js/tail.js) ----------
}
