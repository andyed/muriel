# muriel v0.12.0 — polish discipline + the surfaces concept

*Released 2026-05-24.*

Two additions from a same-day audit of the wider LLM-agent-skill ecosystem. (1) A new [`channels/polish.md`](plugins/muriel/skills/compose/channels/polish.md) — fourteenth output channel — codifies the UI micro-interaction + visual-detail rules that turn an OK interface into one that feels considered. 16 numbered rules, mined verbatim from `thedavidmurray/claude-make-interfaces-feel-better` (archived MIT) because the values are *tuned*, with muriel's 8:1 contrast floor added as a binding gate on top. (2) A new [`vocabularies/surfaces.md`](plugins/muriel/skills/compose/vocabularies/surfaces.md) names the *surfaces* concept (composed-artifact archetypes that compose channels: decks, frames, cards, prototypes, articles, PRDs, dashboards, posters) and cites `nexu-io/html-anything` as the canonical external catalog. The README "Related prior art" section gains five entries surfaced by the audit; full surface implementation is queued.

---

## Headline 1 — `channels/polish.md`

The frontend-polish channel: the codified design-engineering rules that turn an OK interface into one that feels considered. Distinct from sibling channels — [`channels/web.md`](plugins/muriel/skills/compose/channels/web.md) covers editorial HTML and Marginalia (the *prose* surface), [`channels/interactive.md`](plugins/muriel/skills/compose/channels/interactive.md) covers live demos where the reader moves parameters (the *exploratory* surface), and this channel covers the *tactile* surface that any frontend benefits from regardless of its higher-level purpose.

The 16 rules, organized into four groups:

**Universal (apply to nearly every interface)**
- Concentric border radius: `outer = inner + padding`
- Optical over geometric alignment (icon-side padding `−2px`, play-triangle `+2px` shift)
- Shadows over borders for elevation (three-layer `box-shadow` composition)
- 40×40px minimum hit area (no overlapping hit areas)

**Typography**
- `text-wrap: balance` on headings (≤6 lines)
- `text-wrap: pretty` on body text
- `-webkit-font-smoothing: antialiased` once at the root (macOS rendering)
- `font-variant-numeric: tabular-nums` for dynamic numbers

**Surfaces**
- `1px` inset outline on images (`rgba(0,0,0,0.1)` light / `rgba(255,255,255,0.1)` dark)

**Animations** — exact values, never deviate
- CSS transitions for interactive state, keyframes only for one-shot sequences
- Split + stagger enters at ~100ms with `opacity` + `translateY(12px)` + `blur(4px)`
- Subtle exits: `translateY(-12px)` at `150ms` ease-in (never just unmount)
- Contextual icon swaps: `scale 0.25→1` + `opacity 0→1` + `blur 4px→0`, spring `{ type: "spring", duration: 0.3, bounce: 0 }` — **`bounce` must be `0`**, never `0.1`
- `scale(0.96)` on press — never below `0.95` (anything lower feels collapsed, not depressed)
- `AnimatePresence initial={false}` to skip default-state page-load animations

**Performance**
- Never `transition: all` — specify exact properties (`transition-property: scale, opacity`)
- `will-change` only for compositor-friendly properties (`transform`, `opacity`, `filter`, `clip-path`); never `will-change: all`; only when first-frame stutter is observed

Plus a validation checklist, an anti-pattern table (PATTERN→FIX format matching `channels/charts.md`), and a brand-floor reminder that the 8:1 contrast rule still binds — hover and focus states must clear it explicitly.

### Why mine verbatim

The original values are tuned, not arbitrary. `scale(0.96)` not `0.95` because anything lower reads as collapsed. `bounce: 0` not `0.1` because any positive bounce reads as gimmicky. `scale 0.25→1` not `0.5→1` for icon swaps because the smaller start scale is what gives the swap its sense of arrival. Porting these to "approximately the same" loses the property. The mining stance: port the values, attribute the lineage ([thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better), MIT, archived May 2026), add the 8:1 gate on top.

## Headline 2 — `vocabularies/surfaces.md`

muriel's channels are *output substrates* (HTML/CSS, SVG, matplotlib, terminal). The wider Claude-skill ecosystem has converged on a different organizing axis: *surfaces* — composed-artifact archetypes for specific briefs. A "Swiss International deck". An "NYT-style data-chart frame". A "Brutalist web prototype". A "PRD spec page". A "Twitter share card".

```
channels (substrates)              surfaces (composed archetypes)
───────────────────────            ────────────────────────────────
channels/raster.md     ←─┐         "Swiss International deck"
channels/svg.md          ├──→ compose →  "NYT-style data-chart frame"
channels/web.md          │              "PRD spec page"
channels/charts.md       │              "Twitter share card"
channels/polish.md     ←─┘              "Brutalist web prototype"
```

A surface = channel substrate + locked layout pool + locked palette + locked grid + non-negotiable composition rules. The same channel (HTML+CSS via `channels/web.md`) underwrites many surfaces.

[`nexu-io/html-anything`](https://github.com/nexu-io/html-anything) (Apache-2.0, 4.7k★) is the closest contemporary to a fully-fleshed surfaces catalog — ~75 surface skills grouped into nine families:

| Family | Count | Examples |
|---|---:|---|
| **Decks** | ~17 | `deck-swiss-international` (16-col grid, 22 locked layouts, IKB/Lemon/Mint/Safety-Orange themes), `deck-guizang-editorial`, `deck-xhs-pastel`, `deck-pitch` |
| **Frames** (motion / video) | ~11 | `frame-data-chart-nyt`, `frame-glitch-title` (cyan/magenta aberration + CRT scanlines), `frame-light-leak-cinema`, `frame-liquid-bg-hero`, `video-hyperframes` |
| **Social cards** | ~8 | `card-twitter`, `card-xiaohongshu`, `social-reddit-card`, `social-spotify-card`, `social-x-post-card` |
| **Web prototypes** | ~9 | `web-proto-brutalist`, `web-proto-editorial`, `web-proto-soft`, `saas-landing`, `pricing-page` |
| **Articles** | ~4 | `article-magazine`, `blog-post`, `digital-eguide`, `magazine-poster` |
| **Office / PM** | ~9 | `pm-spec`, `team-okrs`, `meeting-notes`, `eng-runbook`, `kanban-board`, `invoice` |
| **Dashboards** | ~4 | `dashboard`, `live-dashboard`, `flowai-team-dashboard` |
| **Posters** | ~2 | `poster-hero`, `magazine-poster` |
| **Specialized** | ~11 | `resume-modern`, `data-report`, `email-marketing`, `mockup-device-3d`, `ppt-keynote` |

### Patterns named (worth mining when muriel ships surfaces)

1. **Typed frontmatter** — `category`, `scenario`, `aspect_hint`, `featured`, `recommended`, `example_source_url`. Lets agents pick the right surface for a brief from data, not prose.

2. **Absolute rules per surface** — `deck-swiss-international` enforces `border-radius: 0` *everywhere*, hairlines only, no shadows/gradients/blur, 16-column grid `gap: 0`, exactly 4 locked themes with no hex modification, 22 layout archetypes (S01 Cover → S22 Image Hero) and no inventing new ones. "Numbers must come from user input — don't invent." This is the surface-specific version of muriel's universal rules; codifying it lets `muriel.critique` enforce per-surface gates the same way it enforces universal contrast.

3. **CJK-first font stacks** — Latin display + `Noto Sans SC` Chinese fallback in the same family. muriel's font stacks are currently Latin-only; the CJK pattern is a queued i18n addition.

4. **"Inspired by" lineage as data** — `example_source_url` + `example_source_label` in frontmatter, not buried in prose. Credit travels with the artifact.

5. **Featured / recommended ranking** — surfaces declare their own registry rank. An agent picking a surface can sort without reading.

### Why a vocab, not a channel — yet

muriel doesn't ship a surface catalog today; today is for naming the concept. Full implementation is queued (see [TODO.md](TODO.md)): the first three surface candidates are `deck-swiss-international` (fully spec'd by html-anything), `frame-data-chart-nyt` (clean editorial constraints, composes `channels/charts.md`), and `pm-spec` (composes `channels/web.md` for a document register). Each ships as `surfaces/<name>/SKILL.md` + `surfaces/<name>/example.html` mirroring html-anything's shape; surface implementation should follow the first concrete brief that wants one, not speculation.

## Related prior art — five new entries

The 2026-05-24 audit surfaced five additional projects worth citing in [README.md](README.md):

- **[anthropics/skills](https://github.com/anthropics/skills)** — the official Anthropic skill monorepo (`brand-guidelines`, `theme-factory`, `canvas-design`, `frontend-design`, `web-artifacts-builder`, `algorithmic-art`, `slack-gif-creator`). Positions muriel against the official baseline: Anthropic ships breadth across many domains; muriel ships depth on one domain with stricter constraints (11 palettes vs 1, two-tier text-safe/decorative split, contrast-by-construction generation, 8:1 floor, motion tokens, audit pipeline).
- **[thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better)** — already cited above as the source for `channels/polish.md`. Different lane from `impeccable`: impeccable runs deterministic anti-pattern detection over a rendered page; this codifies the design-engineering *recipes* you reach for when authoring the page.
- **[wrsmith108/visual-prompt-coach](https://github.com/wrsmith108/visual-prompt-coach)** — pedagogical-visual prompt skill using Dan Roam / Mayer / C4 / cognitive-load / Gestalt-CRAP. Asks the exact 4-question intake muriel's queued constraint-elicitation rule landed on independently — validates the cap.
- **[dot-Justin/teenage-engineering-ui-ux-skill](https://github.com/dot-Justin/teenage-engineering-ui-ux-skill)** — generates Teenage Engineering's visual register through procedural rules ("inspired-by, not cloned"). Useful external precedent for muriel's curator stance.
- **Skill-discovery indices** — [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (1000+ skills), [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) (1,400+ with installer), [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) (community-curated). Discovery tools for the [Sibling skills](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each) table, not authoritative themselves.

## Migration

- Channel count: 13 → 14 (`polish` added). Aesthetic-vocabularies list: 7 → 9 entries (`surfaces` + `data-viz-platforms` added; `data-viz-platforms` was shipped in v0.11.0 but wasn't surfaced in the SKILL.md index — corrected here). No breaking changes; both additions are purely additive.
- pyproject description bumped: "eleven channels" → "fourteen channels"; "raster/SVG/web/gaze helpers" → "raster/SVG/web/gaze/polish helpers".
- README channel count: fifteen → sixteen (14 output + 2 utility).

## Acknowledgements

- [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archived) — full source for `channels/polish.md`. The 16 rules, the four-doc split structure, and the canonical tuned values all port verbatim.
- [nexu-io/html-anything](https://github.com/nexu-io/html-anything) (Apache-2.0) — surfaces taxonomy + patterns documented in `vocabularies/surfaces.md`.
- [wrsmith108/visual-prompt-coach](https://github.com/wrsmith108/visual-prompt-coach), [dot-Justin/teenage-engineering-ui-ux-skill](https://github.com/dot-Justin/teenage-engineering-ui-ux-skill), [anthropics/skills](https://github.com/anthropics/skills) — surfaced by the audit, cited in [README.md](README.md) under "Related prior art".
