#!/usr/bin/env python3
"""Partners section QA: geometry, item counts, label widths, reveal states, screenshots."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/partners'
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
            const r = el.getBoundingClientRect(); return {top: Math.round(r.top + scrollY), h: Math.round(r.height), w: Math.round(r.width)}; };
          const lists = [...document.querySelectorAll('.home-partners-list')].map(l => ({
            real: l.querySelectorAll('.home-partners-item:not(.is-empty)').length,
            empty: l.querySelectorAll('.home-partners-item.is-empty').length,
            cols: getComputedStyle(l).gridTemplateColumns.split(' ').length }));
          const lbl = [...document.querySelectorAll('.home-partners-label .txt')].map(el => Math.round(el.getBoundingClientRect().width));
          const cate = [...document.querySelectorAll('.home-partners-cate .txt')].map(el => Math.round(el.getBoundingClientRect().width));
          const item0 = document.querySelector('.home-partners-item');
          const ir = item0 ? item0.getBoundingClientRect() : null;
          return { wrap: q('.home-partners-wrap'), sec: q('.home-partners'),
                   lists, lbl, cate, item0: ir ? {w: Math.round(ir.width), h: Math.round(ir.height)} : null,
                   docH: document.body.scrollHeight }; })()""")
        ptop = geo['wrap']['top']

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})'); page.wait_for_timeout(80)
            page.evaluate(f'window.scrollTo(0, {int(t)})'); page.wait_for_timeout(60)

        states = {}
        for f in [-0.8, -0.2, 0.4, 1.2]:
            stepped(int(ptop + f * 900))
            page.wait_for_timeout(1300)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
            states[f] = page.evaluate("""(() => {
              const it = [...document.querySelectorAll('.home-partners-item')].slice(0, 8).map(el => +(+getComputedStyle(el).opacity).toFixed(2));
              const lbl = document.querySelector('.home-partners-label .txt');
              return { items8: it, lblOp: lbl ? +(+getComputedStyle(lbl).opacity).toFixed(2) : null }; })()""")
        b.close()
        return geo, states, errs


lg, ls, le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
rg, rs, re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('GEO live:', lg)
print('GEO reb :', rg)
print('states live:', ls)
print('states reb :', rs)
print('errors:', {'live': le[:3], 'reb': re_[:3]})

for f in [-0.8, -0.2, 0.4, 1.2]:
    try:
        a = np.asarray(Image.open(f'{OUT}/live-f{f}.png').convert('RGB'), dtype=float)
        c = np.asarray(Image.open(f'{OUT}/reb-f{f}.png').convert('RGB'), dtype=float)
        d = np.abs(a - c).mean()
        print(f'f={f}: mean abs pixel diff = {d:.1f}')
    except FileNotFoundError:
        pass
