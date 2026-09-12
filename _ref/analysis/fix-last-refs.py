#!/usr/bin/env python3
"""Resolve the last unresolved refs via basename search (decoding quirks), plus report."""
import os, re, urllib.parse as up

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
CDN = os.path.join(M, 'cdn.prod.website-files.com')

# index all files under CDN by basename
by_name = {}
for root, dirs, fs in os.walk(CDN):
    for fn in fs:
        by_name.setdefault(up.unquote(fn), os.path.join(root, fn))

def local_for(url):
    p = up.urlparse(url).path
    segs = [s for s in p.split('/') if s != '']
    dec = up.unquote('/'.join(segs))
    return os.path.normpath(os.path.join(CDN, dec))

ENT = re.compile(r'(&(quot|amp|#\d+|#x[0-9a-fA-F]+);)+$')
pat = re.compile(r'https://cdn\.prod\.website-files\.com/[^"\'\s<>]+')

def clean(u):
    changed = True
    while changed:
        changed = False
        n = ENT.sub('', u)
        if n != u:
            u = n
            changed = True
        while u.endswith(')') and u.count(')') > u.count('('):
            u = u[:-1]
            changed = True
    return u

def resolve(url):
    lf = local_for(url)
    if os.path.exists(lf):
        return lf
    base = up.unquote(url.split('/')[-1])
    # strip query
    base = base.split('?')[0]
    cand = by_name.get(base)
    if cand:
        return cand
    # try partial: name starts with same prefix
    for name, path in by_name.items():
        if name == base:
            return path
    return None

files = []
for root, dirs, fs in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in fs:
        if fn.endswith(('.html', '.css')):
            files.append(os.path.join(root, fn))

fixed = 0
unresolved = []
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    if 'cdn.prod.website-files.com' not in h:
        continue
    orig = h

    def repl(m):
        global fixed
        chunk = m.group(0)
        u = clean(chunk)
        tail = chunk[len(u):]
        lf = resolve(u)
        if lf:
            fixed += 1
            r = os.path.relpath(lf, os.path.dirname(p)).replace(os.sep, '/').replace(' ', '%20')
            return r + tail
        unresolved.append((os.path.basename(p), u[:130]))
        return chunk

    h = pat.sub(repl, h)
    if h != orig:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(h)

print('refs resolved:', fixed)
print('unresolved:', len(unresolved))
for u in unresolved[:10]:
    print('  ', u)

# final sanity: any absolute cdn refs left?
left = 0
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    left += len(pat.findall(h))
print('absolute refs left:', left)

# frame count
frames = 0
for root, dirs, fs in os.walk(CDN):
    for fn in fs:
        if 'frame_' in fn:
            frames += 1
print('frame images on disk:', frames)
