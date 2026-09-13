// Testimonials section: plane flyover + testimonial wipe.
// Ported from the live Testi class (desktop branch). One scalar, `--overlap-clip`,
// drives BOTH the content's clip-path tongue and the plane's horizontal sweep (CSS calc);
// this timeline tweens that variable plus the plane scale, shadow offsets and the
// previous section's cloud push.
export function initTesti() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-testi-wrap');
  if (!wrap) return;
  const section = wrap.querySelector('.home-testi');
  if (!section) return;
  if (innerWidth <= 991) return; // mobile/tablet branch lands in the mobile pass

  // cubic-bezier easing helper (mirrors the live's cinematicSmooth / cinematicSilk)
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
  const csmooth = bezierEase(.25, .1, .25, 1);

  const inner = wrap.querySelector('.home-testi-plane-inner');
  const shadow = wrap.querySelector('.home-testi-plane-img-shadow');
  const whyCloud = document.querySelector('.home-why-cloud-overlap');

  // overlap timeline: [section top + 0.2vh .. + 2.2vh] (as live)
  const secTop = () => section.getBoundingClientRect().top + scrollY;
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: section,
      scrub: true,
      fastScrollEnd: true,
      start: () => secTop() + innerHeight * 0.2,
      end: () => secTop() + innerHeight * 2.2
    }
  });
  tl.fromTo(section, { '--overlap-clip': -60 },
    { '--overlap-clip': 180, ease: csmooth, duration: 1 }, 0);
  if (inner) {
    tl.fromTo(inner, { scale: 1 },
      { yPercent: 0, scale: 1.3, force3D: true, ease: csmooth, duration: 1 }, '<');
  }
  if (shadow) {
    tl.fromTo(shadow, { '--pos-x': -5, '--pos-y': 0, '--scale': .9 },
      { '--pos-x': 3, '--pos-y': 2, '--scale': .5, ease: csmooth, duration: 1 }, '<');
  }
  if (whyCloud) {
    tl.fromTo(whyCloud, { scale: 1, yPercent: 0 },
      { scale: .8, yPercent: -55, ease: csmooth, duration: .5 }, '<');
  }

  // item reveal: rise + fade as the section pins (live: y 26.67px @1440 = 2rem here)
  const items = wrap.querySelectorAll('.home-testi-item');
  const why = document.querySelector('.home-why');
  if (items.length && why) {
    gsap.set(items, { y: '2rem', autoAlpha: 0 });
    gsap.timeline({
      scrollTrigger: { trigger: why, start: 'bottom top+=60%', once: true }
    }).to(items, { y: 0, autoAlpha: 1, ease: csmooth, duration: .8, stagger: .1 });
  }
}
