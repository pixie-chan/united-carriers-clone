#!/usr/bin/env python3
"""Robust paired ship/ocean check (live mirror vs rebuild) at 1920x1080.

Why robust: the live mirror's engine occasionally dies on load (intermittent
pageerror), freezing the why scrub. This harness waits longer, then VERIFIES the
scrub is alive (the ship DOM width must change between two phases) before
capturing; reloads up to N times otherwise.

Metrics per phase (f = viewport heights into `.home-why-wrap`):
  - ship `.home-why-ship-img` rect on both pages (dolly parity)
  - pixel probes at fixed coordinates (water level parity)
  - reference|rebuild composites written for visual review

Run:  python3 ship-water-check2.py
"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/whypair'
REB = 'http://127.0.0.1:8898/index.html'
LIVE = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
PHASES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
VIEW = {'width': 1920, 'height': 1080}
os.makedirs(OUT, exist_ok=True)

SHIP_W = ("(() => { const el = document.querySelector('.home-why-ship-img');"
          "  return el ? Math.round(el.getBoundingClientRect().width) : null; })()")
SHIP_RECT = ("(() => { const el = document.querySelector('.home-why-ship-img');"
             "  if (!el) return null; const b = el.getBoundingClientRect();"
             "  return {w: Math.round(b.width), h: Math.round(b.height),"
             "          top: Math.round(b.top), left: Math.round(b.left)}; })()")
WRAP_TOP = ("(document.querySelector('.home-why-wrap') || document.querySelector('.home-why'))"
            ".getBoundingClientRect().top + scrollY")


def scroll_stepped(page, target, step=1200, delay=100):
    """Live mirror's engine dies on giant instant scrollTo jumps (reads .end of
    undefined, kills the scrub); stepped scrolling is safe on both pages."""
    y = page.evaluate('window.scrollY')
    while abs(y - target) > step:
        y = y + step if target > y else y - step
        page.evaluate(f'window.scrollTo(0, {int(y)})')
        page.wait_for_timeout(delay)
    page.evaluate(f'window.scrollTo(0, {int(target)})')
    page.wait_for_timeout(delay)


def shoot(url, tag, attempts=3):
    for attempt in range(1, attempts + 1):
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_context(viewport=VIEW).new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)[:200]))
            page.goto(url, wait_until='load', timeout=180000)
            page.wait_for_timeout(13000)
            top = page.evaluate(WRAP_TOP)
            # scrub-alive validation between f=1.0 and f=3.5
            w1 = None
            scroll_stepped(page, int(top + 1.0 * 1080))
            page.wait_for_timeout(1500)
            w1 = page.evaluate(SHIP_W)
            scroll_stepped(page, int(top + 3.5 * 1080))
            page.wait_for_timeout(1500)
            w2 = page.evaluate(SHIP_W)
            alive = (w1 is not None and w2 is not None and abs(w1 - w2) > 5)
            print(f'[{tag}] attempt {attempt}: wrapTop={top:.0f} ship w@1.0={w1} w@3.5={w2} '
                  f'scrub_alive={alive} errors={errs[:2]}')
            if not alive and attempt < attempts:
                b.close()
                continue
            rects = {}
            for f in PHASES:
                scroll_stepped(page, int(top + f * 1080))
                page.wait_for_timeout(1600)
                page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
                rects[f] = page.evaluate(SHIP_RECT)
            b.close()
            return top, rects, errs, alive


top_live, r_live, e_live, alive_live = shoot(LIVE, 'live')
top_reb, r_reb, e_reb, alive_reb = shoot(REB, 'reb')

print(f'\nwrapTop live={top_live:.0f} reb={top_reb:.0f}')
print('--- ship rect per phase ---')
for f in PHASES:
    print(f'  f={f}: live={r_live[f]}')
    print(f'         reb ={r_reb[f]}')

print('--- pixel probes ---')
for f in PHASES:
    a = Image.open(f'{OUT}/live-f{f}.png').convert('RGB')
    c = Image.open(f'{OUT}/reb-f{f}.png').convert('RGB')
    print(f'  f={f}:')
    for pt in [(100, 900), (1800, 100), (500, 700), (1450, 450)]:
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
