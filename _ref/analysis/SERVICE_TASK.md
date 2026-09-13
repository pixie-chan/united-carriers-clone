# TASK: Fix the service -> tail handoff (rebuild of unitedcarriers.com)

You are working in /home/zen/projects/united-carriers-clone (a 1:1 static rebuild of unitedcarriers.com).

## Setup (do not disturb)
- The rebuild serves on http://127.0.0.1:8898/ (python http.server, run from site/).
- The live reference mirror serves on http://127.0.0.1:8899/unitedcarriers.com/index.html.
- Both servers MUST stay up. If one is down, stop and report: needs input: server down.
- QA harness: `cd _ref/analysis && python3 service-check.py 2>&1 | tail -14`
  It scrolls BOTH pages through 11 anchors [3300..12100], screenshots to _ref/analysis/repro2/service/,
  and prints mean pixel diffs per anchor. Read the screenshots to see what differs.
- Current diffs (before your work): 5.4, 2.3, 2.4, 1.9, 2.6, 5.1, 2.3, 2.2, 5.7, 81.1, 117.3
  (anchors: 3300, 4100, 4900, 5700, 6500, 7500, 8500, 9500, 10500, 11400, 12100)
  The last two anchors (11400, 12100) are BROKEN. Everything up to 10500 is fine, keep it that way.

## The zone
Scroll y>=11000: the live page is in the "third-screen" phase of the service section (road slide-in,
truck parking, speed HUD, reliability sub-content). In the rebuild that phase is:
- DOM: the .uc-tail block (inside site/index.html between `<!-- SERVICE-TAIL:START` and `<!-- SERVICE-TAIL:END -->`)
- JS: site/js/tail.js
- Its CSS rest-state: _ref/analysis/build-port.py, the `rest_state` string (positions captured from the
  live at scroll 14160) and .uc-tail placement (top: 895.125rem, absolute).
- The PRECEDING screens were just ported in site/js/service.js (timeline tlMoveTruckIn runs from
  first-screen top+450vh to second-screen bottom-100vh; it now hands off into this zone).

## Why it's broken (starting theory, verify yourself)
tail.js's entrance timeline and the uc-tail rest-state were tuned to the OLD pre-port layout (rest state
captured at 14160; entrance window "tailTop() - innerHeight * 1.105" etc). After the port, the live's
actual state at 11400/12100 is an intermediate choreography stage the rebuild does not reproduce yet.
Compare repro2/service/live-11400.png vs reb-11400.png (and 12100) to see exactly what differs
(positions, opacity, which elements are visible, the road/truck/speed states).

## Truth sources
- Live choreography source (readable): _ref/analysis/pretty/Home.js, class `Service` (desktop branch).
  A dumped copy with line context: /tmp/service-class.txt (may be gone if /tmp was cleared; re-extract
  from pretty/Home.js if needed; search for `tlRoadTransition` and `tlTruckRot` and the new-truck tweens).
- Live DOM: _ref/mirror/unitedcarriers.com/index.html (this is what the 8899 mirror serves).
- The live embed CSS for this zone: _ref/analysis/extracts/embedded.css (search home-service-road,
  home-service-new-truck, home-service-third-screen).

## Rules
- CSS is GENERATED: never edit site/css/sections2.css or site/index.html by hand.
  Edit _ref/analysis/build-port.py (rest_state string, emb blocks, or the svc_emb_extra block),
  then run: `cd _ref/analysis && python3 build-port.py && python3 wire-index.py`
- JS edits: site/js/tail.js and/or site/js/service.js directly.
- Keep the scope to y>=11000 behavior. Anchors 3300..10500 must stay at or below their current diffs.
- House style: NEVER use em dashes (U+2014) anywhere (comments included). Use commas, colons, periods.
- After every change: re-run the harness and read the numbers. Iterate until:
  y=11400 and y=12100 diffs <= 12, others <= 8, and the harness reports zero page errors.
- Screenshots are taken ~1.1s after each scroll stop; the live mirror needs stepped scrolling
  (the harness already does this, do not rewrite its scroll method).

## Deliverable
Working code in the repo (JS edited directly; CSS via build-port.py rebuild), and your final message must
include the final harness output (the diff table). End with the status line protocol:
- `result: <headline>` when the acceptance numbers are reached
- `needs input: <question>` if blocked on one human action
- `failed: <reason>` if impossible as framed
