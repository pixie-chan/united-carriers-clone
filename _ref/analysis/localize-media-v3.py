#!/usr/bin/env python3
"""Final mirror localizer: handles comma-separated URL lists, downloads stragglers, rewrites refs. v3."""
import os, re, urllib.request, urllib.parse as up

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}
CDN_DIR = os.path.join(M, 'cdn.prod.website-files.com')

def local_for(url):
    p = up.urlparse(url).path
    segs = [s for s in p.split('/') if s != '']
    dec = up.unquote('/'.join(segs))
    return os.path.normpath(os.path.join(CDN_DIR, dec))

# clean junk files (comma-chained names)
junk = 0
for root, dirs, fs in os.walk(CDN_DIR):
    for fn in fs:
        if ',http' in fn or fn.endswith(',https'):
            os.remove(os.path.join(root, fn))
            junk += 1
print('junk removed:', junk)

files = []
for root, dirs, fs in os.walk(M):
    if os.sep + '_netlify' in root or os.sep + '_vendor' in root:
        continue
    for fn in fs:
        if fn.endswith(('.html', '.css')):
            files.append(os.path.join(root, fn))

url_pat = re.compile(r'https://cdn\.prod\.website-files\.com/[^"\'\s<>)]+')

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
        print('FAIL', url[:130], '->', str(e)[:80])
        return False

def rel(url, page):
    local = local_for(url)
    if not os.path.exists(local):
        return None
    r = os.path.relpath(local, os.path.dirname(page)).replace(os.sep, '/')
    return r.replace(' ', '%20')

dl_ok = dl_fail = 0
rw = 0
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    if 'cdn.prod.website-files.com' not in h:
        continue
    orig = h
    def repl(m):
        global dl_ok, dl_fail
        chunk = m.group(0)
        # expanded chunks can include ",http" chains (attribute lists)
        parts = re.split(r',(?=https?://)', chunk)
        out = []
        for u in parts:
            if not u.startswith('http'):
                out.append(u)
                continue
            if download(u):
                dl_ok += 1
                r = rel(u, p)
                out.append(r if r else u)
            else:
                dl_fail += 1
                out.append(u)
        return ','.join(out)
    h = url_pat.sub(repl, h)
    if h != orig:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(h)
        rw += 1
print(f'refs: ok={dl_ok} fail={dl_fail} | files rewritten={rw}')

left = {}
for p in files:
    h = open(p, encoding='utf-8', errors='ignore').read()
    ms = url_pat.findall(h)
    if ms:
        left[p] = ms[:3]
print('remaining files:', len(left))
for k, v in list(left.items())[:10]:
    print(' ', k.replace(M, ''), len(v), v[:1])
