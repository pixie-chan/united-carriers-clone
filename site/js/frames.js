// Scroll-scrubbed image sequence player (reimplementation of their FrameSequence concept).
// Windowed preloading, lerped progress, canvas draw with cover fit.

export class FrameSequence {
  constructor({ canvas, frames, base = 'assets/frames/', pad = 12 }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.base = base;
    this.frames = frames;
    this.n = frames.length;
    this.pad = pad;
    this.imgs = new Array(this.n).fill(null);
    this.ready = new Array(this.n).fill(false);
    this.target = 0; this.current = 0; this.lastIndex = -1; this.drawnIndex = -1;
    this.paused = false;

    this._resize = () => {
      const r = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(2, Math.round(r.width * dpr));
      canvas.height = Math.max(2, Math.round(r.height * dpr));
    };
    this._resize();
    window.addEventListener('resize', this._resize);

    this._load(0);
    this._raf = () => this._tick();
    this._running = true;
    requestAnimationFrame(this._raf);
  }

  _load(i) {
    if (i < 0 || i >= this.n || this.imgs[i]) return;
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => { this.ready[i] = true; };
    img.src = this.base + this.frames[i];
    this.imgs[i] = img;
  }

  _window(center) {
    for (let i = center - this.pad; i <= center + this.pad; i++) this._load(i);
  }

  _draw(i) {
    const img = this.imgs[i];
    if (!img || !this.ready[i]) return;
    const cw = this.canvas.width, ch = this.canvas.height;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    if (!iw || !ih) return;
    const s = Math.max(cw / iw, ch / ih);
    const dw = iw * s, dh = ih * s;
    this.ctx.clearRect(0, 0, cw, ch);
    this.ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
  }

  setProgress(p) {
    this.target = Math.min(1, Math.max(0, p));
  }

  _tick() {
    if (!this._running) return;
    this.current += (this.target - this.current) * 0.085;
    if (Math.abs(this.target - this.current) < 0.0006) this.current = this.target;
    const idx = Math.round(this.current * (this.n - 1));
    if (idx !== this.lastIndex) {
      this.lastIndex = idx;
      this._window(idx);
    }
    // (re)draw when the wanted frame changed OR the last draw attempt was a miss
    if (idx !== this.drawnIndex || !this.ready[this.drawnIndex]) {
      if (this.ready[idx]) {
        this._draw(idx);
        this.drawnIndex = idx;
      } else {
        for (let d = 1; d < this.n; d++) {
          if (this.ready[idx - d]) { this._draw(idx - d); this.drawnIndex = idx - d; break; }
          if (this.ready[idx + d]) { this._draw(idx + d); this.drawnIndex = idx + d; break; }
        }
      }
    }
    requestAnimationFrame(this._raf);
  }

  destroy() {
    this._running = false;
    window.removeEventListener('resize', this._resize);
  }
}
