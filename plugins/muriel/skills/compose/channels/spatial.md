---
channel: spatial
status: partial-mvp
requires:
  brand: optional
  audience: optional
  reads:
    - muriel.layout
output:
  kinds: [svg, html, css, js]
  registers: [paper, blog, presentation, interactive]
peer_channels:
  - svg
  - web
  - interactive
  - infographics
---

# Spatial — depth scaffolding for layered typography

A small library for putting type into *felt* space — perspective grids that turn the page from a stack of layers into a single volumetric scene, plus a set of Three.js + CSS3DRenderer exemplars that consume the same coordinate system at runtime. Reach for this channel when you need to argue *"these things live in a relationship," not just "these things appear in a list."*

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission and universal rules. Sister channels: [`svg.md`](svg.md) for the static surface this writes onto; [`web.md`](web.md) and [`interactive.md`](interactive.md) for the runtime surfaces the JS exemplars target.

## Why this channel exists

Floating text in 3D space without a perspective scaffold reads as **stacked planes** — there is no felt depth, just layers. The visual system needs three or four well-placed cues — vanishing-point convergence, a horizon anchor, foreshortened transversals — to lock a scene into one continuous space. Once it does, the same screen real estate carries far more information without overcrowding.

This is not a styling trick. Spatial-typography is an explicit lineage in design history — Alberti's *De pictura* (1435) and the *costruzione legittima*; Dürer's perspective machine (1525); architect's blueprint axonometrics; **Muriel Cooper's MIT Visible Language Workshop** (receding planes of type as an information environment); the **Robertson / Mackinlay / Card *Information Visualizer*** cone trees and the **Dumais / Cockburn / Robertson *Data Mountain*** at MSR (spatial memory as an indexing primitive); and the Tron / synthwave horizon-to-VP grid that re-popularised one-point perspective in the 1980s. Every one of those traditions earned its geometry — the depth carried meaning, not decoration.

Pre-flight question for any spatial composition: *if I flattened the scene to a list, would the reader lose information?* If no, ship the list.

## What ships today

| # | Surface | Module / file | What it does |
|---|---|---|---|
| 1 | Static SVG perspective grids | `muriel.spatial` | `grid("1pt"|"2pt"|"3pt"|"iso", BBox)` → `PerspectiveGrid` with `.svg()`. Tron-style cyan-on-near-black defaults; horizon anchor, fade-to-horizon depth weighting, VP annotation toggle. |
| 2 | Shared 3D runtime helpers | `render_assets/_lib/spatial.{css,js}` | `createScene`, `Mountain`, `addFloorGrid`, `addHorizon`, `makePlane` (CSS3D), `FocusController`, `startRenderLoop`. WebGL + CSS3DRenderer stacked so DOM text gets composited in 3D without losing selectability or accessibility. |
| 3 | Layered DOM × perspective grid | `render_assets/spatial-typography/` | Cooper VLW homage — receding planes of DOM type, navigable, on a horizon-anchored grid. Base exemplar for the lib. |
| 4 | Data Mountain (MSR) | `render_assets/mindbendingpixels-mountain/` + `render_assets/sciprogfi-agentchan-mountain/` | Dumais et al. (2001) spatial-memory index — tilted plane group with click-to-focus zones; cards arranged on the slope so spatial position carries identity. Two brand skins (psychodeli + sciprogfi/agentchan). |
| 5 | Perspective Wall | `render_assets/perspective-wall/` + `render_assets/sciprogfi-lux-mesh-wall/` | Mackinlay / Robertson / Card (1991) focus + context — central card readable, peripheral cards foreshortened against the receding wall. Two brand skins (psychodeli + sciprogfi/OHC mesh). |
| 6 | Demo gallery | `render_assets/index.html` | Single page indexing every exemplar with kicker / tag / lineage / source link. |

**Queued.** `muriel.spatial.typeset_scene()` — Python emitter that consumes a `PerspectiveGrid` and a list of DOM blocks and writes a `.html` artifact ready to drop into `render_assets/<name>/index.html`. Closes the design.md → brand.toml → CSS-3D-typography loop so the static SVG grid and the interactive scene share their coordinate system by construction, not by hand-port.

## The static path — `muriel.spatial`

Pure Python, zero deps, SVG-first. Match the muriel ethos: deterministic output, no runtime, exportable to print.

```python
from muriel.spatial import grid
from muriel.layout import BBox

g = grid("1pt", canvas=BBox(0, 0, 1200, 700))
open("grid.svg", "w").write(g.svg(stroke="#7fdfff", bg="#0a0a14"))

g2 = grid("2pt", canvas=BBox(0, 0, 1200, 700), vp_offsets=(-1.5, 1.5))
for vp in g2.vanishing_points:
    print(vp.name, vp.x, vp.y)
```

Four modes, each carrying a different argument shape:

- **`"1pt"` (one-point)** — single VP on the horizon. Corridor / Tron horizon / cinematic into-the-distance. Use when the argument is *"this leads toward a single point."*
- **`"2pt"` (two-point)** — two VPs on the horizon, verticals stay vertical. Architectural cube corner. Use when the argument is *"this object has volume; you're looking at it from a definite vantage."*
- **`"3pt"` (three-point)** — two horizon VPs + one vertical VP (high or low). Looking up at a tower / down into a pit. Use when the argument is *"you are below / above the subject."*
- **`"iso"` (isometric)** — three axes at 30° / 150° / 90°, no convergence. Use when the argument is *"every position is measurable; depth is not a story."*

```bash
python -m muriel.spatial --demo                # 2×2 panel of all four modes
python -m muriel.spatial --demo --mode 1pt     # one mode, full canvas
python -m muriel.spatial --selftest            # assertion suite
```

The result objects (`PerspectiveGrid`, `VanishingPoint`, `GridLine`) are frozen dataclasses you can inspect before emit — the `lines` tuple carries every clipped segment with its `role` (`horizon`, `orthogonal-floor`, `transversal-ceiling`, `from-vp-z`, …) and `weight` (depth-driven opacity). That makes the grid composable into a larger SVG composition rather than only viewable as a standalone document.

## The interactive path — `render_assets/_lib/spatial.{css,js}`

Each exemplar in `render_assets/<name>/index.html` is self-contained: an importmap points `three` at a CDN, the page imports `../_lib/spatial.js`, declares its scene, and starts the render loop. No build step.

```html
<link rel="stylesheet" href="../_lib/spatial.css">

<script type="importmap">
{"imports": {
  "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
}}</script>

<script type="module">
  import { createScene, Mountain, makePlane, FocusController,
           startRenderLoop } from '../_lib/spatial.js';

  const { scene, camera, webglRenderer, cssRenderer } =
    createScene({ cameraPos: [0, 170, 780], lookAt: [0, 130, -300] });

  const mountain = new Mountain(scene, { tiltDeg: 22, depth: 1400 });
  for (const card of cards) {
    const plane = makePlane(card.html, { width: 360, height: 220 });
    const { position, rotation } = mountain.planeToWorld(card.row, card.col);
    plane.position.copy(position); plane.rotation.copy(rotation);
    scene.add(plane);
  }

  startRenderLoop({ scene, camera, webglRenderer, cssRenderer });
</script>
```

The two-renderer stack (`#webgl` underneath, `#css3d` on top) is intentional: WebGL handles the grid / horizon / atmospheric layer at GPU speed; CSS3DRenderer carries the DOM cards so text stays selectable, copyable, and screen-reader-addressable. `pointer-events` is gated on the HUD so floating-corner brand chrome doesn't absorb clicks meant for cards that overlap it in screen space.

### Palette tokens

`_lib/spatial.css` exposes the demo base palette as CSS custom properties at `:root` — every exemplar overrides `--bg` and adds its own card classes, but pulls font stacks and accent colours from this floor:

| Token | Default | Use |
|---|---|---|
| `--bg` | `#07070d` | Page background — demos override per scene mood |
| `--ink` | `#e6e4d2` | Primary text. **15.42:1 contrast on default `--bg`** — passes muriel's 8:1 floor |
| `--ink-dim` | `rgba(230,228,210,0.62)` | Secondary text |
| `--cyan` | `#7fdfff` | Grid lines, hint chips, citation links |
| `--magenta` | `#ff5fa2` | Horizon, hover states, focal accent |
| `--gold` | `#d2b06a` | Editorial highlight (italicised brand chrome) |
| `--mono` | system mono stack | HUD meta, citations, kbd chips |
| `--sans` | system sans stack | Brand chrome, headings |
| `--serif` | system serif stack | Editorial body within DOM cards |

The defaults are deliberately Tron / Cooper-VLW palette-coded so the exemplars all feel like one family. A brand can override by reassigning the tokens at `:root` inside its own demo override block (see `sciprogfi-agentchan-mountain/index.html` for the agent-green override).

## Lineage — where to read more

Each piece of geometry in this channel has prior art that earned it. Cite when you ship something built on the channel; the citation does work, not decoration.

| Period | Source | Geometry it earned |
|---|---|---|
| 1435 | Alberti, *De pictura* | Linear perspective; the *costruzione legittima* construction |
| 1525 | Dürer, *Underweysung der Messung* | Perspective machine; mechanical projection |
| 1980s | Cooper, MIT Visible Language Workshop | Receding planes of type as an information environment |
| 1991 | Mackinlay, Robertson, Card (Xerox PARC) — *The Perspective Wall: Detail and Context Smoothly Integrated* (CHI '91) | Focus + context; central detail readable, peripheral context foreshortened |
| 1993 | Robertson, Mackinlay, Card — *Information Visualizer* | Cone trees; perspective as navigation primitive |
| 1998 | Tron / synthwave / vaporwave | One-point perspective as cultural shorthand for "computer space" |
| 2001 | Dumais, Cuthbertson, Czerwinski, Robertson, van Dantzich (MSR) — *Data Mountain* | Spatial memory as an indexing primitive; cards arranged by location on a tilted plane |

## Anti-prescription — when not to reach for this channel

- **Quantitative comparison.** Perspective foreshortens. If the reader needs to compare values, the foreshortened series will systematically under-weight the back. Use [`science.md`](science.md) or [`infographics.md`](infographics.md).
- **Forms / data entry / chrome.** Tilted text impairs reading speed. Don't tilt anything the user needs to fill in.
- **Tiny screens.** Under ~720px wide, perspective scenes lose their cues and read as visual noise. Fall back to a flat composition.
- **Accessibility-critical surfaces.** CSS3DRenderer preserves DOM text, but screen-reader navigation through a 3D scene is non-trivial; pair every demo with a flat fallback at `prefers-reduced-motion: reduce` and (where the artifact is reference, not exploration) a linked flat-HTML companion.
- **Generic 'add depth' decoration.** If you can't name which lineage (Cooper / Perspective Wall / Data Mountain / Tron) the composition belongs to, you're decorating, not arguing.

## Files this channel owns

```
muriel/spatial.py                                  # static SVG perspective grids
render_assets/_lib/spatial.css                     # shared base palette + HUD
render_assets/_lib/spatial.js                      # createScene / Mountain / FocusController / planeToWorld
render_assets/index.html                           # gallery
render_assets/spatial-typography/index.html        # Cooper VLW exemplar
render_assets/mindbendingpixels-mountain/          # Data Mountain (psychodeli skin)
render_assets/sciprogfi-agentchan-mountain/        # Data Mountain (sciprogfi/agentchan skin)
render_assets/perspective-wall/                    # Mackinlay-Robertson-Card (psychodeli skin)
render_assets/sciprogfi-lux-mesh-wall/             # Perspective Wall (sciprogfi/OHC skin)
```

## Queued

- **`muriel.spatial.typeset_scene()`** — Python emitter that takes a `PerspectiveGrid` + a list of DOM blocks (HTML strings + `("vp", "left", 3)` / `("grid", row, col, depth)` anchor names) and writes a runnable `<scene>/index.html` that wires the same coordinates into the JS lib. Closes the static-↔-interactive loop so a paper figure and a fly-through share their geometry by construction.
- **Reduced-motion fallback emitter.** When a demo loads under `prefers-reduced-motion: reduce`, the lib should swap to a flat composition (the static SVG grid plus the cards laid out by row/col in the document order). One opt-in flag on `startRenderLoop`.
- **`muriel.spatial.cone_tree()`** — Robertson-Mackinlay-Card (1993) hierarchical cone-tree primitive, both as static SVG and as a JS scene. Pairs with the [`diagrams.md`](diagrams.md) dendrogram / pyramid entries when the hierarchy is large enough that a flat tree falls off the page.

See [`TODO.md`](../TODO.md) for cross-channel queue context.
