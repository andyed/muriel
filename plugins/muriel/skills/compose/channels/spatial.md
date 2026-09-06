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
| 2 | Ridgemap (stacked 1D slices) | `muriel.spatial.ridgemap` | `ridgemap(field, BBox)` → `RidgeMap` with `.svg()`. Joy Division *Unknown Pleasures* / Harold Craft 1970 pulsar plot — each row of a 2D scalar field becomes a polyline, rows stacked top-to-bottom, front ridges occlude back ridges via a baseline-closed polygon fill. Sibling primitive to `grid()`: where the perspective grid is a scaffold for *space*, the ridgemap is a scaffold for *scalar fields*. Zero-dep (duck-types numpy ndarray). |
| 3 | Shared 3D runtime helpers | `render_assets/_lib/spatial.{css,js}` | `createScene`, `Mountain`, `addFloorGrid`, `addHorizon`, `makePlane` (CSS3D), `FocusController`, `startRenderLoop`. WebGL + CSS3DRenderer stacked so DOM text gets composited in 3D without losing selectability or accessibility. |
| 4 | Layered DOM × perspective grid | `render_assets/spatial-typography/` | Cooper VLW homage — receding planes of DOM type, navigable, on a horizon-anchored grid. Base exemplar for the lib. |
| 5 | Data Mountain (MSR) | `render_assets/mindbendingpixels-mountain/` + `render_assets/sciprogfi-agentchan-mountain/` | Dumais et al. (2001) spatial-memory index — tilted plane group with click-to-focus zones; cards arranged on the slope so spatial position carries identity. Two brand skins (psychodeli + sciprogfi/agentchan). |
| 6 | Perspective Wall | `render_assets/perspective-wall/` + `render_assets/sciprogfi-lux-mesh-wall/` | Mackinlay / Robertson / Card (1991) focus + context — central card readable, peripheral cards foreshortened against the receding wall. Two brand skins (psychodeli + sciprogfi/OHC mesh). |
| 7 | Orbital Sunburst | `render_assets/orbital-sunburst/` | One partition layout projected two ways: conventional top-view sunburst and an exploded 3D hierarchy stack with pointer, keyboard, orbit, and phone-safe linear controls. |
| 8 | Demo gallery | `render_assets/index.html` | Single page indexing every exemplar with kicker / tag / lineage / source link. |
| 9 | High-count tile field | `render_assets/_lib/atlas.js` + `instanced.js` | The whole corpus as ONE instanced draw call over a two-tier texture atlas (`far`: every item at 64px; `near`: an LRU pool of 256px slots). VRAM is bounded by the tier sizes, not the item count. |
| 10 | Pixel/DOM hybrid | `render_assets/_lib/hybrid.js` | A fixed pool of real DOM elements lent to whatever is close enough to read, swapped against their quads. Keeps selectable text, links, and keyboard focus at a DOM budget that does not grow with the corpus. |
| 11 | Piles | `render_assets/_lib/piles.js` | Mander / Salomon / Wong (CHI 1992) casual organization. Groups become stacks placed on the surface; click spreads a pile in place and collapses it back. Membership is supplied as index lists, so a facet-derived grouping and a hand-made pile are the same object, and an item may sit in several piles — which a folder tree cannot represent. |
| 12 | Keyboard navigation | `render_assets/_lib/navigate.js` | Roving-selection listbox over the field: one tab stop, arrows move in SCREEN space, Home/End/PageUp/PageDown, Tab between piles, type-ahead by pile label, `aria-activedescendant` + a live region. The selection is always promoted to DOM, so focus lands on a real element. |
| 13 | Data Mountain at field scale | `render_assets/data-mountain-field/` | 2,500 tiles on the slope: 4 draw calls, 12 DOM elements, 103 MB of atlas. Ships `check.mjs`, which asserts the budget is bounded and fails if it is not. |

## Scale — when one element per item stops working

The first four runtime exemplars give every item its own `CSS3DObject`. That is
the right shape for a dozen cards and the wrong shape by two orders of magnitude
past it: every card is a DOM element carrying its own `matrix3d`, individually
composited, and `startRenderLoop`'s depth-sort pass walked the scene writing a
`zIndex` for each one on every frame.

The fix is not a faster DOM. It is noticing that **focus+context layouts only
ever demand legibility from a few items at a time** — which is the observation
the Perspective Wall and the Data Mountain were built on in the first place. So
the field splits into three tiers:

| tier | population | backing | carries |
|---|---|---|---|
| far | the whole corpus | one atlas, 64px per tile | colour and shape |
| near | a fixed LRU pool (~256) | 256px atlas slots | a recognizable image |
| DOM | a fixed pool (~12) | real elements | selectable text, links, keyboard focus |

Only the far atlas grows with the corpus, at 16 KB per item. The near and DOM
budgets are constants. Measured on `data-mountain-field/` at 2,500 items: **4
draw calls, 12 DOM elements, 103 MB of atlas** — and the same numbers at 25,000
items apart from the far atlas.

`spatial.js` gained three scale affordances, all backward compatible:

- `startRenderLoop({ sortDom })` — replaces the default `scene.traverse()`
  depth-sort, which is correct and cheap for the dozen-card demos and quadratic
  past a few hundred. `HybridField.sort` is bounded by the DOM pool.
- `makePlane(nodeOrString, …)` — a Node (or array of them) skips the innerHTML
  path entirely, so a consumer rendering scraped third-party titles can stay on
  `textContent`.
- `createScene({ container })` — sizes to an element rather than the window,
  with a `ResizeObserver`, for scenes embedded in an app pane.

And `Mountain.arrange(count, aspectOf, …)` lays a whole corpus on the slope in
justified rows whose target height falls toward the back — the same rule a flat
justified wall uses, except that far rows shrink *and* foreshorten, so a back
row costs almost no screen area while staying present as context. That double
falloff is the reason to put a wall on a slope rather than leave it flat.

### Piles

Piling is the other half of the scale answer. A slope shows you 2,500 things;
it does not tell you which ones belong together. `piles.js` groups them into
stacks, and because a pile, a spread pile, and a re-sorted field are all just
"some instances move to new matrices", the whole vocabulary costs one animated
subset rather than any scene-graph work — `TileField.tick()` writes only
instances actually in flight, so a settled field costs nothing.

Two things the implementation insists on, both load-bearing rather than
decorative:

- **Jitter is deterministic, never random.** A pile that reshuffles its own
  cards each time it collapses destroys the spatial memory the metaphor runs
  on — you found that item last time by remembering it stuck out on the left.
- **Piles carry labels.** Mander et al. leaned on the top item as a visual
  proxy, which works for a desk of documents you wrote yourself and not at all
  for a facet value like `firmware`. Without a label, one heap of coloured
  rectangles is indistinguishable from another.

Pile *count* should stay in the dozens — there is one label element per pile. A
facet with 200 values wants a different treatment than piling.

### Keyboard, and why the hybrid earns its keep

"A GPU quad cannot be focused" is the standing objection to drawing an interface
as pixels, and the DOM tier is the answer: `navigate.js` keeps the *selection*
promoted, so the thing the keyboard points at is a real element with a real
focus ring that a screen reader can read. Navigation drives promotion, not the
reverse.

The model is a listbox with a roving active descendant — one tab stop, not
2,500. Elements are transient (a pool entry is a different item a moment later),
so focus lives on the container and `aria-activedescendant` names the current
card. This is the same contract a virtualized list uses, for the same reason.

Movement is computed in **screen space**, never in the layout's coordinates. The
same corpus is a slope in one layout and a grid of piles in another; "right"
means something different on each, and different again after an orbit.
Projecting to the camera gets all of that for free and requires no layout to
describe its own topology. Two things that bite:

- **The direction cone multiplies, it does not divide.** `perp <= along * CONE`.
  Dividing widens ~29° to ~61°, which on a receding slope is enough for "right"
  to reach two rows nearer the camera — so a Home/End sweep curves off its row.
- **Freeze the camera during a sweep.** Home/End are repeated steps; moving the
  camera between them redefines "right" partway through, and the sweep bends.
  `onSelect` fires once, at the end.

A live region is mandatory, not polish: the visual feedback for "the selection
moved" is a camera move, which conveys precisely nothing to a screen reader.

**Anti-pattern.** Do not raise `poolSize` to "just fit everything." The pool
being small is the design, not a limitation of it; a pool the size of the corpus
is one element per item again, wearing a hybrid's clothes.

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
python -m muriel.spatial --ridgemap            # pulsar-style ridgemap demo
python -m muriel.spatial --selftest            # assertion suite
```

The result objects (`PerspectiveGrid`, `VanishingPoint`, `GridLine`) are frozen dataclasses you can inspect before emit — the `lines` tuple carries every clipped segment with its `role` (`horizon`, `orthogonal-floor`, `transversal-ceiling`, `from-vp-z`, …) and `weight` (depth-driven opacity). That makes the grid composable into a larger SVG composition rather than only viewable as a standalone document.

## The ridgemap path — `muriel.spatial.ridgemap`

Sibling primitive to `grid()`. Where the perspective grid scaffolds *space*, the ridgemap scaffolds *scalar fields*: any source that yields one value per (x, y) — terrain DEM, gaze density, image luminance, attention map, audio spectrogram, weather front — feeds the same emitter, and the rendering is just *which projection of the field you draw*. First shipped projection is the stacked 1D-slice form (Harold Craft's 1970 PSR B1919+21 successive-period chart, popularised by Peter Saville's 1979 Joy Division *Unknown Pleasures* sleeve, ported to statistical density plots by Wilke's *ggridges* in 2016). Filled-isoline, wireframe-protrusion, and hachured-relief projections are queued under the same module.

```python
from muriel.spatial import ridgemap
from muriel.layout import BBox

# field is any 2D iterable — list-of-lists, tuple-of-tuples,
# numpy.ndarray. Each row becomes one ridge polyline.
field = [[...], [...], ...]                        # shape (rows, cols)
rm = ridgemap(field, canvas=BBox(0, 0, 800, 600))
open("ridges.svg", "w").write(rm.svg())             # cream-on-near-black default
open("ridges-lineart.svg", "w").write(rm.svg(fill=None))  # no occlusion, every ridge visible
```

The default `.svg()` paints each ridge with a `fill` that matches the background colour, closed down to the row's baseline — that is the occlusion that makes the stack read as layered rather than transparent. Set `fill=None` to drop the occlusion and let every ridge show through, useful when the back-to-front semantics are not what you're arguing.

Key knobs on `ridgemap(...)`:

- **`amplitude`** — peak excursion (canvas units) for a sample at `vmax`. Default `1.6 × row_spacing`, which makes the tallest peaks rise past the next row's baseline (the overlap that creates the iconic stacked look).
- **`row_spacing`** — vertical distance between baselines. Default fills the canvas: `(canvas.height - 2×pad) / (n_rows - 1)`.
- **`vmin` / `vmax`** — clamp the normalisation range. Default: data min / max.
- **`margin`** — fraction of canvas reserved as padding on every side (default 0.06).

The result object (`RidgeMap`, frozen, with a `ridges` tuple of `Ridge` frozen dataclasses) is composable: read each ridge's `points` and `baseline_y` to drop the geometry into a larger SVG — annotate the strongest peak, overlay a vertical reference axis, etc.

When to reach for ridgemap vs the existing channels:

- **Reach for ridgemap** when the row ordering and stacking direction carry meaning (time-series of successive periods, depth profiles down a core, frequency-over-time spectrogram). The eye reads the stack as *evolution* — that semantics is the whole argument.
- **Reach for [`heatmaps.md`](heatmaps.md) (`render_heatmap`)** when row order doesn't matter and you want value→colour with no occlusion. Better for quantitative comparison across the whole field.
- **Reach for [`science.md`](science.md) (matplotlib `pcolormesh` / `contourf`)** when you need axis labels, value scale legend, and a peer-reviewable figure.

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

## The orbital-sunburst path — hierarchy becomes depth

`render_assets/orbital-sunburst/index.html` is the interactive bridge between a
sunburst chart and a stacked circular interface. It deliberately avoids a
second data model: one recursive partition assigns immutable angles and annular
sector paths, then CSS perspective either collapses every hierarchy level into
a normal top view or separates those same SVG planes along Z.

The separated planes are annuli, not translucent full discs. Every higher
level cuts out its centre so the lower hierarchy remains physically visible
through the stack. A projected label is then constrained to the screen-space
inner edge of the next, nearer annulus: upright type may counter the camera,
but it cannot paint in front of a hierarchy shelf it does not own. Outer
callouts are the explicit exception because leaving the ring is their contract.

Use this pattern when all four claims are true:

- containment is recursive and useful to inspect;
- sibling weight is meaningful enough to earn arc length;
- separating levels reduces occlusion or improves depth navigation; and
- a selected lineage can remain explicit in an upright inspector or breadcrumb.

The interaction grammar is select, rotate into the working position, move among
siblings, and move up or down hierarchy depth. Left/Right step siblings;
Up moves outward to the first authored child and Down returns inward to the
owning parent; Enter commits; Escape returns to root. Pointer hover may
preview but never changes the sector path. Drag orbits the projection, not the
data. On a phone or under reduced motion, collapse to the top view and provide
44 px linear controls for the same canonical nodes.

Psychodeli's consumer pie supplies the state and flyout precedent. Keep hover as
a reversible preview, keyboard focus as an active navigation target, and
selected/live as persistent canonical state; never let a stationary cursor turn
a neighbor selected after the ring rotates. Prefer authored parent/child
ownership over nearest-angle geometry for Up/Down. Treat flyout shapes as
different interaction contracts: an upright inspector explains the current
lineage, a static accessory petal is a quick action owned by one spoke, a flown
DOM chip may cross the SVG boundary, and a replacement sub-pie transfers focus
and gives the hub Back semantics. Do not infer ownership from visual proximity.

The demo vendors Pretext 0.0.5 as a layout layer over the stable sectors. Its
text carrier is selectable rather than implicit: adaptive, screen-upright,
shallow bow, circular rail, radial spoke, and outer callout. Adaptive chooses
whole-run upright text in the foreshortened 3D stack and recovers a shallow bow
when the hierarchy is flat. After the SVG anchors receive CSS perspective, a
screen-space pass restores a physical icon-to-label gap; target paths remain
untouched. This avoids the common error of proving clearance in world space
while glyphs collide in the rendered camera.

Type can be shared per peer ring or locally maximized, with a hard 16 px
physical floor. Natural, balanced, and space-filling tracking are separate
choices. Direction (automatic upright, clockwise, counter-clockwise),
line-to-arc curvature, and restrained letter turn remain independent controls.
Complex scripts are never decomposed into individually positioned characters:
Arabic/RTL and CJK shaping canaries stay whole screen-upright runs. Latin arc
carriers use cumulative-prefix kerning and grapheme segmentation, so combining
marks and emoji remain atomic. The complete text stays in the semantic tree and
inspector; projected decoration is `aria-hidden`.

The production stress fixture projects labels from Psychodeli's `WEDGES`,
`MORE_WEDGES`, `REACT_WEDGES`, and `VIBE_WEDGES` sets onto the immutable demo
partition. Its two-tone command marks use the same deterministic 24-grid SVG
grammar as the pie; emoji appears only in the explicit script canary, never as
the command-icon system. The fixture copies labels and glyph paths for layout
proof, not Psychodeli's canonical menu state or flyout behavior. Typography may
move; target geometry and product state may not.

Keep sunburst and radial-menu semantics separate. A sunburst encodes recursive
containment and proportional weight; a radial menu encodes directional command
selection. A circular silhouette does not make them interchangeable. Do not
explode a sunburst into depth when Z would be decorative, when foreshortening
would conceal a quantitative comparison, or when upright labels and a flat
fallback cannot carry the full choice.

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
| 1970 | Harold Craft, Cornell PhD — successive-period plot of pulsar PSR B1919+21 | Stacked 1D slices of a 2D scalar field; row order = time, x = phase, height = amplitude |
| 1979 | Peter Saville for Joy Division, *Unknown Pleasures* | Same plot, restyled into the most reproduced ridge-plot in graphic design; established back-to-front occlusion as the readable form |
| 1998 | Tron / synthwave / vaporwave | One-point perspective as cultural shorthand for "computer space" |
| 1998 | Robertson, Czerwinski, Larson, Robbins, Thiel, van Dantzich (MSR) — *Data Mountain* (UIST '98) — (Dumais et al. 2001 was the spatial-memory follow-up study) | Spatial memory as an indexing primitive; cards arranged by location on a tilted plane |
| 2016 | Claus O. Wilke — *ggridges* (R package) | Ridge plot ported to statistical density visualisation; established stack-as-distribution-comparison vocabulary |

## Anti-prescription — when not to reach for this channel

- **Quantitative comparison.** Perspective foreshortens. If the reader needs to compare values, the foreshortened series will systematically under-weight the back. Use [`science.md`](science.md) or [`infographics.md`](infographics.md).
- **Forms / data entry / chrome.** Tilted text impairs reading speed. Don't tilt anything the user needs to fill in.
- **Tiny screens.** Under ~720px wide, perspective scenes lose their cues and read as visual noise. Fall back to a flat composition.
- **Accessibility-critical surfaces.** CSS3DRenderer preserves DOM text, but screen-reader navigation through a 3D scene is non-trivial; pair every demo with a flat fallback at `prefers-reduced-motion: reduce` and (where the artifact is reference, not exploration) a linked flat-HTML companion.
- **Generic 'add depth' decoration.** If you can't name which lineage (Cooper / Perspective Wall / Data Mountain / Tron / Unknown Pleasures) the composition belongs to, you're decorating, not arguing.
- **Ridgemap when row order is arbitrary.** Stacking implies sequence (time / depth / index). If the rows could be shuffled without losing meaning, the visual is making an argument the data does not support — use a heatmap.
- **Ridgemap for precise peak comparison.** Front ridges occlude back ridges by construction. If the reader needs to compare row maxima quantitatively, switch to `fill=None` (line-art mode), a heatmap, or small multiples.

## Files this channel owns

```
muriel/spatial.py                                  # static SVG perspective grids + ridgemap
render_assets/_lib/spatial.css                     # shared base palette + HUD
render_assets/_lib/spatial.js                      # createScene / Mountain / FocusController / planeToWorld
render_assets/index.html                           # gallery
render_assets/orbital-sunburst/index.html          # shared 2D sunburst / 3D hierarchy-stack instrument
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
- **Further ridgemap projections.** The `ridgemap` MVP ships only the stacked-1D-slice form. The same `(field, canvas, …)` signature should grow siblings that render the same scalar field as: filled isoline bands (USGS / Imhof quadrangle), wireframe protrusion from a grid (BYTE-cover / Tinney 3D mesh), and hachured / halftone relief. One extractor stage, several emitters — the unifier is *scalar field → topology*. Documenting the taxonomy in a `channels/topography.md` companion before the next emitter lands.
- **Field ingestion from pixels.** Today `ridgemap` takes a 2D numeric array. A small `muriel.spatial.field_from_image(path, downsample=N, channel="luma")` helper would let raster sources (image luminance, video frame Δ, attention/saliency maps) feed the same primitive without callers needing to roll their own resampling. Crosses the channel's first input-is-pixels line — defer until a real artifact needs it.

See [`TODO.md`](../TODO.md) for cross-channel queue context.
