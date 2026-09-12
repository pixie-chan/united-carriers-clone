#!/usr/bin/env python3
"""Post-fix QA: verify crane chain mapping + screenshots vs live pairs."""
import os, json, base64
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/fixqa'
os.makedirs(f'{OUT}/sh', exist_ok=True)
os.makedirs(f'{OUT}/can', exist_ok=True)
os.makedirs(f'{OUT}/src', exist_ok=True)

SVC_F = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.25, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
WHY_F = [1.0, 2.0, 3.5, 5.0, 6.5]
W, H = 1920, 1080

seqs = json.load(open('/home/zen/projects/united-carriers-clone/site/data/frames-sequences.json'))
chain = seqs[0] + seqs[1] + seqs[2]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={'width': W, 'height': H}).new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)[:200]))
    page.goto('http://127.0.0.1:8898/index.html', wait_until='load', timeout=120000)
    page.wait_for_timeout(9000)
    svcTop = page.evaluate("document.querySelector('.home-service').getBoundingClientRect().top + scrollY")
    whyTop = page.evaluate("document.querySelector('.home-why-wrap') ? document.querySelector('.home-why-wrap').getBoundingClientRect().top + scrollY : document.querySelector('.home-why').getBoundingClientRect().top + scrollY")

    # src frames of the chain, at crane canvas size, step 2 (for matching)
    js = """
    async ({ names, w, h }) => {
      const tmp = document.createElement('canvas'); tmp.width = w; tmp.height = h;
      const ctx = tmp.getContext('2d');
      const out = {};
      for (let i = 0; i < names.length; i += 2) {
        const img = new Image();
        img.src = 'assets/frames/' + names[i];
        await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('fail ' + names[i])); });
        const sc = Math.max(w / img.naturalWidth, h / img.naturalHeight);
        const dw = img.naturalWidth * sc, dh = img.naturalHeight * sc;
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
        out[i] = tmp.toDataURL('image/png');
      }
      return out;
    }
    """
    srcs = page.evaluate(js, {'names': chain, 'w': 1785, 'h': 1004})
    for i, data in srcs.items():
        open(f'{OUT}/src/{int(i):03d}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    print('chain src frames:', len(srcs))

    print()
    print('crane canvas timeline after fix (global chain idx -> seq/local):')
    LENS = [len(seqs[0]), len(seqs[1]), len(seqs[2])]
    for f in SVC_F:
        y = int(svcTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1300)
        page.screenshot(path=f'{OUT}/sh/reb-svc-f{f}.png')
        if f <= 5.0:
            data = page.evaluate("document.getElementById('craneCanvas').toDataURL('image/png')")
            open(f'{OUT}/can/f{f}.png', 'wb').write(base64.b64decode(data.split(',', 1)[1]))
    # why shots
    for f in WHY_F:
        y = int(whyTop + f * H)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(1600)
        page.screenshot(path=f'{OUT}/sh/reb-why-f{f}.png')
    print('page errors:', errs[:5])
    b.close()

# match canvas dumps
print()
print('  f   | best chain idx | seq/local')
for f in SVC_F:
    path = f'{OUT}/can/f{f}.png'
    if not os.path.exists(path):
        continue
    cd = Image.open(path).convert('RGB').resize((180, 101))
    best = None
    for fn in os.listdir(f'{OUT}/src'):
        i = int(fn[:-4])
        sf = Image.open(f'{OUT}/src/{fn}').convert('RGB').resize((180, 101))
        d = ImageChops.difference(cd, sf).convert('L')
        h = d.histogram(); tot = 180 * 101
        m = sum(k * c for k, c in enumerate(h)) / tot
        if best is None or m < best[1]: best = (i, m)
    i, m = best
    seq = 0 if i < LENS[0] else (1 if i < LENS[0] + LENS[1] else 2)
    loc = i - (0 if seq == 0 else LENS[0] if seq == 1 else LENS[0] + LENS[1])
    print(f'  {f:<5} | {i:>3} (diff {m:4.1f}) | seq{seq} frame {loc}')

# composites vs live (where available)
print()
def comp(reb, live, out):
    if not (os.path.exists(reb) and os.path.exists(live)):
        print('skip (missing):', out); return
    a = Image.open(live).convert('RGB'); c = Image.open(reb).convert('RGB')
    m = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    m.paste(a, (0, 0)); m.paste(c, (0, a.size[1] + 34))
    ImageDraw.Draw(m).text((12, a.size[1] + 10), f'TOP=live BOTTOM=rebuild {out}', fill='black')
    m.save(f'{OUT}/cmp-{out}.png')

LIVE_SVC = {
    '1.0': 'sweep/live-f01.0.png', '2.0': 'sweep/live-f02.0.png', '3.0': 'sweep/live-f03.0.png',
    '4.0': 'sweep/live-f04.0.png', '4.5': 'sweep/live-f04.5.png', '5.0': 'endgame/live-f05.0.png',
    '5.5': 'endgame/live-f05.5.png', '6.0': 'endgame/live-f06.0.png', '6.25': 'endgame/live-f06.2.png',
    '7.0': 'endgame/live-f07.0.png', '7.5': 'endgame/live-f07.5.png', '8.0': 'endgame/live-f08.0.png',
    '8.5': 'endgame/live-f08.5.png', '9.0': 'endgame/live-f09.0.png',
}
BASE = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2'
for f, lp in LIVE_SVC.items():
    comp(f'{OUT}/sh/reb-svc-f{f}.png', f'{BASE}/{lp}', f'svc-{f}')

LIVE_WHY = {'1.0': 'pair/live-why-f1.png', '2.0': 'pair/live-why-f2.png', '3.5': 'pair/live-why-f3_5.png',
            '5.0': 'pair/live-why-f5.png', '6.5': 'pair/live-why-f6_5.png'}
for f, lp in LIVE_WHY.items():
    comp(f'{OUT}/sh/reb-why-f{f}.png', f'{BASE}/{lp}', f'why-{f}')
print('done')
