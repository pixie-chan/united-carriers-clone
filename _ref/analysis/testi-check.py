#!/usr/bin/env python3
"""Testi section paired capture (live mirror vs rebuild) at a given viewport.

Usage: python3 testi-check.py [width] [height]   (default 1440x900)
Stepped scrolling is mandatory on the live mirror (giant instant jumps kill its engine).
"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

W = int(sys.argv[1]) if len(sys.argv) > 1 else 1440
H = int(sys.argv[2]) if len(sys.argv) > 2 else 900
OUT = f'/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/testi{W}'
os.makedirs(OUT, exist_ok=True)

LIVE = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
REB = 'http://127.0.0.1:8898/index.html'


def scroll_stepped(page, target, step=1200, delay=90):
    y = page.evaluate('window.scrollY')
    while abs(y - target) > step:
        y = y + step if target > y else y - step
        page.evaluate(f'window.scrollTo(0, {int(y)})')
        page.wait_for_timeout(delay)
    page.evaluate(f'window.scrollTo(0, {int(target)})')
    page.wait_for_timeout(delay)


PHASES = [-1.0, -0.5, 0.0, 0.3, 0.6, 0.9, 1.2, 1.6, 2.0, 2.6]


def shoot(url, tag, wait_ms):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': W, 'height': H}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:160]))
        page.on('response', lambda r: errs.append(f'{r.status} {r.url[-60:]}') if r.status >= 400 and '127.0.0.1:8898' not in r.url and 'analytics' not in r.url and 'mixpanel' not in r.url else None)
        page.goto(url, wait_until='load', timeout=180000)
        page.wait_for_timeout(wait_ms)
        top = page.evaluate("(document.querySelector('.home-testi-wrap')||document.querySelector('.home-testi')).getBoundingClientRect().top + scrollY")
        for f in PHASES:
            scroll_stepped(page, int(top + f * H))
            page.wait_for_timeout(1500)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
        b.close()
        return top, errs


ltop, lerr = shoot(LIVE, 'live', 12000)
rtop, rerr = shoot(REB, 'reb', 8000)
print(f'wrapTop live={ltop:.0f} reb={rtop:.0f}  (delta {rtop - ltop:+.0f})')
print('live errors:', lerr[:5])
print('reb  errors:', rerr[:5])

# side-by-side composites at half scale
for f in PHASES:
    a = Image.open(f'{OUT}/live-f{f}.png').convert('RGB')
    c = Image.open(f'{OUT}/reb-f{f}.png').convert('RGB')
    cw, ch = W // 2, H // 2
    comp = Image.new('RGB', (cw * 2 + 4, ch + 22), 'white')
    comp.paste(a.resize((cw, ch)), (0, 22))
    comp.paste(c.resize((cw, ch)), (cw + 4, 22))
    ImageDraw.Draw(comp).text((8, 5), f'LEFT=live RIGHT=rebuild  testi f={f}  {W}x{H}', fill='black')
    comp.save(f'{OUT}/cmp-f{f}.png')
print('composites done ->', OUT)
