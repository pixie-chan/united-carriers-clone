#!/usr/bin/env python3
"""Measure exact live positions/styles of header + hero elements for the rebuild."""
import json
from playwright.sync_api import sync_playwright

JS = r"""() => {
  const out = {};
  const r = el => { if (!el) return null; const b = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
             fs: cs.fontSize, ls: cs.letterSpacing, tt: cs.textTransform, col: cs.color,
             cls: (el.className && el.className.toString ? el.className.toString() : '').slice(0, 90) }; };
  const q = s => document.querySelector(s);
  const byText = (t, tags = 'a,button,div,span,li') => {
    for (const el of document.querySelectorAll(tags)) {
      const txt = (el.textContent || '').trim().toLowerCase();
      if (txt === t.toLowerCase()) return el;
    }
    for (const el of document.querySelectorAll(tags)) {
      const txt = (el.textContent || '').trim().toLowerCase();
      if (txt.includes(t.toLowerCase())) return el;
    }
    return null;
  };
  out.logo = r(q('.header-logo'));
  out.logoChar = r(q('.header-logo-char'));
  out.menuBtn = r(byText('menu'));
  out.workWithUs = r(byText('work with us'));
  out.carbon = r(byText('carbon calculator'));
  out.liveTracking = r(byText('live tracking portal'));
  out.news = r(byText('pinglu'));
  out.navAbout = r(byText('about'));
  const navAbout = byText('about');
  if (navAbout) { const li = navAbout.closest('li') || navAbout.parentElement; out.navLi = r(li); out.navItemHTML = (li ? li.outerHTML : '').slice(0, 300); }
  out.heroLabel = r(q('.home-hero-label'));
  out.heroTitle = r(q('.home-hero-title'));
  out.heroDesc = r(q('.home-hero-desc'));
  out.heroCtas = r(byText('talk with us'));
  out.talkWithUs = r(byText('talk with us'));
  out.ourServices = r(byText('our services'));
  out.globeWrap = r(q('.home-hero-globe'));
  out.globeCanvas = r(q('#globe'));
  out.globeLabel = r(q('.globe-label-text'));
  out.shadowOrange = r(q('.home-hero-globe-shadow.orange'));
  out.headerWrap = r(q('.header, .header-inner'));
  out.headerInner = r(q('.header-inner'));
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    page.goto('https://unitedcarriers.com/', wait_until='load', timeout=90000)
    page.wait_for_timeout(9000)
    data = page.evaluate(JS)
    print(json.dumps(data, indent=1))
    b.close()
