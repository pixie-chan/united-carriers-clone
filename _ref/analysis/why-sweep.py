#!/usr/bin/env python3
"""Sweep: service tail + why section rects/transforms across scroll offsets on the mirror."""
from playwright.sync_api import sync_playwright
import json

URL = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
YS = [13000, 13600, 14160, 14600, 15060, 15300, 15560, 16060, 17000, 18000, 19000, 20000, 20822, 21500]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto(URL, wait_until='load', timeout=90000)
    page.wait_for_timeout(7000)

    # 1) structure dump of service tail + why wrap (class tree, 3 levels)
    struct = page.evaluate("""() => {
      const lines = [];
      const walk = (el, depth) => {
        if (depth > 3) return;
        const cls = (el.className && typeof el.className === 'string') ? el.className.split(' ').filter(c=>!c.startsWith('w-node')).slice(0,4).join('.') : '';
        const tag = el.tagName.toLowerCase();
        if (cls || tag === 'section' || tag === 'footer') lines.push('  '.repeat(depth) + tag + (cls ? '.'+cls : ''));
        for (const c of el.children) walk(c, depth+1);
      };
      const svc = document.querySelector('section.home-service');
      if (svc) {
        lines.push('=== service tail subtree (last child area) ===');
        const kids = svc.querySelectorAll(':scope > *');
        walk(kids[kids.length-1] || svc, 0);
        const subs = svc.querySelector('.home-service-sub-wrap');
        if (subs) { lines.push('=== .home-service-sub-wrap full path ==='); let n = subs, path=[]; while (n && n.tagName !== 'BODY') { path.unshift(n.tagName.toLowerCase()+'.'+(typeof n.className==='string'? n.className.split(' ').filter(c=>!c.startsWith('w-node')).slice(0,3).join('.') : '')); n = n.parentElement; } lines.push(path.join(' > ')); }
      }
      return lines.join('\\n');
    }""")
    print(struct)
    print()

    # 2) scroll sweep of rects/transforms
    SEL = {
      'svc': 'section.home-service',
      'subWrap': '.home-service-sub-wrap',
      'subList': '.home-service-sub-list',
      'whyWrap': '.home-why-wrap',
      'whySec': 'section.home-why',
      'stickWrap': '.home-why-stick-wrap',
      'stick': '.home-why-stick',
      'empt1': '.home-why-empty-block.first-screen',
      'main': '.home-why-main',
      'textWrap': '.home-why-text-wrap',
      'ship': '.home-why-ship',
      'shipImg': '.home-why-ship-img',
      'ocean': '.home-why-ocean',
      'cloudOv': '.home-why-cloud-overlap',
      'testiWrap': '.home-testi-wrap',
    }
    print('scrollY  ' + '  '.join(f'{k:>10}' for k in SEL))
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(900)
        row = page.evaluate("""(sels) => {
          const out = {};
          for (const [k, s] of Object.entries(sels)) {
            const el = document.querySelector(s);
            if (!el) { out[k] = '-'; continue; }
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            const tr = cs.transform === 'none' ? '' : (cs.transform.startsWith('matrix') ? 'tr' : cs.transform.slice(0,20));
            out[k] = `${Math.round(r.top)}|${Math.round(r.height)}|${(cs.opacity==='1'?'':cs.opacity)}${tr?'|'+tr:''}`;
          }
          return out;
        }""", SEL)
        print(f'{y:<8} ' + '  '.join(f'{str(row[k])[:22]:>22}' for k in SEL))
    b.close()
