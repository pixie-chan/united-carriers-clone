#!/usr/bin/env python3
"""Contact sheets + consecutive-diff for repro2 walks."""
from PIL import Image, ImageChops, ImageDraw
import glob, os

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2'

def sheet(prefix, cols=4, tw=440):
    files = sorted(glob.glob(f'{OUT}/{prefix}-*.png'))
    if not files: return
    th = int(tw * 1080 / 1920)
    rows = (len(files) + cols - 1) // cols
    grid = Image.new('RGB', (cols * tw + (cols+1) * 6, rows * (th+22) + 6), 'black')
    d = ImageDraw.Draw(grid)
    for i, f in enumerate(files):
        im = Image.open(f).convert('RGB').resize((tw, th))
        r, c = divmod(i, cols)
        x = 6 + c * (tw + 6); y = 6 + r * (th + 22)
        grid.paste(im, (x, y))
        d.text((x + 4, y + th + 4), os.path.basename(f).replace(prefix + '-', ''), fill='yellow')
    p = f'{OUT}/sheet-{prefix}.png'
    grid.save(p)
    print('sheet', p, f'{len(files)} shots')

def diffs(prefix):
    files = sorted(glob.glob(f'{OUT}/{prefix}-*.png'))
    prev = None
    for f in files:
        im = Image.open(f).convert('L')
        if prev is not None:
            df = ImageChops.difference(prev[1], im)
            h = df.histogram()
            tot = im.size[0] * im.size[1]
            print(f'{prev[0]} -> {f}: mean {sum(i*c for i,c in enumerate(h))/tot:7.2f}  >16: {sum(h[16:])/tot*100:5.1f}%')
        prev = (os.path.basename(f), im)

sheet('reb')
diffs('reb')
