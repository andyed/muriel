# Surfaces — composed-artifact archetypes that compose channels

> **What this vocabulary is.** A survey of the *surfaces* concept — composed-artifact archetypes (a Swiss-international slide deck, an NYT-style data-chart frame, a SaaS landing prototype, a PRD doc page, a Twitter share card) that sit *one layer above* muriel's channels. A channel is an output substrate (HTML/CSS, SVG, matplotlib, terminal). A surface is a composed artifact for a specific brief, expressed *through* one or more channels, with locked layout choices and a published-piece register.
>
> **What this vocabulary is not.** Not a competitor to muriel's channels — surfaces compose channels, they don't replace them. Not a generator catalog (muriel doesn't ship surface generators today; this vocab cites the canonical external catalog). Not a brand system (that's `channels/style-guides.md`).

Part of the [muriel](../SKILL.md) skill. Sibling vocabs: [`vocabularies/data-viz-platforms.md`](data-viz-platforms.md) (Apple HIG / Material / Carbon / Vega-Lite / Plot / FT / Datawrapper charting guides), [`vocabularies/visible-language.md`](visible-language.md) (MIT Cooper VLW), [`vocabularies/kinetic-typography.md`](kinetic-typography.md).

## Channels vs surfaces — why both

```
channels (substrates)              surfaces (composed archetypes)
───────────────────────            ────────────────────────────────
channels/raster.md     ←─┐         "Swiss International deck"
channels/svg.md          ├──→ compose →  "NYT-style data-chart frame"
channels/web.md          │              "PRD spec page"
channels/charts.md       │              "Twitter share card"
channels/polish.md     ←─┘              "Brutalist web prototype"
```

A channel tells you *how to emit pixels for this substrate at muriel's rigor*. A surface tells you *what composition to reach for when the brief is "make me a deck"*. The same channel (HTML+CSS via `channels/web.md`) underwrites many surfaces (decks, magazine articles, dashboards, share cards, PRDs).

muriel today ships fourteen channels and one example surface (`examples/scrutinizer-ridgemap/`). The surface vocabulary lives *here* because formalizing the layer above channels is a queued direction, not shipped code — but the concept is already in use in the wider Claude-skill ecosystem and worth naming.

## The canonical external catalog — html-anything

[`nexu-io/html-anything`](https://github.com/nexu-io/html-anything) (Apache-2.0, 4.7k★ as of 2026-05) ships **75 surface archetypes** grouped into roughly nine families, all rendered as single-file HTML. It's the closest contemporary to a fully-fleshed surfaces catalog; muriel cites it rather than rebuilding its surface taxonomy from scratch.

The nine families:

| Family | Surface count | Examples | Channel substrate |
|---|---:|---|---|
| **Decks** | ~17 | `deck-swiss-international` (16-col grid, 22 locked layouts, IKB/Lemon/Mint/Safety-Orange themes), `deck-guizang-editorial` (magazine ink), `deck-xhs-pastel` (Xiaohongshu-native), `deck-pitch`, `deck-replit`, `deck-hermes-cyber` | HTML + CSS, sometimes PPTX |
| **Frames** (motion / video) | ~11 | `frame-data-chart-nyt` (NYT-newsroom data frame), `frame-glitch-title` (cyan/magenta aberration + CRT scanlines), `frame-light-leak-cinema`, `frame-liquid-bg-hero`, `frame-flowchart-sticky`, `video-hyperframes`, `sprite-animation`, `motion-frames`, `vfx-text-cursor` | HTML + CSS (composed into hyperframes/video) |
| **Cards** (social) | ~8 | `card-twitter`, `card-xiaohongshu`, `social-reddit-card`, `social-spotify-card`, `social-x-post-card`, `social-carousel`, `social-media-dashboard`, `social-media-matrix` | HTML → PNG via headless capture |
| **Web prototypes** | ~9 | `web-proto-brutalist` (Swiss industrial, ASCII decoration), `web-proto-editorial` (serif + grid), `web-proto-soft` (rounded + warm), `saas-landing`, `pricing-page`, `waitlist-page`, `mobile-app`, `mobile-onboarding`, `prototype-web` | HTML + CSS |
| **Articles** | ~4 | `article-magazine`, `blog-post`, `digital-eguide`, `magazine-poster` | HTML + CSS (editorial register) |
| **Office / PM** | ~9 | `pm-spec` (PRD), `team-okrs`, `meeting-notes`, `weekly-update`, `eng-runbook`, `hr-onboarding`, `kanban-board`, `finance-report`, `invoice` | HTML + CSS (document register) |
| **Dashboards** | ~4 | `dashboard`, `live-dashboard`, `flowai-team-dashboard`, `social-media-dashboard` | HTML + CSS + chart libraries |
| **Posters** | ~2 | `poster-hero`, `magazine-poster` | HTML + CSS, single-page display |
| **Specialized** | ~11 | `resume-modern`, `data-report`, `email-marketing`, `mockup-device-3d`, `doc-kami-parchment`, `docs-page`, `wireframe-sketch`, `dating-web`, `gamified-app`, `ppt-keynote`, `social-media-matrix` | varies |

## Patterns worth naming

Even without committing to a muriel-side surface implementation, the html-anything catalog establishes patterns that map onto muriel conventions and inform future channel work:

### 1. Typed frontmatter per surface

Each html-anything skill ships YAML frontmatter with fields muriel doesn't currently emit on channels:

```yaml
name: deck-swiss-international
en_name: "Swiss International Deck"
zh_name: "瑞士国际主义 Deck"      # ← bilingual title (CJK-first instances exist too)
emoji: "🟦"
description: "16 列网格 + 单一饱和 accent + 22 个锁死版面"
category: slides                  # surface family
scenario: marketing               # what brief this serves
aspect_hint: "16:9 横向翻页"        # canvas hint
featured: 50                       # registry sort weight
recommended: 2                     # featured-in-defaults rank
tags: ["swiss", "grid", "international", "ikb"]
example_id: sample-swiss-international
example_source_url: "https://github.com/op7418/guizang-ppt-skill"
example_source_label: "op7418/guizang-ppt-skill"
```

What's transferable to muriel channels — fields worth considering for a `kind: surface` schema extension in [`channels/SCHEMA.md`](../channels/SCHEMA.md): `scenario` (what brief), `aspect_hint` (canvas), `example_source_url` + `example_source_label` (lineage citation as data, not prose).

### 2. Absolute rules per surface (locked-down hex / locked-down grid)

Surfaces enforce non-negotiable constraints inside their archetype. `deck-swiss-international`'s rules read like muriel's universal rules but scoped to one surface:

- **Only direct angles.** `border-radius: 0` everywhere; any curve breaks the surface.
- **1px hairline borders only.** No shadows, no gradients, no blur.
- **16-column grid, gap 0.**
- **Pick exactly one theme from the four locked palettes** — Klein Blue IKB `#002FA7`, Lemon Yellow `#FFD500`, Lemon Green `#C5E803`, Safety Orange `#FF6B35`. **No hex modification, no mixing.**
- **Numbers must come from user input.** Bar heights = real data, proportionally. Inventing numbers breaks the surface.
- **22 locked layouts** (S01 Cover, S02 Vertical Timeline, S03 Statement, ..., S22 Image Hero). Don't invent new layouts; pick from the pool, repeat as needed.

This pattern — *surface = channel substrate + locked layout pool + locked palette + locked typography + locked grid + non-negotiable composition rules* — is exactly what muriel could codify above its channels. Today muriel offers *capability* (the channels emit anything that clears 8:1 / weight×size×opacity / brand tokens); surfaces would offer *opinion* (this *specific* artifact must use this *specific* layout pool against this *specific* canvas).

### 3. CJK-first font stacks

html-anything routinely pairs Latin display fonts with `Noto Sans SC` for Chinese:

```
Inter Tight (Latin display) / Inter (body) / Noto Sans SC (中文) / JetBrains Mono (数据)
```

muriel currently assumes Latin-only font stacks. The CJK pairing pattern (Latin first, CJK fallback in the same family) is a queued addition — see [`TODO.md`](../../../../TODO.md) i18n entry.

### 4. "Inspired by" lineage chain in skill frontmatter

Most html-anything skills cite an `example_source_url` pointing to the prior art they descend from — `op7418/guizang-ppt-skill`, `hyperframes.heygen.com/catalog`, etc. The lineage is shipped *as a frontmatter field*, not buried in prose. Matches muriel's curator stance — credit travels with the artifact.

### 5. Featured / recommended ranking as data

`featured: 50`, `recommended: 2` — surfaces declare their own registry rank. An agent picking a surface for a brief can sort by these without reading the prose. muriel doesn't currently rank its channels/vocabs against each other; if surfaces ship muriel-side, this ranking pattern would let the picker do less work.

## What to mine, what to leave

**Worth mining when muriel ships surfaces:**

- The 9 families as a starting taxonomy (decks / frames / cards / web prototypes / articles / office docs / dashboards / posters / specialized).
- The typed frontmatter shape (`category`, `scenario`, `aspect_hint`, `featured`, `recommended`, `example_source_url`).
- "Absolute rules per surface" as enforceable gates in `muriel.critique` for that surface.
- The "locked layout pool" pattern (`deck-swiss-international`'s 22 S## layouts) as a *layout vocabulary* for the decks family.
- CJK-first font stacks as the default for any i18n-aware surface.

**Worth leaving:**

- The full 75-surface catalog (most are variations of a few core patterns; muriel doesn't need to ship 75 to ship surfaces).
- html-anything's framework choice (Next.js app, registry-driven HTML rendering) — muriel is Python-first.
- The Chinese-marketplace-specific surfaces (`card-xiaohongshu`, `deck-xhs-*`) until a brief actually needs them.
- The "vibe-clone-this-PPTX" image-based skill (different ethos from muriel's deterministic-by-construction generation).

## Citation

When a muriel artifact draws on a surface pattern documented above, cite [`nexu-io/html-anything`](https://github.com/nexu-io/html-anything) with a surface name (e.g., "`deck-swiss-international` lineage"). When the underlying lineage extends further (`deck-swiss-international` cites `op7418/guizang-ppt-skill`), follow the chain — credit travels.

## See also

- [`vocabularies/data-viz-platforms.md`](data-viz-platforms.md) — sibling vocab surveying platform charting guides
- [`channels/charts.md`](../channels/charts.md) — JS chart-library channel (charts.md substrate; surfaces compose charts.md into dashboards)
- [`channels/polish.md`](../channels/polish.md) — UI micro-interaction discipline (orthogonal layer; polish applies to any surface's interactive elements)
- [`channels/style-guides.md`](../channels/style-guides.md) — brand.toml schema (orthogonal; a surface inherits from a brand, the surface itself locks layout / grid / typography choices regardless of brand)
