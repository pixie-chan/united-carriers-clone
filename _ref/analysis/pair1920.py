#!/usr/bin/env python3
"""Paired captures at 1920x1080: live mirror vs rebuild, service crane window + why ship window."""
import os, json
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/pair'
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080

PROBE = """
(() => {
  const q = s => document.querySelector(s);
  const rect = el => { if (!el) return null; const r = el.getBoundingClientRect();
    return { t: Math.round(r.top), l: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height) }; };
  const ship = q('.home-why-ship-img');
  const crane = q('.home-service-crane') || q('#craneCanvas');
  let shipTf = null, shipScale = null;
  if (ship) {
    shipTf = getComputedStyle(ship).transform;
    const r = ship.getBoundingClientRect();
    shipScale = r.width ? +(r.width / (ship.offsetWidth || r.width)).toFixed(4) : null;
  }
  return {
    scrollY: Math.round(scrollY), pageH: document.body.scrollHeight,
    svcTop: q('.home-service') ? Math.round(q('.home-service').getBoundingClientRect().top + scrollY) : null,
    whyTop: q('.home-why') ? Math.round(q('.home-why').getBoundingClientRect().top + scrollY) : null,
    ship: rect(ship), shipTf, shipScale, crane: rect(crane),
    craneCanvas: (() => { const c = q('.home-service-crane canvas') || q('#craneCanvas');
      return c ? { w: c.width, h: c.height } : null; })()
  };
})()
"""

def run(url, prefix):
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': W, 'height': H}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:150]))
        page.goto(url, wait_until='load', timeout=120000)
        page.wait_for_timeout(9000)
        g = page.evaluate(PROBE)
        print(f'[{prefix}] pageH {g["pageH"]} svcTop {g["svcTop"]} whyTop {g["whyTop"]} crane {g["crane"]} craneCanvas {g["craneCanvas"]}')
        svcTop, whyTop = g['svcTop'], g['whyTop']

        res['service'] = []
        for p_ in [0, .2, .4, .6, .8, 1.0, 1.15]:
            y = int(svcTop + (1 + 3.5 * p_) * H)
            page.evaluate(f'window.scrollTo(0, {y})')
            page.wait_for_timeout(1400)
            s = page.evaluate(PROBE)
            f = f'{OUT}/{prefix}-svc-p{int(p_*100):03d}.png'
            page.screenshot(path=f)
            res['service'].append((p_, y, s))
            print(f'[{prefix}] svc p={p_} y={y} scrollY={s["scrollY"]} crane={json.dumps(s["crane"])}', flush=True)

        res['why'] = []
        for f_ in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5]:
            y = int(whyTop + f_ * H)
            page.evaluate(f'window.scrollTo(0, {y})')
            page.wait_for_timeout(1400)
            s = page.evaluate(PROBE)
            f = f'{OUT}/{prefix}-why-f{str(f_).replace(".","_")}.png'
            page.screenshot(path=f)
            res['why'].append((f_, y, s))
            print(f'[{prefix}] why f={f_} y={y} scrollY={s["scrollY"]} ship={json.dumps(s["ship"])} scale={s["shipScale"]}', flush=True)
        b.close()
    if errs: print(f'[{prefix}] ERRORS:', errs[:3])
    return res

live = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live')
reb = run('http://127.0.0.1:8898/index.html', 'reb')
json.dump({'live': {k: v for k, v in live.items()}, 'reb': {k: v for k, v in reb.items()}},
          open(f'{OUT}/probe.json', 'w'), indent=1, default=str)
print('done ->', OUT)
