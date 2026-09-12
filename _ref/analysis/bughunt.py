#!/usr/bin/env python3
"""Bug hunt shots: hero globe, service scrub states, why ship - rebuild + live side by side."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

SHOTS = [
    ('hero', 0),
    ('svc-a', 3400),
    ('svc-b', 5200),
    ('svc-c', 7000),
    ('svc-d', 9000),
    ('svc-e', 11000),
    ('ship-a', 16060),
    ('ship-b', 17000),
    ('ship-c', 18500),
]
OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/bughunt'
os.makedirs(OUT, exist_ok=True)

def shoot(url, prefix, wait_load):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        page.goto(url, wait_until='load', timeout=60000)
        page.wait_for_timeout(wait_load)
        for name, y in SHOTS:
            page.evaluate(f'window.scrollTo(0,{y})')
            page.wait_for_timeout(1800)
            page.screenshot(path=f'{OUT}/{prefix}-{name}.png')
            print(prefix, name, y)
        b.close()

shoot('http://127.0.0.1:8898/index.html', 'reb', 9000)
shoot('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 9000)

# composites
for name, y in SHOTS:
    a = f'{OUT}/live-{name}.png'; c = f'{OUT}/reb-{name}.png'
    if os.path.exists(a) and os.path.exists(c):
        ia = Image.open(a).convert('RGB'); ic = Image.open(c).convert('RGB')
        comp = Image.new('RGB', (ia.size[0], ia.size[1] * 2 + 34), 'white')
        comp.paste(ia, (0, 0)); comp.paste(ic, (0, ia.size[1] + 34))
        ImageDraw.Draw(comp).text((12, ia.size[1] + 10), f'TOP=live BOTTOM=rebuild y={y}', fill='black')
        comp.save(f'{OUT}/cmp-{name}.png')
print('done ->', OUT)
