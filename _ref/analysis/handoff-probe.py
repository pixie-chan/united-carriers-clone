#!/usr/bin/env python3
"""Why-exit / testi-handoff probe: cloud layer opacities + key pixels at fixed scrolls."""
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image

YS = [18600, 19200, 19800, 20400, 21000]


def shoot(url, tag, wait):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        page.goto(url, wait_until='load', timeout=180000)
        page.wait_for_timeout(wait)

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})')
                page.wait_for_timeout(90)
            page.evaluate(f'window.scrollTo(0, {int(t)})')
            page.wait_for_timeout(300)

        out = {}
        for y in YS:
            stepped(y)
            page.wait_for_timeout(1400)
            page.screenshot(path=f'/tmp/hand-{tag}-{y}.png')
            r = page.evaluate("""(() => {
              const op = s => { const el = document.querySelector(s); return el ? getComputedStyle(el).opacity : null; };
              return { ovBg: op('.home-why-cloud-overlap-bg'), ov: op('.home-why-cloud-overlap'),
                       c3: op('.home-why-cloud-decor-item.cloud-3'), c1: op('.home-why-cloud-decor-item.cloud-1'),
                       c2: op('.home-why-cloud-decor-item.cloud-2') }; })()""")
            out[y] = r
        b.close()
        return out


live = shoot('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
reb = shoot('http://127.0.0.1:8898/index.html', 'reb', 8000)
PTS = [(100, 800), (700, 450), (1200, 450), (960, 830)]
for y in YS:
    print(f'== y={y} ==')
    print('   live:', live[y])
    print('   reb :', reb[y])
    a = np.asarray(Image.open(f'/tmp/hand-live-{y}.png').convert('RGB'), dtype=int)
    c = np.asarray(Image.open(f'/tmp/hand-reb-{y}.png').convert('RGB'), dtype=int)
    for (x, yy) in PTS:
        print(f'    {x},{yy}: live={tuple(a[yy, x])} reb={tuple(c[yy, x])}')
