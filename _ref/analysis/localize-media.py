#!/usr/bin/env python3
"""Download every remaining absolute CDN media ref into the mirror and rewrite to relative paths. v2 (robust paths)."""
import os, re, urllib.request, urllib.parse as up

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}
CDN_DIR = os.path.join(M, 'cdn.prod.website-files.com')
os.makedirs(CDN_DIR, exist_ok=True)

def local_for(url):
    """Absolute CDN URL -> on-disk path under the mirror (decoded, so %2F becomes a subdir)."""
    p = up.urlparse(url).path
    segs = [s for s in p.split('/') if s != '']
    dec = up.unquote('/'.join(segs))
    return os.path.normpath(os.path.join(CDN_DIR, dec))

files = []
for root, dirs, fs in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in fs:
        if fn.endswith(('.html', '.css', '.js')):
            files.append(os.path.join(root, fn))

pat = re.compile(r'https://cdn\.prod\.website-files\.com/[^"\'\s<>)]+')
found = set()
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    found.update(pat.findall(h))

print('unique absolute CDN urls:', len(found))

dl = skip = fail = 0
for url in sorted(found):
    local = local_for(url)
    if not local.startswith(M + os.sep):
        print('OUT OF TREE', local)
        skip += 1
        continue
    if os.path.exists(local) and os.path.getsize(local) > 0:
        skip += 1
        continue
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=180).read()
        with open(local, 'wb') as f:
            f.write(data)
        dl += 1
        print('DL', os.path.relpath(local, CDN_DIR)[:120], len(data))
    except Exception as e:
        fail += 1
        print('FAIL', url[:140], '->', e)

print(f'downloaded={dl} already-had={skip} failed={fail}')

def to_rel(url, page):
    local = local_for(url)
    if not os.path.exists(local):
        return None
    rel = os.path.relpath(local, os.path.dirname(page)).replace(os.sep, '/')
    return rel.replace(' ', '%20')

rw = 0
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    orig = h
    h = pat.sub(lambda m: (to_rel(m.group(0), p) or m.group(0)), h)
    if h != orig:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(h)
        rw += 1
print('files rewritten:', rw)

left = 0
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    left += len(pat.findall(h))
print('absolute cdn refs remaining:', left)
