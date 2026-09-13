#!/usr/bin/env python3
"""Footer QA: geometry, page length, particles, marquees, switcher, pixel diffs."""
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/footer'
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
          return { wrap: q('.footer-wrap'), footer: q('.footer'), docH: document.body.scrollHeight }; })()""")
        top = geo['footer']['top'] if geo['footer'] else geo['wrap']['top']

        def stepped(t):
            y = page.evaluate('window.scrollY')
            while abs(y - t) > 1000:
                y = y + 1000 if t > y else y - 1000
                page.evaluate(f'window.scrollTo(0, {int(y)})'); page.wait_for_timeout(80)
            page.evaluate(f'window.scrollTo(0, {int(t)})'); page.wait_for_timeout(60)

        shots = {}
        for f in [-0.6, 0.0, 0.6, 1.4]:
            stepped(int(top + f * 900))
            page.wait_for_timeout(1500)
            page.screenshot(path=f'{OUT}/{tag}-f{f}.png')
        # canvas particles check
        stepped(int(top + 0.3 * 900)); page.wait_for_timeout(2000)
        canvas = page.evaluate("""(() => {
          const c = document.getElementById('footer-particle-canvas');
          if (!c) return null;
          const ctx = c.getContext('2d');
          const d = ctx.getImageData(0, 0, c.width, c.height).data;
          let n = 0;
          for (let i = 3; i < d.length; i += 4 * 97) if (d[i] > 0) n++;
          return { w: c.width, h: c.height, styleW: c.style.width, nonzeroSampled: n }; })()""")
        # marquee lists
        marquee = page.evaluate("""(() => {
          return [...document.querySelectorAll('.footer-info-text-inner')].slice(0, 4).map(l => ({
            kids: l.children.length,
            anim: getComputedStyle(l.firstElementChild || l).animationName })); })()""")
        # switcher: click btn 2
        btns = page.evaluate("(() => document.querySelectorAll('.footer-info-btn').length)()")
        sw = {'nBtns': btns}
        if btns > 2:
            r = page.evaluate("""(() => { const b = document.querySelectorAll('.footer-info-btn')[2];
              const rc = b.getBoundingClientRect(); return [Math.round(rc.left + rc.width / 2), Math.round(rc.top + rc.height / 2)]; })()""")
            page.mouse.click(r[0], r[1])
            page.wait_for_timeout(800)
            sw = page.evaluate("""(() => {
              const btns = [...document.querySelectorAll('.footer-info-btn')].map(b => b.classList.contains('active'));
              const texts = [...document.querySelectorAll('.footer-info-text-inner')].map(t => t.classList.contains('active'));
              const bg = document.querySelector('.footer-info-active');
              return { nBtns: btns.length, btns: btns.findIndex(x => x), texts: texts.findIndex(x => x),
                       bgTf: bg ? getComputedStyle(bg).transform.slice(0, 40) : null }; })()""")
        b.close()
        return geo, canvas, marquee, sw, errs


lg, lc, lm, lsw, le = run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 12000)
rg, rc, rm, rsw, re_ = run('http://127.0.0.1:8898/index.html', 'reb', 8000)
print('GEO live:', lg)
print('GEO reb :', rg)
print('canvas live:', lc)
print('canvas reb :', rc)
print('marquee live:', lm)
print('marquee reb :', rm)
print('switcher live:', lsw)
print('switcher reb :', rsw)
print('errors:', {'live': le[:3], 'reb': re_[:3]})
for f in [-0.6, 0.0, 0.6, 1.4]:
    a = np.asarray(Image.open(f'{OUT}/live-f{f}.png').convert('RGB'), dtype=float)
    c = np.asarray(Image.open(f'{OUT}/reb-f{f}.png').convert('RGB'), dtype=float)
    print(f'f={f}: mean abs pixel diff = {np.abs(a - c).mean():.1f}')
