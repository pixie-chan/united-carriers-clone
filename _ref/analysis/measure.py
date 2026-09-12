#!/usr/bin/env python3
"""Deep-measure unitedcarriers.com: loader frames, geometry, styles, canvases, assets."""
import json, os
from playwright.sync_api import sync_playwright

OUT = os.path.dirname(os.path.abspath(__file__)) + '/measures'
os.makedirs(OUT, exist_ok=True)
URL = 'https://unitedcarriers.com/'

MEASURE_JS = r"""
() => {
  const pick = (el, props) => {
    const cs = getComputedStyle(el);
    const o = {};
    props.forEach(p => o[p] = cs.getPropertyValue(p));
    const r = el.getBoundingClientRect();
    o._rect = { x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height) };
    o._tag = el.tagName.toLowerCase();
    o._class = (el.className || '').toString().slice(0, 120);
    return o;
  };
  const BOXY = ['display','position','width','height','padding','margin','background-color','border-radius','gap','grid-template-columns','flex-direction','overflow','z-index','max-width','min-height'];

  const res = { url: location.href, vw: innerWidth, vh: innerHeight, scrollH: document.body.scrollHeight };

  const walk = [];
  function outline(el, depth, maxdepth) {
    if (depth > maxdepth) return;
    for (const c of el.children) {
      const tag = c.tagName.toLowerCase();
      if (['script','style','link','meta','noscript','template'].includes(tag)) continue;
      const r = c.getBoundingClientRect();
      const cs = getComputedStyle(c);
      walk.push({
        d: depth, tag,
        cls: (typeof c.className === 'string' ? c.className : '').slice(0, 100),
        id: c.id || '',
        text: (c.childElementCount === 0 ? (c.textContent || '') : '').trim().slice(0, 90),
        y: Math.round(r.top + scrollY), h: Math.round(r.height),
        disp: cs.display, pos: cs.position
      });
      if (r.height > 0 && depth < maxdepth) outline(c, depth + 1, maxdepth);
    }
  }
  outline(document.body, 0, 3);
  res.outline = walk.slice(0, 3000);

  const styles = new Map();
  document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,a,span,div,button,li').forEach(el => {
    if (!el.textContent || !el.textContent.trim()) return;
    if (el.childElementCount > 0) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const key = [cs.fontFamily.split(',')[0], cs.fontSize, cs.fontWeight, cs.lineHeight, cs.letterSpacing, cs.textTransform].join(' | ');
    const rec = styles.get(key) || { count: 0, samples: [] };
    rec.count++;
    if (rec.samples.length < 3) rec.samples.push(((el.className || '') + ' :: ' + el.textContent.trim()).slice(0, 90));
    styles.set(key, rec);
  });
  res.textStyles = [...styles.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 80).map(([k, v]) => ({ key: k, count: v.count, samples: v.samples }));

  const colors = new Map();
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    for (const p of ['color', 'background-color']) {
      const v = cs.getPropertyValue(p);
      if (v && v !== 'rgba(0, 0, 0, 0)') colors.set(v, (colors.get(v) || 0) + 1);
    }
  });
  res.colors = [...colors.entries()].sort((a, b) => b[1] - a[1]).slice(0, 40);

  res.canvases = [...document.querySelectorAll('canvas')].map(c => {
    const r = c.getBoundingClientRect();
    return { w: c.width, h: c.height, cssW: Math.round(r.width), cssH: Math.round(r.height), y: Math.round(r.top + scrollY),
             cls: (c.className || '').toString().slice(0, 80),
             parentCls: (c.parentElement && c.parentElement.className || '').toString().slice(0, 80) };
  });
  res.svgs = [...document.querySelectorAll('svg')].slice(0, 120).map(s => {
    const r = s.getBoundingClientRect();
    return { vb: s.getAttribute('viewBox'), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + scrollY),
             cls: (s.getAttribute('class') || '').slice(0, 80), kids: s.children.length };
  });

  res.images = [...document.querySelectorAll('img')].slice(0, 200).map(im => {
    const r = im.getBoundingClientRect();
    return { src: (im.currentSrc || im.src || '').split('/').pop().slice(0, 90), alt: (im.alt || '').slice(0, 60),
             nw: im.naturalWidth, nh: im.naturalHeight, w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + scrollY) };
  });

  const das = {};
  document.querySelectorAll('*').forEach(el => {
    for (const a of el.attributes) {
      if (a.name.startsWith('data-')) das[a.name] = (das[a.name] || 0) + 1;
    }
  });
  res.dataAttrs = Object.entries(das).sort((a, b) => b[1] - a[1]).slice(0, 50);

  const hdr = document.querySelector('header, .nav, nav');
  if (hdr) res.header = pick(hdr, BOXY);
  const ftr = document.querySelector('footer');
  if (ftr) res.footer = pick(ftr, BOXY);

  res.htmlStyle = pick(document.documentElement, BOXY);
  res.bodyStyle = pick(document.body, BOXY);

  res.sections = [...document.querySelectorAll('section, .section')].map(s => {
    const r = s.getBoundingClientRect();
    const cs = getComputedStyle(s);
    const h2 = s.querySelector('h1,h2');
    return { cls: (s.className || '').toString().slice(0, 120), y: Math.round(r.top + scrollY), h: Math.round(r.height),
             bg: cs.backgroundColor, pad: cs.padding, heading: h2 ? h2.textContent.trim().slice(0, 80) : '' };
  });

  return res;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pg = browser.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    shots = []
    def snap(name):
        try:
            pg.screenshot(path=f"{OUT}/load-{name}.png")
            shots.append(name)
        except Exception as e:
            print('shot fail', name, e)
    pg.goto(URL, wait_until='commit', timeout=60000)
    pg.wait_for_timeout(300);  snap('t0300')
    pg.wait_for_timeout(700);  snap('t1000')
    pg.wait_for_timeout(1500); snap('t2500')
    pg.wait_for_timeout(3000); snap('t5500')
    print('loader shots:', shots)
    pg.close()

    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()
    page.goto(URL, wait_until='load', timeout=90000)
    page.wait_for_timeout(8000)
    for i in range(1, 41):
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(60)
    page.wait_for_timeout(1500)
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(1200)
    data = page.evaluate(MEASURE_JS)
    with open(f'{OUT}/desktop.json', 'w') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    with open(f'{OUT}/home-dom.html', 'w') as f:
        f.write(page.content())
    print('scrollH', data['scrollH'], 'outline', len(data['outline']), 'textStyles', len(data['textStyles']))
    print('canvases:', json.dumps(data['canvases'], indent=1)[:900])
    maps = page.evaluate("""() => {
      return [...document.querySelectorAll('svg')]
        .map(s => ({ html: s.outerHTML, r: s.getBoundingClientRect() }))
        .filter(o => o.r.width > 250 && o.r.height > 150)
        .slice(0, 4);
    }""")
    for i, m in enumerate(maps):
        with open(f'{OUT}/big-svg-{i}.svg', 'w') as f:
            f.write(m['html'])
        print('big svg', i, len(m['html']), 'bytes')
    page.close()

    mctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
    mp = mctx.new_page()
    mp.goto(URL, wait_until='load', timeout=90000)
    mp.wait_for_timeout(8000)
    mdata = mp.evaluate(MEASURE_JS)
    with open(f'{OUT}/mobile.json', 'w') as f:
        json.dump(mdata, f, indent=1, ensure_ascii=False)
    print('mobile scrollH', mdata['scrollH'])
    browser.close()
print('DONE')
