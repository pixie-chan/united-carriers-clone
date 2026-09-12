#!/usr/bin/env python3
"""Compare live vs local mirror screenshots: pixel stats + side-by-side composites."""
from PIL import Image, ImageChops, ImageDraw

OUT = '/home/zen/projects/united-carriers-clone/_ref/analysis/verify'
YS = [0, 1800, 3220, 14160, 19920, 22900, 25300, 27400, 27900]

rows = []
for y in YS:
    a = Image.open(f'{OUT}/live-y{y}.png').convert('RGB')
    b = Image.open(f'{OUT}/local-y{y}.png').convert('RGB')
    diff = ImageChops.difference(a, b)
    h = diff.convert('L').histogram()
    tot = a.size[0] * a.size[1]
    pct16 = sum(h[16:]) / tot * 100      # pixels differing noticeably
    pct48 = sum(h[48:]) / tot * 100      # pixels differing a lot
    rows.append((y, pct16, pct48, diff.getbbox()))
    comp = Image.new('RGB', (a.size[0], a.size[1] * 2 + 34), 'white')
    comp.paste(a, (0, 0))
    comp.paste(b, (0, a.size[1] + 34))
    d = ImageDraw.Draw(comp)
    d.text((12, a.size[1] + 10), f'TOP = live unitedcarriers.com    BOTTOM = local mirror    scroll y={y}', fill='black')
    comp.save(f'{OUT}/cmp-y{y}.png')

print(f'{"y":>6}  {"diff>16":>8}  {"diff>48":>8}  bbox')
for y, a, b, bbox in rows:
    print(f'{y:>6}  {a:>7.2f}%  {b:>7.2f}%  {bbox}')
