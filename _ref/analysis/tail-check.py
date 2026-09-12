#!/usr/bin/env python3
"""Check the rebuild tail: screenshots + rects at key scrolls + diff vs live captures."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/qa'
LIVE = '/home/zen/projects/united-carriers-clone/_ref/analysis/verify'
os.makedirs(OUT, exist_ok=True)
YS = [13000, 14160, 14600]

errors, bad = [], []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.on('console', lambda m: errors.append(m.text[:200]) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)[:200]))
    page.on('response', lambda r: bad.append((r.status, r.url[-90:])) if r.status >= 400 else None)
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=60000)
    page.wait_for_timeout(9000)
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(1800)
        page.screenshot(path=f'{OUT}/t-y{y}.png')
    probe = page.evaluate("""() => {
      const r = s => { const e = document.querySelector(s); if (!e) return null;
        const b = e.getBoundingClientRect(); return { y: Math.round(b.top + scrollY), h: Math.round(b.height), x: Math.round(b.left), w: Math.round(b.width) }; };
      return {
        scrollH: document.body.scrollHeight,
        thirdScreen: r('.uc-tail .home-service-third-screen'),
        roadMain: r('.home-service-road-main'),
        subContent: r('.home-service-sub-content'),
        subWrap: r('.home-service-sub-wrap'),
        subList: r('.home-service-sub-list'),
        roadWrap: r('.home-service-road-wrap'),
        road: r('.home-service-road'),
        truck: r('.home-service-new-truck'),
        stick: r('.home-service-new-truck-stick'),
        speed: r('.home-service-speed'),
        title: r('.home-service-title.sub'),
        item0: r('.home-service-sub-item:nth-child(1)'),
        item1: r('.home-service-sub-item:nth-child(2)'),
        item2: r('.home-service-sub-item:nth-child(3)'),
      };
    }""")
    for k, v in probe.items(): print(k, v)
    print('console errors:', len(errors))
    for e in errors[:10]: print('  E', e)
    print('HTTP>=400:', len(bad))
    for s, u in bad[:10]: print('  B', s, u)
    b.close()

print()
for y in YS:
    lp = f'{LIVE}/live-y{y}.png'
    if not os.path.exists(lp):
        lp2 = f'/home/zen/projects/united-carriers-clone/_ref/analysis/whyviews/live-y{y}.png'
        if os.path.exists(lp2):
            lp = lp2
        else:
            print(f'{y}: no live capture'); continue
    a = Image.open(lp).convert('RGB'); c = Image.open(f'{OUT}/t-y{y}.png').convert('RGB')
    d = ImageChops.difference(a, c); h = d.convert('L').histogram(); tot = a.size[0] * a.size[1]
    print(f'{y}: diff>16 {sum(h[16:]) / tot * 100:.2f}%   diff>48 {sum(h[48:]) / tot * 100:.2f}%')
    comp = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    comp.paste(a, (0, 0)); comp.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(comp).text((12, a.size[1] + 10), f'TOP=live BOTTOM=rebuild y={y}', fill='black')
    comp.save(f'{OUT}/tcmp-y{y}.png')
