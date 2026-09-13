// Partners section: logo lattice fill + reveals.
// Ported from the live Partners class (desktop branch): placeholder cells round each
// list to a multiple of the per-row count, then a batch fade/rise reveal for the items.
export function initPartners() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-partners-wrap');
  if (!wrap) return;
  const section = wrap.querySelector('.home-partners');
  if (!section) return;

  // ---- placeholders: remove the pre-baked ones; live does NOT refill (its template sits
  //      in a .hidden div and its runtime leaves the lists at 17/16 with a ragged last row) ----
  wrap.querySelectorAll('.home-partners-item[data-partners-placeholder]').forEach(el => el.remove());

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

  // ---- labels: live leaves them static (no reveal in its runtime); nothing to do ----

  // ---- items: batch fade + rise (live: batchMax 5 desktop / 4 tablet, once) ----
  const items = wrap.querySelectorAll('.home-partners-item');
  gsap.set(items, { autoAlpha: 0 });
  ST.batch(items, {
    start: 'top 85%',
    once: true,
    batchMax: innerWidth > 991 ? 5 : 4,
    onEnter: batch => {
      batch.forEach((el, i) => {
        gsap.set(el, { autoAlpha: 1 });
        gsap.fromTo(el, { y: '6.25rem' }, { y: 0, duration: 1, ease: csmooth, delay: .15 * i });
      });
    }
  });
}
