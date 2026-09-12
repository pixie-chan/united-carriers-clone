<div align="center">

# 🚢 UNITED CARRIERS · CLONE & REBUILD

**A 1:1 offline mirror of [unitedcarriers.com](https://www.unitedcarriers.com) + a fully editable, from-scratch rebuild of it + the complete reverse-engineering toolkit used to port it.**

[![GSAP](https://img.shields.io/badge/GSAP-3.13-88CE02?style=for-the-badge&logo=greensock&logoColor=white)](https://gsap.com)
[![three.js](https://img.shields.io/badge/three.js-r184-000000?style=for-the-badge&logo=threedotjs&logoColor=white)](https://threejs.org)
[![Lenis](https://img.shields.io/badge/Lenis-1.3.11-7C3AED?style=for-the-badge)](https://lenis.darkroom.engineering)
[![No build step](https://img.shields.io/badge/build_step-none_(vanilla_JS)-2ea44f?style=for-the-badge)](.)

[![Mirror](https://img.shields.io/badge/offline_mirror-0.00%25_pixel_diff_%40_6%2F9_scrolls-brightgreen?style=for-the-badge)](.)
[![Tail anchor](https://img.shields.io/badge/rebuild_tail-3.1%25_%40_y14160-yellow?style=for-the-badge)](.)
[![Console](https://img.shields.io/badge/console_errors-0-brightgreen?style=for-the-badge)](.)

</div>

---

## ✨ What is this?

Three things in one repo:

| 🧩 Part | What it is |
|---|---|
| **`_ref/mirror/`** | A byte-for-byte offline capture of the live site (Webflow + Netlify bundle folded in). Verified against the real site at 0.00% pixel diff at 6/9 scroll positions (the rest is live-animation phase, not drift). |
| **`site/`** | **The rebuild.** Written from scratch in vanilla JS + GSAP + three.js + Lenis. Zero build step, zero frameworks, fully readable and editable. This is the actual product: an *editable replica base* made for future customizations (for example: swap the ship for an airplane, re-skin sections, hand parts to another dev). |
| **`_ref/analysis/`** | **The toolkit.** Every Playwright harness, DOM/CSS extractor, measurement run, diff composite and port generator used to reverse-engineer the original and verify the rebuild against it, pixel by pixel. |

> **Why?** Cloning by "eyeballing screenshots" is how you get a lookalike with dead animations. This repo instead ports the real thing: extracted live DOM + media-aware CSS extraction + the original's own GSAP timings, driven by a live-vs-rebuild diff pipeline that reports hard numbers.

---

## 📦 What's inside

```
united-carriers-clone/
├── ANALYSIS.md              reverse-engineering dossier: architecture, design tokens,
│                            section/offset tables, animation inventory, verification runs
├── STATE.md                 living status doc: what is built, what is pending, tooling
│                            cheat-sheet, session logs (read this first)
│
├── site/                    THE REBUILD (own code, no build step)
│   ├── index.html
│   ├── css/
│   │   ├── site.css         tokens: colors, fonts, loader, header, hero, cursor
│   │   ├── sections.css     intro, services, milestones (hand-measured from live)
│   │   └── sections2.css    GENERATED: ported live CSS (rem-rescaled) + grid system
│   ├── js/
│   │   ├── main.js          boot, Lenis, loader choreography
│   │   ├── globe.js         dot globe: 8267 rasterized land dots, airport pins,
│   │   │                    great-circle flight arcs (slerp), fresnel rim, labels
│   │   ├── sections.js      intro + services choreography (frame sequences)
│   │   ├── tail.js          road + truck + reliability screen + scroll speedometer
│   │   ├── why.js           ocean section: three.js water shader (own), ship dolly,
│   │   │                    cloud reveal, list reveals
│   │   ├── cursor.js        dot + lagging outline + scroll-progress ring
│   │   ├── chrome.js        header/topbar hide-on-scroll (matches live)
│   │   └── frames.js        frame-sequence canvas player with draw-retry
│   ├── vendor/              GSAP 3.13, ScrollTrigger, Lenis 1.3.11, three.js r184 (vendored)
│   ├── data/                globe-points.json, land-110m.json, AirportsCollection.json,
│   │                        FlightsCollection.json, frames-sequences.json
│   └── assets/              fonts (5 subsets), 681 images, 763 frame-sequence images,
│                            videos (incl. Sea-wave), ocean textures
│
└── _ref/
    ├── mirror/              1:1 offline mirror of the live site (167 MB)
    │   └── _netlify/        the site's own bundle (chunks, images, WakeSimulation, OceanScene)
    └── analysis/            99 MB of tooling + evidence
        ├── pretty/          beautified live bundle code (Home.js, OceanScene.js, globe.js...)
        ├── extracts/        live DOM + CSS extracts (why.html, tail, tests, port CSS, wids)
        ├── measures/        DOM measurement runs (desktop.json, mobile.json, home-dom.html)
        ├── qa/ verify/ ab/ qaw/ bughunt/whyviews/    screenshot runs + diff composites
        ├── build-port.py    GENERATOR: raw live CSS + embedded overrides -> sections2.css
        ├── wire-index.py    GENERATOR: folds the ported markup blocks into index.html
        ├── compare-ab.py    paired live-vs-rebuild screenshot diff (identical harness)
        ├── tail-check.py / why-check.py / measure scripts / extractors / ...
        └── *.json           measurement tables and fits
```

---

## ✅ Verification (real measured numbers, not vibes)

Every screenshot pair is captured in headless Chromium with an **identical harness** for both sides (same viewport, same scroll procedure, same waits), then diffed pixel by pixel. `diff>16` / `diff>48` = percentage of pixels differing beyond that channel delta.

| Scroll | Live vs rebuild | Note |
|---|---|---|
| `y=0` | 55% / 12% | hero dot-globe: both sides are live 3D animation, rotation phase differs by design |
| `y=1800` | 11% / 8% | intro: reveal-timing residue (count-up phase) |
| `y=3220` | 24% / 22% | services: frame-sequence phase + stacked-container composite |
| `y=13000` | 4.5% / 4.1% | service tail entrance |
| `y=14160` | **3.1% / 2.7%** | service tail anchor (road + truck + reliability) |
| `y=15060` | 47% / 11% | why/ocean: animated water phase dominates the raw diff |

Plus: **0 console errors** and **0 failed requests** at every capture point.

The offline mirror itself compares at **0.00%** against live captures at 6 of 9 scroll positions (the remaining 3 are mid-animation frames on both sides).

---

## 🧠 The interesting engineering bits

- **The rem-scale discovery.** The live site's root font-size is `100vw/172.8` (8.33px at 1440) while the rebuild uses `100vw/108` (13.33px). Every ported value runs through a **x0.625 rescale** in `build-port.py`, which is why ported CSS lands pixel-close instead of 1.6x too big.
- **Media-aware CSS porting.** `build-port.py` walks the minified Webflow stylesheet *with its @media nesting intact*, filters the exact rule sets needed, rescales rem values, merges the page's own embedded override blocks, and emits one generated stylesheet.
- **The webflow grid system** (`[full-width-start] ... [content-start] repeat(16, ...)`) lives in an embedded style block, not the main stylesheet. Ported as-is; that is what makes the 16-column offsets line up.
- **The ship is two stacked images** (ship + wake strip) that bob by equal pixel amounts; the wake in the live version is a GPU wake simulation, ours is an analytic screen-space V plume anchored to the ship's DOM box each frame.
- **Flight arcs use true great-circle slerp.** (Linear lerp + normalize makes long routes dive off the sphere and float into space. Ask us how we know.)
- **Every ScrollTrigger is viewport-relative.** The page scales with window width, so hardcoded scroll positions silently fire 1.33x too early on bigger screens. All triggers compute from element positions + `innerHeight` and re-evaluate on refresh.

---

## 🚀 Run it

No build step, no dependencies. Two static servers:

```bash
# the rebuild
cd site && python3 -m http.server 8898

# the offline mirror of the original (for side-by-side QA)
cd _ref/mirror && python3 -m http.server 8899
```

Then open `http://127.0.0.1:8898/` and compare against `http://127.0.0.1:8899/unitedcarriers.com/index.html`.

QA harnesses need Playwright + Pillow (`pip install playwright pillow`, `playwright install chromium`), e.g.:

```bash
cd _ref/analysis
python3 compare-ab.py      # paired live-vs-rebuild screenshots + diff table
python3 tail-check.py      # tail section anchor check
python3 why-check.py       # ocean section sweep
```

---

## 🗺️ Build status

| Section | Status |
|---|---|
| Loader (wordmark, tickers, dot map, counter) | ✅ |
| Hero + dot globe (own three.js, flight arcs, labels) | ✅ |
| Intro (sticky column, count-up stats) | ✅ |
| Services (frame scrubs: reach stacker, truck) | ✅ (choreography polish pending) |
| Service tail (road, truck, reliability, speedometer) | ✅ 3.1% @ anchor |
| Why / ocean (own water shader, ship dolly, clouds, list) | ✅ (water realism polish pending) |
| Testimonials, partners, insights, FAQ, footer | ⏳ next |
| Mobile pass | ⏳ after sections |

Full details, tooling cheat-sheet and session logs live in **`STATE.md`**.

---

## ⚖️ Disclaimer

This is a study / QA / reverse-engineering project. All original design, code, imagery and content belong to **United Carriers** and their respective owners (built on Webflow + Netlify). The `_ref/mirror/` directory is a local offline capture kept for comparison and verification purposes. Not affiliated with, endorsed by, or intended to compete with the original. If you are a rights holder and want something removed, open an issue.
