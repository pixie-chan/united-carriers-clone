#!/usr/bin/env python3
"""Wire the service tail into site/index.html. Idempotent: run once, guards against double-apply."""
import re

P = '/home/zen/projects/united-carriers-clone/site/index.html'
html = open(P).read()
orig = html

# 1. css link
if 'css/sections2.css' not in html:
    html = html.replace(
        '<link rel="stylesheet" href="css/sections.css">',
        '<link rel="stylesheet" href="css/sections.css">\n  <link rel="stylesheet" href="css/sections2.css">')
    assert 'css/sections2.css' in html, 'sections.css link not found'
else:
    print('css link already present')

# 2. speed HUD as first child of the service section
if 'home-service-speed' not in html:
    speed = '''<section class="home-service">
    <div class="home-service-speed"><div class="home-service-speed-inner active on-start"><div class="home-service-speed-number"><div data-speed="" data-wf--text--text-styles="mono" class="txt w-variant-3648de38-311e-0b18-0c7d-747bd60ae1a8 fs-12" data-current-speed="0" id="svcSpeed">00</div></div><div data-wf--text--text-styles="mono" class="txt w-variant-3648de38-311e-0b18-0c7d-747bd60ae1a8 fs-12">km/h</div></div></div>'''
    html = html.replace('<section class="home-service">', speed, 1)
    assert 'home-service-speed' in html
else:
    print('speed hud already present')

# 3. old service-speed element out
html = html.replace('      <div class="service-speed"><span id="svcSpeed">00</span><span>km/h</span></div>\n', '')

# 4. tail block after the service-sticky close, before section close
if 'SERVICE-TAIL:START' not in html:
    tail = open('/home/zen/projects/united-carriers-clone/site/_tail_block.html').read()
    idx = html.find('</div>\n  </section>\n\n  <!-- milestones -->')
    assert idx > -1, 'service section end marker not found'
    # the `</div>` before `</section>` here closes .service-sticky
    html = html[:idx + len('</div>\n')] + '\n' + tail + '\n' + html[idx + len('</div>\n'):]
else:
    print('tail already present')

# 5. milestones section removed
html = re.sub(r'\n  <!-- milestones -->.*?</section>\n', '\n  <!-- why/ocean, testimonials, partners, insights, faq, footer: built next -->\n', html, flags=re.S)

# 6. why/ocean block after the service tail
if 'WHY:START' not in html:
    why = open('/home/zen/projects/united-carriers-clone/site/_why_block.html').read()
    idx = html.find('<!-- SERVICE-TAIL:END -->')
    assert idx > -1, 'no tail marker'
    html = html[:idx + len('<!-- SERVICE-TAIL:END -->')] + '\n\n' + why + '\n' + html[idx + len('<!-- SERVICE-TAIL:END -->'):]
else:
    print('why already present')

# 7. main.js import hook noted (handled separately)

if html != orig:
    open(P, 'w').write(html)
    print('index.html updated, len', len(html))
else:
    print('no changes')
