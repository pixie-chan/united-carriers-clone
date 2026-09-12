#!/usr/bin/env python3
"""Final-final mirror localizer v4: entity-safe, paren-safe, stubs the 403 placeholder."""
import os, re, urllib.request, urllib.parse as up

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}
CDN_DIR = os.path.join(M, 'cdn.prod.website-files.com')

# stub the hotlink-protected Webflow placeholder
ph_path = os.path.join(CDN_DIR, 'plugins/Basic/assets/placeholder.60f9b1840c.svg')
os.makedirs(os.path.dirname(ph_path), exist_ok=True)
if not os.path.exists(ph_path):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">'
           '<rect width="600" height="400" fill="#e6e6e6"/>'
           '<path d="M260 175h80v50h-80z" fill="#c9c9c9"/></svg>')
    with open(ph_path, 'w') as f:
        f.write(svg)
    print('stubbed placeholder.svg')

def local_for(url):
    p = up.urlparse(url).path
    segs = [s for s in p.split('/') if s != '']
    dec = up.unquote('/'.join(segs))
    return os.path.normpath(os.path.join(CDN_DIR, dec))

files = []
for root, dirs, fs in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in fs:
        if fn.endswith(('.html', '.css')):
            files.append(os.path.join(root, fn))

url_pat = re.compile(r'https://cdn\.prod\.website-files\.com/[^"\'\s<>&]+(&(amp|quot|#\d+|#x[0-9a-fA-F]+);)*[^"\'\s<>]*?\.(?:jpe?g|png|webp|avif|svg|gif|mp4|webm|css|js|woff2?)')
url_pat2 = re.compile(r'https://cdn\.prod\.website-files\.com/[^"\'\s<>]+')

ENT = re.compile(r'(&(quot|amp|#\d+|#x[0-9a-fA-F]+);)+$')

def clean(u):
    u = ENT.sub('', u)
    # trim unbalanced trailing parens
    while u.endswith(')') and u.count(')') > u.count('('):
        u = u[:-1]
    return u

def download(url):
    local = local_for(url)
    if os.path.exists(local) and os.path.getsize(local) > 0:
        return True
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=120).read()
        with open(local, 'wb') as f:
            f.write(data)
        print('DL', os.path.relpath(local, CDN_DIR)[:110], len(data))
        return True
    except Exception as e:
        print('FAIL', url[:120], '->', str(e)[:60])
        return False

def rel(url, page):
    local = local_for(url)
    if not os.path.exists(local):
        return None
    r = os.path.relpath(local, os.path.dirname(page)).replace(os.sep, '/')
    return r.replace(' ', '%20')

ok = fail = rw = 0
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    if 'cdn.prod.website-files.com' not in h:
        continue
    orig = h

    def repl(m):
        global ok, fail
        chunk = m.group(0)
        tail = ''
        u = clean(chunk)
        tail = chunk[len(u):]  # keep trailing entities/parens after url
        parts = re.split(r',(?=https?://)', u)
        out = []
        for part in parts:
            if not part.startswith('http'):
                out.append(part)
                continue
            if download(part):
                ok += 1
                r = rel(part, p)
                out.append(r if r else part)
            else:
                fail += 1
                out.append(part)
        return ','.join(out) + tail

    h = url_pat2.sub(repl, h)
    if h != orig:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(h)
        rw += 1
print(f'ok={ok} fail={fail} rewritten={rw}')

left = 0
lefts = []
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    for m in url_pat2.finditer(h):
        u = clean(m.group(0))
        if local_for(u).startswith(M) and not os.path.exists(local_for(u)):
            left += 1
            if len(lefts) < 8:
                lefts.append((os.path.basename(p), u[:110]))
print('unresolved:', left)
for x in lefts:
    print('  ', x)
