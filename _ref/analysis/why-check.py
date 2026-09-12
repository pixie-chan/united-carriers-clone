#!/usr/bin/env python3
"""Why-section check: rebuild screenshots vs live captures + geometry probe."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw
import json

REB = 'http://127.0.0.1:8898/index.html'
OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/qaw'
LIVE = '/home/zen/projects/united-carriers-clone/_ref/analysis/whyviews'
YS = [14160, 15060, 16060, 17500, 18300, 19000, 19600, 20000]
os.makedirs(OUT, exist_ok=True)

errors, bad = [], []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)[:200]))
    page.on('response', lambda r: bad.append((r.status, r.url[-90:])) if r.status >= 400 else None)
    page.goto(REB, wait_until='load', timeout=60000)
    page.wait_for_timeout(9000)
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(2200)
        page.screenshot(path=f'{OUT}/w-y{y}.png')
    probe = page.evaluate("""() => ({
      scrollH: document.body.scrollHeight,
      wrap: (()=>{const e=document.querySelector('.home-why-wrap');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height)};})(),
      sec: (()=>{const e=document.querySelector('.home-why');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height)};})(),
      stick: (()=>{const e=document.querySelector('.home-why-stick');const r=e.getBoundingClientRect();return {sy:Math.round(r.top),h:Math.round(r.height)};})(),
      shipImg: (()=>{const e=document.querySelector('.home-why-ship-img');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height),x:Math.round(r.left),w:Math.round(r.width)};})(),
      main: (()=>{const e=document.querySelector('.home-why-main');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height)};})(),
      textWrap: (()=>{const e=document.querySelector('.home-why-text-wrap');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height)};})(),
      item0: (()=>{const e=document.querySelector('.home-why-main-item');const r=e.getBoundingClientRect();return {y:Math.round(r.top+scrollY),h:Math.round(r.height)};})()
    })""")
    print(json.dumps(probe, indent=1))
    print('console errors:', len(errors))
    for e in errors[:10]:
        print('  E', e[:170])
    print('HTTP>=400:', len(bad))
    for s, u in bad[:8]:
        print('  B', s, u)
    b.close()

print()
for y in YS:
    lp = f'{LIVE}/live-y{y}.png'
    if not os.path.exists(lp):
        print(f'{y}: no live capture'); continue
    a = Image.open(lp).convert('RGB'); c = Image.open(f'{OUT}/w-y{y}.png').convert('RGB')
    d = ImageChops.difference(a, c); h = d.convert('L').histogram(); tot = a.size[0] * a.size[1]
    print(f'{y}: diff>16 {sum(h[16:]) / tot * 100:6.2f}%   diff>48 {sum(h[48:]) / tot * 100:6.2f}%')
    comp = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    comp.paste(a, (0, 0)); comp.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(comp).text((12, a.size[1] + 10), f'TOP = live    BOTTOM = rebuild    scrollY={y}', fill='black')
    comp.save(f'{OUT}/wcmp-y{y}.png')
print('composites in', OUT)
