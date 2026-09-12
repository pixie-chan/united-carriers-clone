#!/usr/bin/env python3
"""Verification pass 4: dark sequence + why/ship + tail; composites vs live."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/fixqa4'
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1920, 'height': 1080}).new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:200]))
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    whyTop = page.evaluate("(document.querySelector('.home-why-wrap') || document.querySelector('.home-why')).getBoundingClientRect().top + scrollY")
    for f in [5.5, 6.0, 6.25, 6.5, 7.0, 7.5, 8.5, 9.5, 11.5, 13.0]:
        page.evaluate(f'window.scrollTo(0, {int(svcTop + f*1080)})')
        page.wait_for_timeout(1400)
        page.screenshot(path=f'{OUT}/reb-svc-f{f}.png')
    for f in [1.0, 2.0, 3.5, 5.0, 6.5]:
        page.evaluate(f'window.scrollTo(0, {int(whyTop + f*1080)})')
        page.wait_for_timeout(1700)
        page.screenshot(path=f'{OUT}/reb-why-f{f}.png')
    print('page errors:', errs[:6])
    b.close()

BASE = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2'
PAIRS = [
    (f'{OUT}/reb-svc-f5.5.png', f'{BASE}/endgame/live-f05.5.png', 'svc-5.5'),
    (f'{OUT}/reb-svc-f6.0.png', f'{BASE}/endgame/live-f06.0.png', 'svc-6.0'),
    (f'{OUT}/reb-svc-f6.25.png', f'{BASE}/endgame/live-f06.2.png', 'svc-6.25'),
    (f'{OUT}/reb-svc-f6.5.png', f'{BASE}/endgame/live-f06.5.png', 'svc-6.5'),
    (f'{OUT}/reb-svc-f7.0.png', f'{BASE}/endgame/live-f07.0.png', 'svc-7.0'),
    (f'{OUT}/reb-svc-f8.5.png', f'{BASE}/endgame/live-f08.5.png', 'svc-8.5'),
    (f'{OUT}/reb-svc-f9.5.png', f'{BASE}/endgame/live-f09.0.png', 'svc-9.5vslive9'),
    (f'{OUT}/reb-why-f3.5.png', f'{BASE}/pair/live-why-f3_5.png', 'why-3.5'),
    (f'{OUT}/reb-why-f5.0.png', f'{BASE}/pair/live-why-f5.png', 'why-5.0'),
    (f'{OUT}/reb-why-f6.5.png', f'{BASE}/pair/live-why-f6_5.png', 'why-6.5'),
]
for reb, live, name in PAIRS:
    if not (os.path.exists(reb) and os.path.exists(live)):
        print('skip', name); continue
    a = Image.open(live).convert('RGB'); c = Image.open(reb).convert('RGB')
    m = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    m.paste(a, (0, 0)); m.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(m).text((12, a.size[1] + 10), f'TOP=live BOTTOM=rebuild {name}', fill='black')
    m.save(f'{OUT}/cmp-{name}.png')
print('done ->', OUT)
