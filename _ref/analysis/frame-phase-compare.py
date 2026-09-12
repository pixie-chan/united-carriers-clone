#!/usr/bin/env python3
"""Compare displayed crane frame index vs scroll for BOTH sites; match against seq[0]."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import io

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/fphase'
os.makedirs(f'{OUT}/live', exist_ok=True)
os.makedirs(f'{OUT}/reb', exist_ok=True)
os.makedirs(f'{OUT}/src', exist_ok=True)
W, H = 1920, 1080
PHASES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]

CANVAS_SEL = {
    'live': '.home-service-crane canvas',
    'reb': '#craneCanvas',
}

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))
seq0 = seqs[0]
idx_list = list(range(0, 159, 4))  # every 4th frame for matching
src_names = [(i, seq0[i]) for i in idx_list]

PAGE_JS = """
async ({ sel, names, out }) => {
  const canvas = document.querySelector(sel);
  const cw = canvas.width, ch = canvas.height;
  const tmp = document.createElement('canvas');
  tmp.width = cw; tmp.height = ch;
  const ctx = tmp.getContext('2d');
  // dump canvas current content
  const live = canvas.toDataURL('image/png');
  // dump source frames at same size
  const srcs = {};
  for (const [i, name] of names) {
    const img = new Image();
    img.src = 'assets/frames/' + name;
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; });
    const s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
    const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
    srcs[i] = tmp.toDataURL('image/png');
  }
  return { live, srcs };
}
"""

def dump_srcs(page, sel, subdir):
    r = page.evaluate(PAGE_JS, {'sel': sel, 'names': src_names})
    open(f'{OUT}/{subdir}/canvas.png', 'wb').write(base64.b64decode(r['live'].split(',', 1)[1]))
    for i, data in r['srcs'].items():
        p = f'{OUT}/src/frame-{int(i):03d}.png'
        if not os.path.exists(p):
            open(p, 'wb').write(base64.b64decode(data.split(',', 1)[1]))

def run(url, subdir):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport={'width': W, 'height': H}).new_page()
        page.goto(url, wait_until='load', timeout=120000)
        page.wait_for_timeout(9000)
        svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
        for f in PHASES:
            y = int(svcTop + f * H)
            page.evaluate(f'window.scrollTo(0, {y})')
            page.wait_for_timeout(1600)
            sel = CANVAS_SEL[subdir]
            data = page.evaluate(f"document.querySelector('{sel}').toDataURL('image/png')")
            open(f'{OUT}/{subdir}/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
            print(subdir, f, 'saved', flush=True)
        dump_srcs(page, CANVAS_SEL[subdir], subdir)
        b.close()

run('http://127.0.0.1:8899/unitedcarriers.com/index.html', 'live')
run('http://127.0.0.1:8898/index.html', 'reb')

print()
print('best-match frame index per phase:')
print(f'{"f":>5} | {"live":>6} | {"reb":>6}')
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
    print(f'{f:>5} | {row[0]:>10} | {row[1]:>10}')
