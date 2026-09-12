#!/usr/bin/env python3
"""Move the why block after the home-service </section> (one-time fix)."""
P = '/home/zen/projects/united-carriers-clone/site/index.html'
html = open(P).read()

start = html.find('<!-- WHY:START')
end = html.find('<!-- WHY:END -->')
assert start > -1 and end > start, 'why block not found'
end += len('<!-- WHY:END -->')
block = html[start:end]
# remove (also the trailing newline we added)
html = html[:start] + html[end:]
html = html.replace('<!-- SERVICE-TAIL:END -->\n\n\n', '<!-- SERVICE-TAIL:END -->\n')

# find the </section> that closes home-service: first "</section>" after SERVICE-TAIL:END
tail_marker = html.find('<!-- SERVICE-TAIL:END -->')
sec_close = html.find('</section>', tail_marker)
assert sec_close > tail_marker, 'section close not found'
insert_at = sec_close + len('</section>')
html = html[:insert_at] + '\n\n' + block + html[insert_at:]

open(P, 'w').write(html)
print('moved. new len', len(html))
