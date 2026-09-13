#!/usr/bin/env python3
"""1920x1080 paired verification: why water phases + testi timeline parity + geometry.

Stepped scroll (both sides). Live mirror dies on giant instant scroll jumps.
"""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

W, H = 1920, 1080
OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/verify1920'
import os
os.makedirs(OUT, exist_ok=True)


def scroll_stepped(page, target, step=1200, delay=90):
    y = page.evaluate('window.scrollY')
    while abs(y - target) > step:
        y = y + step if target > y else y - step
        page.evaluate(f'window.scrollTo(0, {int(y)})')
        page.wait_for_timeout(delay)
    page.evaluate(f'window.scrollTo(0, {int(target)})')
    page.wait_for_timeout(delay)


def run(url, tag, wait_ms):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': W, 'height': H}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:150]))
        page.goto(url, wait_until='load', timeout=180000)
        page.wait_for_timeout(wait_ms)
        geo = page.evaluate("""(() => {
          const q = s => { const el = document.querySelector(s); if (!el) return null;
            const r = el.getBoundingClientRect(); return {top: Math.round(r.top + scrollY), h: Math.round(r.height)}; };
          return { why: q('.home-why-wrap'), testi: q('.home-testi-wrap'), docH: document.body.scrollHeight }; })()""")
        # why water phases
        wy = geo['why']['top']
        probe = """(() => {
          const gs = (s, p) => { const el = document.querySelector(s); return el ? getComputedStyle(el).getPropertyValue(p).trim() : null; };
          return { clip: gs('.home-testi', '--overlap-clip') }; })()"""
        why_px = {}
        for f in [2.0, 3.5, 5.0]:
            scroll_stepped(page, int(wy + f * H))
            page.wait_for_timeout(1500)
            page.screenshot(path=f'{OUT}/{tag}-why-f{f}.png')
        # testi phases
        ty = geo['testi']['top']
        testi = {}
        for f in [-0.5, 0.3, 0.9, 1.6, 2.4]:
            scroll_stepped(page, int(ty + f * H))
            page.wait_for_timeout(1500)
            page.screenshot(path=f'{OUT}/{tag}-testi-f{f}.png')
            r = page.evaluate(probe)
            img = page.evaluate("""(() => { const el = document.querySelector('.home-testi-plane-img-main img');
              if (!el) return null; const r = el.getBoundingClientRect();
              return { l: Math.round(r.left), w: Math.round(r.width) }; })()""")
            testi[f] = (r['clip'], img)
        b.close()
        return geo, testi, errs


lg, lt, le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
rg, rt, re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('GEO live:', lg)
print('GEO reb :', rg)
print('--- testi timeline (clip / img) ---')
for f in [-0.5, 0.3, 0.9, 1.6, 2.4]:
    print(f'  f={f}: live={lt[f]}  reb={rt[f]}')
print('errors:', {'live': le[:3], 'reb': re_[:3]})

PTS = [(100, 900), (1800, 100), (500, 700), (1450, 450)]
for f in [2.0, 3.5, 5.0]:
    a = np.asarray(Image.open(f'{OUT}/live-why-f{f}.png').convert('RGB'), dtype=int)
    c = np.asarray(Image.open(f'{OUT}/reb-why-f{f}.png').convert('RGB'), dtype=int)
    print(f'--- why f={f} probes ---')
    for (x, y) in PTS:
        print(f'  {x},{y}: live={tuple(a[y, x])} reb={tuple(c[y, x])}')
