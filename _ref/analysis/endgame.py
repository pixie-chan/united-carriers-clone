#!/usr/bin/env python3
"""Endgame map: both sites swept f=5..15 step ~0.5; contact sheets per site (2 rows x N)."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/endgame'
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
PHASES = [5.0, 5.5, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5, 8.0, 8.5, 9.0, 10.0, 11.0, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0]

def run(url, prefix):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': W, 'height': H}).new_page()
        page.goto(url, wait_until='load', timeout=120000)
        page.wait_for_timeout(9000)
        svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
        for f in PHASES:
            y = int(svcTop + f * H)
            page.evaluate(f'window.scrollTo(0, {y})')
            page.wait_for_timeout(1300)
            page.screenshot(path=f'{OUT}/{prefix}-f{f:04.1f}.png')
            print(prefix, f, flush=True)
        b.close()

run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live')
run('http://127.0.0.1:8898/index.html', 'reb')

for prefix in ('live', 'reb'):
    cols = 7
    tw, th = 274, 154
    rows = (len(PHASES) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * (th + 16)), 'white')
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(PHASES):
        im = Image.open(f'{OUT}/{prefix}-f{f:04.1f}.png').resize((tw, th))
        x = (i % cols) * tw; y = (i // cols) * (th + 16)
        sheet.paste(im, (x, y + 16))
        d.text((x + 4, y + 3), f'{prefix} f={f}', fill='black')
    sheet.save(f'{OUT}/sheet-{prefix}.png')
    print('sheet', f'{OUT}/sheet-{prefix}.png', sheet.size)
