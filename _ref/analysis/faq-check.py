#!/usr/bin/env python3
"""FAQ section QA: geometry, reveal states, accordion click behavior, pixel diffs."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/faq'
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
          return { wrap: q('.home-faq-wrap'), sec: q('.home-faq'),
                   items: document.querySelectorAll('.home-faq-main-item').length, docH: document.body.scrollHeight }; })()""")
        top = geo['wrap']['top']

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})'); page.wait_for_timeout(80)
            page.evaluate(f'window.scrollTo(0, {int(t)})'); page.wait_for_timeout(60)

        states = {}
        for f in [-1.0, -0.4, 0.2, 0.8]:
            stepped(int(top + f * 900))
            page.wait_for_timeout(1300)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
            states[f] = page.evaluate("""(() => {
              const g = s => { const el = document.querySelector(s); if (!el) return null;
                const c = getComputedStyle(el);
                return [+(+c.opacity).toFixed(2), c.transform === 'none' ? 'none' : c.transform.slice(0, 24)]; };
              const h2 = document.querySelector('.home-faq-title .heading');
              const ans0 = document.querySelector('.home-faq-main-item-ans');
              return { main: g('.home-faq-main'),
                       h2Style: h2 ? (h2.getAttribute('style') || 'none').slice(0, 60) : null,
                       ans0: ans0 ? getComputedStyle(ans0).display : null }; })()""")

        # accordion interaction test: click item 1, then item 2
        stepped(int(top + 0.2 * 900)); page.wait_for_timeout(800)
        def click_item(i):
            r = page.evaluate(f"""(() => {{ const it = document.querySelectorAll('.home-faq-main-item')[{i}];
              const tw = it.querySelector('.home-faq-main-item-title-wrap') || it;
              const rc = tw.getBoundingClientRect(); return [Math.round(rc.left + rc.width / 2), Math.round(rc.top + rc.height / 2)]; }})()""")
            page.mouse.click(r[0], r[1])
            page.wait_for_timeout(900)
            return page.evaluate("""(() => {
              const its = [...document.querySelectorAll('.home-faq-main-item')];
              return its.map((it, i) => ({ i, active: it.classList.contains('active'),
                ans: (a => a ? getComputedStyle(a).display : null)(it.querySelector('.home-faq-main-item-ans')) }))
                .filter(x => x.active || x.ans === 'block'); })()""")
        open1 = click_item(1)
        page.screenshot(path=f'{OUT}/{tag}-open1.png')
        open2 = click_item(2)
        close1 = click_item(1)   # clicking 1 again should close it
        b.close()
        return geo, states, open1, open2, close1, errs


lg, ls, lo1, lo2, lc1, le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
rg, rs, ro1, ro2, rc1, re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('GEO live:', lg)
print('GEO reb :', rg)
print('states live:', ls)
print('states reb :', rs)
print('click1 live:', lo1, '| reb:', ro1)
print('click2 live:', lo2, '| reb:', ro2)
print('click1-again live:', lc1, '| reb:', rc1)
print('errors:', {'live': le[:3], 'reb': re_[:3]})
for f in [-1.0, -0.4, 0.2, 0.8]:
    a = np.asarray(Image.open(f'{OUT}/live-f{f}.png').convert('RGB'), dtype=float)
    c = np.asarray(Image.open(f'{OUT}/reb-f{f}.png').convert('RGB'), dtype=float)
    print(f'f={f}: mean abs pixel diff = {np.abs(a - c).mean():.1f}')
