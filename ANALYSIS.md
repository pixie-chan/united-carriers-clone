# United Carriers, deep analysis + offline mirror

Date: 2026-09-12
Target: https://unitedcarriers.com/ (Awwwards Site of the Day, Sep 6 2026, 7.28/10, by Bearplus)

## 1. Architecture (how the site is actually built)

Three layers stacked:

1. **Webflow** for markup, CSS, CMS and page routing
   - CSS: `united-carriers.webflow.shared.fc188c3b2.min.css` (439 KB) 
   - Runtime: `webflow.*.js` chunks + jQuery 3.5.1
2. **Custom Vite bundle on Netlify** (`https://united-carriers.netlify.app/main.js`) for all high-end behavior
   - GSAP (`vendor-gsap`), **Lenis** smooth scroll, **Barba.js** page transitions, Swiper (sliders), Three.js (`vendor-three`), WebGL scenes
   - Per-page modules: Home, About, Career, Contact, Service, Article, Insight, Industry, Community, Merchandise, Checkout, Payment, globe
   - Scene modules: `OceanScene` (ship/ocean WebGL), `WakeSimulation`, `frame-sequence` (scroll-scrubbed image sequences), `my-flights` (dot globe + airport/flight data), `layout` (loader, transitions, cursor), `helpers`
3. **Third parties**: cookieyes (consent), mixpanel, gtag, Stripe, Finsweet attributes, Awwwards badge iframe

### The domain whitelist (important finding)
The bundle top-level throws `Error("Unauthorized domain")` unless the hostname is one of
`united-carriers.webflow.io`, `united-carriers-bp.webflow.io`, `united-carriers.netlify.app`, `unitedcarriers.com`.
On any other host the whole engine dies (loader stuck, black page). Our offline copy patches this array
to also allow `127.0.0.1` and `localhost`.

### Runtime external fetches
- `https://unpkg.com/world-atlas@2/land-110m.json` (land polygons for the dot globe). Patched to local `/land-110m.json` in the mirror.
- `https://challenges.cloudflare.com/turnstile/v0/api.js` (contact form captcha, not needed offline)
- `https://ipinfo.io` (geo helper), analytics endpoints (not needed offline)

## 2. Page structure (homepage, desktop 1440)

Total scroll height: **28,230 px**. 10 `<section>` elements:

| # | class | y (px) | h (px) | What it is |
|---|-------|--------|--------|-----------|
| 1 | home-hero | 0 | 2250 | Black hero: dot-map intro, wordmark, tickers, live counter, then WebGL dot globe + "EVERY LEG OF THE JOURNEY" + CTAs |
| 2 | home-intro | 1799 | 1436 | White statement: "WE MOVE FREIGHT. WE OWN THE OUTCOME." + 2 paragraphs + 2,500+ / 20,000+ counters |
| 3 | home-service | 2920 | 12140 | The big scroll piece: "EVERYTHING YOUR FREIGHT NEEDS" with 6 services and scroll-scrubbed equipment frame sequences (crane, truck) |
| 4 | home-why | 14160 | 6662 | "LOGISTICS THAT WORKS AS HARD AS YOU DO." with the WebGL OceanScene (ship + wake) and 5 reason points |
| 5 | home-testi | 19922 | 2991 | "TRUSTED BY BUSINESSES ACROSS APAC" testimonial slider |
| 6 | home-partners | 22913 | 1557 | Airline + shipping line logo marquees |
| 7 | home-ins | 25303 | 812 | "WHAT'S MOVING IN YOUR INDUSTRY" insights list |
| 8 | home-faq | 26114 | 712 | F.A.Q accordion |
| 9 | (footer CTA) | ~26826 | 540 | "READY TO MOVE SMARTER?" (lives inside footer wrap) |
| 10 | footer | 27366 | 864 | Address, links, animated footer logo canvas (2059x318) |

Canvases (desktop): `home-hero-canvas` (dot globe, 900x900), `home-service-crane-sq` (1339x753),
`home-service-truck-sq` (1045x293), `home-why-ocean-img` (1440x900), `footer-logo-canvas-inner` (2059x318).

## 3. The loader (page intro)

Full-screen black overlay (`z-index 999`), revealed in place for ~2.5-4 s while assets preload:

- Left column: `UNITEDCARRIERS` wordmark + **country ticker** (Australia, New Zealand, Hong Kong, China, Vietnam, United States, Thailand, Germany, United Kingdom) in BT Steinhart Mono, dim
- Right column: **live percent counter** (0-100) + dotted circular spinner + **services ticker** (Air Freight, Ocean Freight, Customs Brokerage, Warehousing & 3PL, Project Cargo, Domestic & Linehaul Transport)
- Center: **dot-matrix world map** (halftone dots), white hub dots, ~4 bright blue active nodes (SE Asia / Australasia), arrows animating in
- Top-left: circular progress ring (clipped at corner)
- Exit: counter completes, map fades, curtain lifts (Barba `once` transition), then hero content plays in

## 4. Design tokens (exact)

- Fluid rem: `html { font-size: 100vw / 108 }` -> at 1440px root = 13.333px. Everything sizes in rem.
- Colors: `--color--primary: #0016cb` (electric blue), `--color--secondary: #f50` (orange),
  surfaces: `white`, `#f4f4f4`, `#111`; content: `#111`, `rgba(17,17,17,.72)`, `#1116`, `rgba(17,17,17,.16)`;
  borders `#1113` / `#1111114d`; accent on dark sections: `#f45300`
- Fonts: `BT Steinhart` (headings, 500/700), `BT Steinhart Mono` (labels/buttons, 400), `Helvetica Neue` (body, 400/500).
  Files mirrored: 5 woff2 subsets.
- Type scale (measured at 1440): 8.33px mono labels, 10px mono, 13.33px body (Helvetica Neue 500), 16px, 24px, 26.67px service names, 60px statement text, 80px section headings, 133.33px hero stat counters
- Container: 16 columns, 2rem gap, 4rem page padding
- Breakpoints: 479 / 767 / 991 (Webflow standard)
- Utilities seen in DOM: `data-cursor` (121 uses), `data-marquee` (13), `data-count`, `data-node-type`, `data-link-random`, `data-svg-origin`

## 5. Animation systems inventory

1. **Loader**: percent counter, ticker lists, dot map, curtain lift, content stagger-in
2. **Hero dot globe**: Three.js `Points` globe. Dot positions rasterized in a **Web Worker** from land polygons
   (`world-atlas@2/land-110m.json`, tile step ~1.2 deg, latitude-aware spacing, point-in-polygon).
   Airport pins (`AirportsCollection` inline data: LHR, FRA, DXB...) + animated **flight arcs** (`FlightsCollection`).
   Auto-rotates: `phi += 0.0015` per 16.6ms frame. Desktop cameraZ 2.23, tablet 2.8, mobile 2.7.
   Section pinned: globe scales/moves through the hero (tlGlobe timeline), labels per country.
3. **Service section frames**: TWO pre-rendered image sequences (`frame_df`, `frame_000...frame_124` etc,
   ~762 frames total) scrubbed on canvas by scroll (FrameSequence class: lerp playhead, windowed loading, cache).
   Services list swaps (Air / Ocean / Customs / Warehousing / Project / Domestic) synced to scroll.
4. **OceanScene**: Three.js water (simplex-noise vertex displacement, 68x68 repeated normal map, envmap reflections)
   + `WakeSimulation` (ship wake). Textures: `images/ocean/water-normal.webp`, `ocean-envmap.webp`, `ocean-overlay.webp`.
5. **Marquees**: partners logos + loader tickers (`data-marquee`), continuous loops
6. **Counters**: `data-count` count-up tweens (2,500+, 20,000+)
7. **Custom cursor**: `cursor-main` + `cursor-outline circle` progress ring that tracks page scroll progress,
   trail items, modes for link/hidden/control (`data-cursor`)
8. **Page transitions**: Barba + GSAP cover animation with per-namespace lifecycle (enter/leave hooks)
9. **Footer logo canvas**: particles/scan effect drawing the wordmark
10. **Smooth scroll**: Lenis everywhere (`html` gets `lenis` class), scroll-linked header behavior

## 6. Where everything lives (project)

- `_ref/mirror/` : **complete offline copy** (the 1:1 replica). Entry: `unitedcarriers.com/index.html`.
  - `_netlify/` full Vite bundle + chunks (patched: +localhost hosts, unpkg->local)
  - `cdn.prod.website-files.com/` Webflow CSS/JS/images/fonts/videos/frames (~140 MB of media, 762 frames)
  - `_vendor/` jQuery + Finsweet (rewritten to local)
- `_ref/analysis/` : this repo of forensics
  - `pretty/*.js` beautified bundle sources (Home, layout, OceanScene, globe, frame, my-flights, main)
  - `measures/` deep runtime measurements (desktop.json, mobile.json, DOM snapshot, loader frames)
  - `verify/` live-vs-mirror screenshot pairs + composites
  - scripts: `measure.py` (runtime probe), `verify-shots.py` (paired shots), `compare-shots.py` (pixel diff),
    `frames-download.py`, `localize-media*.py`, `fix-sri.py`, `fetch-netlify.py`

## 7. Verification of the mirror (pixel diff vs live, same viewport 1440x900)

| scroll y | % pixels differing (>16/255) | verdict |
|----------|------------------------------|---------|
| 0        | 1.34% | hero: globe/ocean animation phase only |
| 1800     | 0.00% | exact |
| 3220     | 0.00% | exact |
| 14160    | 0.00% | exact |
| 19920    | 0.83% | ocean waves phase only |
| 22900    | 0.00% | exact |
| 25300    | 0.00% | exact |
| 27400    | 1.26% | footer canvas animation phase |
| 27900    | 0.62% | footer marquee phase |

Scroll height: mirror 28,229 px vs live 28,230 px.
All residual differences are time-phase of running animations, not layout or asset errors.

## 8. Known intentional divergences (offline enablement)

1. Domain whitelist patched (+127.0.0.1, +localhost). Without it: black screen.
2. SRI `integrity` attributes stripped (local rewriting changes bytes; hashes would block CSS/JS).
3. `unpkg.com` land-110m.json -> local `/land-110m.json`.
4. Analytics/consent/Stripe/CAPTCHA calls fail offline by design (mixpanel, gtag, cookieyes, turnstile); visual impact: none.
5. Awwwards badge iframe still loads from awwwards.com when online; offline it disappears.

## 9. Next: the rebuild

The rebuild (`site/`) reimplements the homepage in our own clean HTML/CSS/JS on the same assets:
own loader, own three.js dot globe (same land data + airport/flight JSON), own frame-sequence player,
own ocean shader, own marquee/counters/cursor, Lenis + GSAP vendored locally. Goal: same measured
values (tokens above), verified against the mirror with the same pixel-diff pipeline.

## 10. Rebuild status (phase 1, hero screen)

Built so far in `site/`:
- `index.html`, `css/site.css` (tokens from section 4), `js/main.js` (Lenis + loader + reveal), `js/globe.js`
  (own three.js dot globe: land dots rasterized offline, status-active flight arcs, airport pins,
  fresnel rim amber-top/blue-bottom, projected country labels), `js/cursor.js`
- assets: fonts (5 woff2), 681 images, 763 frame-sequence images, 4 video pairs, airports/flights JSON,
  land-110m TopoJSON, 8267 rasterized globe dots
- vendors vendored locally: GSAP 3.13, ScrollTrigger, Lenis 1.3.11, three.js r184

Verified via DOM-level diff vs live (compare-dom.py): header logo, nav, hero label/H1/desc/CTAs and the
globe canvas all land within a few px of the original (canvas exactly 748,0,900,900; H1 6rem/1.05 at
414,443; CTAs 134x40 at 414/555,827). Pixel diff of the hero is dominated by animation phase only.

Run it: `cd ~/projects/united-carriers-clone/site && python3 -m http.server 8898` then open
http://127.0.0.1:8898/ . Mirror serves the same way on :8899 (root = `_ref/mirror/`, entry
`/unitedcarriers.com/index.html`).

Next phases: intro statement, services scroll section (frame-sequence scrubbing + 6 services),
why/ocean (the WebGL ocean + ship), testimonials, partners marquee, insights, FAQ, footer logo canvas;
then a mobile pass; then section-by-section pixel-diff scoring like section 7.


---

## 8. Port methodology (service tail + why section, 2026-09-12)

Sections beyond services are **ported** from the live sources rather than hand-measured:

- Sources: raw webflow css (media-aware extraction), the page's 16 embedded `<style>` blocks,
  and the measured DOM snapshot (`measures/home-dom.html`). Builder: `_ref/analysis/build-port.py`,
  output `site/css/sections2.css` (~1.9k lines) + `_tail_block.html` + `_why_block.html`.
- **Rem rescale x0.625**: live html font-size is 1440/172.8 (=8.333px); the rebuild's is 100vw/108
  (=13.333px). Every ported rem value is scaled so pixel results match at 1440x900.
- **Grid**: `.container.grid` from embedded block #5 (named-line 16-col grid); w-node id rules
  ported verbatim (grid placement). Live overrides from embedded blocks merged (e.g.
  `.home-service-third-screen{margin-top:-200vh}` - neutralized inside `.uc-tail`).
- **Resting states in CSS, motion in JS**: runtime end values measured from the live (scroll 14160:
  truck top -542px, rot translate -453.6px rot90, inners scale .346/.39 x -61.3px, road-wrap
  translateY(-100px), speed HUD 33px/8.4rem sticky) are baked as `.uc-tail` CSS; JS entrances
  animate toward them.
- **Why/ocean**: own three.js shader (water-normal tiling + equirect env at low weight + the site's
  own overlay photo via saturation blend + luminance mottling + analytic wake in screen space keyed
  to the ship's DOM rect). Ship dolly scrub range fitted numerically to live data:
  [15300,19800] with cubic-bezier(.45,.05,.55,.95); cloud reveal retimed to live pacing (numeric
  ScrollTrigger positions; `vh` strings silently fail to parse in ScrollTrigger).

Verified diffs after the port (diff>16 / diff>48, fresh paired captures): y13000 4.5/4.1,
y14160 3.1/2.7, y17500 28.4/4.0, y19000 44.6/4.8 - residual dominated by animated water phase.
