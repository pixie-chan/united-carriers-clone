#!/usr/bin/env python3
"""Shoot a site (local mirror or live) at fixed scroll positions for 1:1 comparison."""
import sys, json, os
from playwright.sync_api import sync_playwright

url = sys.argv[1]
prefix = sys.argv[2]
OUT = os.path.dirname(os.path.abspath(__file__)) + '/verify'
os.makedirs(OUT, exist_ok=True)

YS = [0, 1800, 3220, 14160, 19920, 22900, 25300, 27400, 27900]

errors, failed = [], []
bad = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('requestfailed', lambda r: failed.append((r.url[:130], str(r.failure)[:60])))
    page.on('response', lambda r: bad.append((r.status, r.url[:130])) if r.status >= 400 else None)
    page.goto(url, wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    page.screenshot(path=f'{OUT}/{prefix}-y0.png')
    # settle scroll
    for i in range(1, 41):
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(70)
    page.wait_for_timeout(1800)
    for y in YS[1:]:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(1100)
        page.screenshot(path=f'{OUT}/{prefix}-y{y}.png')
    probe = page.evaluate("""() => ({
      loader: !!document.querySelector('.loader'),
      globe: !!document.querySelector('#globe'),
      canvases: document.querySelectorAll('canvas').length,
      sections: document.querySelectorAll('section').length,
      scrollH: document.body.scrollHeight,
      lenis: !!(window.smoothScroll && window.smoothScroll.lenis),
      frames: window.__getFrameCacheStats ? window.__getFrameCacheStats() : null,
    })""")
    print(prefix, 'probe:', json.dumps(probe))
    print(prefix, 'console errors:', len(errors))
    for e in errors[:12]:
        print('   E:', e[:150])
    print(prefix, 'HTTP >=400:', len(bad))
    seenb = set()
    for s, u in bad[:60]:
        k = u.rsplit('/', 1)[-1][:80]
        if (s, k) in seenb:
            continue
        seenb.add((s, k))
        print('   B:', s, u)
    print(prefix, 'failed requests:', len(failed))
    seen = set()
    for u, f in failed[:40]:
        k = u.rsplit('/', 1)[-1][:80]
        if k in seen: continue
        seen.add(k)
        print('   F:', u, '|', f)
    b.close()
print('DONE', prefix)
