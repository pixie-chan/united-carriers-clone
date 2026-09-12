#!/usr/bin/env python3
"""Extract airports + flights JSON from the minified my-flights chunk into site/data/."""
import json, re, os

SRC = '/home/zen/projects/united-carriers-clone/_ref/analysis/netlify/chunks/my-flights-DRrlP7HY.js'
OUT = '/home/zen/projects/united-carriers-clone/site/data'
os.makedirs(OUT, exist_ok=True)
s = open(SRC, encoding='utf-8', errors='ignore').read()

def balanced(text, start):
    """from index of '{', return end index (exclusive) of balanced braces, string-aware."""
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return -1

def js_to_json(obj_text):
    # quote bare keys: after { or ,  followed by ident + :
    obj_text = re.sub(r'([{,])\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*:', r'\1"\2":', obj_text)
    return obj_text

found = {}
for m in re.finditer(r'type:"(\w+)"', s):
    tag = m.group(1)
    brace = s.rfind('{', 0, m.start())
    end = balanced(s, brace)
    if end < 0:
        continue
    obj_text = s[brace:end]
    try:
        data = json.loads(js_to_json(obj_text))
        found[tag] = data
        print('extracted', tag, '->', list(data.keys()))
    except Exception as e:
        print('FAILED', tag, str(e)[:120])

for tag, data in found.items():
    path = os.path.join(OUT, tag + '.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=1)
    print('saved', path, os.path.getsize(path), 'bytes')
