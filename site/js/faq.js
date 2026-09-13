// FAQ section: accordion list + title mask reveal.
// Ported from the live Faq class: title does a split-line mask slide (live splits the heading
// and clips it), main rises/fades in, and item clicks run a one-open accordion with a
// ScrollTrigger refresh after the height animation (as live does via jQuery + lenis.resize).
export function initFaq() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const wrap = document.querySelector('.home-faq-wrap');
  if (!wrap) return;
  const section = wrap.querySelector('.home-faq');
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

  // ---- title: mask + split-line slide (as live) ----
  const h2 = wrap.querySelector('.home-faq-title .heading');
  if (h2) {
    const natural = Math.round(h2.getBoundingClientRect().height);
    const inner = h2.innerHTML;
    h2.style.overflow = 'hidden';
    if (natural > 0) h2.style.height = natural + 'px';
    h2.innerHTML = '<div style="display: block; text-align: inherit; position: relative; text-indent: 0px">'
      + '<span class="split-line" style="display: inline-block">' + inner + '</span></div>';
    const span = h2.querySelector('.split-line');
    gsap.set(span, { yPercent: 112 });
    gsap.timeline({ scrollTrigger: { trigger: section, start: 'top 85%', once: true } })
      .to(span, {
        yPercent: 0, duration: 1.1, ease: csmooth,
        onComplete: () => { h2.style.overflow = ''; h2.style.height = ''; }
      });
  }

  // ---- main: rise + fade ----
  const main = wrap.querySelector('.home-faq-main');
  if (main) {
    gsap.set(main, { y: '2rem', autoAlpha: 0 });
    gsap.timeline({ scrollTrigger: { trigger: section, start: 'top 85%', once: true } })
      .to(main, { y: 0, autoAlpha: 1, ease: csmooth, duration: .8 });
  }

  // ---- accordion (one open at a time; refresh ScrollTrigger after the height tween) ----
  const items = [...wrap.querySelectorAll('.home-faq-main-item')];
  if (!items.length) return;

  const closeItem = it => {
    const a = it.querySelector('.home-faq-main-item-ans');
    it.classList.remove('active');
    if (a && a.style.display !== 'none') {
      a.style.height = Math.round(a.getBoundingClientRect().height) + 'px';
      gsap.to(a, {
        height: 0, duration: .45, ease: 'power2.inOut',
        onComplete: () => { a.style.display = 'none'; a.style.height = ''; }
      });
    }
  };
  const openItem = it => {
    const a = it.querySelector('.home-faq-main-item-ans');
    it.classList.add('active');
    if (a) {
      a.style.display = 'block';
      const h = a.scrollHeight;
      gsap.fromTo(a, { height: 0 }, {
        height: h, duration: .45, ease: 'power2.inOut',
        onComplete: () => { a.style.height = ''; }
      });
    }
  };
  items.forEach(it => it.addEventListener('click', () => {
    const wasActive = it.classList.contains('active');
    items.forEach(o => { if (o !== it && o.classList.contains('active')) closeItem(o); });
    if (wasActive) closeItem(it);
    else openItem(it);
    setTimeout(() => ST.refresh(true), 250);
  }));
}
