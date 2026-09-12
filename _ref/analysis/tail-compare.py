#!/usr/bin/env python3
"""Compare live vs rebuild for the tail internals at scroll 14160."""
from playwright.sync_api import sync_playwright
import json, sys

def probe(url, wait_ms, label):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        page.goto(url, wait_until='load', timeout=90000)
        page.wait_for_timeout(wait_ms)
        page.evaluate('window.scrollTo(0,14160)')
        page.wait_for_timeout(2000)
        out = page.evaluate("""() => {
          const R = s => { const e = document.querySelector(s); if (!e) return null;
            const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
            return { y: Math.round(b.top+scrollY), h: Math.round(b.height), x: Math.round(b.left), w: Math.round(b.width),
                     mt: cs.marginTop, pt: cs.paddingTop, mb: cs.marginBottom, pb: cs.paddingBottom, pos: cs.position, top: cs.top }; };
          const V = s => { const e = document.querySelector(s); if (!e) return null;
            return ['--container--one-column','--container--padding','--container--column-gap'].map(v => v + '=' + getComputedStyle(e).getPropertyValue(v).trim()); };
          const roadMainGrid = document.querySelector('.home-service-road-main .container.grid');
          const subGrid = document.querySelector('.home-service-sub-content .container.grid');
          return {
            roadMain: R('.home-service-road-main'),
            roadMainGrid: roadMainGrid ? { pt: getComputedStyle(roadMainGrid).paddingTop, gtc: getComputedStyle(roadMainGrid).gridTemplateColumns.split(' ').slice(0,4).join(' ') + ' ...' } : null,
            roadWrap: R('.home-service-road-wrap'),
            road: R('.home-service-road'),
            roadInner: R('.home-service-road-inner'),
            vars: V('html'),
            subGridGtc: subGrid ? getComputedStyle(subGrid).gridTemplateColumns.split(' ').slice(0,6).join(' ') + ' ...' : null,
            stickWrap3: R('.home-service-stick-wrap.third-screen'),
            subWrap: R('.home-service-sub-wrap'),
            truckWrap: R('.home-service-new-truck-wrap'),
            truckStick: R('.home-service-new-truck-stick'),
            truckStickTop: (() => { const e = document.querySelector('.home-service-new-truck-stick'); return e ? getComputedStyle(e).top : null; })(),
            truckRot: R('.home-service-new-truck-rot'),
            truckRotTop: (() => { const e = document.querySelector('.home-service-new-truck-rot'); return e ? getComputedStyle(e).top : null; })(),
            truck: R('.home-service-new-truck'),
            truckTop: (() => { const e = document.querySelector('.home-service-new-truck'); return e ? getComputedStyle(e).top : null; })(),
          };
        }""")
        print('=====', label, '=====')
        for k, v in out.items():
            print(k, json.dumps(v) if isinstance(v, dict) else v)
        b.close()

probe('http://127.0.0.1:8899/unitedcarriers.com/index.html', 7000, 'LIVE')
probe(sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8898/index.html', 9000, 'REBUILD')
