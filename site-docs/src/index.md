---
title: Interaction design and visual craft
description: A design skill for coding agents, with research-informed interactions, visual production guides, and Wunderkammer collection exploration. Browse the examples and references.
---

# muriel

**Interaction design and visual craft for coding agents.** Muriel helps choose
how information should look and behave, then builds and checks the result in
the project’s own design language. Its guides connect perception and HCI
research to working interfaces, typography, charts, diagrams, and motion.

Named after [Muriel Cooper](vocabularies/visible-language.md), co-founder of
MIT’s Visible Language Workshop. The documentation pairs that lineage with
implementation recipes and examples you can inspect.

[Browse the examples](gallery/){ .md-button }
[Use the skill](SKILL.md){ .md-button }

## Explore a collection with Wunderkammer

Many images need an overview, filters, and a way back to the item you were
reading. **[Wunderkammer](references/collections.md)** is Muriel’s default
collection explorer: a person can pan, zoom, group, compare, and inspect;
an agent can read back the exact selection.

[![Wunderkammer’s collection wall, showing Psychodeli frames grouped by capture month.](examples/wunderkammer-explore.webp){ loading=lazy width=1520 height=950 }](https://andyed.github.io/clipwall-demo/)

[Try the live collection](https://andyed.github.io/clipwall-demo/) ·
[Build your own](references/collections.md) ·
[Read the Visible Language lineage](vocabularies/visible-language.md)

The collection guide covers **Wunderkammer 0.3.0**, including spatial views and
collection documents. The screenshot comes from that release; the live demo
can change independently.

## Start here

- **[Human capabilities](references/human-capabilities.md)** — the cognitive
  and perceptual questions behind an interaction choice.
- **[Spatial](channels/spatial.md)** — 3-D perspective walls and floors for
  typography and imagery. The look behind the [live demos](gallery/).
- **[Charts](channels/charts.md)** — data graphics with the contrast floor and
  brand tokens baked in.
- **[Semantic zoom and linked displays](references/multiscale-coordination.md)** —
  changing representations, coordinated views, and recoverable brushing.
  Explore the [Linked Atlas lab](examples/linked-atlas/index.html).
- **[Zooming interfaces](references/zooming-interfaces.md)** — navigation,
  landmarks, automatic detail, and return context, with Wunderkammer as a reference.
- **[Faceted exploration](references/faceted-exploration.md)** — searchable
  attribute values, contextual counts, explicit scope, and recoverable refinement.
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
| **Channels** | The output media: spatial, charts, infographics, science, raster, SVG, web, interactive, diagrams, video, terminal, density viz, gaze, polish, README. |
| **Vocabularies** | Named aesthetic grammars to borrow conventions from — Visible Language, FUI, kinetic typography, KaTeX, PixiJS, declassified, surfaces, data-viz platform guides, muriel's own brand. |
| **Reference** | Interaction design, collection exploration, zooming, linked displays, dimensions, and style guides. |

Use the left rail to navigate. Every channel page is single-sourced from the
skill itself — what you read here is exactly what the skill carries at render
time.
