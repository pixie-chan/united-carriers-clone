#!/usr/bin/env python3
"""Fine sweep 0..7.5vh through .home-service on both sites; build labeled contact sheets."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/sweep'
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
PHASES = [i * 0.5 for i in range(16)]  # 0 .. 7.5 vh

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
            page.wait_for_timeout(1500)
            page.screenshot(path=f'{OUT}/{prefix}-f{f:04.1f}.png')
            print(prefix, f, 'scrollY', page.evaluate('Math.round(scrollY)'), flush=True)
        b.close()

run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live')
run('http://127.0.0.1:8898/index.html', 'reb')

for prefix in ('live', 'reb'):
    cols, rows = 4, 4
    tw, th = 480, 270
    sheet = Image.new('RGB', (cols * tw, rows * (th + 18)), 'white')
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(PHASES):
        im = Image.open(f'{OUT}/{prefix}-f{f:04.1f}.png').resize((tw, th))
        x = (i % cols) * tw; y = (i // cols) * (th + 18)
        sheet.paste(im, (x, y + 18))
        d.text((x + 6, y + 4), f'{prefix} f={f:.1f}vh', fill='black')
    sheet.save(f'{OUT}/sheet-{prefix}.png')
    print('sheet', f'{OUT}/sheet-{prefix}.png')
