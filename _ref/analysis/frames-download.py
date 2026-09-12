#!/usr/bin/env python3
"""Download all 747 frame-sequence images into the mirror (concurrent)."""
import os, sys, urllib.request, concurrent.futures as cf

M = '/home/zen/projects/united-carriers-clone/_ref/mirror'
CDN = os.path.join(M, 'cdn.prod.website-files.com')
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}

urls = [u.strip() for u in open('/tmp/frame-urls.txt') if u.strip()]
print('frames to check:', len(urls))

def fetch(url):
    name = url.split('/')[-1]
    path = os.path.join(CDN, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return ('skip', 0)
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=60).read()
        with open(path, 'wb') as f:
            f.write(data)
        return ('ok', len(data))
    except Exception as e:
        return ('fail:' + str(e)[:60], 0)

ok = skip = fail = 0
bytes_ = 0
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for res, n in ex.map(fetch, urls):
        if res == 'ok':
            ok += 1
            bytes_ += n
        elif res == 'skip':
            skip += 1
        else:
            fail += 1
            print('FAIL', res)
print(f'done: downloaded={ok} skipped={skip} failed={fail} bytes={bytes_/1e6:.1f}MB')
