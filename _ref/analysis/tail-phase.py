#!/usr/bin/env python3
"""Tail-phase forensics: live f=8..13.5 canvases; reb crane+truck canvas dumps + styles."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/tailph'
os.makedirs(f'{OUT}/live', exist_ok=True)
os.makedirs(f'{OUT}/reb', exist_ok=True)
os.makedirs(f'{OUT}/src34', exist_ok=True)
W, H = 1920, 1080
PHASES = [8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5]

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))

CANVAS_LIST_JS = """
[...document.querySelectorAll('canvas')].map(c => {
  const r = c.getBoundingClientRect();
  const cs = getComputedStyle(c);
  let vis = cs.display !== 'none' && cs.visibility !== 'hidden';
  let el = c, op = 1;
  while (el && el !== document.body) { const s = getComputedStyle(el); if (s.display === 'none') vis = false; op *= parseFloat(s.opacity); el = el.parentElement; }
  return { cls: c.className, parent: c.parentElement.className.slice(0,60),
           w: Math.round(r.width), h: Math.round(r.height), vis, op: +op.toFixed(3),
           inView: r.bottom > 0 && r.top < innerHeight };
})
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    # ---- live ----
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8899/unitedcarriers.com/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    print('=== LIVE canvases on page:')
    for c in page.evaluate(CANVAS_LIST_JS): print('  ', json.dumps(c))
    for f in PHASES:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1300)
        data = page.evaluate("document.querySelector('.home-service-crane canvas').toDataURL('image/png')")
        open(f'{OUT}/live/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
        print('live', f, flush=True)
    page.close()

    # ---- reb ----
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    print('=== REB canvases on page:')
    for c in page.evaluate(CANVAS_LIST_JS): print('  ', json.dumps(c))
    for f in PHASES:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1300)
        d1 = page.evaluate("document.querySelector('#craneCanvas').toDataURL('image/png')")
        open(f'{OUT}/reb/c{f}.png', 'wb').write(base64.b64decode(d1.split(',', 1)[1]))
        d2 = page.evaluate("document.querySelector('#truckCanvas').toDataURL('image/png')")
        open(f'{OUT}/reb/t{f}.png', 'wb').write(base64.b64decode(d2.split(',', 1)[1]))
        print('reb', f, flush=True)
    # src frames for seq3, seq4 at BOTH canvas sizes
    sizes = page.evaluate("""(() => {
      const c = document.getElementById('craneCanvas'), t = document.getElementById('truckCanvas');
      return { crane: {w: c.width, h: c.height}, truck: {w: t.width, h: t.height} };
    })()""")
    print('canvas backing sizes:', sizes)
    js = """
    async ({ seqs, sizes }) => {
      const out = {};
      for (const [sidx, sz, dims] of [[3, 'C', sizes.crane], [4, 'C', sizes.crane], [3, 'T', sizes.truck], [4, 'T', sizes.truck]]) {
        const tmp = document.createElement('canvas'); tmp.width = dims.w; tmp.height = dims.h;
        const ctx = tmp.getContext('2d');
        const names = seqs[sidx];
        for (let i = 0; i < names.length; i += 2) {
          const img = new Image();
          img.src = 'assets/frames/' + names[i];
          await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('fail')); });
          const sc = Math.max(dims.w / img.naturalWidth, dims.h / img.naturalHeight);
          const dw = img.naturalWidth * sc, dh = img.naturalHeight * sc;
          ctx.clearRect(0, 0, dims.w, dims.h);
          ctx.drawImage(img, (dims.w - dw) / 2, (dims.h - dh) / 2, dw, dh);
          out[sidx + '_' + sz + '_' + i] = tmp.toDataURL('image/png');
        }
      }
      return out;
    }
    """
    srcs = page.evaluate(js, {'seqs': seqs, 'sizes': sizes})
    for k, data in srcs.items():
        open(f'{OUT}/src34/{k}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    print('src34:', len(srcs))
    page.close()
    b.close()

# matching
def match(img_path, size_tag):
    cd = Image.open(img_path).convert('RGB').resize((180, 101))
    best = None
    for s in (3, 4):
        for fn in os.listdir(f'{OUT}/src34'):
            if not fn.startswith(f'{s}_{size_tag}_'):
                continue
            sf = Image.open(f'{OUT}/src34/{fn}').convert('RGB').resize((180, 101))
            d = ImageChops.difference(cd, sf).convert('L')
            h = d.histogram(); tot = 180 * 101
            m = sum(k * c for k, c in enumerate(h)) / tot
            if best is None or m < best[2]: best = (s, fn, m)
    return best

print()
print('LIVE crane canvas at tail phases:')
for f in PHASES:
    s, fn, m = match(f'{OUT}/live/f{f}.png', 'C')
    print(f'  f={f:<5} seq{s} {fn} diff {m:5.1f}')
print()
print('REB crane canvas (c) + truck canvas (t) at tail phases:')
for f in PHASES:
    s, fn, m = match(f'{OUT}/reb/c{f}.png', 'C')
    s2, fn2, m2 = match(f'{OUT}/reb/t{f}.png', 'T')
    print(f'  f={f:<5} crane: seq{s} {fn} {m:5.1f}   truck: seq{s2} {fn2} {m2:5.1f}')
