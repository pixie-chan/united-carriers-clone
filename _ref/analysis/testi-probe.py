#!/usr/bin/env python3
"""Testi post-pass numeric probes over the paired captures.

- content wipe edge x at rows (first white run scanning from left)
- plane presence: count of saturated colorful pixels in the mid strip
Usage: python3 testi-probe.py [dir]
"""
import sys
import numpy as np
from PIL import Image

D = sys.argv[1] if len(sys.argv) > 1 else '/home/zen/projects/united-carriers-clone/_ref/analysis/repro2/testi1440'
PHASES = [-1.0, -0.5, 0.0, 0.3, 0.6, 0.9, 1.2, 1.6, 2.0, 2.6]


def content_edge(path, y):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=int)
    row = a[y]
    for x in range(0, a.shape[1]):
        if row[x, 0] > 235 and row[x, 1] > 235 and row[x, 2] > 235:
            seg = row[x:x+40]
            if np.all(seg[:, 0] > 230) and np.all(seg[:, 2] > 230):
                return x
    return -1


def plane_score(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=float)
    strip = a[250:700, :, :]
    mx = strip.max(axis=2)
    mn = strip.min(axis=2)
    sat = mx - mn
    m = np.logical_and(sat > 60, mx > 120)
    return int(m.sum())


print(f'{"f":>5} | live edge | reb edge | live plane | reb plane')
for f in PHASES:
    try:
        le = content_edge(f'{D}/live-f{f}.png', 450)
        re_ = content_edge(f'{D}/reb-f{f}.png', 450)
        lp = plane_score(f'{D}/live-f{f}.png')
        rp = plane_score(f'{D}/reb-f{f}.png')
        print(f'{f:>5} | {le:>9} | {re_:>8} | {lp:>10} | {rp:>9}')
    except FileNotFoundError as e:
        print(f'{f:>5} | missing: {e.filename}')
