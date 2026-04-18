# FUI — Fantasy / Fictional User Interface

The industry term for sci-fi UI: the HUDs, consoles, and data overlays you see in Iron Man, Blade Runner 2049, The Martian, Westworld, The Expanse. Not "cyberpunk" (too broad, that's the umbrella aesthetic). Not "HUD" (that's a UI mode, heads-up). **FUI** is the keyword that unlocks the right references.

Part of the [muriel](../muriel.md) skill, under Aesthetic Vocabularies. See the top-level index for mission and universal rules that apply across every vocabulary.

## Canonical lineage — where to look for inspiration

| Studio / Designer | Work | Notable for |
|---|---|---|
| **Perception NYC** (John LePore) | Iron Man's Stark HUDs, Black Panther's Shuri lab, Avengers | Radial geometry, translucent data layers |
| **Territory Studio** | Blade Runner 2049, The Martian, Ex Machina, Ghost in the Shell (2017) | Analytical overlays, thin-stroke grids, restraint |
| **Ash Thorp** | Prometheus, Ender's Game, Call of Duty Ghosts | Motion-forward reveals, procedural data |
| **GMUNK** (Bradley G. Munkowitz) | TRON: Legacy, Oblivion, Prometheus | Radial/polar compositions, shader-driven textures |
| **Jayse Hansen** | Iron Man 3, Big Hero 6, Star Trek Beyond | Typographic/numeric precision in flight HUDs |

## Visual grammar — the recognizable elements

- **Thin strokes** (0.5–1px) arranged in grids, polar coordinates, concentric rings, or parallel rules
- **Monospace numerics with leading zeros** — `00042`, `0.0384`, `N 40°42'46"`, `T-00:14:22`
- **Radial / polar elements** — dials, compass overlays, scan arcs, rose diagrams. Psychodeli's 10-ring wordmark border is a well-tempered instance of this grammar.
- **Grid overlays** — faint CSS Grid lines in accent color, sometimes animated or parallax-scrolling
- **Leader lines** — thin diagonal strokes from a data point to a typographic callout, like an engineering drawing
- **Scan lines** — subtle horizontal-line texture across the frame (~3% opacity, 2px period). Optional chromatic aberration for CRT nostalgia.
- **Data tickers** — live-updating numbers, `requestAnimationFrame`-driven counters that roll or flicker between values
- **Animated reveals** — elements fade / translate / scale in with staggered 80–200ms delays, not instantly. `cubic-bezier(0.4, 0, 0.2, 1)` for the "precise machinery" feel.
- **Restrained palette** — one dominant accent hue (cyan, amber, red) on near-black. Matches the universal OLED rule.
- **Glitch / noise accents** — used as *punctuation*, never as ambient texture

## Technical substrates — what to build it with

- **SVG** for thin-stroke geometry (rings, grids, crosshairs, rose diagrams). Animate via `requestAnimationFrame`, `<animate>` elements, or CSS transitions on stroke properties.
- **CSS Grid** for the underlying layout. HUD blocks are rectangular arrays; let the cascade do the arithmetic.
- **Canvas2D** for tickers and anything where SVG reflow would be expensive. 60fps number counters, rolling waveforms, heatmap scrubs.
- **WebGL shaders** for fullscreen post-process — scan lines, chromatic aberration, noise. One fragment shader layered on top of everything else.
- **Monospace display fonts:**
  - *Working mono:* IBM Plex Mono, JetBrains Mono, Berkeley Mono (paid, exquisite), Space Mono, Fira Code
  - *Display FUI mono:* Orbitron, Rajdhani, Exo, Share Tech Mono, Audiowide — drawn specifically for sci-fi interfaces
- **Animation timing:** 80–200ms stagger between elements on reveal; `ease-out` for entrance, `ease-in` for exit. Use the Web Animations API (`element.animate(...)`) for programmatic sequencing.

## Restraint rules — FUI is shockingly easy to do badly

- **One loud element per screen.** Everything else is quiet. A single radial scanner, a single rolling data block, a single reveal animation — surrounded by calm typography.
- **Information actually present.** Fake data (`Lorem 0923.88.Ipsum`) reads as fake. Either show real data or stylize the placeholder so clearly nobody mistakes it for real (block rectangles, `████`, `XX.XX`).
- **Motion earns attention.** Don't animate everything simultaneously. Stagger reveals. Let the eye land and re-land.
- **Accessibility still applies.** 8:1 contrast works here too — thin strokes at low opacity fail the rule. Key information must meet WCAG even in the darkest HUD.
- **Type is load-bearing.** Most amateur FUI dies from mushy typography. Pick one monospace face, commit to it, track it tight, and let the numbers do the work.

## Reference archives — where to browse when stuck

- [fuidesign.com](https://fuidesign.com/) — Ash Thorp's curated showcase
- [hudsandguis.com](https://www.hudsandguis.com/) — dormant but canonical Tumblr archive; still the best single-site reference
- [perception.nyc](https://perception.nyc/) / [territorystudio.com](https://territorystudio.com/) — studio portfolios
- CodePen search for `#fui`, `#hud`, `#sci-fi-ui` — community implementations worth forking
- Film stills from the lineage above — particularly Blade Runner 2049 (analytical spread), The Martian (orbital mechanics), Ghost in the Shell 2017 (full-screen data overlays)

## Where FUI fits the current project set

- **Scrutinizer** — the vision-science overlays (eccentricity rings, PPD calibration, sector explorers) are already proto-FUI. Codifying the vocabulary sharpens future work.
- **Cartographer Explorer v2** — session timelines, faceted overviews, approach-retreat dashboards are natural HUD territory.
- **Paper figures** (AdSERP, RecGaze, OSEC) — static gaze-path visualizations can borrow FUI grammar without gimmickry: leader lines, mono numerics, faint grids behind the gaze ribbon.
- **No Kings / iBlipper** — kinetic typography intersects FUI through Territory Studio's work on motion-forward interfaces.
- **OSEC phase explorer** — semantic zoom + FUI grammar is the right pairing.
