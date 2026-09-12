#!/usr/bin/env python3
"""Paired captures with identical harness: live mirror vs rebuild, diffed."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw

BASE = '/home/zen/projects/united-carriers-clone/_ref/analysis'
OUT = f'{BASE}/ab'
os.makedirs(OUT, exist_ok=True)
YS = [0, 1800, 3220, 13000, 14160, 15060]

def shoot(pw, url, prefix, wait_load):
    b = pw.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:120]))
    page.goto(url, wait_until='load', timeout=90000)
    page.wait_for_timeout(wait_load)
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(2000)
        page.screenshot(path=f'{OUT}/{prefix}-y{y}.png')
    b.close()
    return errs

with sync_playwright() as pw:
    e1 = shoot(pw, 'http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live', 7000)
    e2 = shoot(pw, 'http://127.0.0.1:8898/index.html', 'rebn', 9000)
print('live errors:', e1[:3])
print('rebn errors:', e2[:3])

print()
print('  y         diff>16   diff>48')
for y in YS:
    a = Image.open(f'{OUT}/live-y{y}.png').convert('RGB')
    c = Image.open(f'{OUT}/rebn-y{y}.png').convert('RGB')
    d = ImageChops.difference(a, c)
    h = d.convert('L').histogram()
    tot = a.size[0] * a.size[1]
    print(f'  {y:<9} {sum(h[16:]) / tot * 100:6.2f}%   {sum(h[48:]) / tot * 100:6.2f}%')
    comp = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    comp.paste(a, (0, 0)); comp.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(comp).text((12, a.size[1] + 10), f'TOP=live BOTTOM=rebuild y={y}', fill='black')
    comp.save(f'{OUT}/cmp-y{y}.png')
print('composites in', OUT)
