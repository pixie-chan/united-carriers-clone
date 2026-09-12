#!/usr/bin/env python3
"""Measure the live (mirror) why/testi/wrap geometry at rest, dump element rects."""
from playwright.sync_api import sync_playwright
import json

URL = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'

SEL = [
    'body', 'section.home-hero', 'section.home-intro', 'section.home-service',
    '.home-service-mb', '.home-why-wrap', '.home-why-empty-block.bottom',
    'section.home-why', '.home-why-stick-wrap', '.home-why-stick', '.home-why-ocean',
    '.home-why-ocean-img', '.home-why-ship', '.home-why-ship-img', '.home-why-ship-img-inner',
    '.home-why-ship-img-inner.bot', '.home-why-cloud-decor', '.home-why-cloud-overlap',
    '.home-why-cloud-overlap-bg', '.home-why-empty-block.first-screen', '.home-why-main',
    '.home-why-text-wrap', '.home-why-main-content', '.home-why-main-list',
    '.home-why-main-item', '.home-testi-wrap', 'section.home-testi', '.home-testi',
    '.home-testi-plane', '.home-testi-item', '.home-testi-title',
    '.home-partners-wrap', 'section.home-partners', '.home-ins-wrap', 'section.home-ins',
    '.home-faq-wrap', 'section.home-faq', '.footer-wrap', '.footer-cta', 'footer',
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto(URL, wait_until='load', timeout=90000)
    page.wait_for_timeout(7000)
    # scroll to 13000 and let lazy stuff settle
    page.evaluate('window.scrollTo(0,13000)')
    page.wait_for_timeout(2500)
    page.evaluate('window.scrollTo(0,0)')
    page.wait_for_timeout(1500)
    out = page.evaluate("""(sels) => {
      const res = {scrollH: document.body.scrollHeight, els: []};
      for (const s of sels) {
        document.querySelectorAll(s).forEach((el, i) => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          res.els.push({
            sel: s, i, y: Math.round(r.top + scrollY), h: Math.round(r.height),
            w: Math.round(r.width), x: Math.round(r.left),
            pos: cs.position, top: cs.top, bottom: cs.bottom, mt: cs.marginTop,
            z: cs.zIndex, disp: cs.display, vis: cs.visibility, op: cs.opacity,
            tr: cs.transform === 'none' ? '' : cs.transform.slice(0, 60)
          });
        });
      }
      return res;
    }""", SEL)
    print('scrollH:', out['scrollH'])
    for e in out['els']:
        print(json.dumps(e))
    b.close()
