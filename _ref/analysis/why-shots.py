#!/usr/bin/env python3
"""Shoot the mirror (live replica) at why-section scroll offsets for calibration."""
import os
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8899/unitedcarriers.com/index.html'
OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/whyviews'
os.makedirs(OUT, exist_ok=True)
YS = [13000, 14160, 15060, 15560, 16060, 16800, 17500, 18300, 19000, 19600, 20000, 21000]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto(URL, wait_until='load', timeout=90000)
    page.wait_for_timeout(7000)
    # warm scroll pass so all lazy assets (canvas, svgs) exist
    for y in [12000, 14000, 16000, 18000, 20000, 12000]:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(400)
    for y in YS:
        page.evaluate(f'window.scrollTo(0,{y})')
        page.wait_for_timeout(1600)
        page.screenshot(path=f'{OUT}/live-y{y}.png')
        print('shot', y)
    b.close()
print('done ->', OUT)
