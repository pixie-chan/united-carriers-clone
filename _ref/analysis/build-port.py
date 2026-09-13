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
             '.home-service-new-truck-inner', '.svg', '.hidden', '.display-contents', '.w-inline-block']
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
why_extra = '''/* cloud items: intrinsic size before the lazy imgs load, so GSAP's boot-time
   resolution of the CSS translate(-50%, +50%) runs against the final box height
   (otherwise the Y offset caches against a ~20px pre-load box and the items sit
   ~490px too high for the rest of the timeline) */
.home-why-cloud-overlap-item.cloud-1,
.home-why-cloud-overlap-item.cloud-2,
.home-why-cloud-overlap-item.cloud-7 { aspect-ratio: 2604 / 1177; }
.home-why-cloud-overlap-item.cloud-3,
.home-why-cloud-overlap-item.cloud-4,
.home-why-cloud-overlap-item.cloud-5,
.home-why-cloud-overlap-item.cloud-6 { aspect-ratio: 1982 / 1077; }
'''
parts.append(why_extra)
parts.extend(wid_rules)

# ---- testi (plane flyover + testimonial wipe) ----
testi_rules = filter_css(raw, lambda sel: 'home-testi' in sel)
# grid-area assignments that put the plane and the content in the SAME grid cell
TESTI_IDS = ('d93b28c9-8098-8e98-b09a-60fd782943e9',
             '_8c2bb2a7-341e-2863-3238-551e171fae69',
             '_8c2bb2a7-341e-2863-3238-551e171fae6b',
             '_8c2bb2a7-341e-2863-3238-551e171fae6d',
             '_8c2bb2a7-341e-2863-3238-551e171fae81')
testi_node_rules = filter_css(raw, lambda sel: any(i in sel for i in TESTI_IDS), scale=False)
testi_extra = filter_css(
    raw,
    lambda sel: sel.strip().startswith(('.fw-bold', '.w-richtext', '.w-dyn-list',
                                        '.w-dyn-items', '.w-dyn-item')),
    scale=False)
emb_testi = '''/* ===== testi overrides from the live page's embedded custom css ===== */
.home-testi { margin-top: -200vh; }
.home-testi { --overlap-clip: 60; }
.home-testi-plane { opacity: 1; }
.home-testi-plane-img-shadow { transform: translate(calc(var(--pos-x, 0) * 1%), calc(var(--pos-y, 0) * 1%)) scale(var(--scale, 1)); }
/* webflow base element defaults, scoped to this section (global p margins would shift
   the earlier absolutely-positioned custom blocks) */
.home-testi p { margin-top: 0; margin-bottom: 10px; }
.home-testi .w-richtext > *:first-child { margin-top: 0; }
.home-testi .w-richtext > *:last-child { margin-bottom: 0; }
'''
parts.append('\n/* ===== testi (plane + testimonial wipe) ===== */')
parts.extend(testi_rules)
parts.extend(testi_node_rules)
parts.extend(testi_extra)
parts.append(emb_testi)

# ---- partners (logo lattice + reveals) ----
partners_rules = filter_css(raw, lambda sel: 'home-partners' in sel)
PARTNERS_IDS = ('_081b3f2d-08e8-1749-b939-f736c59af826',
                '_081b3f2d-08e8-1749-b939-f736c59af829',
                '_081b3f2d-08e8-1749-b939-f736c59af82e',
                '_081b3f2d-08e8-1749-b939-f736c59af830',
                '_7ff89e7a-eb73-6d9c-cf04-27f240a39a3c',
                '_7ff89e7a-eb73-6d9c-cf04-27f240a39a41',
                '_7ff89e7a-eb73-6d9c-cf04-27f240a39a43',
                'f4770c19-8c50-4513-806c-59af2ed50310')
partners_node_rules = filter_css(raw, lambda sel: any(i in sel for i in PARTNERS_IDS), scale=False)
emb_partners = '''/* ===== partners overrides from the live page's embedded custom css ===== */
/* live paints white via the page-level .main bg (--_color---bg--main); our page base is
   dark, so the region paints itself white (page-base theme audit is an open thread) */
.home-partners-wrap { background-color: var(--_color---bg--main); }
.home-partners-item:hover .home-partners-item-inner { background-color: #f4f4f4; }
.home-partners-item:hover .home-partners-item-thumb { opacity: 0; }
.home-partners-item:hover .home-partners-item-thumb.is-hover { opacity: 1; }
'''
parts.append('\n/* ===== partners ===== */')
parts.extend(partners_rules)
parts.extend(partners_node_rules)
parts.append(emb_partners)

# ---- insights (dark article list + thumbs) ----
ins_rules = filter_css(raw, lambda sel: 'home-ins' in sel)
INS_IDS = ('_0603a309-83b1-05b3-e028-e154d6160042',
           '_0603a309-83b1-05b3-e028-e154d6160050',
           '_0603a309-83b1-05b3-e028-e154d6160053',
           '_0603a309-83b1-05b3-e028-e154d61600b6')
ins_node_rules = filter_css(raw, lambda sel: any(i in sel for i in INS_IDS), scale=False)
emb_ins = '''/* ===== insights overrides from the live page's embedded custom css ===== */
.home-ins-cms-thumb-item.active { opacity: 1; }
.home-ins-cms-item-line { position: relative; overflow: hidden; }
.home-ins-cms-item-line::after { content: ''; position: absolute; inset: 0; background: var(--_color---border--highlight); transform: translateX(-100%); transition: transform 0.6s ease; }
.home-ins-cms-item:hover .home-ins-cms-item-line::after { transform: translateX(0); }
.home-ins-toc-title.active .home-ins-toc-title-ic { transform: rotate(180deg); }
/* raw .btn (scoped to this section: our chrome redefines .btn globally); rems x0.625 */
.home-ins-action .btn { border: var(--border--size) solid var(--_color---border--bold); color: var(--_color---content--main); cursor: pointer; border-radius: 100vmax; flex: 1; justify-content: center; align-items: center; padding: 1.1875rem 1.75rem 1.0625rem; transition: border-color .4s, background-color .4s, color .4s; display: flex; }
.home-ins-action .btn:hover { border-color: var(--_color---border--highlight); }
.home-ins-action .btn-txt { text-align: center; justify-content: center; align-items: center; display: flex; }
/* live's mono meta texts size to the glyph box (fs x 0.795, e.g. 8.33px -> 6.625px high) */
.home-ins-cms-item-info .txt, .home-ins-cms-item-cate .txt, .home-ins-cms-item-cate-inner .txt { line-height: 0.795; }
'''
parts.append('\n/* ===== insights ===== */')
parts.extend(ins_rules)
parts.extend(ins_node_rules)
parts.append(emb_ins)

# ---- faq (accordion) ----
faq_rules = filter_css(raw, lambda sel: 'home-faq' in sel)
FAQ_IDS = ('_2fdd36e9-383a-6cbf-0090-89bdb1e4d5a1',
           '_139a5fba-b318-aed8-456a-5995709192fa',
           'ffca6108-f47c-6400-8997-59ce06e9026d')
faq_node_rules = filter_css(raw, lambda sel: any(i in sel for i in FAQ_IDS), scale=False)
emb_faq = '''/* ===== faq overrides from the live page's embedded custom css ===== */
/* live paints white via the page-level .main bg; our page base is dark (theme audit thread) */
.home-faq-wrap { background-color: var(--_color---bg--main); }
.home-faq-main-list { counter-reset: faq-counter; }
.home-faq-main-item { counter-increment: faq-counter; }
.home-faq-main-item-number .txt { line-height: 0.795; }
.home-faq-main-item-number .txt:not(.w-input):empty { display: block; }
.home-faq-main-item-number .txt::before { content: counter(faq-counter, decimal-leading-zero); }
.home-faq-main-item.active .home-faq-main-item-line { background-color: var(--_color---content--main); }
.home-faq-main-item.active .home-faq-main-item-title { color: var(--_color---content--main); }
.home-faq-main-item.active .home-faq-main-item-dot { background-color: var(--_color---content--main); }
.home-faq-main-item:hover .home-faq-main-item-dot { background-color: var(--_color---content--main); }
.home-faq-main-item:hover .home-faq-main-item-title { color: var(--_color---content--main); }
'''
parts.append('\n/* ===== faq ===== */')
parts.extend(faq_rules)
parts.extend(faq_node_rules)
parts.append(emb_faq)

# ---- cta (wave circles banner) ----
cta_rules = filter_css(raw, lambda sel: sel.strip().startswith('.cta') or 'cta-btn-wrap' in sel)
CTA_IDS = ('16cd6236-a00c-1313-b86e-e3a622eca',)
cta_node_rules = filter_css(raw, lambda sel: any(i in sel for i in CTA_IDS), scale=False)
emb_cta = '''/* ===== cta overrides from the live page's embedded custom css ===== */
.anim-wave { animation: wave 12s linear infinite; }
@keyframes wave { 0% { transform: scale(1); opacity: 0; } 20%, 80% { opacity: 0.65; } 60% { opacity: 1; } 100% { transform: scale(3); opacity: 0; } }
/* raw .btn scoped (our chrome redefines .btn); rems x0.625 */
.cta-btn-wrap .btn { border: var(--border--size) solid var(--_color---border--bold); color: var(--_color---content--main); cursor: pointer; border-radius: 100vmax; flex: 1; justify-content: center; align-items: center; padding: 1.1875rem 1.75rem 1.0625rem; transition: border-color .4s, background-color .4s, color .4s; display: flex; }
.cta-btn-wrap .btn-txt { text-align: center; justify-content: center; align-items: center; display: flex; }
'''
parts.append('\n/* ===== cta ===== */')
parts.extend(cta_rules)
parts.extend(cta_node_rules)
parts.append(emb_cta)

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

# ---------------- HTML: testi (testimonial plane section) ----------------
tpretty = open(f'{EXT}/testi.pretty.html').read()
tstart = tpretty.find('<section')
tend = tpretty.find('</section>') + len('</section>')
assert tstart > -1 and tend > len('</section>'), 'testi section bounds not found'
tblock = tpretty[tstart:tend]
tblock = '<div class="home-testi-wrap">\n' + tblock + '\n</div>'

def clean_style_testi(m):
    val = m.group(1)
    if (('transform' in val) or ('translate' in val) or ('opacity' in val)
            or ('visibility' in val) or ('--scale-factor' in val) or ('top:' in val)
            or ('width:' in val)):
        return ''
    return m.group(0)

tblock = re.sub(r'style="([^"]*)"', clean_style_testi, tblock)
tblock = tblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
tblock = tblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df68/', 'assets/img/')
tblock = re.sub(r'\n{2,}', '\n', tblock)
tblock = '\n'.join('    ' + l if l.strip() else l for l in tblock.split('\n'))
tblock = ('<!-- TESTI:START (ported from live: plane flyover + testimonial wipe) -->\n'
          + tblock + '\n  <!-- TESTI:END -->')
open(f'{SITE}/_testi_block.html', 'w').write(tblock)
print('testi block written:', len(tblock), 'chars -> site/_testi_block.html')
print('testi css rules:', len(testi_rules), '| testi extras:', len(testi_extra))

# ---------------- HTML: partners (logo lattice) ----------------
ppretty = open(f'{EXT}/partners.pretty.html').read()
pstart = ppretty.find('<section')
pend = ppretty.find('<div data-section="dark" class="home-ins-wrap">')
assert pstart > -1 and pend > pstart, 'partners bounds not found'
pblock = ppretty[pstart:pend].rstrip()
# ends with: </section> + .home-partners-bg div + closing </div> of the wrap
pblock = '<div class="home-partners-wrap">\n' + pblock + '\n</div>'
pblock = re.sub(r'style="([^"]*)"', clean_style_testi, pblock)
pblock = pblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
pblock = pblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df68/', 'assets/img/')
pblock = pblock.replace('%2520%25281%2529', '%20(1)')   # double-encoded partners-bg (1) variants
pblock = re.sub(r'\n{2,}', '\n', pblock)
pblock = '\n'.join('    ' + l if l.strip() else l for l in pblock.split('\n'))
pblock = ('<!-- PARTNERS:START (ported from live: logo lattice, hover swap, batch reveal) -->\n'
          + pblock + '\n  <!-- PARTNERS:END -->')
open(f'{SITE}/_partners_block.html', 'w').write(pblock)
print('partners block written:', len(pblock), 'chars -> site/_partners_block.html')
print('partners css rules:', len(partners_rules), '| partners node rules:', len(partners_node_rules))

# ---------------- HTML: insights (dark article list) ----------------
ipretty = open(f'{EXT}/ins.pretty.html').read()
istart = ipretty.find('<section')
iend = ipretty.find('<div class="home-faq-wrap">')
assert istart > -1 and iend > istart, 'insights bounds not found'
iblock = ipretty[istart:iend].rstrip()
iblock = '<div data-section="dark" class="home-ins-wrap">\n' + iblock + '\n</div>'
iblock = re.sub(r'style="([^"]*)"', clean_style_testi, iblock)
iblock = iblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
iblock = iblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df68/', 'assets/img/')
iblock = re.sub(r'\n{2,}', '\n', iblock)
# minify inter-tag whitespace: pretty indentation inserts whitespace text nodes between
# blocks and inline-blocks, which adds strut line boxes (live's html is minified; e.g.
# desc -> inline-block action gap grew by a whole line-height: +27px). Do not indent here.
iblock = re.sub(r'>\s+<', '><', iblock)
iblock = ('<!-- INSIGHTS:START (ported from live: dark article list + thumb hover sync) -->\n'
          + iblock + '\n  <!-- INSIGHTS:END -->')
open(f'{SITE}/_insights_block.html', 'w').write(iblock)
print('insights block written:', len(iblock), 'chars -> site/_insights_block.html')
print('insights css rules:', len(ins_rules), '| insights node rules:', len(ins_node_rules))

# ---------------- HTML: faq (accordion) ----------------
fpretty = open(f'{EXT}/faq.pretty.html').read()
fstart = fpretty.find('<section')
fend = fpretty.find('<div class="home-cta-wrap">')
assert fstart > -1 and fend > fstart, 'faq bounds not found'
fblock = fpretty[fstart:fend].rstrip()
# ends with </section> + the wrap's closing </div>; prepend the wrap open only
fblock = '<div class="home-faq-wrap">\n' + fblock
# keep inline widths (live keeps title 249px / sub-text 179px), strip transform-ish styles
fblock = re.sub(r'style="([^"]*)"', clean_style, fblock)
fblock = fblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
fblock = fblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df68/', 'assets/img/')
fblock = re.sub(r'\n{2,}', '\n', fblock)
fblock = re.sub(r'>\s+<', '><', fblock)   # minify inter-tag whitespace (see insights note)
fblock = ('<!-- FAQ:START (ported from live: accordion list, title mask reveal) -->\n'
          + fblock + '\n  <!-- FAQ:END -->')
open(f'{SITE}/_faq_block.html', 'w').write(fblock)
print('faq block written:', len(fblock), 'chars -> site/_faq_block.html')
print('faq css rules:', len(faq_rules), '| faq node rules:', len(faq_node_rules))

# ---------------- HTML: cta (wave circles banner, static) ----------------
cstart = fpretty.find('<div class="home-cta-wrap">')
cend = fpretty.find('<div id="w-node-_0e256e74')
assert cstart > -1 and cend > cstart, 'cta bounds not found'
cblock = fpretty[cstart:cend].rstrip()
cblock = re.sub(r'style="([^"]*)"', clean_style, cblock)
cblock = cblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df6b/', 'assets/img/')
cblock = cblock.replace('https://cdn.prod.website-files.com/6a44eec1ed1af2c4c403df68/', 'assets/img/')
cblock = re.sub(r'\n{2,}', '\n', cblock)
cblock = re.sub(r'>\s+<', '><', cblock)
cblock = ('<!-- CTA:START (ported from live: wave circles, static) -->\n'
          + cblock + '\n  <!-- CTA:END -->')
open(f'{SITE}/_cta_block.html', 'w').write(cblock)
print('cta block written:', len(cblock), 'chars -> site/_cta_block.html')
print('cta css rules:', len(cta_rules), '| cta node rules:', len(cta_node_rules))
