#!/usr/bin/env python3
"""Measure service-tail end-state at scroll 14160 on the mirror + speed HUD markup."""
from playwright.sync_api import sync_playwright
import json

URL = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
SEL = [
    '.home-service-third-screen', '.home-service-new-truck-wrap', '.home-service-new-truck-stick',
    '.home-service-new-truck-rot', '.home-service-new-truck', '.home-service-new-truck-inner.only-car',
    '.home-service-new-truck-inner.container-truck',
    '.home-service-road-main', '.home-service-road-wrap', '.home-service-road', '.home-service-road-center',
    '.home-service-road-left', '.home-service-road-right', '.home-service-road-bot',
    '.home-service-sub-content', '.home-service-stick-wrap.third-screen', '.home-service-stick.third-screen',
    '.home-service-title.sub', '.home-service-title.sub h2', '.home-service-desc.sub',
    '.home-service-sub-wrap', '.home-service-sub-list', '.home-service-sub-item', '.home-service-sub-ic',
    '.home-service-sub-title', '.home-service-sub-desc',
    '.home-service-speed', '.home-service-speed-inner', '.home-service-speed-number',
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto(URL, wait_until='load', timeout=90000)
    page.wait_for_timeout(7000)
    page.evaluate('window.scrollTo(0,13000)')
    page.wait_for_timeout(1200)
    page.evaluate('window.scrollTo(0,14160)')
    page.wait_for_timeout(2200)
    out = page.evaluate("""(sels) => {
      const res = [];
      for (const s of sels) {
        document.querySelectorAll(s).forEach((el, i) => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          res.push({sel: s, i,
            abs: Math.round(r.top + scrollY), x: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height),
            fs: cs.fontSize, lh: cs.lineHeight, ff: cs.fontFamily.split(',')[0], fw: cs.fontWeight,
            col: cs.color, bg: cs.backgroundColor, tt: cs.textTransform, ls: cs.letterSpacing,
            disp: cs.display, pos: cs.position, tr: cs.transform === 'none' ? '' : cs.transform.slice(0, 70),
            op: cs.opacity, vis: cs.visibility, z: cs.zIndex
          });
        });
      }
      return res;
    }""", SEL)
    for e in out:
        print(json.dumps(e))

    # speed HUD markup
    sp = page.evaluate("""() => {
      const el = document.querySelector('.home-service-speed');
      return el ? el.outerHTML.slice(0, 2500) : 'NONE';
    }""")
    print('\\n=== SPEED HUD ===')
    print(sp)
    b.close()
