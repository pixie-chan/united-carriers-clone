# United Carriers clone: project state

Purpose: an **editable replica base** (future edits: swap the ship for an airplane, fix bugs, hand parts
to a human). Keep the rebuild code clean and documented. Resume phrase: "resume united carriers".

## Layout

- `site/` : THE REBUILD (own HTML/CSS/JS, editable). `index.html` (~66K),
  `css/{site,sections,sections2}.css`, `js/{main,globe,sections,tail,why,chrome,cursor,frames}.js`,
  `vendor/` (GSAP 3.13, ScrollTrigger, Lenis 1.3.11, three.js r184), `assets/{fonts,img,frames,video}`,
  `data/` (globe-points, land-110m, airports, flights, frames-sequences).
- `_ref/mirror/` : complete offline mirror of the real site, verified 1:1 (ANALYSIS.md §7).
- `_ref/analysis/` : all tooling + evidence.
- `ANALYSIS.md` : architecture, tokens, sections, animation inventory, verification results.

## How to run

    cd ~/projects/united-carriers-clone/site && python3 -m http.server 8898 --bind 0.0.0.0
    cd ~/projects/united-carriers-clone/_ref/mirror && python3 -m http.server 8899 --bind 0.0.0.0

- rebuild: http://127.0.0.1:8898/ (LAN: http://10.162.67.201:8898/), mirror: http://127.0.0.1:8899/unitedcarriers.com/index.html
- Phone access: `sudo sh /tmp/uc-open-ports.sh` (recreate if /tmp cleared: two ufw allow lines for 8898/8899).

## Status

**Working (verified against fresh live captures, compare-ab.py):**

1. Loader, hero + dot globe, intro, services (crane/truck frame scrub) as before.
2. **Service tail** (NEW, ported from live's `.home-service-third-screen`): road + truck + reliability
   block, geometry matches live within ~2px (road 653x560, truck stick/truck/rot all aligned, sub-items
   at 989/13710). Entrance scrub + parking + scroll-velocity speedometer (`02 KM/H` HUD).
3. **Why/ocean section** (NEW): sticky ocean, ship dolly (scale 1 -> .082, fitted scrub range
   [15300,19800]), ship bob yoyo, cloud decor + 7-item cloud fly-in (timed to live pacing), text/items
   reveals. Own three.js ocean shader (water-normal + equirect env + the site's overlay photo via
   saturation blend + analytic wake anchored to the ship DOM). Section lands at 15060, page math matches
   live (wrap 15060->21728).
4. Chrome: header/topbar hide on scroll-down / show on scroll-up (as live); cursor parks at (0,0) at
   rest like live (was center screen, 128px ring -> 4rem now).

**Pixel diffs (fresh paired captures, diff>16 / diff>48):**
- y0 55.3/12.4 (globe rotation phase), y1800 11.1/8.4 (intro reveal timings), y3220 33.7/32.9 (service
  choreography), y13000 4.5/4.1, y14160 3.1/2.7 (tail), y15060 44.8/10.5 (ocean, animated phase).
- why anchors: 17500 28.4/4.0, 19000 44.6/4.8, 19600 49.9/12.4, 20000 55.8/24.0 - remaining diff is
  dominated by animated water/cloud phase, not placement.

**Not built yet:**
- testimonials (home-testi-wrap; the airplane section), partners marquee, insights, FAQ, footer
  (CTA + footer logo canvas). Copy/structure for all in `_ref/analysis/measures/home-dom.html`;
  extracts in `_ref/analysis/extracts/` (testi/partners/ins/faq/footer .pretty.html).
- Mobile pass (never done).
- Service choreography polish (first/second screens: live shows equipment order, cards later;
  y3220 diff 33.7%).
- Ocean fine-tuning: sun-glint character, moire at high zoom, wake side-foam fade; cloud item
  contrast at mid-flight (20000 diff>48 24%).

## Key learnings (ported sections)

1. **The live site's html font-size is 1440/172.8 = 8.333px** (body 13.3333). Our rebuild uses
   100vw/108 = 13.3333. All ported live values are rem-rescaled **x0.625** by build-port.py.
2. **The real grid system is in an embedded <style> block (#5)**: `.container.grid` is a named-line
   16-col grid (`[full-width-start] minmax(padding-inline,1fr) [content-start] repeat(16,...)`).
   The webflow css's own `.container.grid {grid-template-columns:1fr}` is overridden by it.
3. Webflow id rules (`#w-node-...{grid-area:...}`) do the per-element grid placement; they are ported.
4. The live page's webflow badge ("Site of the Day", "Access all to ships") is 3rd-party injected, NOT
   in the DOM snapshot - do not replicate; it accounts for part of raw diff.
5. ScrollTrigger `start: 'top+=400vh top'` does NOT parse (vh unsupported) - it silently falls back to
   a much earlier start. Use numeric scroll positions (this bug once made the whole cloud reveal play
   5000px early).
6. Two scrubbed timelines writing the same object property fight: last-updating wins per frame and can
   freeze stale values. Keep one owner per property (wake scale now = st.shipScale * DOM wrapScale).

## Tooling (`_ref/analysis/`)

- `build-port.py` : regenerates `site/css/sections2.css` + `site/_tail_block.html` + `site/_why_block.html`
  from the raw webflow css (media-aware extract, rem x0.625) + embedded style blocks. Re-runnable.
- `wire-index.py` : idempotent index.html wiring (css link, speed hud, tail block, why block).
- `fix-why-position.py` : one-time move of the why block after `</section>`.
- `qa-rebuild.py` : rebuild shots [0,1800,3220,4200,13000] + diffs vs `verify/` (legacy).
- `tail-check.py` : tail screenshots [13000,14160,14600] + diffs vs live.
- `why-check.py` : why screenshots [14160..20000] + diffs vs `whyviews/live-*.png` + composites in `qaw/`.
- `compare-ab.py` : fresh paired captures live-mirror vs rebuild at [0,1800,3220,13000,14160,15060].
- `why-measure.py`, `why-sweep.py`, `tail-measure.py`, `tail-compare.py` : geometry probes.
- `extracts/` : pretty-printed live DOM per section + ported css dumps + embedded.css.

## Open threads / next steps (priority order)

1. Sections: testi + partners BUILT and verified at 1440 AND 1920 (partners pixel diff 1.3-2.1; testi
   timeline exact). Next in order: insights -> FAQ -> footer (same port pipeline).
2. After sections: mobile pass (media queries are already ported into sections2.css).
3. Service choreography polish (first/second screens) to fix y3220.
4. Ocean polish: first pass DONE (2026-09-13 morning: NoColorSpace textures + level match + view-angle
   gradient + broad churn wash; column profiles now track live at f=2). Remaining deltas: f=4+ far-field
   brightness (live right side stays ~120-126B out to x1530; ours decays to ~97), water micro-contrast in
   some patches, cloud wash at section exit (f=6) weaker than live (165B vs 240B), awwwards badge omitted
   (third-party embed), hull-edge streaks a touch too clean.
5. Re-run full QA (qa-rebuild + why-check + compare-ab) and update ANALYSIS.md numbers.
6. PAGE BASE THEME AUDIT: live page base = white (body/.main --bg--main) with local dark var-remaps
   (why-main, service-speed); ours = dark body + local whites. Partners paints its own white now. Before
   the final QA, audit all sections on the white base model (and as insights[dark]/faq/footer land).

Servers left running at pause unless the box restarts.

## Session log 2026-09-12 (late): user-reported bug fixes

User flagged: "the forklift and ship, and the last flight is totally bugged".

1. **"forklift" = the Konecranes reach stacker, service screen 1.** Fixed three coupled issues:
   - DOM containers (svc-containers imgs) were floating high + a wrong early y-shift animation; positions now
     match live exactly (white 67.5rem/34.275rem, blue 67.5/47.775, orange 79.125/47.775; only a gentle exit drift).
   - The crane canvas sat 127px too high (top 5.5rem -> 15.03rem = live's y200).
   - The crane sequence ran over the wrong scroll window; now its own trigger [3820, 6970] linear (live's
     first-screen top+100vh -> top+450vh), so the drawn frame matches the live's at a given scroll.
   - Result: y3220 diff 33.7% -> 24.0%.
2. **Ship wake was on the wrong side and blocky.** The live's stern is at the TOP (bow down) and the wake trails
   ABOVE it; our shader drew below (bow side) and cut a hard rectangle. Wake now anchors to the ship's DOM box
   (uShipTop/uShipHalfW/uShipHalfLen uniforms fed from the img rect each frame), trails above the stern as a
   soft V with domain-warped speckle + density noise. Still less photoreal than the live's GPGPU wake sim
   (document in open threads; further tuning = diminishing returns).
3. **"last flight" = globe flight arcs.** Long flights (145/128deg) used linear lerp + normalize: the arc dove
   off the great circle and floated past the limb. Now true great-circle slerp + altitude x0.22 (arcs hug the
   globe) + airport pins r1.001/size .009 + dot cloud scaled 0.996 (no limb spill). Vision re-check: 9/10.
4. Also: header/topbar hide distance fixed (children stick out below the box: hide by offsetHeight+190,
   previously the logo+nav stayed visible on scroll).

Final QA numbers at the time of writing (compare-ab.py): y0 55.2/12.4 (globe anim phase), y1800 11.1/8.4,
y3220 24.0/22.4, y13000 4.5/4.1, y14160 3.1/2.7, y15060 46.7/11.4 (animated water).

## Session log 2026-09-12 (late #2): viewport-relative triggers (critical lesson)

User reported "animations aren't working at all" at their real window size. Root cause: several ScrollTriggers
used HARDCODED scroll positions measured at the 1440x900 QA viewport. The page height scales with viewport
(rem = 100vw/108), so at 1920x950 the page is 27470px tall and every hardcoded trigger fired ~1.33x too early:
the crane sequence, tail entrance, ship dolly and cloud reveal were all FINISHED by the time the user reached
the sections (looked frozen / "super bugged").

RULE: never hardcode scroll positions in this project. Use function-based start/end computed from element
positions + innerHeight (re-evaluated on ScrollTrigger refresh/resize). Fixed in sections.js (crane:
svcTop+1vh..+4.5vh), tail.js (entrance: tailTop-1.105vh..+1.18vh; speed windows: sublist bottom - 0.625vh),
why.js (ship dolly: wrapTop+0.267vh..+5.267vh; clouds: wrapTop+4vh..sectionBottom+1vh).

Verified: ship dolly mid-flight at BOTH 1920x950 (width 446 mid) and 1440x900 (220 mid); crane/tail/clouds
mid-states confirmed by screenshot at 1920. 1440 QA unchanged (y13000 4.5%, y14160 3.1%).

Note: at phone width (390px) the page is still desktop-only (rem scales to 3.6px, hero clips). Mobile pass
remains a dedicated milestone; not a regression.

---

## Repo

Public: https://github.com/pixie-chan/united-carriers-clone (created 2026-09-12, initial commit 3d08309,
3336 files / 418 MB, remote byte-sum matches local exactly).

## Session log 2026-09-12 (late #3): services choreography rebuilt (forklift) + ship wake reshape

User report: "forklift animation and ship animation are completely broken". Forensic pass at 1920x1080 against the
live mirror (_ref/analysis/repro2*.py, forensic.py, frame-phase-compare2.py - canvas pixel dumps + frame matching):

FORKLIFT / service screen-1 canvas
- The live's canvas is a THREE-sequence chain: seq0 (159f) -> seq1 (97f) -> seq2 (97f). Boundaries are seamless
  (end/start frame diffs < 1.0). Measured live mapping (offsets from .home-service top, in viewport heights):
  seq0 [1.00..2.26], seq1 [2.26..3.79], seq2 [3.79..4.53], then hold on the last frame.
- The old build played ONLY seq0 over [1..4.5] (~2.5x too slow) and never played seq1/seq2 (the carry + truck-load
  phases) - hence "completely broken". sections.js now concatenates seq0+1+2 and scrubs the global index over the
  measured windows. Verified: displayed frame within +-3 of live at every phase (f=2.5 -> seq1 f13 vs live 15, etc).
- .home-service-land: live has a full-width #111 ground band at top 55.1rem / h 5.62rem painted OVER the canvas
  (machine wheels sink into it). It was missing (machine floated on white). Added to index.html + sections.css;
  paint order: canvases -> land -> containers -> dark -> head -> cta -> cards.
- Container stack sits ON the land: live tops are white 28.18rem / blue+orange 41.62rem. Old values were +6.1rem
  too low (cropped stack). Canvas top also corrected 15.03rem -> 8.89rem (same +6.1rem offset). Machine scene now
  matches live pixel-for-pixel at f=2.0 (checked column samples).
- Dark panel: rises from the bottom over ~[4.3..6.0vh] and RESTS covering the bottom 60% (top edge y=432 @1920):
  it is NOT a full-screen cover. GSAP TRAP (cost an hour): do not combine a CSS `transform: translateY(100%)`
  pre-state with yPercent tweens - GSAP decomposes the CSS transform into its y cache (1080px) and yPercent stacks
  ON TOP of it, so the element never reveals. Drive `y` in px instead.
- Dark-screen typography: filmstrip behavior - heading enters from the right (~6.4vh), settles left (~7.0), exits
  left (~7.7) as the cards roll in (cards sweep retimed to ~[7.8..9.6vh]). Second line "Under one group." ghosted
  (rgba(255,255,255,.24)) as live. Single desc paragraph (old build had two overlapping). "Our Services" pill
  button added, centered at 55.3rem, fades with the dark.
- Verified 1920x1080: dark boundary within ~4-30px of live at every phase (432/432 at rest), no JS errors.
- Known remaining (next pass): live's top white band carries a truck + giant ghost "OUR SERVICES" wordmark
  scrolling horizontally (~f 6.5-10); the clone's band is empty there.

SHIP / ocean wake (js/why.js)
- The wake "side wash" rendered as TWO FULL-HEIGHT GLOWING BEAMS (exp(-((dx-halfW*1.14)/s)^2)*0.45 * screen-height
  fade = solid bright strips, no noise). Replaced: bow-wave V (bottom end, flaring out+down), thin broken hull
  streaks (stern->bow fade, width tied to ship scale), faint stern trail above, all modulated by churn/speckle
  noise and scaled by a size gate so the wake fades as the ship shrinks. Water brightened (deep 0.031/0.094/0.210,
  stronger normal-mod + env). Ship orientation confirmed from the asset: stern (superstructure) at TOP, bow DOWN.

Tooling added: _ref/analysis/repro2.py (phase walk + contact sheets), canvas-dump.py / frame-match.py /
frame-phase-compare2.py (in-page canvas dumps matched against source frames to find the displayed frame index),
forensic.py / tail-phase.py (5-sequence identification), skeleton.py, sweep-svc.py, endgame.py, verify4.py.
QA imagery under _ref/analysis/repro2/ is gitignored (large PNGs).

## Session log 2026-09-13 (morning): ocean water parity pass

Context: last session ended mid-verification; why.js carried uncommitted changes (NoColorSpace + tuning)
that were never probed or committed. This pass verified, completed and committed them.

- **QA harness flakiness ROOT-CAUSED**: the live mirror's engine intermittently dies on giant instant
  `window.scrollTo` jumps (pageerror "Cannot read properties of undefined (reading 'end')" -> why-scrub
  frozen: ship stuck at 541px, white clouds frozen over the scene, probes read white 254). Stepped scrolling
  (<=1200px per step, ~100ms apart) is 100% reliable across repeated runs. ship-water-check2.py now
  validates scrub-liveness (ship width MUST change between two phases) and retries before capturing.
- **Texture colour space**: textures sampled raw inside a custom ShaderMaterial need `THREE.NoColorSpace`;
  SRGBColorSpace made the GPU linearize -> washed-out desaturated water. The fix is correct, kept.
- **Measured fixes this pass** (fresh paired captures, 1920x1080, stepped scroll both sides):
  - deep 0.095/0.270 -> 0.086/0.245; large-scale mottle restored (.88+.22); speckle grain 64/46 -> 96/70;
    hull side foam 0.12+0.60*breakup; bow armLine 0.95; foam mix 1.45 clamp .88; scGate fades later
    (0.008..0.05).
  - NEW view-angle gradient (top +10% / bottom -10%): live has per-pixel fresnel, our V was constant -> the
    flat look. f=2 right-side column profile now: live 148/128/117/106/99 vs ours 156/116/108/102/97.
  - NEW broad churned-water wash (wake component 4): wide soft bright field decaying laterally from the
    hull. Live keeps a bright textured field hundreds of px out even when the ship is small; ours was a
    thin hull band only.
- **Dolly parity verified numerically** (ship width, live vs reb): 510/516 (f1), 414/416 (f2), 266/253 (f3),
  130/113 (f4), 58/49 (f5), settled identical 40/196/442/940 (f6). Mid-range shrink a hair fast; accepted.
- Known remaining: see Open threads #4. Awwwards badge = third-party embed (div#awwwards), omitted by
  design unless wanted.
- Tooling: ship-water-check.py (paired capture), ship-water-check2.py (robust: stepped scroll + liveness
  check + retry), both kept in _ref/analysis; QA imagery in repro2/whypair/ (gitignored).

## Session log 2026-09-13 (testi build)

- Testi (plane flyover + testimonial wipe) BUILT via the port pipeline: build-port.py now filters the
  .home-testi css + the w-node grid rules (plane and content share grid cell 1/1, was the missing piece)
  + webflow base p margins SCOPED to the section (a global p rule would shift the early abs-positioned
  blocks); _testi_block.html generated from testi.pretty.html; wire-index.py inserts after WHY:END
  (replace-capable for re-runs); js/testi.js ports the overlap timeline (--overlap-clip -60->180, plane
  scale 1->1.3, shadow vars, why-cloud push) + the item rise/fade reveal; main.js calls initTesti.
- VERIFIED 1440x900: geometry all EXACT (wrap h 2991, content-inner 1911, list 1496, item2 559, p mb 10px);
  timeline values match live to <0.1 units (clip/scale/shadow/img rect at every phase); zero console
  errors. Earlier f=3.0 sticky "mismatch" was page truncation (testi is last section so far), not a bug.
- Paired captures at 10 phases in repro2/testi1440/ (gitignored). Visual review + 1920x1080 pass pending.

## Session log 2026-09-13 (continuation): testi handoff + cloud timing

- Testi visual pass + 1920 check DONE. Testi timeline matches live at BOTH viewports (clip/scale/img
  rect to <0.5px at 1440 and sub-unit at 1920; geometry: testi wrap h exact 3825 both at 1920).
- Why-exit cloud arrival was ~200px LATE vs live; recalibrated all 9 cloud-overlap tweens against a
  measured opacity ramp (live: sheet 19350-20150 @1440; items c2->c7->c1->c3->c5->c4->c6). Now within
  ~0.05-0.1 opacity at every sampled scroll.
- GSAP %-TRANSFORM CACHING BUG (important): cloud items carry CSS translate(-50%, +50%); GSAP caches
  the % as px at boot, when lazy images are unloaded and the item box is ~21px tall -> the +50% Y
  offset froze at +10px instead of +490/+449/+254 for c1/c5/c6 (only positive-Y items; negative-Y
  items fine). Fix: explicit aspect-ratio per item (build-port why_extra) so the box has its final
  height before GSAP touches it. ty now matches live exactly (490.4/448.7/254.3).
- Late-phase water: added dolly-progress darkening (-16%) + wash taper; handoff pixel grids now
  mean|diff| ~26-34 (was 147-180). RESIDUAL (open): late-phase top-strip is still ~+30-60 (sum RGB)
  brighter than live in patches (diffuse, not structural; visible only in side-by-side stills).
- Note: at 1920 the pre-why sections run +1680px taller than live (why top: live 18400 vs reb 20080).
  Section-relative phases are all exact; the absolute page offset needs an audit of hero/intro/
  service/tail tops at 1920 (add to QA thread).
- QA scripts: handoff-probe.py, testi-probe.py, verify-1920.py (kept).

## Session log 2026-09-13 (continuation 2): partners built

- Partners section BUILT via the port pipeline (logo lattice, hover crossfade, batch reveal) and verified
  at 1440 and 1920: pixel diff 1.3-2.1 (essentially identical), geo within 1px, counts exact (17/16, no
  placeholder fill - live's runtime leaves the templates in a .hidden div, so no refill: matched).
- Learned: .hidden/{display:none} base rule was missing from our css (a 818px ghost row inside the grid);
  .hidden added to KEEP_BASE. Live label/cate texts are STATIC (live's runtime never animates them);
  our reveal removed to match. Inline label widths (339/1032px) are build artifacts: live runtime has
  none (natural 334/1027), stripping them in the block is correct.
- PAGE BASE THEME (open thread): live model = white body/.main + local dark var-remaps; ours = dark body
  + local whites. Partners region now paints its own white via .home-partners-wrap. Before the final QA,
  audit every section over a white page base (insights is dark, faq/footer TBD) - see open threads.

## Session log 2026-09-13 (continuation 3): insights built

- Insights (dark article list + thumbs) BUILT + verified: section h EXACT 812, pixel diff 0.7-1.1
  in-section, hover sync exact, reveal states match (action+main rise 26.67px/fade at 'top 90%').
- PAGE BODY FONT FIXED: our body was font-size 1.2rem (16px) vs live's effective 13.33px (= 1rem in
  our rem system) + lh 1.3. Every inherited-size element was ~20% large (e.g. insights item meta texts).
  Verified no regression on partners (pixel diff unchanged 1.3-2.1).
- Base classes that had been missing (now in KEEP_BASE): .display-contents, .w-inline-block, .hidden.
- Live's small mono texts size to the GLYPH box (fs x 0.795, e.g. 8.33px -> 6.625px) - replicated with
  scoped line-height .795 on .home-ins-cms-item-* mono texts. Watch for this pattern in later sections.
- Pitfall: pretty-printing blocks inserts whitespace text nodes between blocks and inline-blocks (adds
  strut lines); insights block now collapses inter-tag whitespace (>\s+<). Live html is minified.
- Insights block links: our hrefs kept the extract's absolute "/insights/..." (live mirror rewrote the
  extract's originals to relative "insights.html"); left as-is, revisit for local link fidelity.

## Session log 2026-09-13 (continuation 4): faq built

- FAQ BUILT + verified: geometry within 1px (wrap h 711 vs 712), reveal states identical (title mask
  style lifecycle matches live exactly: width 249 + overflow hidden + height 63 during approach, cleared
  at rest), accordion click behavior identical on both sides (one-open, toggle, reopen). Pixel diff
  1.1-2.9 in valid ranges (deeper phases clamp-differs until CTA/footer exist).
- Title reveal = split-line MASK slide (live splits the heading, clips it, slides the line up); ported
  manually in faq.js (wrap span + yPercent + clearProps on complete).
- FAQ numbers are CSS counters (faq-counter, decimal-leading-zero) via embedded rules + fs-10 mono with
  the glyph-box line-height 0.795.
- Same page-base theme pattern: .home-faq-wrap paints its own white (live: page-level .main bg).
