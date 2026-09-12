#!/usr/bin/env python3
"""Print section skeleton (top/height) for both sites so the structural map is explicit."""
import json
from playwright.sync_api import sync_playwright

SEL = [
    '.home-intro', '.home-service', '.home-service-first-screen', '.home-service-empty-block.first-screen',
    '.home-service-empty-block.second-screen', '.home-service-main', '.home-service-main-inner',
    '.home-service-cards', '.service-cards', '.home-service-list', '.uc-tail',
    '.home-why', '.home-why-wrap', '.home-why-empty-block.first-screen', '.home-why-main',
]

JS = """
(sels) => {
  const out = {};
  for (const s of sels) {
    const el = document.querySelector(s);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    out[s] = { top: Math.round(r.top + scrollY), h: Math.round(r.height) };
  }
  return { pageH: document.body.scrollHeight, sections: out };
}
"""

def run(url, label):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1920, 'height': 1080}).new_page()
        page.goto(url, wait_until='load', timeout=120000)
        page.wait_for_timeout(9000)
        res = page.evaluate(JS, SEL)
        print(f'== {label} pageH={res["pageH"]}')
        for k, v in res['sections'].items():
            print(f'   {k:44s} top={v["top"]:>7}  h={v["h"]:>7}')
        b.close()

run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'LIVE')
run('http://127.0.0.1:8898/index.html', 'REBUILD')
