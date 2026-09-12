#!/usr/bin/env python3
"""DOM-level comparison: live site vs rebuild, same logical elements."""
import json
from playwright.sync_api import sync_playwright

JS = r"""() => {
  const r = el => { if (!el) return null; const b = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height), fs: cs.fontSize, lh: cs.lineHeight, disp: cs.display }; };
  const q = s => document.querySelector(s);
  const out = {};
  out['logo'] = r(q('.header-logo'));
  if (out['logo']) out['logo'] = Object.assign(out['logo'], { lc: [...document.querySelectorAll('.header-logo .header-logo-char')].map(c => r(c)), single: r(q('.header-logo .header-logo-char-single')), full: r(q('.header-logo .header-logo-char-full')) });
  out['navUl'] = r(q('.header-nav ul, .header-menu-list'));
  out['aboutA'] = r(q('.header-nav li a, .header-link'));
  out['news'] = r(q('.topbar-news, .related-news-link'));
  out['carbon'] = r(q('.topbar-links a, .related-news-link'));
  out['workBtn'] = r(q('.topbar .btn, .header-cta'));
  out['heroLabel'] = r(q('.hero-label, .home-hero-label'));
  out['heroH1'] = r(q('.hero-h1, .home-hero-title'));
  out['heroDesc'] = r(q('.hero-desc, .home-hero-desc'));
  out['cta1'] = r(q('.hero-ctas .btn:first-child, .home-hero-cta a'));
  out['cta2'] = r(q('.hero-ctas .btn:last-child, .home-hero-cta a:last-child'));
  out['globeWrap'] = r(q('.home-hero-globe'));
  out['canvas'] = r(q('#globe'));
  return out;
}"""

def grab(url):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        page.goto(url, wait_until='load', timeout=90000)
        page.wait_for_timeout(9000)
        d = page.evaluate(JS)
        b.close()
        return d

live = grab('https://unitedcarriers.com/')
mine = grab('http://127.0.0.1:8898/index.html')

print(f'{"element":12} | {"LIVE x,y,w,h":>24} | {"REBUILD x,y,w,h":>24} | delta')
for k in live:
    a, b = live.get(k), mine.get(k)
    def f(v):
        if not v: return 'missing'
        return f'{v["x"]},{v["y"]},{v["w"]},{v["h"]}'
    d = ''
    if a and b:
        d = f'dx{b["x"]-a["x"]:+d} dy{b["y"]-a["y"]:+d} dw{b["w"]-a["w"]:+d} dh{b["h"]-a["h"]:+d}'
    print(f'{k:12} | {f(a):>24} | {f(b):>24} | {d}')
    if k == 'logo' and a and b:
        print('   live logo parts:', json.dumps(a.get('lc')), 'single:', a.get('single'), 'full:', a.get('full'))
        if b.get('lc') is not None:
            print('   mine logo parts:', json.dumps(b.get('lc')))
