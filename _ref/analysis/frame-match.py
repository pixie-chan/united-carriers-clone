#!/usr/bin/env python3
"""Dump source frames (via in-page decode) + match them against the live canvas dumps."""
import os, json, base64, hashlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import io

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2'
CDIR = f'{OUT}/canvas'
os.makedirs(f'{CDIR}/src', exist_ok=True)
W, H = 1920, 1080

PAGE_JS = """
async (names) => {
  const canvas = document.getElementById('craneCanvas');
  const cw = canvas.width, ch = canvas.height;
  const tmp = document.createElement('canvas');
  tmp.width = cw; tmp.height = ch;
  const ctx = tmp.getContext('2d');
  const out = {};
  for (const [i, name] of names) {
    const img = new Image();
    img.src = 'assets/frames/' + name;
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; });
    const s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
    const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
    out[i] = tmp.toDataURL('image/png');
  }
  return out;
}
"""

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))
seq0 = seqs[0]
idx_list = [0, 10, 20, 30, 45, 60, 80, 100, 120, 135, 150, 158]
names = [(i, seq0[i]) for i in idx_list]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=90000)
    page.wait_for_timeout(8000)
    dumps = page.evaluate(PAGE_JS, names)
    for i, data in dumps.items():
        raw = data.split(',', 1)[1]
        open(f'{CDIR}/src/frame-{int(i):03d}.png', 'wb').write(base64.b64decode(raw))
        print('src frame', i, seq0[int(i)], 'len', len(raw))
    b.close()

# --- compare source frames among themselves
print()
print('source frame self-diffs (mean, >16%):')
base = Image.open(f'{CDIR}/src/frame-000.png').convert('RGB')
for i in idx_list:
    im = Image.open(f'{CDIR}/src/frame-{i:03d}.png').convert('RGB')
    d = ImageChops.difference(base, im).convert('L')
    h = d.histogram(); tot = im.size[0]*im.size[1]
    print(f'  f000 vs f{i:03d}: mean {sum(k*c for k,c in enumerate(h))/tot:6.2f}  >16: {sum(h[16:])/tot*100:5.1f}%')

# --- match canvas dumps against source frames
print()
print('canvas dump best-match source frame:')
for f in sorted(os.listdir(CDIR)):
    if not f.startswith('crane-'): continue
    cd = Image.open(f'{CDIR}/{f}').convert('RGB')
    small = cd.resize((180, 101))
    best = None
    for i in idx_list:
        sf = Image.open(f'{CDIR}/src/frame-{i:03d}.png').convert('RGB').resize((180, 101))
        d = ImageChops.difference(small, sf).convert('L')
        h = d.histogram(); tot = 180*101
        m = sum(k*c for k,c in enumerate(h))/tot
        if best is None or m < best[1]: best = (i, m)
    print(f'  {f}: best frame {best[0]:3d} (mean diff {best[1]:.2f})')
