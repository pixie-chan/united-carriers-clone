#!/usr/bin/env python3
"""Probe full tail + handoff DOM state at y=11400 and y=12100 for live vs rebuild."""
from playwright.sync_api import sync_playwright
import json, sys

YS = [10500, 11400, 12100]


def stepped(page, t):
    y = page.evaluate('window.scrollY')
    while abs(y - t) > 600:
        y = y + 600 if t > y else y - 600
        page.evaluate(f'window.scrollTo(0, {int(y)})')
        page.wait_for_timeout(90)
    page.evaluate(f'window.scrollTo(0, {int(t)})')
    page.wait_for_timeout(1100)


def probe(url, wait_ms, label):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)[:120]))
        page.goto(url, wait_until='load', timeout=90000)
        page.wait_for_timeout(wait_ms)
        out = {}
        for y in YS:
            stepped(page, y)
            r = page.evaluate("""() => {
              const q = s => document.querySelector(s);
              const info = s => { const e = q(s); if (!e) return null;
                const cs = getComputedStyle(e); const b = e.getBoundingClientRect();
                const tr = cs.transform;
                return { op: cs.opacity, vis: cs.visibility, top: cs.top, scale: cs.getPropertyValue('--scale-factor'),
                         tr: tr === 'none' ? 'none' : tr, y: Math.round(b.top + scrollY),
                         h: Math.round(b.height), x: Math.round(b.left), w: Math.round(b.width) }; };
              return {
                scrollY: Math.round(scrollY),
                roadWrap: info('.home-service-road-wrap'),
                road: info('.home-service-road'),
                roadMain: info('.home-service-road-main'),
                roadBig: info('.home-service-road-big'),
                roadBigImg: info('.home-service-road-big-img'),
                truckWrap: info('.home-service-new-truck-wrap'),
                truckStick: info('.home-service-new-truck-stick'),
                truckRot0: info('.home-service-new-truck-rot'),
                truckRotAll: Array.from(document.querySelectorAll('.home-service-new-truck-rot')).map(e => { const cs=getComputedStyle(e); return { tr: cs.transform, top: cs.top, op: cs.opacity }; }),
                truck: info('.home-service-new-truck'),
                truckInnerOnly: info('.home-service-new-truck-inner.only-car'),
                truckInnerCont: info('.home-service-new-truck-inner.container-truck'),
                main: info('.home-service-main'),
                secondScreen: info('.home-service-second-screen'),
                thirdScreen: info('.home-service-third-screen'),
                title3: info('.home-service-third-screen .home-service-title'),
                desc3: info('.home-service-third-screen .home-service-desc'),
                subList: info('.home-service-sub-list'),
                subItem0: info('.home-service-sub-item'),
                speedInner: (() => { const e = q('.home-service-speed-inner'); return e ? { cls: e.className, op: getComputedStyle(e).opacity } : null; })(),
                roadStick: info('.home-service-road-stick'),
              };
            }""")
            out[y] = r
        b.close()
        return out, errs


live, el = probe('http://127.0.0.1:8899/unitedcarriers.com/index.html', 12000, 'LIVE')
reb, er = probe('http://127.0.0.1:8898/', 7000, 'REBUILD')
print('live errors:', el)
print('reb errors:', er)
for y in YS:
    print(f'\n===== y={y} =====')
    for k in live[y]:
        lv = live[y][k]
        rv = reb[y].get(k)
        if isinstance(lv, list):
            print(f'  {k}:')
            for i, item in enumerate(lv):
                ri = rv[i] if rv and i < len(rv) else None
                print(f'    [{i}] live={json.dumps(item)} reb={json.dumps(ri)}')
        else:
            print(f'  {k}: live={json.dumps(lv)}  reb={json.dumps(rv)}')
