# FUI — Fantasy / Fictional User Interface

The industry term for sci-fi UI: the HUDs, consoles, and data overlays in Iron Man, Blade Runner 2049, The Martian, Westworld, The Expanse. Not "cyberpunk" (too broad — that's the umbrella aesthetic). Not "HUD" (that's a UI mode — heads-up). **FUI** is what to search when looking for references.

Part of the [muriel](../SKILL.md) skill, under Aesthetic Vocabularies. See the top-level index for mission and universal rules that apply across every vocabulary.

## When to reach for it

- **Agent-as-instrument readouts.** When the agent's output wants to feel like telemetry — live stats, mission clocks, bearing readouts, signal traces — rather than a paragraph of prose.
- **Research and demo framing.** Eye-tracking visualizers, pupillometry dashboards, saliency overlays: FUI grammar gives instrument-style credibility without leaning on dashboard-chrome clichés.
- **Product marketing for technical tools.** Scrutinizer, Psychodeli, AdSERP viewers — things that *are* instruments read well in instrument grammar.

Don't reach for it when:

- The content is editorial prose. FUI adds chrome that the words have to fight through. Use [marginalia](https://github.com/andyed/marginalia) via [`channels/web.md`](../channels/web.md).
- The information isn't real. FUI applied to fake data reads as cosplay. Either ship real numbers or stylize the placeholder so clearly nobody mistakes it for real (`████`, `XX.XX`).
- Ambient decoration is the actual goal. See [`vocabularies/kinetic-typography.md`](kinetic-typography.md) or [`vocabularies/visible-language.md`](visible-language.md) — different traditions, different payoffs.

## Canonical lineage

| Studio / Designer | Work | Notable for |
|---|---|---|
| **Perception NYC** (John LePore) | Iron Man's Stark HUDs, Black Panther's Shuri lab, Avengers | Radial geometry, translucent data layers |
| **Territory Studio** | Blade Runner 2049, The Martian, Ex Machina, Ghost in the Shell (2017) | Analytical overlays, thin-stroke grids, restraint |
| **Ash Thorp** | Prometheus, Ender's Game, Call of Duty Ghosts | Motion-forward reveals, procedural data |
| **GMUNK** (Bradley G. Munkowitz) | TRON: Legacy, Oblivion, Prometheus | Radial/polar compositions, shader-driven textures |
| **Jayse Hansen** | Iron Man 3, Big Hero 6, Star Trek Beyond | Typographic/numeric precision in flight HUDs |

## Visual grammar

- **Thin strokes** (0.5–1px) arranged in grids, polar coordinates, concentric rings, or parallel rules.
- **Corner brackets** (L-shaped marks at the corners of data blocks). Cheap signature, high legibility.
- **Monospace numerics with leading zeros** — `00042`, `0.0384`, `N 40°42'46"`, `T-00:14:22`. `font-variant-numeric: tabular-nums` is the CSS for this.
- **Radial / polar elements** — dials, compass overlays, scan arcs, rose diagrams. Psychodeli's 10-ring wordmark border is a well-tempered instance.
- **Grid overlays** — faint lines in accent color, sometimes animated or parallax-scrolling.
- **Leader lines** — thin diagonal strokes from a data point to a typographic callout, like an engineering drawing.
- **Scan lines** — subtle horizontal-line texture across the frame (~3% opacity, 2px period). Optional chromatic aberration for CRT nostalgia.
- **Data tickers** — live-updating numbers, `requestAnimationFrame`-driven counters that roll or flicker between values.
- **Animated reveals** — elements fade / translate / scale in with staggered 80–200ms delays, not instantly. `cubic-bezier(0.4, 0, 0.2, 1)` for the "precise machinery" feel; this is muriel's `--mg-ease-emphasis`.
- **Restrained palette** — one dominant accent hue (cyan, amber, red) on near-black. Matches the universal OLED rule.
- **Glitch / noise accents** — used as *punctuation*, never as ambient texture.

## Substrate decision

| Layer | Pick | Why |
|---|---|---|
| **Thin-stroke geometry** (compass rings, grids, crosshairs, corner brackets) | **SVG** | Lossless scaling; `stroke-width` and `stroke-dasharray` animate on CSS/rAF; no pixel aliasing. |
| **Text + layout** | **HTML + CSS Grid** with `font-variant-numeric: tabular-nums` | Tabular digits stop the ticker from juddering; Grid does the block arithmetic for free. |
| **Tickers, waveforms, scrub overlays** | **Canvas2D + `requestAnimationFrame`** | 60fps redraw without DOM reflow; cheap enough for dozens of simultaneous readouts. Use [pretext](https://chenglou.me/pretext/) when the animation needs precise text measurement; see [`channels/interactive.md`](../channels/interactive.md#typographic-canvas-with-pretext). |
| **Post-process** (scan lines, chromatic aberration, noise, glitch) | **CSS `repeating-linear-gradient`** for scan lines; **WebGL2 fragment shader** for anything spatially-varying | Scan lines don't need a GPU; glitch does. One fullscreen WebGL pass on top is enough — don't try to render the whole HUD in WebGL. |
| **3D depth** (HUD-in-scene, e.g. Iron Man's in-helmet view) | **Three.js with Troika SDF text** | Respect the SDF alpha rule (see below). Rare; most FUI work is 2D. |

**Not** PixiJS unless you have 10k+ particle-dense elements. FUI is sparse and thin-stroked; PixiJS is overkill.

## Common failures

- **Mushy typography.** Most amateur FUI dies here. Pick one monospace face, commit to it, track tight, and let the numbers do the work. Don't mix display and working mono in the same block.
- **Juddering counters.** Ticker digits changing width causes layout shift each frame. Fix with `font-variant-numeric: tabular-nums` on the container — this is a one-line fix that people forget.
- **Decorative strokes below 55/255.** Muriel's universal rule: decorative elements need ≥55/255 on a dark background or they vanish on small screens. Thin-stroke grids at 10% opacity look right on a 5K display and disappear on a phone.
- **SDF text alpha fades.** Never modulate alpha on Troika/BMFont SDF text — it breaks distance-field antialiasing. Cross-fade via RGB tween or scale instead. (See [`vocabularies/kinetic-typography.md`](kinetic-typography.md) for the canonical phrasing.)
- **Fake data that reads as fake.** `Lorem 0923.88.Ipsum` is worse than `████`. Stylized blanks commit to being blanks; Lorem-style placeholders read as lazy worldbuilding.
- **Everything animating at once.** If the reveal stagger collapses to zero, the composition reads as a pop-in, not as machinery waking up. Keep 80–200ms gaps between elements.
- **Chrome without content.** Corner brackets, scan lines, and thin-stroke grids don't substitute for information. A FUI block with nothing to say is a cosplay prop.
- **Contrast drift mid-animation.** A reveal that tweens from `opacity: 0` passes through low-contrast states for several frames. If it dips below 8:1 for more than a frame on readable text, fix by tweening translate/scale instead.

## Reference exemplar

**[`examples/fui-scaffold.html`](../examples/fui-scaffold.html)** — a single-file scaffold demonstrating the four load-bearing primitives:

1. **Data ticker** — `rAF`-driven counter with leading zeros, mission clock, packet hex, all tabular-nums.
2. **Radial compass** — SVG thin-stroke rings, 36 tick marks (every 9th longer for cardinals), rotating needle bound to time.
3. **Canvas waveform** — scrolling signal trace with RMS/peak readouts; shows how Canvas2D and SVG coexist inside the same HUD block.
4. **Staggered reveal** — CSS animation using muriel's `--mg-duration-reveal` and `--mg-ease-emphasis` tokens with `--mg-stagger: 120ms` between blocks.

Also demonstrates: corner brackets via `::before`/`::after`, scan-line overlay via `repeating-linear-gradient`, `prefers-reduced-motion` fallback, 8:1 contrast on every text element, brand-token CSS custom properties (overridable from a `StyleGuide.to_css_vars()` drop-in).

Open it directly in a browser: `open examples/fui-scaffold.html` (macOS) or the equivalent.

## Reference archives

- [fuidesign.com](https://fuidesign.com/) — Ash Thorp's curated showcase.
- [hudsandguis.com](https://www.hudsandguis.com/) — dormant but canonical Tumblr archive; still the best single-site reference.
- [perception.nyc](https://perception.nyc/) / [territorystudio.com](https://territorystudio.com/) — studio portfolios.
- CodePen search for `#fui`, `#hud`, `#sci-fi-ui` — community implementations worth forking.
- Film stills from the lineage above — particularly Blade Runner 2049 (analytical spread), The Martian (orbital mechanics), Ghost in the Shell 2017 (full-screen data overlays).

## Integration with other muriel channels

- **[`channels/interactive.md`](../channels/interactive.md)** — the scaffold lives here as a runnable pattern; CodePen Prefill it to hand readers a live fork.
- **[`channels/video.md`](../channels/video.md)** — capture the running scaffold with Playwright or `desktop-control`, then burn captions with ffmpeg.
- **[`channels/raster.md`](../channels/raster.md)** — screenshot a frozen frame for hero images or paper figures.
- **[`channels/style-guides.md`](../channels/style-guides.md)** — swap the four CSS custom properties at the top of the scaffold for a brand's palette; the composition inherits.
- **[`vocabularies/kinetic-typography.md`](kinetic-typography.md)** — the overlap surface: sci-fi title cards are kinetic typography in the FUI idiom. The SDF alpha rule belongs to both vocabularies.

## Rules that always apply

Muriel's universal rules don't relax because the interface is fictional:

- **8:1 contrast minimum** on every text element, including mid-animation states.
- **Decorative strokes ≥55/255** on a dark background.
- **Measure before drawing.** Canvas at `devicePixelRatio` for crisp strokes on hidpi; SVG `viewBox` for scale independence.
- **Label every number.** `Bearing 042°` not `042`; `T-00:14:22` not `14:22`.
- **No false profundity.** If a tick mark moves and you can't state the reason in one sentence, it shouldn't move.
