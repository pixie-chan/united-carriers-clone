#!/usr/bin/env python3
"""Recursively fetch the netlify Vite bundle (main.js + chunks + scene assets)."""
import re, os, urllib.request, urllib.parse

BASE = 'https://united-carriers.netlify.app/'
OUT = 'netlify'
os.makedirs(OUT, exist_ok=True)

EXT = r'(?:js|mjs|css|png|jpe?g|webp|avif|svg|gif|glb|gltf|bin|ktx2|hdr|exr|mp4|webm|json|woff2?|ttf|otf|mp3|wasm)'
pat = re.compile(r'["\'(](?:\.{1,2}/|/)?([A-Za-z0-9_@./-]+\.' + EXT + r')["\'()]')

seen, queue = set(), ['main.js']
count = 0
while queue:
    u = queue.pop(0)
    if u in seen:
        continue
    seen.add(u)
    url = urllib.parse.urljoin(BASE, u)
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
    except Exception as e:
        print('FAIL', u, e)
        continue
    count += 1
    rel = url.replace(BASE, '')
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path) or OUT, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    print('OK', rel, len(data))
    if rel.endswith(('.js', '.mjs', '.css')):
        text = data.decode('utf-8', 'ignore')
        for m in pat.finditer(text):
            nrel = m.group(1)
            if nrel.startswith(('http', '//')):
                continue
            nurl = urllib.parse.urljoin(url, nrel)
            if nurl.startswith(BASE):
                n2 = nurl.replace(BASE, '')
                if n2 not in seen:
                    queue.append(n2)
print('TOTAL DOWNLOADED', count)
