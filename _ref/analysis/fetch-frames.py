#!/usr/bin/env python3
"""Download all service frame-sequence images from the CDN into site/assets/frames/."""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DEST = '/home/zen/projects/united-carriers-clone/site/assets/frames'
os.makedirs(DEST, exist_ok=True)
d = json.load(open('/tmp/frame_arrays.json'))

jobs = {}
for name, arr in d.items():
    for it in arr:
        url = it['hostedUrl']
        fn = url.split('/')[-1]
        jobs[fn] = url
print(f'total unique frames: {len(jobs)}')

done = fail = skip = 0
fails = []

def fetch(item):
    fn, url = item
    path = os.path.join(DEST, fn)
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return ('skip', fn)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 uc-mirror'})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) < 500:
                raise ValueError('too small')
            tmp = path + '.tmp'
            with open(tmp, 'wb') as f:
                f.write(data)
            os.rename(tmp, path)
            return ('ok', fn)
        except Exception as ex:
            if attempt == 2:
                return ('fail', f'{fn}: {ex}')
            time.sleep(1 + attempt)

t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(fetch, it) for it in jobs.items()]
    for i, fut in enumerate(as_completed(futs)):
        status, info = fut.result()
        if status == 'ok': done += 1
        elif status == 'skip': skip += 1
        else: fail += 1; fails.append(info)
        if (i + 1) % 50 == 0:
            print(f'{i+1}/{len(jobs)} | ok {done} skip {skip} fail {fail} | {time.time()-t0:.0f}s', flush=True)

print(f'DONE ok {done} skip {skip} fail {fail} in {time.time()-t0:.0f}s')
for f in fails[:10]:
    print('FAIL:', f)
