#!/usr/bin/env python3
"""Match live+reb crane canvas dumps (fphase/) against seq0, src frames from reb page."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/fphase'
W, H = 1920, 1080
PHASES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))
seq0 = seqs[0]
idx_list = list(range(0, 159, 2))

PAGE_JS = """
async (names) => {
  const canvas = document.querySelector('#craneCanvas');
  const cw = canvas.width, ch = canvas.height;
  const tmp = document.createElement('canvas');
  tmp.width = cw; tmp.height = ch;
  const ctx = tmp.getContext('2d');
  const srcs = {};
  for (const [i, name] of names) {
    const img = new Image();
    img.src = 'assets/frames/' + name;
    await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('load fail ' + name)); });
    const s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
    const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
    srcs[i] = tmp.toDataURL('image/png');
  }
  return srcs;
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    # dump src frames
    names = [(i, seq0[i]) for i in idx_list]
    srcs = page.evaluate(PAGE_JS, names)
    for i, data in srcs.items():
        open(f'{OUT}/src/frame-{int(i):03d}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    print('src frames dumped:', len(srcs))
    # dump reb canvas at phases
    os.makedirs(f'{OUT}/reb', exist_ok=True)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    for f in PHASES:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1600)
        data = page.evaluate("document.querySelector('#craneCanvas').toDataURL('image/png')")
        open(f'{OUT}/reb/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
        print('reb', f, 'saved', flush=True)
    b.close()

print()
print(f'{"f":>5} | {"live":>12} | {"reb":>12}')
for f in PHASES:
    row = []
    for sub in ('live', 'reb'):
        cd = Image.open(f'{OUT}/{sub}/f{f}.png').convert('RGB').resize((180, 101))
        best = None
        for i in idx_list:
            sf = Image.open(f'{OUT}/src/frame-{i:03d}.png').convert('RGB').resize((180, 101))
            d = ImageChops.difference(cd, sf).convert('L')
            h = d.histogram(); tot = 180 * 101
            m = sum(k * c for k, c in enumerate(h)) / tot
            if best is None or m < best[1]: best = (i, m)
        row.append(f'{best[0]:3d} ({best[1]:.1f})')
    print(f'{f:>5} | {row[0]:>12} | {row[1]:>12}')
