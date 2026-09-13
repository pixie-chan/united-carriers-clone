#!/usr/bin/env python3
"""Service section paired QA: stepped scroll through the first/second screens, screenshots + diffs."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/service'
import os
os.makedirs(OUT, exist_ok=True)

ANCHORS = [3300, 4100, 4900, 5700, 6500, 7500, 8500, 9500, 10500, 11400, 12100]


def stepped_scroll(page, target):
    cur = page.evaluate('window.scrollY')
    while abs(cur - target) > 600:
        cur += 600 if target > cur else -600
        page.evaluate(f'window.scrollTo(0, {cur})')
        page.wait_for_timeout(90)
    page.evaluate(f'window.scrollTo(0, {target})')
    page.wait_for_timeout(1100)


def run(url, tag, wait_first):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:130]))
        pg.goto(url, wait_until='load', timeout=60000)
        pg.wait_for_timeout(wait_first)
        for y in ANCHORS:
            stepped_scroll(pg, y)
            pg.screenshot(path=f'{OUT}/{tag}-{y}.png')
        # canvas non-blank checks (sample the drawn canvas)
        canv = pg.evaluate("""(() => {
          const out = {};
          for (const k of ['crane', 'truck']) {
            const c = document.querySelector('.home-service-' + k + '-sq');
            if (!c) { out[k] = null; continue; }
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(0, 0, c.width, c.height).data;
            let n = 0;
            for (let i = 3; i < d.length; i += 4 * 97) { if (d[i] > 0) n++; }
            out[k] = { w: c.width, h: c.height, nonzeroSampled: n };
          }
          return out;
        })()""")
        print(f'{tag}: canvas {canv} | errors {errs[:3]}')
        b.close()


run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
run('http://127.0.0.1:8898/', 'reb', 7000)

for y in ANCHORS:
    a = np.asarray(Image.open(f'{OUT}/live-{y}.png').convert('RGB'), dtype=float)
    c = np.asarray(Image.open(f'{OUT}/reb-{y}.png').convert('RGB'), dtype=float)
    d = np.abs(a - c).mean()
    print(f'y={y}: mean abs pixel diff = {d:.1f}')
