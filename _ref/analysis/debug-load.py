#!/usr/bin/env python3
"""Probe the runtime state of local mirror vs live site to find what never completes."""
from playwright.sync_api import sync_playwright

PROBE = """() => {
  const g = s => { const el = document.querySelector(s); if (!el) return null; const cs = getComputedStyle(el);
    return { cls: (el.className || '').toString().slice(0, 130), op: cs.opacity, disp: cs.display, vis: cs.visibility, z: cs.zIndex }; };
  return {
    bodyCls: document.body.className.slice(0, 200),
    htmlCls: document.documentElement.className.slice(0, 120),
    loader: g('.loader'),
    hero: g('.home-hero'),
    heroTitle: g('.home-hero-title'),
    hasBarbaWrapper: !!document.querySelector('[data-barba="wrapper"]'),
    hasBarbaContainer: !!document.querySelector('[data-barba="container"]'),
    barbaNs: (document.querySelector('[data-barba-namespace]') || {}).getAttribute ? document.querySelector('[data-barba-namespace]').getAttribute('data-barba-namespace') : null,
    fonts: document.fonts.status,
    ready: document.readyState,
    loaderText: (document.querySelector('.loader') ? document.querySelector('.loader').textContent : '').replace(/\\s+/g, ' ').trim().slice(0, 200),
    scrollHeight: document.body.scrollHeight,
    gsap: !!window.gsap,
    smoothScroll: !!window.smoothScroll,
    initHiddenCount: document.querySelectorAll('[data-init-hidden]').length,
    loadingClass: document.body.classList.contains('is-loading'),
    hiddenHeroEls: [...document.querySelectorAll('.home-hero-title, .home-hero-desc, .home-hero-label')].map(e => ({ cls: e.className, op: getComputedStyle(e).opacity })),
    framesStats: window.__getFrameCacheStats ? window.__getFrameCacheStats() : null,
  };
}"""

def probe(url, tag):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        msgs = []
        page.on('console', lambda m: msgs.append((m.type, m.text[:220])))
        page.on('pageerror', lambda e: msgs.append(('PAGEERROR', str(e)[:320])))
        page.goto(url, wait_until='load', timeout=90000)
        page.wait_for_timeout(10000)
        r = page.evaluate(PROBE)
        print('====', tag)
        for k, v in r.items():
            print('  ', k, '=', v)
        print('   --- last console msgs:')
        for t, m in msgs[-22:]:
            print('   ', t, '|', m)
        b.close()

probe('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'LOCAL MIRROR')
probe('https://unitedcarriers.com/', 'LIVE')
