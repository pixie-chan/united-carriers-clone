#!/usr/bin/env python3
"""Full-page end-to-end pass: paired screenshots at fixed scrolls, pixel diffs.
Run after all sections exist (page lengths match, no clamp artifacts)."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
import os

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/fullpass'
os.makedirs(OUT, exist_ok=True)
SCROLLS = [450, 4200, 8400, 13000, 16860, 20800, 23375, 25579, 26570, 27300]


def run(url, tag, wait):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:120]))
        page.goto(url, wait_until='load', timeout=180000)
        page.wait_for_timeout(wait)

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})'); page.wait_for_timeout(70)
            page.evaluate(f'window.scrollTo(0, {int(t)})'); page.wait_for_timeout(100)

        for s in SCROLLS:
            stepped(s)
            page.wait_for_timeout(900)
            page.screenshot(path=f'{OUT}/{tag}-{s}.png')
        b.close()
        return errs


le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('errors:', {'live': le[:3], 'reb': re_[:3]})
tot = []
for s in SCROLLS:
    a = np.asarray(Image.open(f'{OUT}/live-{s}.png').convert('RGB'), dtype=float)
    c = np.asarray(Image.open(f'{OUT}/reb-{s}.png').convert('RGB'), dtype=float)
    d = np.abs(a - c).mean()
    tot.append(d)
    print(f'y={s:6d}: mean abs diff = {d:6.1f}')
print(f'OVERALL: mean {np.mean(tot):.1f} | worst {max(tot):.1f}')
