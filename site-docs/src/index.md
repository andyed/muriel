# muriel

**A multi-constraint solver for visual production.** muriel turns a brief —
"make me a deck / a paper figure / a gaze plot / a share card" — into a
deterministic, reproducible artifact for human eyes, across sixteen output
channels. Named after Muriel Cooper, founder of the MIT Visible Language
Workshop.

It is a curator before it is an originator: it lifts the sharpest structural
patterns from sibling skills, ports their agent-actionable detection tables,
attributes the lineage, and overrides anything that fights its universal rules.

[See the live demo gallery ↗](gallery/){ .md-button .md-button--primary }
[Read the skill ↗](SKILL.md){ .md-button }

## Start here

New to muriel? These are the highest-leverage channels — each is a self-contained
recipe set you can route a brief to:

- **[Spatial](channels/spatial.md)** — 3-D perspective walls and floors for
  typography and imagery. The look behind the [live demos](gallery/).
- **[Charts](channels/charts.md)** — data graphics with the contrast floor and
  brand tokens baked in.
- **[Infographics](channels/infographics.md)** — explanatory layouts that earn
  every element on the page.
- **[Science](channels/science.md)** — paper figures, reproducible and
  publication-ready.

Then browse the full **[channel map](SKILL.md)**, or jump straight into the
**[live demo gallery ↗](gallery/)** to see spatial typography rendered in the
browser.

## The 8:1 rule

One constraint stays active at render time above all others:

> **8:1 contrast minimum on all text. Compute the WCAG ratio. No exceptions.**

Contrast is necessary but not sufficient — size, weight, and opacity compound on
legibility. The floors that pair with the 8:1 rule:

- **Body weight ≥ 500 (medium).** Regular weight + muted color + 9:1 contrast
  still reads thin at small sizes.
- **Footer / caption text ≥ 16 px.**
- **No `opacity` on text** — it composites the effective ratio below the raw
  value and erodes glyph thickness.
- **Decorative elements ≥ 55/255** on a dark background, or they vanish on small
  screens.

The canonical OLED palette: cream `rgb(230,228,210)` on near-black
`rgb(10,10,15)`. Pure white is too harsh. (This documentation site is built to
the same floor — every text token here is computed ≥ 8:1 against its surface.)

## The channel concept

Each **channel** is a dedicated output medium with its own deep recipes, tooling,
and hard-won lessons. The top-level skill is the map; the channel subfiles are
the territory. A brief routes to one or more channels; the universal rules
(8:1 contrast, weight/size/opacity floors, brand tokens, reproducibility) bind
across all of them.

| Group | What it covers |
|---|---|
| **Channels** | The output media: spatial, charts, infographics, science, raster, SVG, web, interactive, diagrams, video, terminal, density viz, gaze, polish. |
| **Vocabularies** | Named aesthetic grammars to borrow conventions from — Visible Language, FUI, kinetic typography, KaTeX, PixiJS, declassified, surfaces, data-viz platform guides, muriel's own brand. |
| **Reference** | Cross-channel constants: dimensions (social cards, device footprints, print) and style-guides (the `brand.toml` schema). |

Use the left rail to navigate. Every channel page is single-sourced from the
skill itself — what you read here is exactly what the skill carries at render
time.
