#!/usr/bin/env python3
"""Assemble sections2.css for the rebuild.

Sources:
  - raw webflow stylesheet (media-aware extraction, rem values rescaled x0.625:
    live html font-size is 1440/172.8 = 8.333px, the rebuild uses 1440/108 = 13.333px)
  - the live page's embedded custom css (grid system block + overrides)
Output: site/css/sections2.css + site/_tail_block.html
Re-runnable."""
import re, os

BASE = '/home/zen/projects/united-carriers-clone'
EXT = f'{BASE}/_ref/analysis/extracts'
SITE = f'{BASE}/site'
RAW = f'{BASE}/_ref/mirror/cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/css/united-carriers.webflow.shared.fc188c3b2.min.css'

REM_SCALE = 0.625  # 8.3333 / 13.3333

def split_rules(s):
    rules, i, n = [], 0, len(s)
    while i < n:
        b = s.find('{', i)
        if b == -1:
            break
        sel = s[i:b].strip()
        depth, j = 1, b + 1
        while j < n and depth:
            if s[j] == '{':
                depth += 1
            elif s[j] == '}':
                depth -= 1
            j += 1
        rules.append((sel, s[b + 1:j - 1]))
        i = j
    return rules

def scale_rem(text):
    def rep(m):
        v = float((m.group(1) or '') + m.group(2)) * REM_SCALE
        s = f'{v:.6f}'.rstrip('0').rstrip('.')
        if s in ('-0', ''):
            s = '0'
        return s + 'rem'
    return re.sub(r'(?<![\w.-])(-?)(\d*\.?\d+)rem', rep, text)

def filter_css(src, pred, scale=True):
    out = []
    for sel, body in split_rules(src):
        if sel.startswith('@media') or sel.startswith('@supports'):
            inner = filter_css(body, pred, scale)
            if inner:
                out.append(sel + ' {')
                out.append('\n'.join('  ' + l for l in '\n'.join(inner).split('\n')))
                out.append('}')
        elif pred(sel):
            out.append(f'{sel} {{ {body.strip()} }}' if not scale else f'{sel} {{ {scale_rem(body.strip())} }}')
    return out

raw = open(RAW).read()
emb = open(f'{EXT}/embedded.css').read()

KEEP_BASE = ['.w-container', '.w-layout-grid', '.w-layout-blockcontainer', '.container',
             '.txt', '.fw-med', '.img-df', '.heading', '.cl-note', '.hidden-mb', '.hidden-dsk',
             '.home-service-new-truck-inner', '.svg']
def keep_base(sel):
    return any(sel.strip().startswith(k) for k in KEEP_BASE)

INCLUDE = ['home-service-third-screen', 'home-service-new-truck', 'home-service-road',
           'home-service-sub-content', 'home-service-sub-wrap',
           'home-service-sub-list', 'home-service-sub-item', 'home-service-sub-ic',
           'home-service-sub-title', 'home-service-sub-desc', 'home-service-stick-wrap.third-screen',
           'home-service-stick.third-screen', 'home-service-stick {', 'home-service-title',
           'home-service-desc', 'home-service-speed']
EXCLUDE = ['road-big', 'road-line', '-mb', 'main-road', 'truck-sq', 'truck-cont', 'truck-car',
           'truck-wheel', 'truck-full', 'crane']
def keep_tail(sel):
    if not any(t in sel for t in INCLUDE):
        return False
    if any(t in sel for t in EXCLUDE):
        return False
    return True

base_rules = filter_css(raw, keep_base)
tail_rules = filter_css(raw, keep_tail)

WIDS_IDS = ['_1c8a6a0f', '_483eca59', '_51706e81', 'e88a8de6', '_4134f74f', '_84c9d057', '_240aa9fd',
            '_61e3d646', '_76be832d', '_897d092c', '_4f47b0a5', 'ebabe29a', '_870e7c28', '_6d2f58df',
            '_5cd857c2', '_0cdf9015', '_50c47f1d', 'b8d0896c', 'c7b9355f', '_5ee1322c', 'f6688c0f']
wid_rules = filter_css(raw, lambda sel: any(i in sel for i in WIDS_IDS), scale=False)

# why/ocean rules
WHY_INCLUDE = ['home-why', 'in-icon']
why_rules = filter_css(raw, lambda sel: any(t in sel for t in WHY_INCLUDE))

# embedded overrides touching home-why (scaled)
emb_rules = []
for sel, body in split_rules(emb):
    if sel.startswith('/*') or not sel.strip():
        continue
    if 'home-why' in sel:
        emb_rules.append(f'{sel} {{ {scale_rem(body.strip())} }}')
emb_why = '/* ===== why/ocean overrides from live embedded css ===== */\n' + '\n'.join(emb_rules)

# grid system block (#5) from embedded css
grid_block = '''/* ===== grid system (live embedded custom css) ===== */
:root { --page-padding: max((100vw - var(--container--max-width)) / 2, 0px); }
.container.grid,
.full-width {
  --padding-inline: calc(var(--container--padding) - var(--container--column-gap));
  --content-max-width: calc(var(--container--max-width) - (var(--container--padding) * 2));
  padding: 0;
  display: grid;
  grid-template-columns:
    [full-width-start]
    minmax(var(--padding-inline), 1fr)
    [content-start]
    repeat(var(--container--column), minmax(0, calc(min(
      100% - (var(--padding-inline) * 2) - (var(--container--column-gap) * (var(--container--column) - 1)),
      var(--content-max-width) - (var(--container--column-gap) * (var(--container--column) - 1))
    ) / var(--container--column))))
    [content-end]
    minmax(var(--padding-inline), 1fr)
    [full-width-end];
  gap: 0 var(--container--column-gap);
}
.container.grid > :not(.full-width),
.full-width > :not(.full-width) { grid-column: content; }
.container.grid > .full-width,
.container.grid > .full-width-wrap {
  grid-column: full-width;
  display: grid;
  grid-template-columns: minmax(0px, 1fr);
}
'''

# live embedded overrides relevant to the tail (rescaled)
emb_live = '''/* ===== overrides from the live page's embedded custom css (rescaled) ===== */
.uc-tail { color: var(--_color---content--main); }
.home-service-third-screen { margin-top: -200vh; }
.home-service-sub-item:last-child { border-bottom: none; padding-bottom: 0; }
.home-service-road { --scale-factor: 1; transform: scale(var(--scale-factor)); transform-origin: left top; }
.home-service-speed-tens, .home-service-speed-units, .home-service-speed-decimals { will-change: transform; }
.home-service-speed-inner .txt { height: 1.125rem; }
'''

# tail rest-state: OUR-rem values (do not scale; captured from live at scroll 14160)
rest_state = '''/* ===== tail rest-state: runtime end values captured from the live site (scroll 14160, 1440x900).
   The JS entrance animates _from_ these compositions back to them, so the resting state is CSS. ===== */
.uc-tail { position: absolute; top: 676.125rem; left: 0; right: 0; height: 234.375rem; z-index: 3; background: #fff; }
.uc-tail .home-service-third-screen { margin-top: 0; }
.uc-tail .home-service-new-truck-wrap { opacity: 1; }
.uc-tail .home-service-new-truck-stick { top: 0; }
.uc-tail .home-service-new-truck-rot { top: 40.624rem; transform: translate(0rem, -34.0196rem) rotate(90deg); }
.uc-tail .home-service-new-truck { top: -40.65rem; transform: scale(1.1098); }
.uc-tail .home-service-new-truck-inner.only-car { transform: translate(-4.598rem, -0.0412rem) scale(0.346); }
.uc-tail .home-service-new-truck-inner.container-truck { transform: translate(-4.598rem, -0.0412rem) scale(0.39, 0.346); }
.uc-tail .home-service-road-wrap { transform: translateY(-7.5rem); }
'''

header = ''':root {
  --container--padding: 2.5rem;
  --container--column-gap: 1.25rem;
  --container--column: 16;
  --container--max-width: 100vw;
  --container--one-column: calc((var(--container--max-width) - ((var(--container--column) - 1)*var(--container--column-gap)) - (var(--container--padding)*2))/var(--container--column));
  --container--width: min(100vw, var(--container--max-width));
  --_color---bg--main: white;
  --_color---content--main: #111;
  --_color---content--note: #1116;
  --_color---content--soft: #111111b8;
  --_color---content--sub: #111111e0;
  --_color---border--light: #1111111a;
  --_color---border--main: #1113;
  --_color---border--bold: #1111114d;
  --_color---border--highlight: #111;
  --_color---bg--sf-1: #f4f4f4;
  --_color---bg--sf-2: #111;
  --_color---secondary: #f50;
  --_color---primary: #0016cb;
  --_color---m-white: white;
  --_color---m-black: #111;
  --border--size: 1px;
  --font--heading: "BT Steinhart", Arial, sans-serif;
  --font--body: "Helvetica Neue", Arial, sans-serif;
  --font--button: "BT Steinhart Mono", Arial, sans-serif;
}
'''

parts = [header,
         '/* ===== base layout + text primitives (verbatim from live css, rem-rescaled) ===== */']
parts.extend(base_rules)
parts.append('\n' + grid_block)
parts.append('\n/* ===== service tail ===== */')
parts.extend(tail_rules)
parts.append(emb_live)
parts.append(rest_state)
parts.append('\n/* ===== why / ocean ===== */')
parts.extend(why_rules)
parts.append(emb_why)
parts.extend(wid_rules)

out = '\n\n'.join(parts)
out = out.replace('url(../6a44', 'url(../assets/img/6a44')
out = out.replace('--_color---content--black\\<deleted\\|variable-6e7d8137-8713-9ff4-5cea-f92e6216a872\\>', '--_color---unused')

open(f'{SITE}/css/sections2.css', 'w').write(out)
print('sections2.css written:', len(out), 'chars')
print('base rules:', len(base_rules), '| tail rules:', len(tail_rules), '| wid rules:', len(wid_rules))

# sanity checks
for probe in ['55.367rem', '78.4rem', 'padding: 2.5rem', '7.2rem', '4.5rem']:
    print(f'  contains {probe!r}:', probe in out)

# ---------------- HTML: service tail (unchanged generation) ----------------
pretty = open(f'{EXT}/svc-tail.pretty.html').read()
start = pretty.find('<div id="w-node-_1c8a6a0f-02bc-6c80-8ad5-417920171824-c403df38" class="home-service-third-screen">')
assert start > -1, 'third-screen not found'
i, depth, pos = start, 0, start
while True:
    nxt_open = pretty.find('<div', i)
    nxt_close = pretty.find('</div>', i)
    if nxt_open == -1:
        nxt_open = 10 ** 9
    if nxt_close == -1:
        raise RuntimeError('unbalanced')
    if nxt_open < nxt_close:
        depth += 1
        i = nxt_open + 4
    else:
        depth -= 1
        i = nxt_close + 6
        if depth == 0:
            end = i
            break
block = pretty[start:end]

def clean_style(m):
    val = m.group(1)
    if (('transform' in val) or ('translate' in val) or ('opacity' in val)
            or ('visibility' in val) or ('--scale-factor' in val) or ('top:' in val)):
        return ''
    return m.group(0)

block = re.sub(r'style="([^"]*)"', clean_style, block)
block = block.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
block = re.sub(r'\n{2,}', '\n', block)
block = '\n'.join('    ' + l if l.strip() else l for l in block.split('\n'))

wrapped = f'''<!-- SERVICE-TAIL:START (ported from live: road + truck + reliability) -->
  <div class="uc-tail">
{block}
  </div>
  <!-- SERVICE-TAIL:END -->'''
open(f'{SITE}/_tail_block.html', 'w').write(wrapped)
print('tail block written:', len(wrapped), 'chars')

# ---------------- HTML: why / ocean ----------------
wpretty = open(f'{EXT}/why.pretty.html').read()
wsec_start = wpretty.find('<section')
wsec_end = wpretty.find('</section>') + len('</section>')
wblock = wpretty[wsec_start:wsec_end]
wrap_open = ('<div class="home-why-wrap">\n  <div id="w-node-a2d02a8a-5ed4-c914-303f-5c19c3e2a3b4-c403df38" '
             'class="home-why-empty-block bottom"></div>\n')
wblock = wrap_open + wblock + '\n</div>'
print('why raw block chars:', len(wblock))

# replace the webflow-3d ocean element with our own canvas
wblock = re.sub(
    r'<webflow-3d[^>]*scene="OceanScene"[^>]*>.*?</webflow-3d>',
    '<div class="home-why-ocean-img" style="width:100%;height:100vh;display:block"><canvas id="oceanCanvas" width="1440" height="900" style="display:block;width:100%;height:100%"></canvas></div>',
    wblock, flags=re.S)
wblock = re.sub(r'style="([^"]*)"', clean_style, wblock)
wblock = wblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
wblock = wblock.replace('https://cdn.prod.website-files.com/6a460d6f92801e715322d1d6/', 'assets/video/')
wblock = re.sub(r'\n{2,}', '\n', wblock)
wblock = '\n'.join('    ' + l if l.strip() else l for l in wblock.split('\n'))
if not wblock.lstrip().startswith('<!-- WHY:START'):
    wblock = '<!-- WHY:START (ported from live: sticky ocean + ship + clouds + why list) -->\n' + wblock + '\n  <!-- WHY:END -->'
open(f'{SITE}/_why_block.html', 'w').write(wblock)
print('why block written:', len(wblock), 'chars -> site/_why_block.html')
