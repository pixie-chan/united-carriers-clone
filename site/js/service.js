// Service section: first/second screens - crane + truck frame sequences and the
// scroll choreography, ported from the live Service class (desktop branch).
// The third-screen (road/truck parking/speed HUD continues in tail.js).
import { FrameSequence, getFrameUrls } from './frame-seq.js';
import { SEQ } from './service-frames.js';

export function initService() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-service-wrap');
  if (!wrap) return;
  const doc = document;

  // live's f(n, unit): px conversions. rem = live root font (0.5787vw).
  const f = (n, unit) => {
    if (unit === 'vh') return window.innerWidth <= 767 ? window.innerHeight * (n / 100) : window.innerHeight * (n / 100);
    if (unit === 'vw') return window.innerWidth * (n / 100);
    if (unit === 'rem') return (n / 10) * (window.innerWidth / 172.8);
    return 0;
  };
  const rem = n => (n / 10) * (window.innerWidth / 172.8);   // same as f(n,'rem')

  const first = wrap.querySelector('.home-service-first-screen');
  const second = wrap.querySelector('.home-service-second-screen');
  if (!first || !second) return;

  // ---------- frame sequences (desktop) ----------
  const craneCanvas = wrap.querySelector('.home-service-crane-sq');
  const truckCanvas = wrap.querySelector('.home-service-truck-sq');

  let craneSeq = null;
  if (craneCanvas) {
    const lift = getFrameUrls(SEQ.y, true);    // skipOdd
    const rot = getFrameUrls(SEQ.k, false);
    const put = getFrameUrls(SEQ.T, true);     // skipOdd
    craneSeq = new FrameSequence({
      canvas: craneCanvas,
      frames: [...lift, ...rot, ...put],
      windowed: true,
      fit: 'cover',
      concurrency: 6,
      progressive: true,
      lerp: 1,
      scrollTrigger: {
        trigger: first,
        start: `top+=${f(100, 'vh') + 1} top`,
        end: `top+=${f(450, 'vh')} top`,
        scrub: true
      }
    });
  }

  let truckSeq = null;
  if (truckCanvas) {
    const frames = getFrameUrls(SEQ.S, true);  // skipOdd
    const lead = window.innerWidth > 991 ? 0 : 20;
    truckSeq = new FrameSequence({
      canvas: truckCanvas,
      frames: [...new Array(lead).fill(frames[0]), ...frames],
      windowed: true,
      fit: 'contain',
      clear: true,
      concurrency: 6,
      progressive: true,
      lerp: 1,
      scrollTrigger: {
        trigger: second,
        start: `bottom-=${f(180, 'vh')} bottom`,
        end: `bottom-=${f(100, 'vh')} bottom`,
        scrub: true
      }
    });
  }

  // ---------- tlMoveCraneIn: crane static slides in, hands off to the frame canvas ----------
  const craneStaticCw = wrap.querySelectorAll('.home-service-crane-static.cont-w');
  const craneStaticCar = wrap.querySelectorAll('.home-service-crane-static.o-car');
  gsap.set(craneStaticCw, { clipPath: 'inset(34.5% 2.6% 41.8% 86%)' });
  wrap.querySelectorAll('.home-service-crane-static img').forEach(im => im.removeAttribute('loading'));

  const tlMoveCraneIn = gsap.timeline({
    scrollTrigger: { trigger: first, start: 'top top+=50%', end: `top+=${f(100, 'vh')} top`, scrub: true }
  });
  tlMoveCraneIn
    .fromTo(craneStaticCar, { x: -rem(500) }, { x: 0, ease: 'none', duration: 1 }, 0)
    .to(craneCanvas, { autoAlpha: 1, duration: 0, ease: 'linear' })
    .to([...craneStaticCar, ...craneStaticCw], { autoAlpha: 0, duration: 0, ease: 'linear' });

  // ---------- tlCraneRot: crane lifts + rotates while the truck rolls in ----------
  const crane = wrap.querySelector('.home-service-crane');
  const contWrap = wrap.querySelector('.home-service-cont-wrap');
  const truck = wrap.querySelector('.home-service-truck');
  const truckWheels = wrap.querySelectorAll('.home-service-truck-wheel-i');

  const tlCraneRot = gsap.timeline({
    scrollTrigger: { trigger: first, start: `top+=${f(250, 'vh')} top`, end: `top+=${f(440, 'vh')} top`, scrub: true }
  });
  tlCraneRot
    .to(truck, { autoAlpha: 1, duration: 0 })
    .to(contWrap, {
      xPercent: 80, scale: 0.85, yPercent: 8,
      keyframes: {
        '0%': { filter: 'blur(0px)', autoAlpha: 1 },
        '80%': { filter: 'blur(1px)', autoAlpha: 1 },
        '100%': { filter: 'blur(3px)', autoAlpha: 0.95 }
      },
      ease: 'none', duration: 0.7
    }, '<')
    .to(craneCanvas, {
      transformOrigin: 'center bottom',
      keyframes: {
        '0%': { rotationZ: 360, y: 0 },
        '30%': { rotationZ: 360.5, y: rem(10) },
        '70%': { rotationZ: 357, y: rem(12) },
        '100%': { rotationZ: 360, y: rem(12) },
        easeEach: 'linear'
      },
      ease: 'none', duration: 0.7
    }, '<')
    .to(crane, { xPercent: 20.9, ease: 'linear', duration: 0.7 })
    .to(craneCanvas, { scale: 0.9, transformOrigin: 'center bottom', y: -rem(9.6), ease: 'none', duration: 0.7 }, '<.1')
    .fromTo(truck, { x: f(100, 'vw') }, { x: 0, ease: 'none', duration: 0.8 }, '<')
    .from(truckWheels, {
      rotationZ: 1440, ease: 'linear', duration: 0.8,
      modifiers: { rotationZ: gsap.utils.unitize(v => parseFloat(v) % 360) }
    }, '<');

  gsap.set(wrap.querySelector('.home-service-main'), { autoAlpha: 0 });

  // ---------- tlMoveTruckIn: screens swap, truck parks, texts scroll horizontally ----------
  const mainInner = wrap.querySelector('.home-service-main-inner');
  const textWrap = wrap.querySelector('.home-service-text-wrap');
  const label = wrap.querySelector('.home-service-label');
  const land = wrap.querySelector('.home-service-land');
  const scene = wrap.querySelector('.home-service-scene');
  const truckInner = wrap.querySelector('.home-service-truck-inner');
  const outTops = wrap.querySelectorAll('.home-service-crane-static.out-top');
  const outBots = wrap.querySelectorAll('.home-service-crane-static.out-bot');
  const main = wrap.querySelector('.home-service-main');
  const truckCont = wrap.querySelector('.home-service-truck-cont');
  const speedInner = doc.querySelector('.home-service-speed-inner');
  const cMs = () => window.innerWidth / (mainInner.offsetWidth + window.innerWidth);

  const tlMoveTruckIn = gsap.timeline({
    scrollTrigger: {
      trigger: first,
      start: `top+=${f(450, 'vh')} top`,
      end: `bottom-=${f(100, 'vh')} bottom`,
      endTrigger: second,
      scrub: true,
      onEnter: () => {
        gsap.set([main, truckCont, ...outTops, ...outBots, mainInner], { autoAlpha: 1 });
        gsap.set(craneCanvas, { autoAlpha: 0 });
        speedInner && speedInner.classList.add('active');
      },
      onLeaveBack: () => {
        gsap.set([main, truckCont, ...outTops, ...outBots, mainInner], { autoAlpha: 0 });
        gsap.set(craneCanvas, { autoAlpha: 1 });
        speedInner && speedInner.classList.remove('active');
      }
    }
  });
  tlMoveTruckIn
    .to(wrap.querySelector('.home-service-stick.second-screen'), { top: 0, ease: 'sine.inOut', duration: 1 }, '<')
    .to(land, { height: f(60, 'vh'), ease: 'sine.inOut', duration: 1 }, '<')
    .to(truckInner, { transformOrigin: '0% 100%', scale: window.innerWidth > 991 ? 0.6 : 1, ease: 'sine.inOut', duration: 1, immediateRender: false }, '<')
    .to(scene, { transformOrigin: '-5% 100%', scale: window.innerWidth > 991 ? 0.55 : 0.95, ease: 'sine.inOut', duration: 1 }, '<')
    .to(outTops, { yPercent: -18, ease: 'sine.inOut', duration: 1 }, '<')
    .to(scene, { xPercent: -80, ease: 'linear', duration: 1, filter: 'blur(5px)', y: rem(5) }, '<+=0.4')
    .to(truckWheels, {
      rotationZ: 2880, ease: 'linear', duration: 1,
      modifiers: { rotationZ: gsap.utils.unitize(v => parseFloat(v) % 360) },
      onStart: () => speedInner && speedInner.classList.add('on-start'),
      onReverseComplete: () => speedInner && speedInner.classList.remove('on-start')
    }, '<')
    .to(truckInner, { xPercent: window.innerWidth > 991 ? -12 : -20, ease: 'none', duration: 0.5 }, '<+=0.48')
    .to(label, { autoAlpha: 1, duration: 0, ease: 'none' }, '<')
    .to(label, { x: () => -label.offsetWidth, duration: 3, ease: 'none' }, '<')
    .to(mainInner, { x: () => -mainInner.offsetWidth, duration: 3, ease: 'none' }, '<')
    .to(textWrap, {
      keyframes: [
        { x: 0, duration: 3 * cMs(), ease: 'none' },
        { x: window.innerWidth > 991 ? 0 : () => mainInner.offsetWidth, duration: 3 * (1 - cMs()), ease: 'none' }
      ],
      ease: 'none'
    }, '<')
    .to(land, { autoAlpha: 0, duration: 0, ease: 'none' }, '<+=0.32')
    .to(truckInner, { xPercent: 0, x: window.innerWidth > 991 ? rem(325) : 0, duration: 2, ease: 'none' }, '<+=0.2')
    .to(truckWheels, {
      rotationZ: 4320, ease: 'linear', duration: 2,
      modifiers: { rotationZ: gsap.utils.unitize(v => parseFloat(v) % 360) }
    }, '<');

  // ---------- reveals ----------
  // m-style: mask + inner slide (single-line text elements)
  const mReveal = (el, st) => {
    if (!el) return null;
    const nat = Math.round(el.getBoundingClientRect().height);
    const html = el.innerHTML;
    el.style.overflow = 'hidden';
    if (nat > 0) el.style.height = nat + 'px';
    el.innerHTML = `<div style="display:block;text-align:inherit;position:relative;text-indent:0px"><span class="svc-split" style="display:inline-block;will-change:transform">${html}</span></div>`;
    const span = el.querySelector('.svc-split');
    gsap.set(span, { yPercent: 112 });
    return gsap.timeline({ scrollTrigger: st, defaults: { ease: 'power3.out', duration: 1 } })
      .to(span, { yPercent: 0, onComplete: () => { el.style.overflow = ''; el.style.height = ''; } });
  };
  // i-style: rise + fade
  const iReveal = (el, st, fromY = rem(10)) => {
    if (!el) return null;
    gsap.set(el, { y: fromY, autoAlpha: 0 });
    return gsap.timeline({ scrollTrigger: st })
      .to(el, { y: 0, autoAlpha: 1, duration: 0.8, ease: 'power3.out' });
  };

  // third-screen reveals (elements live in the uc-tail continuation)
  mReveal(doc.querySelector('.home-service-third-screen .home-service-title .heading'),
    { trigger: doc.querySelector('.home-service-third-screen .home-service-title'), start: 'top 85%', once: true });
  mReveal(doc.querySelector('.home-service-third-screen .home-service-desc .txt'),
    { trigger: doc.querySelector('.home-service-third-screen .home-service-desc'), start: 'top 85%', once: true });

  // sub items: batch of 1
  const subItems = doc.querySelectorAll('.home-service-sub-item');
  if (subItems.length) {
    gsap.set(subItems, { autoAlpha: 0 });
    ST.batch(subItems, {
      start: 'top 85%',
      batchMax: 1,
      once: true,
      onEnter: batch => {
        batch.forEach((el, i) => {
          gsap.set(el, { autoAlpha: 1 });
          const tl = gsap.timeline({ delay: 0.15 * i });
          iReveal(el, { trigger: el, start: 'top 95%', once: true });
          mReveal(el.querySelector('.home-service-sub-title .heading'), { trigger: el, start: 'top 85%', once: true });
          mReveal(el.querySelector('.home-service-sub-desc .txt'), { trigger: el, start: 'top 85%', once: true });
        });
      }
    });
  }

  // horizontal reveals inside the truck-in scroll (containerAnimation)
  requestAnimationFrame(() => {
    const st = tlMoveTruckIn.scrollTrigger;
    if (!st) return;
    const inner = wrap.querySelector('.home-service-main-inner');
    mReveal(wrap.querySelector('.home-service-title'), { trigger: inner, start: 'left left', containerAnimation: tlMoveTruckIn, once: true });
    iReveal(wrap.querySelector('.home-service-btn-wrap'), { trigger: inner, start: 'left left', containerAnimation: tlMoveTruckIn, once: true });
    mReveal(wrap.querySelector('.home-service-sub .txt'), { trigger: inner, start: 'left left', containerAnimation: tlMoveTruckIn, once: true });
    wrap.querySelectorAll('.home-service-item').forEach(item => {
      iReveal(item, { trigger: item, start: 'left left+=60%', containerAnimation: tlMoveTruckIn, once: true });
      item.querySelectorAll('.home-service-item-title .heading h3').forEach(h => {
        mReveal(h, { trigger: item, start: 'left left+=60%', containerAnimation: tlMoveTruckIn, once: true });
      });
      mReveal(item.querySelector('.home-service-item-desc .txt'), { trigger: item, start: 'left left+=60%', containerAnimation: tlMoveTruckIn, once: true });
    });
  });

  // keep GSAP sizes fresh
  ST.addEventListener('refreshInit', () => {
    if (craneSeq) craneSeq.refresh();
    if (truckSeq) truckSeq.refresh();
  });
}
