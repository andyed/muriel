# Data-viz platforms — cross-platform charting vocabulary

> **What this vocabulary is.** A short survey of the major platform charting guides that muriel can cite when a figure leaves the paper-figure register: when a chart will live in an iOS app, a Material-themed admin panel, an enterprise Carbon dashboard, an Observable notebook, or a newsroom data-story. None of these guides are *muriel's* opinion — muriel's opinion is encoded in `channels/science.md`, `channels/infographics.md`, and the universal rules — but a cited platform precedent is often the right way to settle a discussion that muriel doesn't have a hard rule for.
>
> **What this vocabulary is not.** Not a chart-type taxonomy (that's `channels/infographics.md`'s 10-type table). Not a colour-palette reference (that's `muriel.palettes`). Not a "which JS chart library" recommendation (that's [`channels/charts.md`](../channels/charts.md), which covers Recharts / ECharts / Chart.js / Plotly / D3 with 22 numbered rules and a per-library config table). **`channels/charts.md` is the sibling channel here** — it covers chart *libraries*, this vocab covers platform design *guides*. Reach for that channel when picking an implementation; reach for this vocab when defending a principle to a reviewer.

Part of the [muriel](../SKILL.md) skill. Sibling vocabs: [`vocabularies/visible-language.md`](visible-language.md) (MIT Cooper VLW), [`vocabularies/fui.md`](fui.md), [`vocabularies/pixijs.md`](pixijs.md).

## When to reach for this

- An artifact is being ported between registers (paper figure → iOS chart, dashboard → editorial story) and needs a cross-platform precedent for accessibility, motion, or type sizing.
- A reviewer (`muriel-critique`, human, or otherwise) raises an issue muriel's docs don't have a hard rule for — Apple HIG / Material / Carbon may have ruled on it explicitly.
- A `brand.toml` for a client lives downstream of a specific platform's design system and you want to know what they've already pre-decided.
- An accessibility audit needs a precedent — Apple's audio-graph and Material/Carbon's contrast tokens give you something defensible to cite.

## The platforms

Each entry: who owns it, what license its docs sit under (matters for citation discipline), what it's distinctively good at, where it converges with muriel, where it diverges.

### Apple — *Charting data* (Human Interface Guidelines)

- **Source.** [Apple HIG — Charting data](https://developer.apple.com/design/human-interface-guidelines/charting-data). Canonical surface: Swift Charts (iOS 16+, macOS 13+).
- **License.** © Apple Inc., all rights reserved. Standard developer-site terms — free to read and link, **not** free to redistribute verbatim. Cite by URL + paraphrase, same scholarly pattern muriel uses for Tufte / Bertin / Cooper.
- **Distinctive contribution.** **Audio graphs** — Swift Charts emits sonified narrations for VoiceOver, so a chart is navigable by ear, not only by sight. No other major platform has this baked in. Also: **Dynamic Type** (chart text scales with user accessibility settings) and automatic **light/dark mode** adaptation.
- **Convergent with muriel.** Hierarchy via size + weight, hue carries semantics not decoration, motion is purposeful (no bounce/elastic), don't crowd labels — all already in `channels/web.md`'s anti-pattern list and `channels/science.md`'s plot-readability rules. Cite Apple HIG when a reviewer asks "where is that rule from?" and you want a non-academic precedent.
- **Divergent.** Apple's register is *interactive surfaces*, not *paper figures*. Detail-on-demand via tap is a chart pattern muriel's `channels/science.md` doesn't endorse (a paper figure must read at-print without interaction). For static figures, ignore the interaction layer of Apple's guidance; for screenshots of iOS apps, follow it.
- **Cite when:** porting a paper figure to a Swift Charts surface; auditing an iOS-bound chart's accessibility; arguing for audio-graph parity in a brief that owns native iOS deliverables.

### Google — *Material Design 2 — Data visualization* {#google-material-design-3-data-viz}

- **Source.** [Material Design 2 — Data visualization](https://m2.material.io/design/communication/data-visualization.html). This is the legacy Material 2 guide; its site is no longer maintained. There is no equivalent guide at the former Material 3 URL.
- **Distinctive contribution.** Practical examples of chart selection, labels, hierarchy, and interaction in app interfaces. Use it as a historical design reference, checking implementation details against the platform you are building for.
- **Convergent with muriel.** Choose a chart for the question, give it a clear reading order, and reveal additional detail through interaction when the task calls for it.
- **Scope.** This guide does not define a shared “Material Charts” library across Compose, Flutter, and the web. [Material 3 design tokens](https://m3.material.io/foundations/design-tokens/overview) are a separate reference for theme values; connecting a chart library to those tokens is implementation work.
- **Cite when:** discussing chart purpose, labeling, or detail-on-demand in a Material-styled app. Identify the guide as Material 2 when citing it.

### IBM — *Carbon Charts*

- **Source.** [Carbon Design System — Data visualization](https://www.carbondesignsystem.com/building-blocks/data-visualization/overview). Library: [@carbon/charts](https://github.com/carbon-design-system/carbon-charts) (D3-based).
- **License.** Code is Apache 2.0. Documentation site terms permit citation; verify per-page before lifting paragraphs.
- **Distinctive contribution.** **Enterprise-dashboard chart taxonomy** — when to use a *combo chart* vs a *stacked area*, when a *meter* outperforms a *donut*, exhaustive guidance for ops / observability / BI surfaces. Strong accessibility patterns (focus rings, ARIA descriptions, keyboard navigation across data points).
- **Convergent with muriel.** Catalog-first thinking — Carbon answers "which chart for this question?" the same way `channels/infographics.md` answers "which template for this argument?".
- **Divergent.** Enterprise voice; conservative palette; expects you're building a 50-chart dashboard, not a single hero figure. The visual register is intentionally muted, which can read corporate against muriel's OLED brand defaults.
- **Cite when:** building dashboards, defending dense-data layouts, or sourcing keyboard-navigation patterns for interactive charts.

### Vega / Vega-Lite — *Grammar of Graphics*

- **Source.** [Vega-Lite](https://vega.github.io/vega-lite/) — declarative chart grammar (JSON spec). UW Interactive Data Lab + Voyager team. Lineage: Wilkinson's *Grammar of Graphics* (1999) → Hadley Wickham's `ggplot2` (2009) → Vega (2014) → Vega-Lite (2017).
- **License.** [BSD-3-Clause](https://github.com/vega/vega-lite/blob/main/LICENSE). Examples and prose freely reusable with attribution.
- **Distinctive contribution.** The **grammar itself** — a chart as a composition of `data + transform + mark + encoding`. Once you can spell a chart in Vega-Lite, you can spell it anywhere. Spec-as-artifact: the JSON *is* the chart, no library binding needed. Strong on **interaction grammar** (selections, brushes, linked views).
- **Convergent with muriel.** Declarative > imperative is exactly `channels/diagrams.md`'s spec-first ethos. Vega-Lite specs round-trip cleanly with `muriel/tools/diagrams` patterns.
- **Divergent.** Vega-Lite's default theming is academic (white background, thin grey gridlines); muriel's brand-token discipline overrides this aggressively. The grammar is also opinionated about *what a chart is* — long-form data, tidy columns — which doesn't match every input shape.
- **Cite when:** debating chart composition vs. configuration; teaching the grammar-of-graphics lineage; defending a spec-first pipeline.

### Observable — *Plot*

- **Source.** [Observable Plot](https://observablehq.com/plot/). Mike Bostock's post-D3 chart opinion.
- **License.** [ISC](https://github.com/observablehq/plot/blob/main/LICENSE). Permissive; examples freely citable.
- **Distinctive contribution.** **Conciseness** — a Plot spec is shorter than the equivalent Vega-Lite for most exploratory charts. **Marks** abstraction (`dot`, `line`, `barY`, `tick`) reads as English. Designed for the explore-then-publish loop in Observable notebooks specifically but works standalone.
- **Convergent with muriel.** Same grammar-of-graphics lineage as Vega-Lite. Same "spec-first" discipline.
- **Divergent.** Less complete than Vega-Lite (no full interaction grammar yet); intended for *exploration* register more than *publication* register. Defaults are Bostock-y rather than brand-token-y.
- **Cite when:** quick exploratory analysis in a notebook; small interactive charts where Vega-Lite's spec weight is overkill; teaching the post-D3 idiom.

### Financial Times — *Visual Vocabulary*

- **Source.** [FT Visual Vocabulary](https://ft-interactive.github.io/visual-vocabulary/) — the Financial Times' poster + companion app classifying chart types by communication purpose.
- **Reuse.** The FT’s [Chart Doctor licence note](https://github.com/Financial-Times/chart-doctor/blob/main/README.md#licence) distinguishes MIT-licensed software from FT content. Link to the vocabulary; do not assume the poster or its illustrations share the software licence.
- **Distinctive contribution.** **Communication-purpose taxonomy** — *Deviation, Correlation, Ranking, Distribution, Change-over-time, Magnitude, Part-to-whole, Spatial, Flow*. Nine purposes, each with a handful of canonical chart types. Closer to muriel's `channels/infographics.md` taxonomy than to a "which library" guide.
- **Convergent with muriel.** Purpose-first classification matches muriel's "argument decides chart" framing. The FT taxonomy is the single best public artifact for that move.
- **Divergent.** Editorial voice; intended for journalism, not science papers or apps. Doesn't address accessibility, motion, or interaction.
- **Cite when:** picking a chart type from a list of candidates; teaching the "argument first, chart second" discipline; cross-referencing infographics templates.

### Datawrapper Academy

- **Source.** [Datawrapper Academy](https://academy.datawrapper.de/). Newsroom-aimed chart education from Datawrapper / Lisa Charlotte Muth.
- **License.** Page-by-page; most articles are clearly readable but reuse permission varies. Cite by URL + paraphrase; check individual posts before quoting at length.
- **Distinctive contribution.** **Editorial register** — concrete *do/don't* examples drawn from real published charts. Strong on colour psychology (named, not just hex), label placement, and "what would a reader actually understand?".
- **Convergent with muriel.** Reader-first framing; named anti-patterns (cf. impeccable's named bans in `channels/web.md`).
- **Divergent.** Journalism, not science; assumes Datawrapper's interactive surface; opinionated colour palettes that may not match a `brand.toml`.
- **Cite when:** a chart will land in a newsroom-adjacent register; defending a specific colour choice with public-facing precedent.

<span id="what-they-converge-on"></span>
<span id="what-they-diverge-on"></span>

## How to compare them

These references have different scopes. FT starts with communication purpose; Carbon pairs chart types with implementation resources; Apple focuses on platform behavior; the legacy Material guide illustrates chart presentation in apps. Use the source that addresses the actual design decision.

Muriel’s own requirements still apply: readable labels, redundant cues when color carries meaning, purposeful motion, and its stricter text-contrast target. Do not attribute these requirements to every platform without a specific supporting passage. A design guide, a library default, and a tested accessibility behavior are different kinds of evidence.

## How to borrow

Name the platform, link to the relevant section, and distinguish the source’s guidance from the decision you are making:

> **[Material Design 2 — Data visualization](https://m2.material.io/design/communication/data-visualization.html):** The guide illustrates ways to reveal more detail through interaction. For this dashboard, we will keep the key comparison visible and put supplementary values in a keyboard-accessible detail view.

Paraphrase the relevant idea and explain its application to the artifact. Check the source before quoting or reusing images.

## Prior art / upstream

This vocab borrows the survey-with-citation pattern from:

- [Bang Wong — *Points of view: Color blindness*](https://www.nature.com/articles/nmeth.1618) (Nature Methods, 2011) — single-source citation discipline.
- [`channels/infographics.md` § Prior art / upstream](../channels/infographics.md) — the K-Dense survey pattern at channel scale.
- pbakaus/impeccable — the named-ban list pattern, applied here to platform-divergence calls rather than typographic bans.
