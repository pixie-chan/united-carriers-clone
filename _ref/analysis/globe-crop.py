#!/usr/bin/env python3
"""Detect the globe disc extent in live vs rebuild screenshots + crop comparison."""
from PIL import Image, ImageDraw

LIVE = '/home/zen/projects/united-carriers-clone/_ref/analysis/verify/live-y0.png'
MINE = '/home/zen/projects/united-carriers-clone/_ref/analysis/qa/r-y0.png'
OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/qa/globe-cmp.png'

a = Image.open(LIVE).convert('RGB')
b = Image.open(MINE).convert('RGB')

def disc(img, thr=80):
    g = img.convert('L')
    px = g.load()
    minx, maxx, miny, maxy = 9999, 0, 9999, 0
    for y in range(0, img.size[1], 2):
        for x in range(700, img.size[0], 2):
            if px[x, y] > thr:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    return (minx, miny, maxx, maxy)

da = disc(a)
db = disc(b)
print('live bright-region bbox:', da, 'centre', ((da[0] + da[2]) // 2, (da[1] + da[3]) // 2), 'size', (da[2] - da[0], da[3] - da[1]))
print('mine bright-region bbox:', db, 'centre', ((db[0] + db[2]) // 2, (db[1] + db[3]) // 2), 'size', (db[2] - db[0], db[3] - db[1]))

crop = (680, 0, 1440, 900)
ca = a.crop(crop)
cb = b.crop(crop)
w = crop[2] - crop[0]
h = crop[3] - crop[1]
comp = Image.new('RGB', (w, h * 2 + 30), 'white')
comp.paste(ca, (0, 0))
comp.paste(cb, (0, h + 30))
ImageDraw.Draw(comp).text((8, h + 9), 'TOP=live  BOTTOM=rebuild  (globe region)', fill='black')
comp.save(OUT)
print('saved', OUT)
