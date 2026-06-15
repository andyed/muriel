---
name: muriel
description: "A multi-constraint solver for visual production — raster, SVG, web, interactive, polish, video, terminal, density viz, gaze, science, infographics, diagrams, spatial, charts across fourteen output channels plus dimensions + style-guides cross-channel references. Brand tokens, 8:1 contrast rule, and dimension constants stay active at render time. Use when the user needs any visual artifact for human eyes."
---

# muriel — Multi-channel visual production


## Channels

Each channel has a dedicated subfile with deep recipes, tooling, and lessons. This top-level index is the map; the subfiles are the territory.

| Channel | Format | Deep dive |
|---|---|---|
| **Raster** | PNG/JPG | [`channels/raster.md`](channels/raster.md) — Pillow, `typeset.py`, store dimensions, fonts, inline pattern |
| **Vector** | SVG | [`channels/svg.md`](channels/svg.md) — `svgwrite`, `cairosvg`, Mermaid, Excalidraw, `viewBox` theming |
| **Web** | HTML + CSS | [`channels/web.md`](channels/web.md) — marginalia, pandoc filter, Playwright/weasyprint capture, data-URI |
| **Interactive** | WebGL / Canvas / D3 | [`channels/interactive.md`](channels/interactive.md) — single-file scaffold, PermalinkManager, CodePen, Observable |
| **Video** | MP4 / GIF | [`channels/video.md`](channels/video.md) — ffmpeg + `desktop-control` + tooltip burn + editing recipes |
| **Terminal** | Unicode | [`channels/terminal.md`](channels/terminal.md) — `chart.py` bar charts, sparklines, tables |
| **Density viz** | PNG | [`channels/heatmaps.md`](channels/heatmaps.md) — Tobii-style Gaussian overlays |
| **Gaze plots** | PNG / SVG / JS | [`channels/gaze.md`](channels/gaze.md) — scanpath, bubble, AOI timeline, saccade rose |
| **Science** | matplotlib + LaTeX | [`channels/science.md`](channels/science.md) — rcparams, stats reporting, notebook editorial, paper figures |
| **Dimensions** | *cross-channel reference* | [`channels/dimensions.md`](channels/dimensions.md) — social cards, device footprints, viewport tiers, video, paper/print, favicons, scale factors |
| **Style guides** | *brand schema* | [`channels/style-guides.md`](channels/style-guides.md) — brand.toml schema, loader, rule enforcement, CSS/matplotlibrc derivation, example brand.toml files |
| **Infographics** | SVG → PNG | [`channels/infographics.md`](channels/infographics.md) — 10 types × layout patterns × colorblind-safe palettes, deterministic SVG (not AI), 60-30-10 color / 60-40 viz:text rule, 5-point quality rubric at 8:1 |
| **Diagrams** | SVG | [`channels/diagrams.md`](channels/diagrams.md) — rhetorical primitives (2×2 matrix, N-step cycle, Venn shipped; comparison pair, funnel, stack, DAG, spectrum, pyramid, heat-grid queued); plus Mermaid → SVG/ASCII and TeX → SVG (MathJax) Node-bridges. Each preset carries an epistemic precondition and an anti-prescription. |
| **Spatial** | SVG + HTML/WebGL | [`channels/spatial.md`](channels/spatial.md) — depth scaffolding for layered typography. `muriel.spatial` perspective grids (1pt / 2pt / 3pt / iso) + `render_assets/` Three.js + CSS3DRenderer exemplars sharing one helper lib. Cooper VLW / Mackinlay-Robertson-Card / Dumais Data Mountain lineage. |
| **Charts** | JS chart libraries | [`channels/charts.md`](channels/charts.md) — Recharts, ECharts, Chart.js, Plotly, D3/SVG. 22 numbered rules, per-library quick-ref, anti-pattern PATTERN→FIX tables, can-I-remove test, chart-type guide, validation checklist. muriel-strict 8:1 color tokens override the Tufte palette. (matplotlib lives in `channels/science.md`.) |
| **Polish** | CSS / TSX / HTML | [`channels/polish.md`](channels/polish.md) — UI micro-interaction + visual-detail discipline. 16 numbered rules: concentric border radius, optical alignment, shadows-over-borders, image outlines, 40×40px hit area, interruptible transitions, split-and-stagger enters, subtle exits, contextual icon animations (`scale 0.25→1` + `blur 4px→0` + `bounce: 0`), `scale(0.96)` on press, no `transition: all`, `will-change` only on compositor-friendly properties, tabular nums, macOS font smoothing, `text-wrap: balance` / `pretty`. Mined from [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archived). |


## Aesthetic vocabularies

Design grammars worth naming explicitly when a project's visual register calls for something specific. A menu of established traditions — borrow their conventions, don't reinvent them.

- [`vocabularies/fui.md`](vocabularies/fui.md) — **Fantasy / Fictional User Interface.** Sci-fi HUDs. Perception NYC, Territory Studio, Ash Thorp, GMUNK lineage. Thin strokes, mono numerics, staggered reveals, radial geometry, restrained palettes.
- [`vocabularies/visible-language.md`](vocabularies/visible-language.md) — **Visible Language Workshop.** The MIT Media Lab design tradition (Cooper, Small, Ishizaki, Maeda → Processing → pretext). Information landscapes, multi-scale typography, typography as data structure. Contemporary substrate: [`@chenglou/pretext`](https://chenglou.me/pretext/). See also `channels/interactive.md` for the pretext API and the `pretext-coachella` reference exemplar.
- [`vocabularies/pixijs.md`](vocabularies/pixijs.md) — **PixiJS 2D WebGL/WebGPU substrate.** When Canvas/D3 runs out of headroom and Three.js is overkill. Particle-dense gaze overlays, shader-driven foveation demos, audio-reactive visuals. Pin to `^8.18`. **Lifted from [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) (MIT)** — they did the documentation work; we curated the relevant subset. Read upstream for depth.
- [`vocabularies/kinetic-typography.md`](vocabularies/kinetic-typography.md) — **Letters that move with intent.** Saul Bass → Kyle Cooper → Territory Studio lineage. Max contrast, strategic motion, rehearsed emotional vocabulary, SDF alpha rule. Substrate options: pretext for typographic Canvas2D animation, iblipper for a full animation-as-language pipeline (single-frame social graphics *and* animated kinetic type), Troika SDF for 3D scenes. Invoke `/iblipper` when the output itself is the animated artifact or the rhetorical-typography social-graphic still.
- [`vocabularies/katex.md`](vocabularies/katex.md) — **KaTeX math typesetting for the web.** When prose has math in it and the artifact lands on a web surface (marginalia essay, blog post, in-page explainer). MIT, CDN-clean, no bundler. Pin to `^0.16`. Reference exemplar: [`inside_the_math`](https://github.com/andyed/psychodeli-webgl-port/blob/main/inside_the_math/index-marginalia.html) — `.eq-block` pattern, sectional background accents, auto-render config. Don't use for paper figures (use `channels/science.md` matplotlib + LaTeX); don't use for moving math (use Manim CE).
- [`vocabularies/declassified.md`](vocabularies/declassified.md) — **Released, leaked, seized, discovered.** The visual register of the document-not-meant-for-the-reader. FBI Vault / FOIA reading-room / Wikileaks / Stasi-files lineage. Six provenance values (foia, leak, seizure, discovery, open, seized-annotated), two redaction grammars (gov-at-creation vs view-time-censorship), exemption-code system, classification banners, decl stamps, case-file paratext, aging-as-era-distance, and a four-handed marginalia vocabulary (red/blue/pencil/typewriter-strike). Use for fiction documents framed as released, worldbuilding bibles, or editorial pieces *about* secrecy.
- [`vocabularies/muriel-brand.md`](vocabularies/muriel-brand.md) — **muriel's own brand identity.** Inward-facing — canonical spec for the six-bar mark (Müller-Brockmann grid + Cooper VLW lineage), color tokens (`#e6e4d2` cream, `#0a0a0f` near-black, `#50b4c8` cyan accent), wordmark conventions (`muriel` always lowercase, `built with muriel` as canonical attribution), sizing rules including the subpixel rendering floor, and drop-in HTML/SVG snippets for inline + block "built with muriel" credits. Reach for this any time a project wants to attribute muriel — never trace the favicon.
- [`vocabularies/data-viz-platforms.md`](vocabularies/data-viz-platforms.md) — **Cross-platform charting design guides** (Apple HIG, Google Material 3, IBM Carbon, Vega-Lite, Observable Plot, FT Visual Vocabulary, Datawrapper Academy). License posture spelled out per platform — citable precedents to reach for when porting a paper figure to an iOS / Material / Carbon surface, or when a reviewer raises an accessibility / motion / type-sizing point muriel doesn't have a hard rule for. Sibling to `channels/charts.md` (which covers chart *libraries*); this vocab covers platform *guides*.
- [`vocabularies/surfaces.md`](vocabularies/surfaces.md) — **Composed-artifact archetypes that compose channels.** A surface is what a brief means by "make me a deck / share card / PRD / video frame" — locked layout pool, locked palette, locked grid, non-negotiable composition rules, expressed through one or more channels. muriel doesn't ship a surface catalog today; this vocab cites [nexu-io/html-anything](https://github.com/nexu-io/html-anything) (Apache-2.0, 4.7k★) as the canonical external catalog and names the patterns worth mining when muriel ships surfaces: 9 surface families (decks / frames / cards / web prototypes / articles / office / dashboards / posters / specialized), typed frontmatter (`category` / `scenario` / `aspect_hint` / `featured` / `recommended` / `example_source_url`), "absolute rules per surface" as enforceable gates, CJK-first font stacks, "inspired by" lineage chains as data.

Additional vocabularies (Swiss grid, editorial, brutalist, newsprint) can be added here without restructuring the skill.

---

## Sibling skills — what we borrow from each

muriel is a curator before it is an originator. When a third-party skill overlaps muriel's territory, the move is: lift the structural patterns and rule names worth quoting, port the agent-actionable detection tables, attribute the lineage, and override anything that fights our universal rules (8:1 contrast, weight/size/opacity floors, brand tokens, reproducibility). The table below records what we've taken and from where, so future overlap-discoveries don't restart the same audit.

| Sibling skill | What we took | What we kept ours | Where it lives in muriel |
|---|---|---|---|
| [caylent/tufte-data-viz](https://github.com/caylent/tufte-data-viz) | 22 numbered rule structure · per-library quick-ref tables (Recharts/ECharts/Chart.js/Plotly/D3) · anti-pattern PATTERN→FIX detection format · can-I-remove test · chart-type guidance table · validation checklist · "titles assert findings" / "compared to what?" / "don't chart what a sentence can say" as universal rules | 8:1 text floor (their default `#666`/`#e41a1c` fail at 5.7/4.7) · weight × size × opacity floor · OLED palette · brand-token system · `muriel.contrast` audit step · reproducibility ("save the script alongside the output") | [`channels/charts.md`](channels/charts.md) — full port with muriel-strict tokens; back-ported rules into the per-chart rules above |
| [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) | Curated PixiJS v8 documentation subset (Application setup, Sprite, Container, Filter, particle patterns) | Pinned to `^8.18`; framed around muriel's particle-dense gaze overlays / shader-driven foveation / audio-reactive use cases | [`vocabularies/pixijs.md`](vocabularies/pixijs.md) |
| [K-Dense AI scientific-agent-skills — matplotlib](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/matplotlib/SKILL.md) | OO interface as default · `constrained_layout=True` over `tight_layout()` for multi-panel · viridis/cividis preference · 72/150/300 DPI by medium framing | OLED rcparams · 8:1 audit · figsize ≥ 10×6 · paper-channel statistical reporting helpers · LaTeX/PGF bridge | [`channels/science.md`](channels/science.md) "Prior art / upstream" section |
| [K-Dense AI — statistical-analysis](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/statistical-analysis/SKILL.md) | Test-selection vocabulary (assumption checks, when to use which test) | Standard-library-only reporting helpers (`muriel.stats`) — no `scipy`/`pingouin` dependency · APA leading-zero stripping · null-as-detection-limit framing · pre-committed vs. exploratory labels | [`channels/science.md`](channels/science.md) "Statistical reporting" |
| [K-Dense AI — scientific-critical-thinking](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/scientific-critical-thinking/SKILL.md) | GRADE system · Cochrane Risk of Bias vocabulary · bias taxonomy (Cognitive/Selection/Measurement/Analysis/Confounding) — useful for naming *why* a claim is weak in editorial passes | n/a — pure vocabulary import | referenced inline when editorial passes need bias-naming |
| [K-Dense AI — market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/market-research-reports/SKILL.md) | (queued) 50+ page report template structure · PESTLE / Porter / TAM-SAM-SOM section conventions | Will use marginalia + weasyprint (or LaTeX) over their proprietary `.sty` · 300 DPI visuals · 8:1 contrast pass on every figure | queued — `channels/market-research.md` (see TODO) |
| [K-Dense AI — pptx](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/pptx/SKILL.md) | (queued) `pptxgenjs` (JS) → `soffice` PDF → `pdftoppm` per-slide PNG → Pillow thumbnail grid generate→render→inspect loop · 10 named palettes · "no accent lines under titles" AI-tell heuristic | Skip their fixed templates (converge to sameness, fight multi-constraint-solver ethos) · use muriel brand tokens · 8:1 audit on slide text | queued — `channels/pptx.md` (see TODO) |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HTML → MP4 video pipeline · GSAP timeline conventions · transcribe/tts/preview/render CLI · registry block + component system · website-to-video capture | Slot into video channel as a substrate option (not a replacement for desktop-control/ffmpeg) · use muriel brand tokens · audio-reactive PixiJS frames via custom renderer (queued) | [`channels/video.md`](channels/video.md) |
| [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) | 16 numbered UI-polish rules with **mathematical-precision framing** (`outer = inner + padding`, exact `scale(0.96)` press, exact `scale 0.25→1` + `bounce: 0` for icon swaps, ~100ms stagger between semantic chunks, 40×40px hit area minimum) · split-doc structure (typography / surfaces / animations / performance) · canonical recipes (shadow-as-border three-layer composition, cross-fade icon pattern without motion dependency) | 8:1 brand floor still binds for any text-bearing UI · `muriel.contrast` audit step required on hover + focus states · explicit anti-pattern table format (PATTERN→FIX) instead of prose-only rationale | [`channels/polish.md`](channels/polish.md) — full port; archived MIT upstream so the lineage citation is the documentation |
| [nexu-io/html-anything](https://github.com/nexu-io/html-anything) | The **surfaces** concept — composed-artifact archetypes (deck, frame, card, prototype, article, office-doc, dashboard, poster) that compose channels · 9-family taxonomy with ~75 reference surface skills · typed frontmatter shape (`category` / `scenario` / `aspect_hint` / `featured` / `recommended` / `example_source_url`) · "absolute rules per surface" enforcement pattern (`deck-swiss-international`'s `border-radius: 0` everywhere, 22 locked layouts S01–S22, no hex modification of the 4 themes) · "inspired by" lineage chain shipped as a frontmatter field · CJK-first font stacks (Latin display + `Noto Sans SC` body) | Python-native (their stack is Next.js / TS) · 8:1 contrast floor binds on every surface · `muriel.contrast` audit on the composed output · don't bundle the full 75-surface catalog (most are variations of a few core patterns) · skip the Chinese-marketplace-specific surfaces until a brief demands them · skip the vibe-clone-a-PPTX image-based skill (different ethos from deterministic-by-construction generation) | [`vocabularies/surfaces.md`](vocabularies/surfaces.md) — survey + patterns named, full surface implementation queued (see TODO) |

### Curator workflow

When a new skill is suggested as overlapping muriel:

1. **Read it fully** — SKILL.md, every rule file, the README, the live demo if there is one. Don't form an opinion from the description alone.
2. **Diff against muriel's existing coverage.** What does it have that we don't? What do we have that it doesn't? Look for structural patterns (numbering, naming, table formats) separately from content.
3. **Score against muriel's universal rules.** Does its color palette pass 8:1? Does it respect weight × size × opacity? Does it ship importable code or pure docs? Flag every divergence.
4. **Decide the borrow shape:**
   - **Lift structure** when their format (numbered rules, PATTERN→FIX tables, validation checklists) is sharper than ours.
   - **Port content** when they cover something we don't (a chart library, a chart type, a report template).
   - **Quote vocabulary** when their naming sticks (GRADE, range-frame, slopegraph) — use their names so cross-references stay legible.
   - **Override tokens** when their palette/contrast/typography rules are weaker than ours. Note the divergence explicitly in the channel doc.
   - **Skip wholesale adoption** when their conventions converge to sameness (fixed templates, AI-image generation, single brand voice) — those fight muriel's multi-constraint-solver ethos.
5. **Attribute** in the channel's "Prior art / upstream" section. Link to the source, name the license, note specific divergences.
6. **Record the take** in this table so the next overlap discovery starts from the curated diff, not from scratch.

---

## Universal rules

Codified from per-project bug fixes — apply to **every** channel:

- **8:1 contrast minimum** on all text. Compute the WCAG ratio. No exceptions.
- **Contrast is necessary, not sufficient.** Size, weight, and opacity compound on legibility. At small sizes (≤14 px / ≤10 pt), regular weight + muted color + 9:1 contrast still reads thin and dim — even when the math passes. Floors that pair with the 8:1 rule: **body weight ≥ 500 (medium)**, **footer/caption text ≥ 16 px**, **no `opacity` on text** (it composites the effective ratio below the raw value and erodes glyph thickness). When in doubt, promote color, bump size, add weight — in that order. (See `channels/science.md` for the matplotlib version.)
- **Decorative elements ≥55/255** on a dark background, or they vanish on small screens.
- **Measure before drawing.** Bbox / `viewBox` / `getBoundingClientRect` first; auto-shrink on overflow.
- **Label every number.** Units and context required.
- **OLED palette:** `(230,228,210)` cream on `(10,10,15)` near-black. Pure white is too harsh.
- **One font treatment per app/paper.** Vary background, not typography.
- **Optical alignment > mathematical alignment.** Nudge 2-4px when adjacent to UI elements.
- **Generated > drawn.** If the data could drive it, it should.
- **Reproducible > one-off.** Save the script alongside the output.
- **No false profundity.** Substance over hype.

### Anti-slop checklist (forbidden AI-tells)

The 8:1 rules above say what craft *is*; this says what generated-default slop *looks like*. These are the patterns that make an artifact read as machine-default rather than deliberate — the negative space of muriel's ethos. Scan against them before shipping any artifact. (Curated from [OpenCoworkAI/open-codesign](https://github.com/OpenCoworkAI/open-codesign)'s anti-slop digest, MIT; generalized from web-only to all channels. Channel-specific tells live in the subfiles — `fui.md` on stylized blanks, `echarts.md`/`charts.md` on "don't ship from memory" and accent-lines-under-titles.)

- **Default tool palettes.** Tailwind blue `#3b82f6` or Tailwind grays as the entire neutral scale; the `#0E0E10`-everywhere + one-purple-accent "minimal dark" page. Commit to a real palette.
- **Pure black `#000` text or pure white `#fff` surfaces.** Use near-black/near-white with a slight hue cast (the OLED cream rule generalized).
- **Overused default fonts.** Inter, Roboto, Arial, Helvetica, Playfair Display — unless the brief asks. A font choice is a design decision, not a fallback.
- **Placeholder content.** Lorem ipsum, "John Doe", "Acme Corp", round-number filler (`100%`, `1,234`), stale dates. Content must be domain-specific. If a value is genuinely unknown, use a stylized blank (`████`), not lazy filler — see `fui.md`.
- **Hotlinked external images.** No `unsplash.com` / `picsum.photos` / `placeholder.com` / `randomuser.me`. Inline SVG, generated assets, local files, or data URIs only — this is the reproducible/self-contained rule restated.
- **Logo-as-letter-in-rounded-square.** A soft square with one centered initial reads as a stub. Use a constructed monogram, a wordmark, or an explicit "YOUR LOGO HERE" placeholder that admits it's a placeholder.
- **Repeated-card filler.** Six identical 1:1 feature cards (24px icon + two-word title + one sentence); testimonial rows of circular-avatar + name + five stars; the three-column nav footer + social-icon row. Vary the rhythm or cut the section.
- **Decorative emoji as section icons** unless the brief asks for them.
- **Center-aligned body paragraphs.** Center headings if you must; never the body.
- **Gradient-blob hero** + bold sans headline + generic screenshot mockup. The house style of every generated landing page.

### Prose anti-slop (AI writing tells)

The checklist above is about how an artifact *looks*; this is about how its **prose reads**. Any channel that ships sentences — notebook editorial, blog explainers, captions, doc copy, marginalia — should scan against these before shipping. They're the textual equivalent of the gradient-blob hero: the patterns that make writing read as machine-default. (Curated from [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop), MIT.)

- **Throat-clearing openers.** "It turns out", "Here's the thing", "The uncomfortable truth is", "Let me be clear". Cut the runway; start at the sentence that matters.
- **Binary-contrast scaffolds.** "Not because X. Because Y.", "The question isn't X. It's Y.", "It's not this, it's that", "not just X but also Y". The single most common AI-explainer tell. State the thing directly.
- **Vague declaratives.** "The implications are significant", "The reasons are structural", "The stakes are high". Name the implication, the reason, the stake — or delete the sentence.
- **Adverb crutches.** really, just, genuinely, simply, actually, literally, fundamentally, truly. Almost always deletable with no loss.
- **False agency.** "the data tells us", "the culture shifts", "the market rewards". Inanimate subjects with human verbs. Name who acts.
- **Dramatic fragmentation / punchy endings.** "X. That's it.", three-item lists, every paragraph closing on a quotable one-liner. Vary rhythm; not every paragraph earns a mic-drop.
- **Meta-commentary.** "Let me walk you through", "Plot twist:", "Hint:". The reader doesn't need a tour guide.
- **Em-dash overuse and staccato.** Stylistic, not a hard ban — but if every other sentence has an em-dash or trails into "Not always. Not perfectly.", it reads generated.

Optional gate: score a draft on Directness / Rhythm / Trust / Authenticity / Density (1–10 each); below 35/50 wants a revision pass.

**Register carve-out.** These are defaults for editorial and explainer prose, *not* overrides for genre conventions. In scientific writing specifically: passive voice is conventional in methods sections ("participants were randomized", "data were filtered") and should not be force-converted; hedging is required, not slop — "not detected at this granularity" is correct precision, not softening to strip. When a stop-slop rule fights the genre, the genre wins.

## Visualization principles

For data-driven channels (raster plots, SVG, interactive JS, science, charts), apply Tufte/Bertin/CRAP via these high-leverage patterns. The first three are composition patterns; the next three are per-chart rules that catch ~80% of agent-generated chart problems before they ship.

### Composition patterns

- **Small multiples** — same chart, repeated, with one variable changing. Lets the eye compare without re-anchoring. Reach for this whenever you'd otherwise build a complex multi-series single chart.
- **Linked displays / brushing** — selecting in one view highlights the corresponding marks in every other view. D3's strength. Perfect for exploratory dashboards, OSEC phase explorers, and any "facets that share a record set" interface.
- **Semantic zoom** — representation *changes* by zoom level, not just scale. Overview shows aggregate; mid zoom shows clusters; deep zoom shows individual records. Different from optical zoom. Pairs with linked displays for the OSEC sector explorer pattern.

### Per-chart rules (universal)

- **Titles assert findings.** The chart title states the insight, not the axis description. "Revenue Surged 23% in Q3" — not "Revenue by Quarter, 2024". The subtitle adds context ("vs. prior year, USD millions"). If the data has no clear finding, the chart may not be needed (see the next rule).
- **Compared to what?** Every chart includes at least one reference element — a baseline line, target band, prior-period series, or peer group. A solitary line with no comparison fails the "compared to what?" test and should be rebuilt with context.
- **Don't chart what a sentence can say.** 1–2 numbers → write a sentence with inline context ("Revenue was $4.2M, up 23% from Q2"). A simple ranking of 3–5 items → consider a table. Charts earn their space by revealing patterns, trends, or distributions that prose and tables cannot. A chart of two bars is almost always worse than a sentence.

These rules distill the Tufte/Bertin/Gestalt/CRAP framing. For 22-rule chart-library guidance (Recharts/ECharts/Chart.js/Plotly/D3), see [`channels/charts.md`](channels/charts.md). For matplotlib + paper figures, [`channels/science.md`](channels/science.md).

## Interaction design grounding

When building interactive demos or UI affordances around the visuals, the design choices have empirical anchors:

- **Fitts's Law** — pointing time = `a + b·log₂(D/W + 1)`. Big targets close to the cursor are fast; small targets far away are slow. Implication: primary controls go large and near the user's current attention point. Fisheye expansion is Fitts's Law made visible.
- **Hick's Law** — choice time = `a + b·log₂(n + 1)`. Decision time grows logarithmically with options. Implication: collapse n>7 options into hierarchy or progressive disclosure.
- **Fisheye menus** — focus+context lens that expands the item under the cursor while compressing peripheral items (the user's own MS Human Factors thesis, Clemson). The trick: each item gets a *guaranteed minimum size* below the lens floor so distant items remain clickable, not just visible.
- **Marginalia callouts** — typographic affordances (pull quotes, asides, margin notes) are the editorial equivalent of fisheye: they create a visual hierarchy that lets the eye sample without losing the through-line.
- **Cortical magnification & foveation** — the retinal-side reason fisheye works at all. Inside the Math is the canonical explainer; reference it when explaining *why* focus+context isn't a UI gimmick.
- **"It is impossible to separate the visual design from the design of the interface."** — David Small, [*Navigating Large Bodies of Text*](https://smg.media.mit.edu/library/small1996.html) (IBM Systems Journal, 1996). Visual grammar and interaction grammar are the same grammar. Every choice about how text renders is a choice about how people navigate it — and vice versa. See [`vocabularies/visible-language.md`](vocabularies/visible-language.md) for the full MIT Media Lab lineage this is drawn from.

Use these as design rationale in figure captions and blog posts — the vocabulary is precise, the laws are quantified, and the lineage runs from psychophysics through typography to interaction design.

---

## Shipping a social card — validation pass

Exporting the PNG isn't shipping it. Cards live or die in the platforms' preview crawlers, which cache aggressively and silently. After every social-card export — OG, X/Twitter, LinkedIn, GitHub repo preview — run the validators before declaring done:

- **LinkedIn:** [Post Inspector](https://www.linkedin.com/post-inspector/) — paste the public URL where the card is referenced. Force-refreshes the LinkedIn cache on each request, so it's the cheapest re-check.
- **X / Twitter:** paste the URL into a draft tweet/post (most reliable). The classic [Twitter Card Validator](https://cards-dev.twitter.com/validator) has been intermittently retired; treat it as best-effort.
- **Facebook / Meta / WhatsApp / Slack / iMessage:** [Sharing Debugger](https://developers.facebook.com/tools/debug/) covers Facebook + Messenger. Slack/iMessage unfurl from OG meta directly — if Facebook resolves correctly, those usually do too. Re-scrape via the debugger to bust cache.
- **GitHub repo "Social preview":** committing `assets/og.png` does **not** attach it. The image must be uploaded via repo *Settings → General → Social preview → Edit*. Filesystem assets are decoration only; the live preview is a separate uploaded blob.

Common failure modes the validators catch:
- Stale cache showing the previous card — re-scrape via each tool to invalidate.
- Wrong dimensions cropped (1200×630 OG vs 1200×675 X — different aspect ratios; X crops OG-shaped images).
- Missing/incorrect `<meta property="og:image" content="…">` absolute URL (must be absolute, not relative).
- Mixed-content blocks (HTTP image referenced from an HTTPS page).
- Image > 5 MB triggers fallback on some platforms; recompress if so.

---

## When to use

Whenever the user needs a visual artifact for human eyes — store assets, paper figures, blog post explainers, video demos, terminal output, scientific plots, infographics, screenshots, gaze visualizations. Invoke with `/muriel` followed by what's needed.

## Channel reference map

When the task lands in a specific channel, read the corresponding subfile *first* before executing:

| If the task is… | Read |
|---|---|
| App store assets, icons, banners, wordmarks, Pillow compositing | `channels/raster.md` |
| Paper figures, data-driven diagrams, SVG theming, Mermaid, Excalidraw | `channels/svg.md` |
| Blog posts, marginalia pages, pandoc → HTML/PDF, web capture, data-URI | `channels/web.md` |
| Interactive demos, WebGL/Canvas/D3, CodePen, Observable, permalink state | `channels/interactive.md` |
| Product demo videos, ffmpeg, tooltip burn, GIF generation | `channels/video.md` |
| Unicode bar charts, sparklines, terminal output, README tables | `channels/terminal.md` |
| Tobii-style density heatmaps from fixation data | `channels/heatmaps.md` |
| Scanpath plots, AOI timelines, bubble scanpaths, saccade roses | `channels/gaze.md` |
| matplotlib figures, stats reporting, notebook editorial, LaTeX hooks | `channels/science.md` |
| "What size should this be?" — social card / device / viewport / paper / video dimensions | `channels/dimensions.md` |
| Loading a brand's design tokens, enforcing brand ownership rules, deriving CSS / rcparams from a brand | `channels/style-guides.md` |
| Social-shareable explainers, LinkedIn/X cards, README hero images, single-image infographics | `channels/infographics.md` |
| Charts in a web app or blog post (Recharts/ECharts/Chart.js/Plotly/D3), chart code review | `channels/charts.md` |
| UI polish, micro-interactions, "make it feel better", animations, hover states, border radius math, optical alignment | `channels/polish.md` |
| Sci-fi HUD aesthetic, FUI grammar, Territory/Perception lineage | `vocabularies/fui.md` |
| Surface archetypes (deck / frame / card / prototype / article / dashboard / PRD), html-anything lineage, "absolute rules per surface" pattern | `vocabularies/surfaces.md` |
| Apple HIG / Material / Carbon / Vega-Lite / Plot / FT / Datawrapper — cross-platform charting precedents | `vocabularies/data-viz-platforms.md` |
| Multi-scale typography, information landscapes, pretext, Cooper/Small lineage | `vocabularies/visible-language.md` |
| Particle-dense gaze overlays, shader filters, PixiJS v8 patterns | `vocabularies/pixijs.md` |
| Animated typography, emotional motion vocabulary, Bass/Cooper/Territory lineage | `vocabularies/kinetic-typography.md` |

For a multi-channel task (e.g., a blog post with an interactive demo captured as a paper figure), read the relevant subfiles in order of primary channel first.

---

## TODO

### Raster
- [x] **Drop shadow with blur** — Implemented via `ImageFilter.GaussianBlur` in `render_text()` shadow effect.
- [x] **Template system** — `ascii-charts/typeset.py` ships `amazon-icon`, `amazon-small-icon`, `tvos-topshelf`, `play-feature` templates via `render_asset(template=...)`.
- [x] **Batch from JSON** — `generate_from_manifest("assets.json")` in `typeset.py`.
- [ ] **Multi-line text layout** — Auto-wrap long text with configurable max-width, line-height, and alignment.
- [ ] **Curved/arc text** — Text along a circular path for badges, seals, and circular icon borders.
- [ ] **Gradient text fill** — Linear/radial gradient fills inside letterforms.
- [ ] **Screenshot compositing** — Place device-framed app screenshots into promotional images. See expanded roadmap below.
- [ ] **Brand color extraction** — Auto-extract dominant colors from a background image.

#### Screenshot designer features — roadmap

> The screenshot-beautifier category (Pika, Shots.so, CleanShot X, Screely, BrandBird, Canva screenshot editor, Screen Studio, Rotato, Previewed, Mockdrop, Screenshot.rocks, BrowserFrame, Figma mockup plugins) has converged on a fairly standard feature set. Port the useful ones into muriel's raster channel as opinionated presets. We're stealing the feature menu, not the products.

**P0 — table stakes (ship first):**
- [ ] **`drop_shadow(offset, blur, color, spread)`** — multi-layer ambient + key shadows, Material-3 style. Existing `render_text()` shadow handles text only; this is for composited screenshots/images.
- [ ] **`fade_edge(side, ramp_px, curve="linear"|"ease")`** — progressive alpha ramp on any side (top/right/bottom/left) or radial. Andy's seed feature; rare as a preset outside Pika + Screen Studio.
- [ ] **`border_radius(r)`** — rounded corners on the screenshot/image before compositing.
- [ ] **`background(kind, …)`** — unified API with kinds: `solid`, `linear_gradient`, `radial_gradient`, `mesh_gradient` (3–5 color blobs), `image_blur`, `noise_overlay`, `transparent`.
- [ ] **`caption(text, position, style_token)`** — bound to brand tokens; enforces 8:1 contrast at render time, not as lint pass.
- [ ] **App Store + social dimension presets** — named constants already in [`channels/dimensions.md`](channels/dimensions.md); confirm coverage: `IPHONE_69_PORTRAIT` 1290×2796, `IPAD_13_PORTRAIT` 2064×2752, `OG_IMAGE` 1200×630, `X_CARD` 1200×675, `IG_SQUARE` 1080×1080, `IG_STORY` 1080×1920, `PRODUCT_HUNT` 1270×760.

**P1 — distinctive, low effort:**
- [ ] **`tilt(angle_deg, axis)`** — 2D affine shear (cheap fake-3D). Real perspective later.
- [ ] **`device_frame(kind)`** — PNG overlay library. Minimum kit: `iphone_15_pro_dynamic_island`, `macbook_pro`, `browser_chrome_light`, `browser_chrome_dark`, `browser_safari_mac`, `ipad`.
- [ ] **`browser_url_bar(url, title)`** — editable text rendered into the chrome asset (the URL is half the joke).
- [ ] **`spotlight(x, y, radius, falloff)`** — radial bright spot for "look here" emphasis.
- [ ] **`vignette(strength, shape="oval"|"rect")`** — classic framing effect.
- [ ] **`noise(amount)`** — post-filter; fights banding on gradients.
- [ ] **`glow(color, blur, intensity)`** — outer glow (Psychodeli audio-reactive aesthetic).

**P2 — differentiators:**
- [ ] **`glass_panel(rect, blur, tint)`** — frosted backdrop card behind device (2023–2026 aesthetic).
- [ ] **`numbered_callout(x, y, n, leader_to=(x,y))`** — step markers 1…n with leader line (BrandBird / CleanShot).
- [ ] **`reflection(height_frac, opacity)`** — iPod-style mirror under device.
- [ ] **`bento_grid(cells)`** — template compositor for N screenshots + brand palette (Pika).
- [ ] **`glass_reflection_overlay(asset)`** — pre-baked highlight PNG multiplied over screen for fake HDRI (Rotato lite).
- [ ] **`auto_blur_regions(detector)`** — heuristic blur for emails/tokens in debug captures. Scrutinizer-relevant when publishing validation screenshots.
- [ ] **`magnifier(x, y, radius, zoom)`** — BrandBird's "Highlight Product Feature" tool. Circular zoom-in lens on a specific UI region.
- [ ] **`annotation(arrow|rect|circle|emoji, x, y, …)`** — BrandBird/CleanShot annotation primitives.

**P3 — out of channel (skip or defer elsewhere):**
- Animated MP4 / GIF export → [`channels/video.md`](channels/video.md).
- Ray-traced 3D device renders → pre-render pipeline; muriel just ships the baked PNGs.
- Scene compositing (flat-lay, in-hand) → defer; not on brand for Scrutinizer/Psychodeli.
- AI screenshot editing (Magic Edit / Magic Grab / Magic Eraser from Canva; Uizard Screenshot Scanner reverse-engineering to mockups) → different skill; muriel is deterministic.

### SVG
- [ ] **Gaze ribbon primitive** — `typeset.svg.gaze_ribbon(fixations)` reusable across AdSERP / RecGaze work.
- [ ] **F-pattern overlay primitive** — Colored band generator from phase-segmented gaze data.
- [ ] **OSEC phase diagram primitive** — Multi-band horizontal timeline.
- [ ] **Excalidraw → clean-export pipeline** — Batch re-export with `roughness:0`, Helvetica, solid fills.
- [ ] **Mermaid CLI wrapper** — Themed output matching marginalia `--mg-*` palette.

### Interactive JS
- [ ] **Extract shared `permalink.js`** — Pull the PermalinkManager pattern out of Scrutinizer/Psychodeli for demos outside those repos.
- [ ] **Demo loader snippet for marginalia** — `<mg-demo src="...">` custom element that lazy-loads an iframe.
- [ ] **Single-file demo bundler** — Inline CSS/JS/images as data URIs to produce a standalone `.html`.

### Web rendering & static capture
- [x] **Responsive viewport-sweep capture** — Shipped as `muriel/capture.py`. `capture_responsive(url, tiers=..., output_dir=...)` writes retina PNGs for every tier in one call. CLI: `python -m muriel.capture <url>`. Playwright optional dependency.
- [ ] **Small-multiples capture script** — Loop a demo across parameter values via URL hash, screenshot each, assemble into a grid. (Related to `capture.py` but captures *parameter* sweeps, not *viewport* sweeps.)
- [ ] **Marginalia + weasyprint paper template** — `@page` rules for A4 + letter, figure captions, bibliography.
- [ ] **Playwright device-frame compositor** — Replace manual Photoshop mockups with real HTML-rendered device frames.

### Pandoc + marginalia
- [x] **`marginalia/pandoc/marginalia.lua` filter** — Shipped as commit 4c66c16 on the marginalia repo.
- [x] **`marginalia/pandoc/template.html`** — Shipped alongside filter.
- [x] **US Constitution example** — Shipped at `marginalia/pandoc/examples/us-constitution.md`.
- [ ] **Markdown → PDF via marginalia + weasyprint** — End-to-end pipeline for paper drafts with marginalia styling preserved.

### Science
- [x] **`channels/science.md` subsection** — rcparams defaults, stats reporting, notebook editorial, LaTeX hooks, worked recipes.
- [x] **`muriel/matplotlibrc_dark.py` + `_light.py`** — Both rcparams blocks shipped as importable modules with graceful fallback when matplotlib is absent. Light variant matches the F explainer warm editorial palette.
- [x] **Statistical reporting helpers** — `muriel/stats.py` ships `format_comparison`, `format_null`, `format_correlation`, `format_auc`, `format_chi2`, `format_exploratory`, `cohens_d`, `cohens_d_paired`, `fisher_ci`, `apa_number`, `format_p`, `format_ci`. Standard library only. Enforces U+2212 minus signs, APA leading-zero stripping, detection-limit phrasing for nulls.
- [x] **`muriel/contrast.py` WCAG audit** — Standard-library-only module with `contrast_ratio`, `check_text_pair`, `audit_svg`, `audit_html`, and a `python -m muriel.contrast <file.svg|file.html>` CLI (exit 0 / 1 / 2 / 3 for CI use). Classifies CSS selectors as text / decorative / ambiguous via substring hints. HTML mode walks `<style>` blocks plus inline `style="…"` attributes, resolves `var(--token)` chains, and runs the legibility-floor pass alongside contrast. Used for the 8:1 compliance audit that caught three failing text roles in word-fingerprints, four failing tokens in marginalia's light theme, and the text-muted/accent/TOC failures on the F-explainer AI Lab restyling pass.
- [x] **`muriel/dimensions.py` screen-size constants** — `Size` / `Device` / `PaperSize` NamedTuples with aspect labels and scale methods. 34 dotted-name registry entries (social cards, video, viewports), 17 device footprints with physical + CSS + scale factor, 5 paper sizes with DPI-aware pixel conversion, `figsize_for()` helper for 7 academic venues (CHI/ACM/IUI/IEEE/PNAS/Nature/LNCS), CLI self-test. Paired with `channels/dimensions.md`.
- [ ] **Figure caption template tool** — Generate caption skeletons from a figure spec dict.
- [ ] **Pre-registration boilerplate generator** — Common methods-section templates with fill-in slots.
- [x] **`muriel/contrast.py` HTML audit + legibility pass** — Added `audit_html()` and dispatched the CLI on file extension. Parses `<style>` blocks (skipping `@media` / `@keyframes` / `@supports`), resolves `var(--name)` chains, walks inline `style="…"` attributes with per-color deduplication, auto-detects `body { background }`. Legibility-floor pass runs on both SVG and HTML: `font-size ≤ 14px` with weight `< 500` warns "sub-floor"; `opacity` on any text-color rule warns "opacity erodes contrast"; `font-size ≤ 16px` on footer/byline/caption/figcaption selectors warns "below 16px caption floor". Status now has four tiers — PASS / WARN (below required but ≥ WCAG-AA) / FAIL (below AA) / SKIP (decorative). Fixes the silent-PASS bug on HTML files and on SVG `<text fill="…">` attributes via the same inline-walker pattern.
- [ ] **`muriel/contrast.py` SVG inline-fill attributes** — `audit_html` already walks inline `style="…"`, but standalone SVG files with `<text fill="#aaa">` attributes (no `<style>` block) still slip through. Port the inline-style walker to `audit_svg` so the original silent-PASS bug (`docs/v1-orientation-columns.svg`, 2026-04-26) is also closed.
- [ ] **`muriel/contrast.py` marginalia-token audit** — Add a `audit_marginalia_tokens()` helper that reads `marginalia.css` and verifies every `--mg-*` custom property against both theme backgrounds.

### Web (editorial variant)
- [x] **Light editorial palette documented** — `channels/web.md` now has a section on the F-explainer pattern, with the `.outer-note` / `.stats-detail` / `.has-dropcap` / staged-h2 extensions catalogued.
- [ ] **Generalize `.outer-note` and `.stats-detail` back into marginalia** — Currently F-explainer-only; worth promoting to the main library if a second project adopts them.
- [ ] **Build-script variant of the pandoc bridge** — Node script using `marginalia-md.js` for projects that prefer browser-side conversion over pandoc.

### Video
- [x] **`channels/video.md`** — Recordly + desktop-control + ffmpeg + `burn-tooltips.sh` recipes shipped.
- [x] **hyperframes integration** — HeyGen's Apache-2.0 HTML → MP4 tool wired into the video channel. Installed via `npx skills add heygen-com/hyperframes -y -g` — registers `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/website-to-hyperframes`, `/gsap` as slash commands. Documented in [`channels/video.md`](channels/video.md) with pick-the-substrate-by-source-of-truth decision table.
- [ ] **Scrutinizer release-video prototype** — port `scrutinizer-www/src/blog/drafts/video-script-v2.6.md` and `video-script-minecraft-fast-demo.md` into hyperframes compositions. First proof that the HTML → MP4 path works for Scrutinizer release announcements. Bonus: the scripts already have precise timecodes + tooltip text.
- [ ] **`scrutinizer.app` → promo video** — invoke `/website-to-hyperframes` against scrutinizer.app and produce a 30–60s promo. Benchmark auto-generated quality vs hand-authored compositions.
- [ ] **PixiJS Frame Adapter** — bring muriel's PixiJS vocabulary (shader-driven gaze overlays, audio-reactive visuals) into hyperframes as a custom renderer. Unlocks Scrutinizer/Psychodeli WebGL demos as composable video blocks.

### Upstream ports — K-Dense scientific-agent-skills

> [K-Dense AI's `scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) is an MIT-licensed family of research skills. Several overlap muriel's territory enough to borrow structure, templates, or tooling from. These are ports / adaptations, not wholesale adoption — muriel has its own brand rules and palette commitments.

- [x] **Infographics type × style matrix** — Shipped as [`channels/infographics.md`](channels/infographics.md). 10 types × layout patterns × 8:1-strict rubric, Wong/IBM/Tol colorblind-safe palettes named. Deterministic SVG (not AI image generation) — muriel's lane. K-Dense's AI pipeline explicitly not adopted. First exemplar: Scrutinizer foveation explainer at `scrutinizer-www/src/img/explainers/foveation.{svg,png,py}` — portrait 1080×1920, Anatomical + Statistical + Comparison hybrid, passes `muriel/contrast.py` at 8:1 across all 9 text roles.
- [ ] **Market-research long-form PDF channel** — New `channels/market-research.md`. 50+ page templated report: Front matter (5pp) → Core analysis (35pp: market definition, TAM/SAM/SOM sizing, PESTLE, Porter's Five Forces, segmentation, technology trends, regulatory, risk) → Strategic section (10pp: recommendations, roadmap, financials) → Back matter (5pp). LaTeX + `market_research.sty` or weasyprint+marginalia. 5–6 core visuals minimum at 300 DPI. Directly relevant to PM work (Quora/Poe, future roles). Source: [K-Dense market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/market-research-reports/SKILL.md).
- [ ] **PPTX visual-QA pipeline** — New `channels/pptx.md`. Swipe the infrastructure (not the rigid templates): `pptxgenjs` (JS, muriel-native) for generation → LibreOffice `soffice` for PDF conversion → `pdftoppm` for per-slide PNG → Pillow thumbnail grid for visual inspection. This is the real gold: the generate → render → inspect → fix loop. Include K-Dense's 10 palettes + font pairings + the "no accent lines under titles" AI-tell heuristic as brand defaults. Skip K-Dense's fixed templates — they converge to sameness, which fights muriel's multi-constraint-solver ethos. Source: [K-Dense pptx](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/pptx/SKILL.md).
- [ ] **Colorblind-safe palette commitment** — Wong, IBM, Tol as named palettes in `channels/style-guides.md` alongside the OLED/editorial palettes. Ship as importable constants in `muriel/palettes.py` (or extend `muriel/matplotlibrc_*.py` with `CATEGORICAL_WONG`, `CATEGORICAL_IBM`, `CATEGORICAL_TOL`). Cross-reference from [`channels/science.md`](channels/science.md) color section.
- [ ] **scientific-schematics compatibility shim** — K-Dense's [literature-review](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/literature-review/SKILL.md) and hypothesis-generation skills require a [`scientific-schematics`](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/scientific-skills/scientific-schematics) skill as a mandatory dependency for figures (PRISMA diagrams, flowcharts, synthesis maps). If muriel wants to interoperate with the K-Dense workflow, expose a compatible interface (Python entry point that matches their expected call signature) that delegates to muriel's SVG + raster channels. Low-priority until a project actually needs it.
- [ ] **Markitdown → marginalia post-processor** — Separate tool (not a muriel channel). Microsoft's [`markitdown`](https://github.com/microsoft/markitdown) converts 15+ formats to markdown. K-Dense [wraps it](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/markitdown/SKILL.md) with AI image descriptions. Build a thin pipe: `markitdown file.pdf | marginalia-inject > out.md` that adds marginalia callout syntax (`.outer-note`, pull-quotes, sidenotes) to markdown output. If it proves useful, propose upstream as a markitdown plugin rather than forking.
