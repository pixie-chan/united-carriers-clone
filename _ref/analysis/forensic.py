#!/usr/bin/env python3
"""Full forensic: match live's crane-canvas dumps against ALL 5 sequences, all phases."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/forensic'
os.makedirs(f'{OUT}/live', exist_ok=True)
os.makedirs(f'{OUT}/reb', exist_ok=True)
os.makedirs(f'{OUT}/src', exist_ok=True)
W, H = 1920, 1080

PHASES_LIVE = [1.0, 1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
PHASES_REB = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))

DUMP_SRC_JS = """
async ({ seqs, dst }) => {
  const canvas = document.querySelector('#craneCanvas');
  const cw = canvas.width, ch = canvas.height;
  const tmp = document.createElement('canvas');
  tmp.width = cw; tmp.height = ch;
  const ctx = tmp.getContext('2d');
  const out = {};
  for (let s = 0; s < seqs.length; s++) {
    const names = seqs[s];
    const step = names.length > 80 ? 3 : 2;
    for (let i = 0; i < names.length; i += step) {
      const img = new Image();
      img.src = 'assets/frames/' + names[i];
      await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('fail ' + names[i])); });
      const sc = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
      const dw = img.naturalWidth * sc, dh = img.naturalHeight * sc;
      ctx.clearRect(0, 0, cw, ch);
      ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
      out[s + '_' + i] = tmp.toDataURL('image/png');
    }
  }
  return out;
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # ---------- live dumps ----------
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8899/unitedcarriers.com/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    canvases = page.evaluate("""
      [...document.querySelectorAll('.home-service canvas')].map(c => ({
        cls: c.parentElement.className, w: c.width, h: c.height }))
    """)
    print('live canvases in .home-service:', json.dumps(canvases))
    for f in PHASES_LIVE:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1500)
        data = page.evaluate("document.querySelector('.home-service-crane canvas').toDataURL('image/png')")
        open(f'{OUT}/live/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
        print('live', f, flush=True)
    page.close()

    # ---------- reb: src frames + dumps ----------
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    srcs = page.evaluate(DUMP_SRC_JS, {'seqs': seqs})
    for k, data in srcs.items():
        open(f'{OUT}/src/{k}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    print('src frames:', len(srcs))
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    for f in PHASES_REB:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1500)
        for cid, sel in (('f', '#craneCanvas'), ('t', '.svc-containers') ):
            pass
        data = page.evaluate("document.querySelector('#craneCanvas').toDataURL('image/png')")
        open(f'{OUT}/reb/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
        tdata = page.evaluate("document.querySelector('#truckCanvas').toDataURL('image/png')")
        open(f'{OUT}/reb/t{f}.png', 'wb').write(base64.b64decode(tdata.split(',', 1)[1]))
        print('reb', f, flush=True)
    page.close()
    b.close()

# ---------- matching ----------
src_keys = {}
for fn in os.listdir(f'{OUT}/src'):
    s, i = fn[:-4].split('_')
    src_keys.setdefault(int(s), []).append(int(i))
for s in src_keys: src_keys[s] = sorted(src_keys[s])

def match(img_path, allow_seqs=(0, 1, 2, 3, 4)):
    cd = Image.open(img_path).convert('RGB').resize((180, 101))
    best = None
    for s in allow_seqs:
        for i in src_keys.get(s, []):
            sf = Image.open(f'{OUT}/src/{s}_{i}.png').convert('RGB').resize((180, 101))
            d = ImageChops.difference(cd, sf).convert('L')
            h = d.histogram(); tot = 180 * 101
            m = sum(k * c for k, c in enumerate(h)) / tot
            if best is None or m < best[2]: best = (s, i, m)
    return best

print()
print('LIVE canvas timeline (best seq/frame):')
for f in PHASES_LIVE:
    s, i, m = match(f'{OUT}/live/f{f}.png')
    print(f'  f={f:<5} seq{s} frame {i:>3}  diff {m:5.1f}')
print()
print('REB crane canvas timeline:')
for f in PHASES_REB:
    s, i, m = match(f'{OUT}/reb/f{f}.png')
    print(f'  f={f:<5} seq{s} frame {i:>3}  diff {m:5.1f}')
print()
print('REB truck canvas timeline:')
for f in PHASES_REB:
    s, i, m = match(f'{OUT}/reb/t{f}.png')
    print(f'  f={f:<5} seq{s} frame {i:>3}  diff {m:5.1f}')
