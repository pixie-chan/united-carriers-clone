#!/usr/bin/env python3
"""Strip integrity attributes (SRI breaks after local rewriting) + fetch finsweet chunks."""
import os, re, urllib.request

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}

n = 0
for root, dirs, fs in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in fs:
        if fn.endswith('.html'):
            p = os.path.join(root, fn)
            h = open(p, encoding='utf-8', errors='ignore').read()
            h2 = re.sub(r'\s+integrity="[^"]*"', '', h)
            if h2 != h:
                open(p, 'w', encoding='utf-8').write(h2)
                n += 1
print('stripped integrity in', n, 'files')

# finsweet: find chunk refs in the vendored file, download them from jsdelivr
p = os.path.join(M, '_vendor', 'finsweet-attributes.js')
t = open(p, encoding='utf-8', errors='ignore').read() if os.path.exists(p) else ''
refs = sorted(set(re.findall(r'["\'](\.{0,2}/?(?:dist/)?chunk-[A-Z0-9]+\.js)["\']', t)))
print('finsweet chunk refs found:', len(refs))
os.makedirs(os.path.join(M, '_vendor', 'dist'), exist_ok=True)
got = 0
for r in refs:
    name = r.split('/')[-1]
    url = 'https://cdn.jsdelivr.net/npm/@finsweet/attributes@2/dist/' + name
    dst = os.path.join(M, '_vendor', 'dist', name)
    if os.path.exists(dst):
        continue
    try:
        req = urllib.request.Request(url, headers=UA)
        d = urllib.request.urlopen(req, timeout=60).read()
        open(dst, 'wb').write(d)
        got += 1
    except Exception as e:
        print('FAIL', name, str(e)[:60])
print('finsweet chunks downloaded:', got)

# check what attributes.js actually imports precisely
imports = re.findall(r'import[^;]{0,120};', t)[:6]
for i in imports:
    print('IMPORT>', i[:140])
