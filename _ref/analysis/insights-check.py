#!/usr/bin/env python3
"""Insights section QA: geometry, reveal states, hover sync, pixel diffs."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/insights'
import os
os.makedirs(OUT, exist_ok=True)


def run(url, tag, wait):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:150]))
        page.goto(url, wait_until='load', timeout=180000)
        page.wait_for_timeout(wait)
        geo = page.evaluate("""(() => {
          const q = s => { const el = document.querySelector(s); if (!el) return null;
            const r = el.getBoundingClientRect(); return {top: Math.round(r.top + scrollY), h: Math.round(r.height)}; };
          return { wrap: q('.home-ins-wrap'), sec: q('.home-ins'), items: document.querySelectorAll('.home-ins-cms-item').length,
                   thumbs: document.querySelectorAll('.home-ins-cms-thumb-item').length, docH: document.body.scrollHeight }; })()""")
        top = geo['wrap']['top']

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})'); page.wait_for_timeout(80)
            page.evaluate(f'window.scrollTo(0, {int(t)})'); page.wait_for_timeout(60)

        states = {}
        for f in [-0.8, -0.3, 0.3, 0.9]:
            stepped(int(top + f * 900))
            page.wait_for_timeout(1300)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
            states[f] = page.evaluate("""(() => {
              const g = s => { const el = document.querySelector(s); if (!el) return null;
                const c = getComputedStyle(el);
                return [+(+c.opacity).toFixed(2), c.transform === 'none' ? 'none' : c.transform.slice(0, 26)]; };
              return { action: g('.home-ins-action'), main: g('.home-ins-main') }; })()""")
        # hover sync test (at f=0.3)
        stepped(int(top + 0.3 * 900)); page.wait_for_timeout(800)
        r = page.evaluate("""(() => { const it = document.querySelectorAll('.home-ins-cms-item')[2];
          const rc = it.getBoundingClientRect(); return [Math.round(rc.left + rc.width / 2), Math.round(rc.top + rc.height / 2)]; })()""")
        page.mouse.move(r[0], r[1], steps=6)
        page.wait_for_timeout(700)
        hover = page.evaluate("""(() => {
          const items = [...document.querySelectorAll('.home-ins-cms-item')].map(e => e.className.includes('active'));
          const thumbs = [...document.querySelectorAll('.home-ins-cms-thumb-item')].map(e => e.className.includes('active'));
          return { items, thumbs }; })()""")
        page.screenshot(path=f'{OUT}/{tag}-hover.png')
        b.close()
        return geo, states, hover, errs


lg, ls, lh, le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
rg, rs, rh, re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('GEO live:', lg)
print('GEO reb :', rg)
print('states live:', ls)
print('states reb :', rs)
print('hover live:', lh)
print('hover reb :', rh)
print('errors:', {'live': le[:3], 'reb': re_[:3]})
for f in [-0.8, -0.3, 0.3, 0.9]:
    a = np.asarray(Image.open(f'{OUT}/live-f{f}.png').convert('RGB'), dtype=float)
    c = np.asarray(Image.open(f'{OUT}/reb-f{f}.png').convert('RGB'), dtype=float)
    print(f'f={f}: mean abs pixel diff = {np.abs(a - c).mean():.1f}')
