// Service tail: road slide-in + truck parking + reliability sub-content.
// Ported from the live Service class (desktop branch): tlTruckRot, tlRoadTransition,
// tlTruckPosition, tlSpeedometerRemove. The live plays all of these on the second-screen
// trigger, so the whole choreography lives here now.

export function initTail() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const doc = document;
  const wrap = doc.querySelector('.home-service-wrap');
  if (!wrap) return;

  // live's f(n, unit): px conversions. rem = live root font (0.5787vw).
  const f = (n, unit) => {
    if (unit === 'vh') return window.innerHeight * (n / 100);
    if (unit === 'vw') return window.innerWidth * (n / 100);
    if (unit === 'rem') return (n / 10) * (window.innerWidth / 172.8);
    return 0;
  };
  const big = window.innerWidth > 991;

  const second = doc.querySelector('.home-service-second-screen');
  if (!second) return;

  const roadBig = doc.querySelector('.home-service-road-big');
  const roadBigImg = doc.querySelector('.home-service-road-big-img');
  const road = doc.querySelector('.home-service-road');
  const roadWrap = doc.querySelector('.home-service-road-wrap');
  const main = doc.querySelector('.home-service-main');
  const cms = doc.querySelector('.home-service-cms');
  const textWrap = doc.querySelector('.home-service-text-wrap');
  const label = doc.querySelector('.home-service-label');
  const truckSq = doc.querySelector('.home-service-truck-sq');
  const truckInner = doc.querySelector('.home-service-truck-inner');
  const newTruckWrap = doc.querySelector('.home-service-new-truck-wrap');
  const newTruckStick = doc.querySelector('.home-service-new-truck-stick');
  const newTruckRots = doc.querySelectorAll('.home-service-new-truck-rot');
  const newTruck = doc.querySelector('.home-service-new-truck');
  const newTruckInners = doc.querySelectorAll('.home-service-new-truck-inner');
  const onlyCar = doc.querySelector('.home-service-new-truck-inner.only-car');
  const containerTruck = doc.querySelector('.home-service-new-truck-inner.container-truck');
  const subList = doc.querySelector('.home-service-sub-list');
  const speedInner = doc.querySelector('.home-service-speed-inner');

  const paddingTop = parseFloat(getComputedStyle(main).paddingTop) || 0;
  const r = f(60, 'vh') / f(big ? 244 : 172.3, 'rem');
  const s = (big ? 782.675 : 748.816) / (2880 / 809);
  const d = (big ? 244 : 172.3) / s;

  // ---------- tlTruckRot: the parked truck canvas slides, label/main roll away,
  // the wide road fades up underneath (live start: second bottom - 180vh + 1px) ----------
  gsap.set(roadBig, { autoAlpha: 0, filter: 'blur(1px)' });
  road.style.setProperty('--scale-factor', r);

  const tlTruckRot = gsap.timeline({
    scrollTrigger: {
      trigger: second,
      start: `bottom-=${f(180, 'vh') + 1} bottom`,
      end: `bottom-=${f(100, 'vh')} bottom`,
      scrub: true
    }
  });
  tlTruckRot
    .to(doc.querySelectorAll('.home-service-cms, .home-service-btn-wrap'), {
      autoAlpha: 0,
      rotationX: big ? -90 : 0,
      y: big ? cms.offsetHeight + paddingTop : 0,
      filter: 'blur(2px)',
      duration: 1,
      ease: 'none'
    })
    .to(main, {
      '--road-height': `${f(20, 'vh')}px`,
      keyframes: {
        '0%': { '--bright-fade': 0 },
        '40%': { '--bright-fade': 1 },
        '100%': { '--bright-fade': 0 }
      },
      backgroundColor: '#0C0C0C',
      duration: 1,
      ease: 'none'
    }, '<=0')
    .to(roadBig, { x: -f(100, 'vw'), filter: 'blur(0px)', autoAlpha: 1, duration: 1, ease: 'none' }, '<=0')
    .to(doc.querySelector('.home-service-main-road.top'), {
      backgroundColor: '#0C0C0C', duration: 1, ease: 'none'
    }, '<=0')
    .fromTo(roadBigImg, { scaleY: 0 }, {
      scaleY: 1, backgroundColor: '#0C0C0C', duration: 1, ease: 'none'
    }, '<=0')
    .to(doc.querySelectorAll('.home-service-truck-cont, .home-service-truck-car, .home-service-truck-wheel'), {
      autoAlpha: 0, duration: 0, ease: 'none'
    }, '<=.05')
    .to(truckSq, { autoAlpha: 1, duration: 0, ease: 'none' }, '<=0')
    .to(textWrap, {
      rotationX: big ? 0 : -90,
      y: big ? 0 : textWrap.offsetHeight + 3 * paddingTop,
      filter: 'blur(2px)',
      duration: 1,
      ease: 'none',
      autoAlpha: 0
    }, '<=0')
    .to(label, {
      y: cms.offsetHeight + paddingTop, duration: 1, ease: 'none', autoAlpha: 0
    }, '<=0')
    .to(truckInner, {
      y: f(10, 'vh'), yPercent: big ? 35 : 58, duration: 1, ease: 'none'
    }, '<=0.1')
    .to(truckSq, {
      bottom: 0, left: 0, scale: 1.04 * 1.0435, duration: 1, ease: 'none'
    }, '<=0')
    .to(truckSq, { autoAlpha: 0, duration: 0, ease: 'none' })
    .to(newTruckWrap, { autoAlpha: 1, duration: 0, ease: 'none' }, '<=0')
    .to(newTruckInners, { x: big ? 0 : f(-20, 'rem'), duration: 0, ease: 'none' }, '<=0');

  // ---------- tlRoadTransition: new truck parks on the incoming straight road ----------
  const tlRoadTransition = gsap.timeline({
    scrollTrigger: {
      trigger: second,
      start: `bottom-=${f(100, 'vh')} bottom`,
      end: 'bottom bottom',
      scrub: true,
      fastScrollEnd: true
    }
  });
  tlRoadTransition
    .to(newTruckInners, { xPercent: 0, yPercent: 0, duration: 0.5 })
    .to(roadBig, { x: -f(200, 'vw'), duration: 1, ease: 'none' }, '<=0')
    .from(roadWrap, { x: f(100, 'vw'), duration: 1, ease: 'none' }, '<=0')
    .to(road, { '--scale-factor': 1, duration: 0.5, ease: 'none' }, '<=.6')
    .to(main, { scale: 1 / r, duration: 0.5, ease: 'none' }, '<=0')
    .to(newTruck, { scale: d, yPercent: -80, y: 0, duration: 0.5, ease: 'none' }, '<=0')
    .to(newTruckStick, { top: f(20, 'vh'), duration: 0.5, ease: 'none' }, '<=0')
    .to(newTruckInners, {
      scale: big ? 0.346 : 0.49,
      xPercent: -60,
      y: -f(120, 'rem'),
      yPercent: big ? -0.3 : -0.8,
      x: 0,
      duration: 0.5,
      ease: 'none'
    }, '<=0')
    .to(newTruckRots, { rotation: 90, duration: 1, ease: 'power1.inOut' })
    .to(onlyCar, { rotation: 12, duration: 0.4, ease: 'power1.inOut', yoyo: true, repeat: 1 }, '<=0')
    .to(containerTruck, { rotation: -12, duration: 0.4, ease: 'power1.inOut', yoyo: true, repeat: 1 }, '<0.1')
    .to(containerTruck, { scaleX: big ? 0.39 : 0.555, duration: 0.4, ease: 'power1.inOut' }, '<=0')
    .to([roadWrap, main], { y: -f(120, 'rem'), duration: 0.6, ease: 'none' }, '<=0')
    .to(newTruckRots, { y: -f(220, 'rem'), duration: 0.7, ease: 'none' }, '<=0')
    .to(main, { autoAlpha: 0, duration: 0, ease: 'none' }, '<=0');

  // ---------- tlTruckPosition: truck settles into its final parked slot ----------
  const tlTruckPosition = gsap.timeline({
    scrollTrigger: {
      trigger: subList,
      start: `top+=${f(30, 'vh')} bottom`,
      end: `top+=${f(50, 'vh')} center`,
      scrub: true
    }
  });
  tlTruckPosition
    .to(newTruck, {
      duration: 1, ease: 'none', scale: d, top: -f(big ? 650 : 560, 'rem'), xPercent: 0, yPercent: 0
    }, '<=0')
    .to(newTruckInners, {
      x: 0, y: 0, xPercent: big ? -9.4 : -3.4, duration: 1, ease: 'none'
    }, '<=0')
    .to(newTruckStick, { top: 0, duration: 1, ease: 'none' }, '<=0')
    .to(newTruckRots, {
      y: -(f(big ? 650 : 560, 'rem') - f(50, 'vh') + f((big ? 244 : 172.3) / 809 * 2880 / 2, 'rem')),
      duration: 1,
      ease: 'none'
    }, '<=0');

  // ---------- speedometer removal (live: sub-list bottom at 62.5% viewport) ----------
  if (speedInner) {
    gsap.timeline({
      scrollTrigger: {
        trigger: subList,
        start: 'bottom top+=62.5%',
        onEnter: () => speedInner.classList.remove('active', 'on-start'),
        onLeaveBack: () => speedInner.classList.add('active', 'on-start')
      }
    });
  }

  // ---------- speed HUD: scroll-velocity speedometer (same math as live) ----------
  const speedNum = doc.querySelector('.home-service-speed-inner [data-speed]');
  if (speedInner && speedNum) {
    let t = 0, prev = window.scrollY;
    gsap.ticker.add((time, deltaTime) => {
      const sc = window.scrollY;
      const active = speedInner.classList.contains('active') && speedInner.classList.contains('on-start');
      let target;
      if (active) {
        const v = Math.abs(sc - prev) / (deltaTime / 1000);
        target = Math.min(95, (isFinite(v) ? v : 0) / 25);
      } else target = 0;
      const ease = target > t ? 0.1 : (target === 0 ? 0.15 : 0.06);
      t += (target - t) * ease;
      if (t < 0.5 && target === 0) t = 0;
      const o = Math.round(t);
      if (speedNum.dataset.currentSpeed !== String(o)) {
        speedNum.textContent = String(o).padStart(2, '0');
        speedNum.dataset.currentSpeed = String(o);
      }
      prev = sc;
    });
  }
}
