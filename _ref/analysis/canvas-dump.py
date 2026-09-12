#!/usr/bin/env python3
"""Dump crane+truck canvas pixels at scroll steps through the crane window; hash + pair-diff."""
import os, hashlib, json
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/canvas'
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080

DUMP = """
(() => {
  const out = {};
  for (const [k, id] of [['crane','craneCanvas'], ['truck','truckCanvas']]) {
    const c = document.getElementById(id);
    if (!c) { out[k] = null; continue; }
    out[k] = c.toDataURL('image/png');
  }
  out.scrollY = Math.round(scrollY);
  return out;
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:200]))
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=90000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    print('svcTop', svcTop)
    steps = [0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    for f in steps:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1200)
        d = page.evaluate(DUMP)
        for k in ('crane', 'truck'):
            v = d.get(k)
            if v and v.startswith('data:image/png;base64,'):
                raw = v.split(',', 1)[1]
                open(f'{OUT}/{k}-{f}vh.png', 'wb').write(__import__('base64').b64decode(raw))
                print(k, f, 'scrollY', d['scrollY'], 'hash', hashlib.md5(raw.encode()).hexdigest()[:10], 'len', len(raw))
            else:
                print(k, f, 'NO DUMP')
    b.close()
print('errors:', errs[:3])
