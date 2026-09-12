// Header + topbar chrome: hide on scroll-down, show on scroll-up (as on the live site).
// Live also hides the header on first scroll-down (~translateY -100px) and reveals it on any
// scroll-up gesture; the QA captures are all downward jumps, so the hidden state is what matters.

export function initChrome() {
  const gsap = window.gsap;
  const header = document.querySelector('.header');
  const topbar = document.querySelector('.topbar');
  if (!gsap || (!header && !topbar)) return;
  const els = [header, topbar].filter(Boolean);
  let last = window.scrollY;
  let hidden = false;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    const down = y > last + 2;
    const up = y < last - 2;
    last = y;
    if (down && y > 120 && !hidden) {
      hidden = true;
      // children (logo with top offset, absolute-positioned nav) stick out well below the box,
      // so translate by the box height plus generous margin
      gsap.to(els, { y: (i, el) => -(el.offsetHeight + 190), duration: 0.45, ease: 'power2.out', overwrite: 'auto' });
    } else if ((up || y < 120) && hidden) {
      hidden = false;
      gsap.to(els, { y: 0, duration: 0.45, ease: 'power2.out', overwrite: 'auto' });
    }
  }, { passive: true });
}
