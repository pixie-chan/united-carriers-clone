// Custom cursor: dot + lagging outline with a scroll-progress ring (as on the original).
export function initCursor() {
  const main = document.querySelector('.cursor-main');
  const outline = document.querySelector('.cursor-outline');
  if (!main || !outline || !window.gsap) return;
  const gsap = window.gsap;

  const circle = outline.querySelector('circle');
  const R = parseFloat(circle.getAttribute('r')) || 62;
  const C = 2 * Math.PI * R;
  circle.style.strokeDasharray = C;
  circle.style.strokeDashoffset = C;

  let mx = 0, my = 0, cx = 0, cy = 0;
  window.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });

  gsap.to([main, outline], { opacity: 1, duration: .4, delay: .6 });
  main.style.opacity = 0; outline.style.opacity = 0;

  function raf() {
    cx += (mx - cx) * 0.14;
    cy += (my - cy) * 0.14;
    gsap.set(main, { x: mx, y: my, xPercent: -50, yPercent: -50 });
    gsap.set(outline, { x: cx, y: cy, xPercent: -50, yPercent: -50 });
    const max = document.documentElement.scrollHeight - innerHeight;
    const p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    circle.style.strokeDashoffset = C * (1 - p);
    requestAnimationFrame(raf);
  }
  raf();
}
