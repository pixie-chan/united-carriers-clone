#!/usr/bin/env python3
"""Ship/ocean water check: fresh paired capture (live mirror vs rebuild) at 1920x1080.

Shoots the same phases (f = viewport heights into the why section) on both pages,
prints pixel probes at fixed coordinates plus the ship DOM rect per phase,
and writes reference|rebuild composites for visual review.

Run:  python3 ship-water-check.py
"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/shipqa7'
REB = 'http://127.0.0.1:8898/index.html'
LIVE = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
PHASES = [2.0, 3.5, 5.0, 6.5]
os.makedirs(OUT, exist_ok=True)


def shoot(url, tag):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1920, 'height': 1080}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:150]))
        page.goto(url, wait_until='load', timeout=120000)
        page.wait_for_timeout(9000)
        top = page.evaluate(
            "(document.querySelector('.home-why-wrap') || document.querySelector('.home-why'))"
            ".getBoundingClientRect().top + scrollY")
        rects = {}
        for f in PHASES:
            page.evaluate(f'window.scrollTo(0, {int(top + f * 1080)})')
            page.wait_for_timeout(1800)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
            r = page.evaluate(
                "(() => { const el = document.querySelector('.home-why-ship-img');"
                "   if (!el) return null; const b = el.getBoundingClientRect();"
                "   return {w: Math.round(b.width), h: Math.round(b.height),"
                "           top: Math.round(b.top), left: Math.round(b.left)}; })()")
            rects[f] = r
        b.close()
        return errs, rects


e_live, r_live = shoot(LIVE, 'live')
e_reb, r_reb = shoot(REB, 'reb')
print('live errors:', e_live)
print('reb  errors:', e_reb)

print('--- ship .home-why-ship-img rect per phase ---')
for f in PHASES:
    print(f'  f={f}: live={r_live[f]}  reb={r_reb[f]}')

print('--- pixel probes ---')
for f in PHASES:
    a = Image.open(f'{OUT}/live-f{f}.png').convert('RGB')
    c = Image.open(f'{OUT}/reb-f{f}.png').convert('RGB')
    print(f'  f={f}:')
    for pt in [(100, 900), (1800, 100), (500, 700), (1450, 450), (960, 540)]:
        print(f'    {pt} live={a.getpixel(pt)} reb={c.getpixel(pt)}')

for f in PHASES:
    a = Image.open(f'{OUT}/live-f{f}.png').convert('RGB')
    c = Image.open(f'{OUT}/reb-f{f}.png').convert('RGB')
    w, h = 960, 540
    comp = Image.new('RGB', (w * 2 + 4, h + 22), 'white')
    comp.paste(a.resize((w, h)), (0, 22))
    comp.paste(c.resize((w, h)), (w + 4, 22))
    ImageDraw.Draw(comp).text((8, 5), f'LEFT=live RIGHT=rebuild f={f}', fill='black')
    comp.save(f'{OUT}/cmp-f{f}.png')
print('done ->', OUT)
