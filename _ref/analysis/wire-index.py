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

# 8. testi block after WHY:END (replace if already present, so re-runs pick up regen)
if 'TESTI:START' in html:
    a = html.find('<!-- TESTI:START')
    b2 = html.find('<!-- TESTI:END -->') + len('<!-- TESTI:END -->')
    testi = open('/home/zen/projects/united-carriers-clone/site/_testi_block.html').read()
    html = html[:a] + testi + html[b2:]
else:
    testi = open('/home/zen/projects/united-carriers-clone/site/_testi_block.html').read()
    idx = html.find('<!-- WHY:END -->')
    assert idx > -1, 'no why marker'
    html = html[:idx + len('<!-- WHY:END -->')] + '\n\n' + testi + '\n' + html[idx + len('<!-- WHY:END -->'):]
    html = html.replace('<!-- why/ocean, testimonials, partners, insights, faq, footer: built next -->',
                        '<!-- partners, insights, faq, footer: built next -->')
    html = html.replace('<!-- remaining sections (why/ocean, testimonials, partners, insights, faq, footer): built next -->',
                        '<!-- remaining sections (partners, insights, faq, footer): built next -->')

# 9. partners block after TESTI:END (replace-capable)
if 'PARTNERS:START' in html:
    a = html.find('<!-- PARTNERS:START')
    b2 = html.find('<!-- PARTNERS:END -->') + len('<!-- PARTNERS:END -->')
    partners = open('/home/zen/projects/united-carriers-clone/site/_partners_block.html').read()
    html = html[:a] + partners + html[b2:]
else:
    partners = open('/home/zen/projects/united-carriers-clone/site/_partners_block.html').read()
    idx = html.find('<!-- TESTI:END -->')
    assert idx > -1, 'no testi marker'
    html = html[:idx + len('<!-- TESTI:END -->')] + '\n\n' + partners + '\n' + html[idx + len('<!-- TESTI:END -->'):]
    html = html.replace('<!-- partners, insights, faq, footer: built next -->',
                        '<!-- insights, faq, footer: built next -->')
    html = html.replace('<!-- remaining sections (partners, insights, faq, footer): built next -->',
                        '<!-- remaining sections (insights, faq, footer): built next -->')

# 10. insights block after PARTNERS:END (replace-capable)
if 'INSIGHTS:START' in html:
    a = html.find('<!-- INSIGHTS:START')
    b2 = html.find('<!-- INSIGHTS:END -->') + len('<!-- INSIGHTS:END -->')
    ins = open('/home/zen/projects/united-carriers-clone/site/_insights_block.html').read()
    html = html[:a] + ins + html[b2:]
else:
    ins = open('/home/zen/projects/united-carriers-clone/site/_insights_block.html').read()
    idx = html.find('<!-- PARTNERS:END -->')
    assert idx > -1, 'no partners marker'
    html = html[:idx + len('<!-- PARTNERS:END -->')] + '\n\n' + ins + '\n' + html[idx + len('<!-- PARTNERS:END -->'):]

if html != orig:
    open(P, 'w').write(html)
    print('index.html updated, len', len(html))
else:
    print('no changes')
