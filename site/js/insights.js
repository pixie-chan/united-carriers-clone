// Insights section: dark article list with thumbnail hover-sync.
// Ported from the live Insight class: action + main rise/fade in as the section enters
// (desc and items are static), and hovering an article row activates its thumbnail.
export function initInsights() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-ins-wrap');
  if (!wrap) return;
  const section = wrap.querySelector('.home-ins');
  if (!section) return;

  // cubic-bezier easing helper (mirrors the live's cinematicSmooth)
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

  // ---- reveal: action + main rise 26.67px live (= 2rem) and fade, as the section enters ----
  const els = [wrap.querySelector('.home-ins-action'), wrap.querySelector('.home-ins-main')].filter(Boolean);
  if (els.length) {
    gsap.set(els, { y: '2rem', autoAlpha: 0 });
    gsap.timeline({ scrollTrigger: { trigger: section, start: 'top 90%', once: true } })
      .to(els, { y: 0, autoAlpha: 1, ease: csmooth, duration: .8, stagger: .1 });
  }

  // ---- hover sync: article row <-> thumbnail (live interact()) ----
  const items = [...wrap.querySelectorAll('.home-ins-cms-item')];
  const thumbs = [...wrap.querySelectorAll('.home-ins-cms-thumb-item')];
  if (items.length && thumbs.length) {
    if (!thumbs.some(t => t.classList.contains('active'))) {
      thumbs[0].classList.add('active');
      items[0].classList.add('active');
    }
    const onEnter = e => {
      const i = items.indexOf(e.currentTarget);
      thumbs.forEach(t => t.classList.remove('active'));
      if (thumbs[i]) thumbs[i].classList.add('active');
      items.forEach(t => t.classList.remove('active'));
      e.currentTarget.classList.add('active');
    };
    items.forEach(it => it.addEventListener('mouseenter', onEnter));
  }
}
