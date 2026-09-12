#!/usr/bin/env python3
"""Debug: (a) live intro rects at scroll 2350 + true counter values, (b) rebuild crane canvas state."""
import json
from playwright.sync_api import sync_playwright

LIVE_JS = r"""() => {
  const R = el => { if (!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), fs: cs.fontSize,
             text: (el.textContent || '').trim().slice(0, 40) }; };
  const q = s => document.querySelector(s);
  const qa = s => [...document.querySelectorAll(s)];
  return {
    h2: R(q('.home-intro h2')),
    img: R(q('.home-intro img')),
    p1: R(qa('.home-intro .txt')[0]),
    p2: R(qa('.home-intro .txt')[1]),
    btn: R(q('.home-intro a')),
    label: R((() => { for (const e of qa('div,span')) if (e.childElementCount === 0 && (e.textContent || '').toLowerCase().includes('from countless')) return e; })()),
    counts: qa('[data-count]').map(e => ({ attr: e.getAttribute('data-count'), txt: e.textContent.trim() })),
    stats: qa('.home-intro [class*="stat"]').slice(0, 8).map(e => ({ cls: e.className.toString().slice(0, 50), r: R(e) }))
  };
}"""

MINE_JS = r"""() => {
  const c = document.getElementById('craneCanvas');
  const rect = c ? c.getBoundingClientRect() : null;
  const reqs = performance.getEntriesByType('resource').filter(e => e.name.includes('frames/'));
  return {
    crane: c ? { w: c.width, h: c.height, cw: Math.round(rect.width), ch: Math.round(rect.height),
                 x: Math.round(rect.x), y: Math.round(rect.y) } : null,
    frameReqs: reqs.length,
    frameSample: reqs.slice(0, 3).map(e => e.name.split('/').pop()),
    frameFailed: reqs.filter(e => e.responseStatus >= 400).map(e => e.name.split('/').pop()).slice(0, 5),
    title: document.title
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto('https://unitedcarriers.com/', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    page.evaluate('window.scrollTo(0,2350)')
    page.wait_for_timeout(2500)
    d = page.evaluate(LIVE_JS)
    print('LIVE INTRO @2350:')
    for k, v in d.items():
        print(' ', k, '=', json.dumps(v)[:300])

    mp = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    warns = []
    mp.on('console', lambda m: warns.append((m.type, m.text[:180])) if m.type in ('warning', 'error') else None)
    mp.on('pageerror', lambda e: warns.append(('pageerror', str(e)[:180])))
    mp.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=60000)
    mp.wait_for_timeout(9000)
    mp.evaluate('window.scrollTo(0,3220)')
    mp.wait_for_timeout(2500)
    d2 = mp.evaluate(MINE_JS)
    print('REBUILD CRANE @3220:')
    for k, v in d2.items():
        print(' ', k, '=', json.dumps(v)[:300])
    print('rebuild console warn/err:')
    for t, m in warns[-10:]:
        print('   ', t, m)
    b.close()
