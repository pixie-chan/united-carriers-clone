// Footer: particle logo canvas + info marquees + info switcher + reveals.
// Ported from the live layout.js classes (kt/bt/vt/Ot/ft/mt/Mt/St).
export function initFooter() {
  const gsap = window.gsap, ST = window.ScrollTrigger;
  if (!gsap || !ST) return;
  const el = document.querySelector('.footer');
  if (!el) return;

  // ---------- ParticleText (bt + vt + Ot) ----------
  class Particle {
    constructor(originX, originY, effect, color, dpr) {
      this.originX = originX; this.originY = originY; this.effect = effect;
      this.x = Math.random() * effect.width; this.y = Math.random() * effect.height;
      this.ctx = effect.ctx; this.color = color;
      this.vx = 0; this.vy = 0;
      this.ease = .04 + .04 * Math.random();
      this.targetEase = .2 + .2 * Math.random();
      this.friction = .8 + .15 * Math.random();
      this.size = 2 * dpr;
    }
    update() {
      if (this.effect.mouse.isActive) {
        const dx = this.effect.mouse.x - this.x, dy = this.effect.mouse.y - this.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < this.effect.mouse.radius) {
          this.ease = this.targetEase;
          const d = Math.sqrt(d2);
          const force = -(this.effect.mouse.actualRadius - d) / this.effect.mouse.actualRadius * 150 * (.5 + Math.random());
          this.vx += dx / d * force + (Math.random() - .5);
          this.vy += dy / d * force + (Math.random() - .5);
        }
      }
      this.x += (this.vx *= this.friction) + (this.originX - this.x) * this.ease;
      this.y += (this.vy *= this.friction) + (this.originY - this.y) * this.ease;
      this.ctx.fillStyle = this.color;
      this.ctx.beginPath();
      this.ctx.arc(this.x, this.y, this.size / 2, 0, 2 * Math.PI);
      this.ctx.fill();
    }
  }

  class ParticleEffect {
    constructor(canvas, config, dpr, parentW, parentH) {
      this.canvas = canvas; this.width = canvas.width; this.height = canvas.height;
      this.parentW = parentW || canvas.width; this.parentH = parentH || canvas.height;
      this.ctx = canvas.getContext('2d'); this.config = config; this.dpr = dpr;
      this.particlesArray = []; this.gap = 4 * dpr;
      const r = 3000 * dpr;
      this.mouse = { radius: r, actualRadius: Math.sqrt(r), x: -1e3, y: -1e3, isActive: false, timeout: null };
      this.canvasOffset = { left: 0, top: 0 };
      this.updateOffset = () => {
        const rct = canvas.getBoundingClientRect();
        this.canvasOffset.left = rct.left + window.scrollX;
        this.canvasOffset.top = rct.top + window.scrollY;
      };
      this.updateOffset();
      this.handleMouseMove = e => {
        this.mouse.x = (e.pageX - this.canvasOffset.left) * this.dpr;
        this.mouse.y = (e.pageY - this.canvasOffset.top) * this.dpr;
        this.mouse.isActive = true;
        clearTimeout(this.mouse.timeout);
        this.mouse.timeout = setTimeout(() => { this.mouse.isActive = false; }, 100);
      };
      window.addEventListener('mousemove', this.handleMouseMove);
      this.loadImage().then(() => this.init());
    }
    loadImage() {
      return new Promise(res => {
        let src = '';
        if (this.config.imageSelector) {
          const im = document.querySelector(this.config.imageSelector);
          if (im) src = im.src;
        }
        if (!src) return res();
        this.image = new Image();
        this.image.crossOrigin = 'Anonymous';
        this.image.src = src;
        this.image.onload = res;
        this.image.onerror = () => res();
      });
    }
    resize(w, h, pw, ph) {
      this.width = w; this.height = h;
      if (pw) this.parentW = pw; if (ph) this.parentH = ph;
      this.updateOffset(); this.init();
    }
    init() {
      this.particlesArray = [];
      if (!this.image) return;
      const iw = this.image.width || this.image.naturalWidth || 300;
      const ih = this.image.height || this.image.naturalHeight || 150;
      const scale = Math.min(this.parentW / iw, this.parentH / ih) * (this.config.scale || .8);
      const dw = iw * scale, dh = ih * scale;
      const ox = (this.width - dw) / 2, oy = (this.height - dh) / 2;
      this.ctx.clearRect(0, 0, this.width, this.height);
      this.ctx.drawImage(this.image, ox, oy, dw, dh);
      const data = this.ctx.getImageData(0, 0, this.width, this.height);
      this.ctx.clearRect(0, 0, this.width, this.height);
      const y0 = Math.max(0, Math.floor(oy)), y1 = Math.min(this.height, Math.ceil(oy + dh));
      const x0 = Math.max(0, Math.floor(ox)), x1 = Math.min(this.width, Math.ceil(ox + dw));
      for (let y = y0; y < y1; y += this.gap)
        for (let x = x0; x < x1; x += this.gap) {
          const i = 4 * (y * this.width + x);
          const r = data.data[i], g = data.data[i + 1], b = data.data[i + 2], a = data.data[i + 3];
          if (a > 0) this.particlesArray.push(new Particle(x, y, this, `rgba(${r}, ${g}, ${b}, ${a / 255})`, this.dpr));
        }
    }
    update() {
      this.ctx.clearRect(0, 0, this.width, this.height);
      for (let i = 0; i < this.particlesArray.length; i++) this.particlesArray[i].update();
    }
    destroy() { window.removeEventListener('mousemove', this.handleMouseMove); clearTimeout(this.mouse.timeout); }
  }

  class ParticleText {
    constructor(canvas, configIn = {}) {
      this.canvas = typeof canvas === 'string' ? document.querySelector(canvas) : canvas;
      if (!this.canvas) return;
      this.config = { color: '#A0A0A0', scale: 1, ...configIn };
      this.dpr = window.devicePixelRatio || 1;
      this.resize();
      this.effect = new ParticleEffect(this.canvas, this.config, this.dpr, this.parentW, this.parentH);
      this.handleResize = () => {
        this.resize();
        this.effect.resize(this.canvas.width, this.canvas.height, this.parentW, this.parentH);
      };
      window.addEventListener('resize', this.handleResize);
      this.animate = this.animate.bind(this);
      this.observer = new IntersectionObserver(es => {
        es.forEach(en => {
          if (en.isIntersecting) gsap.ticker.add(this.animate);
          else gsap.ticker.remove(this.animate);
        });
      });
      this.observer.observe(this.canvas);
    }
    resize() {
      const par = this.canvas.parentNode || document.body;
      const w = par.clientWidth || window.innerWidth;
      const h = par.clientHeight || window.innerHeight;
      this.parentW = w * this.dpr; this.parentH = h * this.dpr;
      const cw = 1.5 * w, ch = 3 * h;
      this.canvas.width = cw * this.dpr;
      this.canvas.height = ch * this.dpr;
      this.canvas.style.width = `${cw}px`;
      this.canvas.style.height = `${ch}px`;
    }
    animate() { this.effect.update(); }
  }

  if (window.innerWidth > 991) {
    const pc = el.querySelector('#footer-particle-canvas');
    if (pc) new ParticleText(pc, { imageSelector: '#source-image-footer', color: '#A0A0A0', scale: 1 });
  }

  // ---------- info marquees (ft) ----------
  const setupMarquee = list => {
    const first = list.querySelector('[data-marquee="item"]');
    if (!first) return;
    const clone = first.cloneNode(true);
    const w = first.getBoundingClientRect().width;
    if (!w || w <= 0) return;
    const target = Math.max(window.innerWidth, list.getBoundingClientRect().width || 0);
    const count = Math.ceil(target / w) + 1;
    list.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const c = clone.cloneNode(true);
      c.style.animationDuration = `${Math.ceil(w / 40)}s`;
      c.classList.add('anim-marquee');
      list.appendChild(c);
    }
  };
  el.querySelectorAll('.footer-info-text-list').forEach(l => setupMarquee(l));

  // ---------- info switcher (kt) ----------
  const btns = [...el.querySelectorAll('.footer-info-btn')];
  const texts = [...el.querySelectorAll('.footer-info-text-inner')];
  const activeBg = el.querySelector('.footer-info-active');
  const updateActiveBg = (i = 0) => {
    if (!activeBg) return;
    const xp = 100 * i;
    const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });
    tl.to(activeBg, { xPercent: xp, duration: .45 }, 0)
      .to(activeBg, { scaleX: .95, scaleY: .85, duration: .2 }, 0)
      .to(activeBg, { scaleX: 1, scaleY: 1, duration: .3 }, .2);
  };
  const switchTab = i => {
    btns.forEach((b, n) => n === i ? b.classList.add('active') : b.classList.remove('active'));
    texts.forEach((t, n) => n === i ? t.classList.add('active') : t.classList.remove('active'));
    updateActiveBg(i);
  };
  if (btns.length) {
    btns.forEach((b, i) => b.addEventListener('click', e => { e.preventDefault(); switchTab(i); }));
    if (activeBg) {
      const idx = btns.findIndex(b => b.classList.contains('active'));
      const n = idx !== -1 ? idx : 0;
      gsap.set(activeBg, { xPercent: 100 * n, scaleX: 1, scaleY: 1 });
    }
  }

  // ---------- reveals (Nt groups with mt / Mt / St) ----------
  // mt: split-line sweep via --bg-progress (embedded block #4 css)
  const mtReveal = (node, delay = 0) => {
    if (!node || !node.textContent) return null;
    const html = node.innerHTML;
    // NOTE: no width pinning here. The live sets width = offsetWidth+5 first, but we run at
    // boot (fonts/loader pending) where offsetWidth is tiny and the pin wraps the text into a
    // tall column. The pin is a reflow micro-optimization only; skip it.
    node.innerHTML = `<span class="split-line-p" style="--color-final: currentColor"><span>${html}</span></span>`;
    const span = node.firstElementChild;
    gsap.set(span, { '--bg-progress': 30 });
    return {
      animation: gsap.to(span, {
        '--bg-progress': 100, duration: 1.2, ease: 'power1.inOut',
        onComplete: () => { node.innerHTML = html; }
      }),
      delay
    };
  };
  // Mt: line grow
  const mtLine = (node, delay = 0, isCenter = false) => {
    if (!node) return null;
    gsap.set(node, { scaleX: 0, transformOrigin: isCenter ? 'center center' : 'top left' });
    return { animation: gsap.to(node, { scaleX: 1, duration: 1.2, ease: 'power1.inOut' }), delay };
  };
  // St: rise from y
  const stRise = (node, delay = 0, y = '0.5rem') => {
    if (!node) return null;
    gsap.set(node, { y });
    return { animation: gsap.to(node, { y: 0, duration: 1.2, ease: 'power1.inOut' }), delay };
  };
  const group = (triggerEl, items) => {
    if (!triggerEl) return;
    const specs = items.filter(Boolean);
    if (!specs.length) return;
    ST.create({
      trigger: triggerEl, start: 'top bottom', once: true,
      onEnter: () => {
        const tl = gsap.timeline();
        specs.forEach((s, i) => tl.add(s.animation, i === 0 ? 0 : `-=${1.2 - (s.delay || .1)}`));
      }
    });
  };
  group(el.querySelector('.footer-sub'), [mtReveal(el.querySelector('.footer-sub .txt'))]);
  group(el.querySelector('.footer-menu'), [
    mtLine(el.querySelector('.footer-menu .footer-menu-line')),
    ...['.footer-menu .footer-label .txt', '.footer-menu .footer-link .txt'].flatMap(sel =>
      [...el.querySelectorAll(sel)].map(n => mtReveal(n, .1))),
    mtReveal(el.querySelector('.footer-content-payment-desc .txt'), .15),
    stRise(el.querySelector('.footer-content-payment-ic-wrap'), .1)
  ]);
  if (window.innerWidth > 768) {
    group(el.querySelector('.footer-menu'), [
      mtReveal(el.querySelector('.footer-socials .footer-label .txt')),
      mtReveal(el.querySelector('.footer-socials .footer-link .txt'))
    ]);
  }
}
