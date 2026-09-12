#!/usr/bin/env python3
"""Repro pass #2: walk the rebuild at 1920x1080 through the crane (forklift) window and the
ship dolly window, screenshot every step, probe canvas pixel state + console errors."""
import os, json
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2'
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080

PROBE = """
(() => {
  const out = { errors: [] };
  const crane = document.getElementById('craneCanvas');
  const prob = (canvas) => {
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (!ctx) return { w: canvas.width, h: canvas.height, note: 'no 2d ctx' };
    let n = 0, nb = 0;
    try {
      const d = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
      for (let i = 0; i < d.length; i += 4 * 37) { // sparse sample
        n++;
        if (d[i+3] > 8 && (d[i] + d[i+1] + d[i+2]) > 30) nb++;
      }
    } catch (e) { return { w: canvas.width, h: canvas.height, note: String(e).slice(0,80) }; }
    return { w: canvas.width, h: canvas.height, sampled: n, nonblank: nb, pct: +(100*nb/n).toFixed(1) };
  };
  out.scrollY = Math.round(scrollY);
  out.crane = prob(crane);
  const truck = document.getElementById('truckCanvas');
  out.truck = prob(truck);
  const shipImg = document.querySelector('.home-why-ship-img');
  if (shipImg) {
    const r = shipImg.getBoundingClientRect();
    out.ship = { top: Math.round(r.top), left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height),
                 tf: getComputedStyle(shipImg).transform };
  }
  const svc = document.querySelector('.home-service');
  const why = document.querySelector('.home-why');
  if (svc) { const r = svc.getBoundingClientRect(); out.svc = { top: Math.round(r.top), h: Math.round(r.height) }; }
  if (why) { const r = why.getBoundingClientRect(); out.why = { top: Math.round(r.top), h: Math.round(r.height) }; }
  out.pageH = document.body.scrollHeight;
  return out;
})()
"""

def walk(page, prefix, targets):
    rows = []
    for name, y in targets:
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1300)
        state = page.evaluate(PROBE)
        # strip errors key that we don't set here
        shot = f'{OUT}/{prefix}-{name}.png'
        page.screenshot(path=shot)
        rows.append((name, y, state))
        print(f'{prefix} {name} y={y}', json.dumps(state, ensure_ascii=False)[:220], flush=True)
    return rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': W, 'height': H})
    page = ctx.new_page()
    console = []
    page.on('console', lambda m: console.append((m.type, m.text[:180])) if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: console.append(('pageerror', str(e)[:200])))
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=90000)
    page.wait_for_timeout(9000)

    # locate sections
    loc = page.evaluate("""(() => {
      const q = s => { const el = document.querySelector(s); if (!el) return null;
        const r = el.getBoundingClientRect(); return { top: Math.round(r.top + scrollY), h: Math.round(r.height) }; };
      return { svc: q('.home-service'), whyWrap: q('.home-why-wrap'), why: q('.home-why'), tail: q('.uc-tail') };
    })()""")
    print('sections at 1920x1080:', json.dumps(loc), flush=True)
    vh = H
    svcTop = loc['svc']['top'] if loc['svc'] else 0
    wrapTop = loc['whyWrap']['top'] if loc['whyWrap'] else 0

    # service / forklift walk: window = svcTop+1vh .. svcTop+4.5vh (post-fix), sample wider
    svc_targets = []
    for i, f in enumerate([0.4, 0.9, 1.2, 1.6, 2.0, 2.5, 3.0, 3.6, 4.2, 4.6, 5.2, 6.0, 7.0]):
        svc_targets.append((f'svc{i:02d}-{f}vh', int(svcTop + f * vh)))
    walk(page, 'reb', svc_targets)

    # why / ship walk: dolly window = wrapTop+0.267vh .. wrapTop+5.267vh
    why_targets = []
    for i, f in enumerate([0.3, 0.8, 1.3, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8, 5.3, 5.8, 6.4, 7.2]):
        why_targets.append((f'why{i:02d}-{f}vh', int(wrapTop + f * vh)))
    walk(page, 'reb', why_targets)

    b.close()

print('CONSOLE (errors/warnings/pageerrors):', len(console))
for t, m in console[:20]:
    print('  ', t, m)
print('done ->', OUT)
