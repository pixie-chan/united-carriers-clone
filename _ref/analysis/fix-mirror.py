#!/usr/bin/env python3
"""Fold netlify bundle + vendor libs into the mirror, rewrite external refs, inventory videos."""
import os, re, shutil, urllib.request

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
A = '/home/zen/projects/united-carriers-clone/_ref/analysis'

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}

# 1. netlify bundle into the mirror
dst = os.path.join(M, '_netlify')
if not os.path.exists(dst):
    shutil.copytree(os.path.join(A, 'netlify'), dst)
    print('copied netlify bundle ->', dst)

# 2. vendor libs
os.makedirs(os.path.join(M, '_vendor'), exist_ok=True)
def fetch(url, path):
    if os.path.exists(path):
        return
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=60).read()
    with open(path, 'wb') as f:
        f.write(data)
    print('fetched', os.path.basename(path), len(data))

fetch('https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js?site=6a44eec1ed1af2c4c403df6b',
      os.path.join(M, '_vendor', 'jquery-3.5.1.min.js'))
fetch('https://cdn.jsdelivr.net/npm/@finsweet/attributes@2/attributes.js',
      os.path.join(M, '_vendor', 'finsweet-attributes.js'))

# 3. rewrite refs in html/css
PATS = [
    (re.compile(r'https://united-carriers\.netlify\.app(/[^"\'\s)]*)?'), '_netlify'),
    (re.compile(r'https://d3e54v103j8qbb\.cloudfront\.net/js/jquery-3\.5\.1\.min\.dc5e7f18c8\.js\?site=6a44eec1ed1af2c4c403df6b'), '_vendor/jquery-3.5.1.min.js'),
    (re.compile(r'https://cdn\.jsdelivr\.net/npm/@finsweet/attributes@2/attributes\.js'), '_vendor/finsweet-attributes.js'),
]
count = 0
for root, dirs, files in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in files:
        if not fn.endswith(('.html', '.css')):
            continue
        p = os.path.join(root, fn)
        h = open(p, encoding='utf-8', errors='ignore').read()
        orig = h
        for pat, targetdir in PATS:
            if not pat.search(h):
                continue
            if pat.match(h) is None and pat.search(h) is None:
                continue
            def repl(m, targetdir=targetdir, p=p):
                suffix = (m.group(1) or '') if m.re.groups else ''
                rel = os.path.relpath(os.path.join(M, targetdir), os.path.dirname(p)).replace(os.sep, '/')
                return rel + suffix
            h = pat.sub(repl, h)
        if h != orig:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(h)
            count += 1
print('rewrote', count, 'files')

# 4. inspect remaining absolute CDN refs in index.html
idx = os.path.join(M, 'unitedcarriers.com', 'index.html')
h = open(idx, encoding='utf-8').read()
rem = [(m.start(), m.group(0)) for m in re.finditer(r'https://cdn\.prod\.website-files\.com[^"\'\s)]*', h)]
print('\nremaining absolute CDN refs in index.html:', len(rem))
for pos, u in rem[:14]:
    ctx = h[max(0, pos - 60):pos + len(u) + 20].replace('\n', ' ')
    print('  ...', ctx[:220])

# 5. sitewide video / poster inventory
vids = set()
pos_v = set()
for root, dirs, files in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in files:
        if not fn.endswith('.html'):
            continue
        hh = open(os.path.join(root, fn), encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'data-video-urls="([^"]+)"', hh):
            for u in m.group(1).split(','):
                u = u.strip()
                if u:
                    vids.add(u)
        for m in re.finditer(r'data-poster-url="([^"]+)"', hh):
            pos_v.add(m.group(1).strip())
vids = sorted({v if v.startswith('http') else 'https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/' + v.lstrip('/') for v in vids})
print('\nVIDEO URLS:', len(vids))
for v in vids[:25]:
    print('  ', v)
print('\nPOSTER URLS:', len(pos_v))
for v in list(sorted(pos_v))[:12]:
    print('  ', v)
