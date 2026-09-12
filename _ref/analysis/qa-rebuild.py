#!/usr/bin/env python3
"""QA the rebuild: screenshots at key scroll offsets + diff vs live captures."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw

URL = 'http://127.0.0.1:8898/index.html'
BASE = '/home/zen/projects/united-carriers-clone/_ref/analysis'
OUT = f'{BASE}/qa'
LIVE = f'{BASE}/verify'
YS = [0, 1800, 3220, 4200, 13000]
os.makedirs(OUT, exist_ok=True)

errors, bad = [], []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)[:200]))
    page.on('response', lambda r: bad.append((r.status, r.url[-90:])) if r.status >= 400 else None)
    page.goto(URL, wait_until='load', timeout=60000)
    page.wait_for_timeout(9000)
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(1500)
        page.screenshot(path=f'{OUT}/r-y{y}.png')
    probe = page.evaluate("""() => ({
      loaderGone: !document.querySelector('.loader'),
      scrollH: document.body.scrollHeight,
      sections: [...document.querySelectorAll('section')].map(s => ({ cls: s.className, y: Math.round(s.getBoundingClientRect().top + scrollY), h: Math.round(s.getBoundingClientRect().height) })),
      fonts: document.fonts.status
    })""")
    print('probe:', {k: probe[k] for k in ('loaderGone', 'scrollH', 'fonts')})
    for s in probe['sections']:
        print('  sec:', s)
    print('console errors:', len(errors))
    for e in errors[:12]:
        print('  E', e[:170])
    print('HTTP>=400:', len(bad))
    for s, u in bad[:8]:
        print('  B', s, u)
    b.close()

print()
print('  y        diff>16   diff>48')
for y in YS:
    lp = f'{LIVE}/live-y{y}.png'
    if not os.path.exists(lp):
        print(f'  {y:<8} (no live capture at this offset)')
        continue
    a = Image.open(lp).convert('RGB')
    c = Image.open(f'{OUT}/r-y{y}.png').convert('RGB')
    d = ImageChops.difference(a, c)
    h = d.convert('L').histogram()
    tot = a.size[0] * a.size[1]
    print(f'  {y:<8} {sum(h[16:]) / tot * 100:6.2f}%   {sum(h[48:]) / tot * 100:6.2f}%')
    comp = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    comp.paste(a, (0, 0))
    comp.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(comp).text((12, a.size[1] + 10), f'TOP = live    BOTTOM = rebuild    scrollY={y}', fill='black')
    comp.save(f'{OUT}/cmp-r-y{y}.png')
print('composites in', OUT)
