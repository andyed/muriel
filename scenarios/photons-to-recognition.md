# Scenario — Photons to Recognition

A multi-channel canonical demo binding several queued muriel channels into one coherent narrative artifact: how visual information flows from the retinal sensors, through the optic nerve and thalamus, into the cortical visual hierarchy, and converges on object recognition.

The arc exists for two reasons:

1. **As a Scrutinizer 2027 talk-deck-as-explainer** — sequential panels readable as standalone images on a stage screen, but composable as a single landscape infographic for blog / social distribution.
2. **As a forcing function for the channel work.** Each panel is a worked example that justifies a queued muriel channel's existence. Building the arc proves the channels carry the load.

## Audience

- Primary: vision-science / HCI / perception researchers who already know V1 / V4 / IT but haven't seen them assembled with cone density and cortical magnification in one frame.
- Secondary: technical product audiences (LinkedIn / X / blog posts) curious about why peripheral vision is so different from foveal — the question the existing 2D Scrutinizer foveation explainer (`build_foveation.py`) already answers at a smaller scale.

## Format outputs (all from one source pipeline)

| Output | Where it lands | Substrate |
|---|---|---|
| **Sequential talk slides** (one per panel + intermediate beats) | Conference deck, slide-by-slide reveal | Each panel exported as 1920×1080 PNG; deck is a wrapper |
| **Single-image infographic** | LinkedIn / X social card, blog hero | Composed via `muriel.tools.diagrams` layout grid; portrait 1080×1920 like the existing foveation explainer, or landscape 1920×1080 |
| **Interactive blog post** | scrutinizer-www article | niivue + Three.js + ECharts widgets inline in marginalia |
| **Static figure for paper** | Future Scrutinizer arxiv paper | Same panels, exported at 300dpi via the science channel |

The point: one source-of-truth pipeline produces every output. No per-format hand-rebuild.

## The five panels

### Panel 1 — Photons hit the retina

**Claim:** *The eye does not see uniformly. The fovea has ~150,000 cones/mm²; the periphery has ~5,000.*

**Visual:** 3D heatmap of cone density painted on the back inner wall of the eye. PyVista, deterministic camera, exported as a still. Falloff is on the curved surface — the geometry is part of the argument.

**Channel:** `channels/3d.md` (queued — PyVista exemplar)

**Pairs with:** the existing 2D side-view at `~/Documents/dev/scrutinizer-repo/scrutinizer-www/src/img/explainers/build_foveation.py`. That diagram answers "where is the fovea"; this one answers "what's actually on the retinal surface."

### Panel 2 — Retina maps to cortex unevenly

**Claim:** *V1 allocates roughly 50% of its surface to the central 5° of vision. The retinotopic map is logarithmically compressed.*

**Visual:** Side-by-side. Left: the retina as a flat disc, eccentricity rings. Right: the V1 cortical surface, same data points transformed through the log-polar mapping. Reference: Schwartz (1980) computational anatomy of the visual cortex; Blauch / Alvarez / Konkle (2026) FOVI for the modern framing.

**Channel:** `channels/brain.md` (queued — MNE `mne.viz.Brain` + custom log-polar transform)

**Connecting beat:** "the central 5° you just saw on the retina becomes half the visual cortex"

### Panel 3 — The visual hierarchy

**Claim:** *V1 → V2 → V4 → IT (ventral, "what") and V1 → MT → MST → parietal (dorsal, "where / how"). Information arrives in waves: retina ~30ms, V1 ~70ms, IT ~170ms.*

**Visual:** Brain mesh with the visual-pathway regions colored from the Glasser HCP-MMP1.0 atlas. Optionally animated propagation: each region lights up at its onset latency (Schmolesky 1998 / Bullier 2001 / Lamme & Roelfsema 2000 timings).

**Channel:** `channels/brain.md` (queued — `brain.visual_pathway()` headline helper)

**Connecting beat:** "the cortical real estate from panel 2 isn't a single processor — it's a hierarchy with two streams."

### Panel 4 — Information flow magnitudes

**Claim:** *Not every neuron projects to every next region. The flow has shape — some pathways carry the bulk, others are sparse.*

**Visual:** Sankey diagram. Nodes: retina, LGN, V1, V2, V3, V4, IT, MT, MST, parietal, prefrontal. Link widths: approximate fiber-tract weights from connectome data (HCP, or qualitative estimates from neuroanatomy — magnocellular vs parvocellular splits at LGN; ventral vs dorsal at V1 output).

**Channel:** `channels/diagrams.md` (queued — Sankey primitive)

**Anti-prescription discipline applies:** the magnitudes have to be real, or sourced from a published estimate. A "qualitatively-weighted" Sankey is worse than a DAG.

**Connecting beat:** "the hierarchy in panel 3 has *bandwidth*. Here's where it goes."

### Panel 5 — What converges

**Claim:** *IT cortex represents object categories. By 170ms post-stimulus, the brain has answered "is this a face / an animal / a tool / a place".*

**Visual:** Sunburst diagram. Center: "IT response at 170ms." Outer ring: top-level object categories (face / body / animal / tool / scene / object). Next ring: subcategories. Sized by approximate cortical population responding (face-selective FFA carries one of the largest categorical patches; tools carry less; etc.).

**Channel:** `channels/diagrams.md` (queued — sunburst, in the hierarchy-family entry)

**Closing beat:** "from photons hitting cones to a category label, in 170ms across five computational stages."

## Channel build order (forces the sequencing)

This scenario depends on three queued channels. To make the arc shippable end-to-end, the channels must land in roughly this order:

1. **`channels/3d.md` (with PyVista)** — Panel 1 + Panel 2 right side
2. **`channels/diagrams.md` Sankey + sunburst-and-family** — Panels 4 + 5 (these can ship before brain since they don't depend on it)
3. **`channels/brain.md` (with MNE-Python)** — Panels 2 left side + Panel 3, the largest lift, leave for last because it's the most novel

If one panel slips, the deck still makes sense with a placeholder slide. If two slip, the arc is broken.

## Reusability — each panel is also a standalone

Every panel is designed to ship independently:

- Panel 1 alone: a follow-on social card to the existing foveation explainer
- Panel 2 alone: a stand-alone "cortical magnification, explained" article
- Panel 3 alone: a one-image reference for "the visual hierarchy" — useful in any vision-research blog post
- Panel 4 alone: an information-flow diagram for any pipeline talk
- Panel 5 alone: a categorical-recognition reference card

This is intentional. The channels need to produce reusable atoms; the arc is what proves they compose.

## Brand and contrast contract

Everything passes muriel's universal rules:

- 8:1 contrast on every text element
- Decorative strokes ≥55/255 on dark background
- Single font family (Inter, matching scrutinizer-www canonical palette)
- OLED palette baseline; brand-token import from `scrutinizer-www`'s palette if it exists

The arc is also a stress-test of the cross-channel brand discipline: five channels, one palette, one type system, one motion vocabulary. If the arc looks coherent, the channels are behaving.

## Critique pass

When each panel is rendered, run the `muriel-critique` agent on it (with `channel: brain` / `3d` / `diagrams` as appropriate). The agent's vision-inventory + honest-hedging + rasterization workflow is exactly what this arc needs since several panels are SVG (Sankey, sunburst) and the rest are PyVista/MNE PNG output.

Once panels exist, run critique again on the *composed* infographic — the cross-panel rhythm, type hierarchy, color consistency, and connecting-beat legibility are different judgment calls than the per-panel pass.

## Distribution

| Surface | Format | Where |
|---|---|---|
| Conference talk | Slide-by-slide PNG | Stage projector |
| LinkedIn / X | Single composed PNG | Andy's social handles |
| Scrutinizer blog | Interactive HTML article with embedded niivue + ECharts widgets | scrutinizer-www |
| Quora | "Adventures in AI Coding" Space | Quora Space |
| arxiv | Static figure inside a Scrutinizer 2027 paper | Future submission |

## Open questions

- **Does the deck need a Panel 0 (motivation)?** Probably yes — a single image of "the world we think we see" overlaid with "the world the eye actually delivers" (the whole visual scene blurred in periphery, sharp only at fixation). Could be a Scrutinizer pixel-density visualization.
- **Animation budget.** The most compelling version is animated (timing waves through the hierarchy in panel 3, Sankey flow in panel 4). Are we shipping animated panels, or static-only? Animated requires the video channel + ffmpeg.
- **Does the Sankey need real connectome data?** Or are qualitative neuroanatomy estimates acceptable for a popular-audience deck? Real connectome data adds rigor but the labels become specialist; qualitative loses precision but stays legible.
- **Where does color sit?** Color processing is a parvocellular-only pathway; it could be a Panel 3.5 ("not all visual information takes the same path"). Adds a beat but lengthens the deck.

## Status

Plan only. None of the channels exist yet. See `TODO.md` for the queued channel work this depends on.
