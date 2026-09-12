#!/usr/bin/env python3
"""Rasterize land polygons into sphere dot points (same math as their worker) for the rebuild."""
import json, math

SRC = '/home/zen/projects/united-carriers-clone/site/data/land-110m.json'
OUT = '/home/zen/projects/united-carriers-clone/site/data/globe-points.json'

src = json.load(open(SRC))
tr = src['transform']
sx, sy = tr['scale']
tx, ty = tr['translate']

arcs = []
for arc in src['arcs']:
    pts = []
    x = y = 0
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)

def ring_from(idxs):
    pts = []
    for i in idxs:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts

polys = []
for geom in src['objects']['land']['geometries']:
    if geom['type'] == 'MultiPolygon':
        for poly in geom['arcs']:
            polys.append([ring_from(r) for r in poly])
    elif geom['type'] == 'Polygon':
        polys.append([ring_from(r) for r in geom['arcs']])

def in_ring(lon, lat, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

STEP = 1.2
points = []
for rings in polys:
    outer = rings[0]
    lons = [p[0] for p in outer]
    lats = [p[1] for p in outer]
    if not lons:
        continue
    minLon, maxLon = min(lons), max(lons)
    minLat, maxLat = min(lats), max(lats)
    lat = math.floor((minLat - 1) / STEP) * STEP
    while lat <= maxLat + 1:
        cosl = max(0.15, math.cos(math.radians(lat)))
        lonStep = STEP / cosl
        odd = round(abs(lat / STEP)) % 2
        lon = math.floor((minLon - 1) / lonStep) * lonStep + (lonStep * 0.5 if odd else 0)
        while lon <= maxLon + 1:
            if in_ring(lon, lat, outer) and not any(in_ring(lon, lat, r) for r in rings[1:]):
                phi = math.radians(90 - max(-90, min(90, lat)))
                th = math.radians(lon + 180)
                x = -math.sin(phi) * math.cos(th)
                y = math.cos(phi)
                z = math.sin(phi) * math.sin(th)
                points.append([round(x, 4), round(y, 4), round(z, 4)])
            lon += lonStep
        lat += STEP

json.dump({'points': points, 'tileDeg': STEP}, open(OUT, 'w'))
print('polygons:', len(polys), '| dot points:', len(points), '| saved', OUT)
