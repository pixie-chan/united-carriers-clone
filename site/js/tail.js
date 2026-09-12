// Service tail: road slide-in + truck parking + reliability sub-content.
// Resting composition lives in CSS (sections2.css "tail rest-state"); this module adds the
// entrance scrubs and the scroll-velocity speedometer, ported from the live site's choreography.

export function initTail() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const tail = document.querySelector('.uc-tail');
  if (!tail) return;

  const roadWrap = tail.querySelector('.home-service-road-wrap');
  const road = tail.querySelector('.home-service-road');
  const truckWrap = tail.querySelector('.home-service-new-truck-wrap');
  const truckRots = tail.querySelectorAll('.home-service-new-truck-rot');
  const truck = tail.querySelector('.home-service-new-truck');
  const truckStick = tail.querySelector('.home-service-new-truck-stick');

  // ---------- entrance: road slides in from the right, truck arrives and parks ----------
  // viewport-relative window (recomputed on refresh): starts ~1.2 screens before the tail, settles just inside it
  const tailTop = () => tail.getBoundingClientRect().top + scrollY;
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: tail, scrub: true,
      start: () => tailTop() - innerHeight * 1.105,
      end: () => tailTop() + innerHeight * 1.18
    }
  });
  if (roadWrap) tl.fromTo(roadWrap, { x: '100vw' }, { x: 0, duration: 1, ease: 'none' }, 0);
  if (road) tl.fromTo(road, { '--scale-factor': 2.65 }, { '--scale-factor': 1, duration: 1, ease: 'none' }, 0);
  if (truckWrap) tl.fromTo(truckWrap, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4, ease: 'none' }, 0.08);
  if (truckStick) tl.fromTo(truckStick, { top: '16.67px' }, { top: 0, duration: 0.5, ease: 'none' }, 0.4);
  if (truckRots.length) tl.fromTo(truckRots, { rotation: 0, y: 0 }, { rotation: 90, y: '-34.0196rem', duration: 0.9, ease: 'power1.inOut' }, 0.1);
  if (truck) tl.fromTo(truck, { top: '-20rem', scale: 0.5 }, { top: '-40.65rem', scale: 1.1098, duration: 0.9, ease: 'none' }, 0.1);

  // ---------- speed HUD: scroll-velocity speedometer (same math as live) ----------
  const speedInner = document.querySelector('.home-service-speed-inner');
  const speedNum = document.getElementById('svcSpeed');
  if (speedInner && speedNum) {
    let t = 0, prev = window.scrollY;
    gsap.ticker.add((time, deltaTime) => {
      const s = window.scrollY;
      const active = speedInner.classList.contains('active') && speedInner.classList.contains('on-start');
      let f;
      if (active) {
        const v = Math.abs(s - prev) / (deltaTime / 1000);
        f = Math.min(95, (isFinite(v) ? v : 0) / 25);
      } else f = 0;
      const d = f > t ? 0.1 : (f === 0 ? 0.15 : 0.06);
      t += (f - t) * d;
      if (t < 0.5 && f === 0) t = 0;
      const o = Math.round(t);
      if (speedNum.dataset.currentSpeed !== String(o)) {
        speedNum.textContent = String(o).padStart(2, '0');
        speedNum.dataset.currentSpeed = String(o);
      }
      prev = s;
    });

    // visibility windows (viewport-relative, recomputed on refresh)
    const speedOff = () => {
      const sl = document.querySelector('.home-service-sub-list') || tail;
      return (sl.getBoundingClientRect().bottom + scrollY) - innerHeight * 0.625;
    };
    ST.create({
      trigger: document.querySelector('.home-service'), start: 'top bottom', end: () => speedOff(),
      onEnter: () => speedInner.classList.add('active'),
      onLeaveBack: () => speedInner.classList.remove('active'),
      onLeave: () => { speedInner.classList.remove('active', 'on-start'); }
    });
    ST.create({
      trigger: tail,
      start: () => tailTop() - innerHeight * 1.04,
      end: () => speedOff(),
      onEnter: () => speedInner.classList.add('on-start'),
      onLeaveBack: () => speedInner.classList.remove('on-start')
    });
  }
}
