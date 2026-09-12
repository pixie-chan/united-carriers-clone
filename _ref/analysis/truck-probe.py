#!/usr/bin/env python3
"""Live truck-sq canvas behavior: rect/opacity/frame across f=4.5..7; match vs seq3."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/truckph'
os.makedirs(f'{OUT}/live', exist_ok=True)
os.makedirs(f'{OUT}/src3', exist_ok=True)
W, H = 1920, 1080
PHASES = [4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 7.0]

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8899/unitedcarriers.com/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    for f in PHASES:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1400)
        info = page.evaluate("""(() => {
          const c = document.querySelector('.home-service-truck-sq');
          const r = c.getBoundingClientRect();
          let op = 1, el = c;
          while (el && el !== document.body) { op *= parseFloat(getComputedStyle(el).opacity); el = el.parentElement; }
          return { t: Math.round(r.top), l: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height), op: +op.toFixed(3) };
        })()""")
        data = page.evaluate("document.querySelector('.home-service-truck-sq').toDataURL('image/png')")
        open(f'{OUT}/live/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
        print(f'f={f}', json.dumps(info), flush=True)
    # src frames for seq3 at 1394x391
    js = """
    async ({ names, w, h }) => {
      const tmp = document.createElement('canvas'); tmp.width = w; tmp.height = h;
      const ctx = tmp.getContext('2d');
      const out = {};
      for (let i = 0; i < names.length; i += 2) {
        const img = new Image();
        img.src = 'assets/frames/' + names[i];
        await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('fail')); });
        const sc = Math.max(w / img.naturalWidth, h / img.naturalHeight);
        const dw = img.naturalWidth * sc, dh = img.naturalHeight * sc;
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
        out[i] = tmp.toDataURL('image/png');
      }
      return out;
    }
    """
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    srcs = page.evaluate(js, {'names': seqs[3], 'w': 1394, 'h': 391})
    for i, data in srcs.items():
        open(f'{OUT}/src3/f-{int(i):03d}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    print('src3 frames:', len(srcs))
    b.close()

print()
print('live truck-sq canvas frame matching:')
for f in PHASES:
    cd = Image.open(f'{OUT}/live/f{f}.png').convert('RGB').resize((240, 68))
    best = None
    for fn in os.listdir(f'{OUT}/src3'):
        i = int(fn[2:-4])
        sf = Image.open(f'{OUT}/src3/{fn}').convert('RGB').resize((240, 68))
        d = ImageChops.difference(cd, sf).convert('L')
        h = d.histogram(); tot = 240 * 68
        m = sum(k * c for k, c in enumerate(h)) / tot
        if best is None or m < best[1]: best = (i, m)
    print(f'  f={f:<6} frame {best[0]:>3}  diff {best[1]:5.1f}')
