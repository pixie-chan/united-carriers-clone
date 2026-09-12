#!/usr/bin/env python3
"""Measure live intro + services layout at their scroll positions."""
import json
from playwright.sync_api import sync_playwright

JS = r"""() => {
  const out = {};
  const R = el => { if (!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
             fs: cs.fontSize, lh: cs.lineHeight, col: cs.color, bg: cs.backgroundColor,
             cls: (el.className || '').toString().slice(0, 70), text: (el.textContent || '').trim().slice(0, 60) }; };
  const q = s => document.querySelector(s);
  const qa = s => [...document.querySelectorAll(s)];
  const findText = t => [...document.querySelectorAll('div,span,p,h2,h3')].find(e => (e.childElementCount === 0) && (e.textContent || '').trim().toLowerCase().includes(t));
  out['intro h2'] = R(q('.home-intro h2'));
  out['intro p1'] = R(qa('.home-intro .txt')[0]);
  out['intro p2'] = R(qa('.home-intro .txt')[1]);
  out['intro btn'] = R(q('.home-intro a'));
  out['intro img'] = R(q('.home-intro img'));
  out['intro stat label'] = R(findText('from countless journeys'));
  const counts = qa('.home-intro [data-count]');
  out['intro counts'] = counts.map(e => R(e));
  out['svc h2'] = R(q('.home-service h2'));
  out['svc p1'] = R(qa('.home-service .txt')[0]);
  out['svc p2'] = R(qa('.home-service .txt')[1]);
  const items = qa('.home-service-item');
  out['svc item count'] = items.length;
  out['svc item0 title'] = R(q('.home-service-item .home-service-item-title h3'));
  out['svc item0'] = R(items[0]);
  const speed = findText('km/h');
  out['speed label'] = R(speed);
  out['speed parent cls'] = speed ? (speed.parentElement.className || '').toString().slice(0,70) : null;
  out['svc canvases'] = qa('.home-service canvas').map(c => ({ id: c.id, cls: c.className.toString().slice(0,50), r: R(c) }));
  out['svc imgs'] = qa('.home-service img').slice(0, 12).map(im => ({ src: (im.currentSrc || im.src || '').split('/').pop().slice(0, 60), r: R(im) }));
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto('https://unitedcarriers.com/', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    for sy in (2200, 3400):
        page.evaluate(f'window.scrollTo(0,{sy})')
        page.wait_for_timeout(1600)
        data = page.evaluate(JS)
        print(f'===== scrollY {sy} =====')
        for k, v in data.items():
            if k in ('intro counts', 'svc imgs', 'svc canvases'):
                print(' ', k, ':')
                for x in v:
                    print('    ', json.dumps(x)[:220])
            else:
                print(' ', k, '=', json.dumps(v)[:220])
    b.close()
