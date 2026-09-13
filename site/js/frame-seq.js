// FrameSequence: canvas image-sequence player, ported from the live bundle's
// frame-sequence module (windowed loading, progressive, lerped playhead, cover/contain fit).
// Frames resolve to local files: assets/frames/<basename>.
import { SEQ } from './service-frames.js';

const memCache = new Map();   // url -> HTMLImageElement
const pending = new Map();    // url -> Promise

export function clearFrameSequenceCache() {
  memCache.forEach(im => { im.onload = null; im.onerror = null; im.src = ''; });
  memCache.clear();
  pending.clear();
}

export function getFrameUrls(entries, skipOdd = false) {
  if (!Array.isArray(entries)) return [];
  const filterOdd = !!skipOdd;
  const step = filterOdd ? 2 : 1;
  let out = entries;
  if (step > 1) {
    out = entries.filter((name, i) => {
      const m = String(name).match(/\d+$/);
      if (m) return parseInt(m[0], 10) % step === 0;
      return i % step === 0;
    });
  }
  return out.map(name => `assets/frames/${name}`);
}

export class FrameSequence {
  constructor(opts) {
    const gsap = window.gsap;
    this.canvas = opts.canvas;
    this.ctx = this.canvas.getContext('2d');
    this.frameURLs = opts.frames || [];
    this.scrollTriggerVars = opts.scrollTrigger || {};
    this.fit = opts.fit || 'cover';
    this.concurrency = opts.concurrency || 6;
    this.progressive = opts.progressive !== false;
    this.onReady = opts.onReady || null;
    this.onProgress = opts.onProgress || null;
    this.autoResize = opts.autoResize !== false;
    this.clear = opts.clear || false;
    this.lerpFactor = opts.lerp || 0.15;
    this.cacheRadius = opts.cacheRadius || 6;
    this.loadTimeout = opts.loadTimeout || 10000;
    this.windowed = opts.windowed === true;
    this.images = new Array(this.frameURLs.length);
    this.loadedSet = new Set();
    this.totalFrames = this.frameURLs.length;
    this.playhead = { frame: 0 };
    this.currentFrame = -1;
    this.isReady = false;
    this._destroyed = false;
    this._targetFrame = 0;
    this._displayFrame = 0;
    this._boundTick = this._tick.bind(this);
    this._lastRenderedRawFrame = -1;
    this._firstFrameReady = false;
    this._loadQueue = [];
    this._queuedFrames = new Set();
    this._pendingFrames = new Set();
    this._activeLoads = 0;
    this._tween = null;
    this._st = null;
    this._resizeObserver = null;
    this._setupCanvas();
    this._initScrollAnimation();
    this._preloadFrames();
  }

  _setupCanvas() {
    this._updateCanvasSize();
    if (this.autoResize) {
      this._resizeObserver = new ResizeObserver(() => {
        this._updateCanvasSize();
        this.currentFrame = -1;
        this._render();
        clearTimeout(this._resizeTimer);
        this._resizeTimer = setTimeout(() => { this._st && this._st.refresh(); }, 200);
      });
      this._resizeObserver.observe(this.canvas);
    }
  }

  _updateCanvasSize() {
    const dpr = window.devicePixelRatio || 1;
    const r = this.canvas.getBoundingClientRect();
    this.canvas.width = Math.max(2, r.width * dpr);
    this.canvas.height = Math.max(2, r.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this._displayWidth = r.width;
    this._displayHeight = r.height;
  }

  _preloadFrames() {
    if (this.totalFrames === 0) return;
    if (this.windowed) this._ensureFramesAround(this._targetFrame);
    else for (let i = 0; i < this.totalFrames; i++) this._queueFrame(i);
  }

  _queueFrame(i, front = false) {
    if (i < 0 || i >= this.totalFrames) return;
    if (this.loadedSet.has(i) || this._pendingFrames.has(i) || this._queuedFrames.has(i)) return;
    this._queuedFrames.add(i);
    if (front) this._loadQueue.unshift(i); else this._loadQueue.push(i);
    this._pumpLoadQueue();
  }

  _ensureFramesAround(frame) {
    if (!this.windowed) return;
    const t = Math.max(0, Math.min(Math.round(frame), this.totalFrames - 1));
    const dv = frame - (this._lastTargetFrame ?? frame);
    this._lastTargetFrame = frame;
    this._scrollVelocity = 0.7 * (this._scrollVelocity ?? 0) + 0.3 * dv;
    const vel = Math.abs(this._scrollVelocity);
    const r = Math.max(this.cacheRadius || 12, Math.min(45, Math.round(12 + 12 * vel)));
    let ahead, behind;
    if (this._scrollVelocity > 0.1) { ahead = Math.round(1.5 * r); behind = Math.round(0.3 * r); }
    else if (this._scrollVelocity < -0.1) { ahead = Math.round(0.3 * r); behind = Math.round(1.5 * r); }
    else { ahead = r; behind = r; }
    this._activeLookaheadRadius = Math.max(ahead, behind);
    this._queueFrame(t, true);
    const stride = vel > 2.5 ? 2 : 1;
    for (let i = 1; i <= ahead; i += stride) this._queueFrame(t + i);
    for (let i = 1; i <= behind; i += stride) this._queueFrame(t - i);
    this._evictFarFrames(t, Math.max(60, 2.5 * r));
  }

  _pumpLoadQueue() {
    while (!this._destroyed && this._activeLoads < this.concurrency && this._loadQueue.length) {
      const i = this._loadQueue.shift();
      this._queuedFrames.delete(i);
      const t = Math.round(this._targetFrame);
      const lookahead = this._activeLookaheadRadius || 45;
      if (this.windowed && this._firstFrameReady && Math.abs(i - t) > lookahead) continue;
      this._activeLoads++;
      this._pendingFrames.add(i);
      this._loadFrameWithRetry(i).then(img => {
        if (!img || this._destroyed) return;
        this.images[i] = img;
        this.loadedSet.add(i);
        this.onProgress && this.onProgress(this.loadedSet.size, this.totalFrames);
        if (!this._firstFrameReady) { this._firstFrameReady = true; this.isReady = true; this.currentFrame = -1; this._render(); }
        if (Math.floor(this._targetFrame) === i) { this._lastRenderedRawFrame = -1; this._render(); }
        this._evictFarFrames(Math.round(this._targetFrame));
      }).catch(() => {}).finally(() => {
        this._activeLoads--;
        this._pendingFrames.delete(i);
        this._pumpLoadQueue();
      });
    }
  }

  async _loadFrameWithRetry(i) {
    for (let attempt = 0; attempt < 2; attempt++) {
      try { return await this._loadFrameOnce(i); }
      catch (e) { if (attempt === 1) throw e; }
    }
    return null;
  }

  _loadFrameOnce(i) {
    const url = this.frameURLs[i];
    if (!url) return Promise.resolve(null);
    const cached = memCache.get(url);
    if (cached && cached.complete && cached.naturalWidth > 0) return Promise.resolve(cached);
    if (pending.has(url)) return pending.get(url);
    const p = new Promise((resolve, reject) => {
      if (this._destroyed) return resolve(null);
      const im = new Image();
      im.crossOrigin = 'anonymous';
      let done = false;
      const finish = (fn, v) => { if (!done) { done = true; clearTimeout(to); im.onload = null; im.onerror = null; pending.delete(url); fn(v); } };
      const to = setTimeout(() => { im.src = ''; finish(reject, new Error('timeout')); }, this.loadTimeout);
      im.onload = () => { if (im.naturalWidth > 0) memCache.set(url, im); finish(resolve, im); };
      im.onerror = () => finish(reject, new Error('image error'));
      im.src = url;
    });
    pending.set(url, p);
    return p;
  }

  _evictFarFrames(center, keep = 50) {
    if (!this.windowed) return;
    this.loadedSet.forEach(i => {
      if (Math.abs(i - center) <= keep) return;
      const im = this.images[i];
      if (im) {
        im.onload = null; im.onerror = null;
        const url = this.frameURLs[i];
        if (!(url && memCache.has(url))) im.src = '';
      }
      this.images[i] = null;
      this.loadedSet.delete(i);
    });
  }

  _initScrollAnimation() {
    const gsap = window.gsap;
    this._tween = gsap.to(this.playhead, {
      frame: this.totalFrames - 1,
      ease: 'none',
      scrollTrigger: {
        ...this.scrollTriggerVars,
        onUpdate: () => {
          this._targetFrame = this.playhead.frame;
          if (this.windowed) this._ensureFramesAround(this._targetFrame);
          this._startLerpLoop();
        }
      }
    });
    this._st = this._tween.scrollTrigger;
  }

  _startLerpLoop() {
    if (this._isLerping) return;
    this._isLerping = true;
    window.gsap.ticker.add(this._boundTick);
  }

  _tick() {
    if (this._destroyed) return;
    const d = this._targetFrame - this._displayFrame;
    const ad = Math.abs(d);
    if (ad < 0.05) {
      this._displayFrame = this._targetFrame;
      this._renderFrame(this._displayFrame);
      this._isLerping = false;
      window.gsap.ticker.remove(this._boundTick);
      return;
    }
    const k = this.lerpFactor + (1 - this.lerpFactor) * Math.min(1, ad / 1.5);
    this._displayFrame += d * k;
    this._renderFrame(this._displayFrame);
  }

  _renderFrame(f) {
    if (this.totalFrames === 0) return;
    const t = Math.max(0, Math.min(f, this.totalFrames - 1));
    const idx = Math.floor(t);
    if (this._lastRenderedRawFrame === idx) return;
    const img = this._getReadyImage(idx);
    if (!img) { this._ensureFramesAround(idx); return; }
    const ctx = this.ctx;
    const w = this._displayWidth, h = this._displayHeight;
    if (!w || !h) return;
    if (this.clear) ctx.clearRect(0, 0, w, h);
    const p = this._computeDrawParams(img.naturalWidth, img.naturalHeight, w, h);
    ctx.globalAlpha = 1;
    ctx.drawImage(img, p.sx, p.sy, p.sw, p.sh, p.dx, p.dy, p.dw, p.dh);
    this._lastRenderedRawFrame = idx;
  }

  _render() { this._renderFrame(this._displayFrame); }

  _getReadyImage(i) {
    const im = this.images[i];
    if (im && im.complete && im.naturalWidth > 0) return im;
    const best = this._findBestFrame(i);
    return best !== -1 ? this.images[best] : null;
  }

  _findBestFrame(i) {
    for (let d = 1; d < this.totalFrames; d++) {
      const lo = i - d, hi = i + d;
      if (lo >= 0) { const im = this.images[lo]; if (im && im.complete && im.naturalWidth > 0) return lo; }
      if (hi < this.totalFrames) { const im = this.images[hi]; if (im && im.complete && im.naturalWidth > 0) return hi; }
    }
    return -1;
  }

  _computeDrawParams(iw, ih, w, h) {
    const ir = iw / ih, cr = w / h;
    if (this.fit === 'cover') {
      if (ir > cr) {
        const sw = ih * cr;
        return { sx: (iw - sw) / 2, sy: 0, sw, sh: ih, dx: 0, dy: 0, dw: w, dh: h };
      }
      const sh = iw / cr;
      return { sx: 0, sy: (ih - sh) / 2, sw: iw, sh, dx: 0, dy: 0, dw: w, dh: h };
    }
    if (ir > cr) {
      const dh = w / ir;
      return { sx: 0, sy: 0, sw: iw, sh: ih, dx: 0, dy: (h - dh) / 2, dw: w, dh };
    }
    const dw = h * ir;
    return { sx: 0, sy: 0, sw: iw, sh: ih, dx: (w - dw) / 2, dy: 0, dw, dh: h };
  }

  goToFrame(f) {
    this.playhead.frame = Math.max(0, Math.min(f, this.totalFrames - 1));
    this._render();
  }

  get progress() {
    return this.totalFrames > 1 ? this.playhead.frame / (this.totalFrames - 1) : 0;
  }

  get loadedCount() { return this.loadedSet.size; }

  refresh(stVars = null) {
    if (stVars) {
      if (this._tween) { this._tween.revert(); this._tween.kill(); }
      if (this._st) this._st.kill();
      this.scrollTriggerVars = stVars;
      this._initScrollAnimation();
    } else if (this._st) this._st.refresh();
    this._updateCanvasSize();
    this.currentFrame = -1;
    this._render();
  }

  destroy() {
    this._destroyed = true;
    if (this._boundTick) window.gsap.ticker.remove(this._boundTick);
    clearTimeout(this._resizeTimer);
    if (this._tween) this._tween.kill();
    if (this._st) this._st.kill();
    if (this._resizeObserver) { this._resizeObserver.disconnect(); this._resizeObserver = null; }
    this.images.forEach((im, i) => {
      if (im) {
        im.onload = null; im.onerror = null;
        const url = this.frameURLs[i];
        if (!(url && memCache.has(url))) im.src = '';
      }
    });
    this.images = [];
    this.loadedSet.clear();
    this._loadQueue = [];
    this._queuedFrames.clear();
    this._pendingFrames.clear();
    if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.isReady = false;
    this.currentFrame = -1;
  }
}
