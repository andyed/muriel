# Changelog

All notable changes to muriel are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
version numbers follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **`channels/readme.md` — repo front pages on a renderer you don't control.**
  A README is a visual artifact rendered by a hostile, non-configurable
  renderer, read once, at a glance, by someone deciding whether to close the
  tab — and until now no channel owned it. Documents the GitHub sanitizer
  contract (what survives, what is stripped silently, and six gotchas
  including that the README's first screenful is not the *page's* first
  screenful, and that "dark mode" is five themes so a baked page background
  bands against dark dimmed). Ships a badge budget with an 8:1 floor on both
  theme families, `<picture>` theme pairing, and a running-text-as-image
  prohibition that keeps wordmarks legal and link text illegal. The channel's
  distinguishing move is that the artifact is renderable: `muriel capture` the
  live repo page, `muriel squint` the result, and the hierarchy claim becomes
  testable rather than arguable. Structural AI-tell rules are spec'd in the
  doc and queued into `muriel.aiism`. Renderer-contract observations credited
  to [aza-ali/github-readme-crisp-links](https://github.com/aza-ali/github-readme-crisp-links)
  (MIT); its headline technique — link text as gradient SVG wordmarks — is
  explicitly not adopted.

- **`muriel.patterns.wavefield()`** — clean-room, zero-dependency layered SVG
  contours with two explicit modes: seeded harmonic synthesis for reproducible
  visual structure, and caller-supplied normalized series for semantic signal
  geometry. Returns frozen, inspectable layers with values, points, baselines,
  and open/closed cubic paths; emits viewBox-first SVG with `<title>`/`<desc>`,
  CSS-token fallbacks, and line-art support. Three generated proof artifacts
  cover a decorative divider, an illustrative signal, and illustrative
  uncertainty slices. Inspired by and credited to
  [anup-a/svgwave](https://github.com/anup-a/svgwave), with no upstream code or
  assets incorporated because its repository license prohibits modification
  and commercial use despite an ISC label in `package.json`.

## [0.14.0] — 2026-08-07

**A second body, and a broken mount.** Two things ship. The urgent one first: **if you installed muriel from a checkout, your install is probably broken and looks fine.** `install.sh` only ever *added* mounts, and its existence check was true for a dangling symlink and true for a stale directory alike — so a mount that pointed at a pre-migration path reported "already exists, leaving alone" indefinitely. Observed on the author's own machine: no muriel subagent resolved at all, and every deep reference `SKILL.md` links was unreachable from the installed skill. Re-run `./install.sh`; it now reports what is wrong and `--repair` fixes it without deleting anything. The feature: muriel gains a **design jury** — five seats with different loss functions and different evidence access, a split between defect finding and direction selection, and a ledger that scores each seat against what happened next. Long-form notes: [`releases/v0.14.0.md`](releases/v0.14.0.md).

### Added

- **`references/jury.md` — how to run a jury.** muriel had one critic playing juror, chair, and bailiff at once, and no ranking apparatus at all: Compare mode could produce N directions with nothing able to choose between them. The jury splits that into **two bodies with two aggregation rules**. Defect finding takes the union at max severity — asymmetric loss, since a false positive costs one wasted fix and a false negative ships. Direction selection uses comparative judgement with splits **reported rather than averaged**, because where the panel splits *is* the unsettled design decision, which is muriel's whole remit. Deterministic checks (`muriel.contrast`, `muriel.devibe`, the impeccable pre-scan) enter as stipulated facts; no seat may vote a measured contrast failure down to "fine, it's decorative."
- **Five jury seats, all shipping as subagents.** Seat diversity comes from loss function and evidence access, not persona — N copies of one critic share priors and produce correlated errors. `muriel-squinter` (hierarchy under blur), `muriel-thumbnail` (signal at 1/8 and 16 px), `muriel-stranger` (premise legibility, brief withheld), `muriel-forger` (distinguishability from generic output), `muriel-pedant` (labels, units, numeric claims). Each emits a sealed ballot with per-seat randomized option order; none casts a verdict.
- **`muriel.squint` — the blur ladder and thumbnail companions.** Derives sigma from a *measured* half-survival constant — a feature of width `d` retains half its contrast at `d ≈ 2.1σ`, re-measured on every test run — rather than a fixed pixel radius, so the check behaves the same on a 400 px sprite and a 3000 px poster. Emits `light`/`medium`/`heavy`/`luma` for the Squinter and `eighth`/`px16`/`px16_zoom` for the Thumbnail. `python -m muriel squint <image>`.
- **The ledger.** Every finding emits a `muriel.jury.finding` record scored `hit`/`miss`/`noise`/`open` against what happened next, so "worst critic wins" becomes principled rather than merely loud: a seat running high noise gets its severities discounted automatically. `precision = hit/(hit+noise)` deliberately excludes `miss` — weighing "the human dismissed it" as slop would mechanically silence the Stranger, whose entire job is a finding teams dismiss.

### Fixed

- **`install.sh` mounts could not self-heal, and silently didn't.** Both mounts are now **one directory symlink each** — the only shape that cannot rot, since a new channel, reference, or seat then appears in the live install the moment it lands in the checkout. Claude Code scans `~/.claude/agents/` recursively and identifies a subagent by its `name:` frontmatter rather than its path, so a single `~/.claude/agents/muriel` mount registers every seat including ones added later. The script now verifies *where* a mount points instead of that something is there: symlinks it owns are repointed automatically, a legacy per-item directory is reported and left alone until `--repair` moves it to `muriel.bak-<timestamp>`. Nothing is deleted. Legacy per-file agent links are retired only when they resolve into the checkout.
- **`muriel.squint` skipped the matte on palettized PNGs.** The alpha check missed mode `P` with a `tRNS` chunk, so transparent pixels resolved to an arbitrary palette entry while the result recorded a matte that was never applied — deciding figure/ground, which is exactly what the tool measures, by palette index. Small UI exports are commonly mode `P`.

## [0.13.0] — 2026-06-27

**The 8:1 floor turns outward.** v0.12.0 hardened muriel's universal 8:1 contrast floor *inward*; this release is the floor reaching *outward* and gaining maturity. It now (1) **re-gates an external corpus** — the `ui-ux-pro-max` colour sets target WCAG 3:1/AA, so `muriel.uipromax` measures every one against the 8:1 floor instead of trusting the source; (2) **gets code-aware** — `muriel.devibe` masks `<pre>`/`<code>`/comment content so a page *documenting* AI-design tells (muriel's own docs) isn't false-flagged for having them; and (3) **gains its first principled exception** — `muriel.contrast` now exempts logotypes/wordmarks per WCAG 1.4.3, because a brand glyph is a recognizable *shape*, not running text. Alongside: a DTCG token importer, the motion duration-binary + easing/scale axes, contrast auditing for HTML (not just SVG), `aiism` per-rule suppression, composition rules folded into `channels/polish.md`, and a Mermaid zoom/pan/expand shell for `channels/diagrams.md`. Long-form notes: [`releases/v0.13.0.md`](releases/v0.13.0.md).

### Added

- **`muriel.uipromax` — the `ui-ux-pro-max` corpus, re-gated to 8:1.** Vendors seven CSV reference tables (colors, typography, ui-reasoning, ux-guidelines, styles, charts, icons) verbatim under MIT, plus an accessor layer that re-measures the corpus's WCAG-3:1/AA colour sets against muriel's universal 8:1 floor via `muriel.contrast`. `palettes.uipromax_brand_palettes` and `critique.uipromax_anti_patterns` surface it; `muriel uipromax` browses and audits it. The data is unchanged — muriel adds no colours; muriel's contribution is the accessor + the 8:1 re-gate. Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) via [All-The-Vibes/ATV-Design](https://github.com/All-The-Vibes/ATV-Design) (both MIT). Attribution wired into `pyproject` and `THIRD_PARTY_NOTICES.md`.
- **`muriel.devibe` — code-aware AI-design-tell scanner.** A scanner for the visual signatures of AI-default design, made *code-aware*: it masks `<pre>`/`<code>`/HTML-comment content so a site that documents the tells (like muriel's own MkDocs docs) isn't flagged for naming them. Landed early as commit `6480774` to unblock the docs build.
- **`muriel.contrast` HTML audit.** `audit_html()` parses `<style>` blocks (skipping `@media`/`@keyframes`/`@supports`), resolves `var(--name)` chains, walks inline `style="…"` colours with per-colour dedup, and auto-detects `body { background }`. Status now has four tiers — PASS / WARN (below required but ≥ WCAG-AA) / FAIL (below AA) / SKIP (decorative). Fixes the silent-PASS bug on HTML files and on SVG `<text fill="…">` attributes.
- **`muriel.contrast` logotype exemption (WCAG 1.4.3).** A `_LOGOTYPE_HINTS` classifier tier — `.logo` / `.wordmark` / `.logotype` / `.lettermark` / `.brandmark` / `.monogram` selectors classify as decorative (`SKIP`, exempt), because a logotype is a recognizable brand *shape*, not text parsed for meaning. Checked *before* the text hints so it wins over the generic `mark` text hint that `wordmark`/`lettermark`/`brandmark` contain; a bare `<mark>` highlight still classifies as text. Mirrors the softened global rule (readable text → hard 8:1; logotypes/decorative lettering → exempt).
- **`import-tokens` — DTCG → `brand.toml`.** Convert a Design Tokens Community Group `tokens.json` into a muriel `brand.toml`, so a design team's existing token export drops straight into muriel's two-tier schema.
- **`muriel.motion` duration binary + axes.** Duration binary (utility ≤ 100 ms / cinematic ≥ 1500 ms) plus easing-by-direction, entrance-scale floor, and scale validation — `easing_for("enter"|"exit"|"move")`, `validate_scale()`, `validate_properties()`. Paraphrased from `All-The-Vibes/ATV-Design`'s `emil-design-eng-inspired` (MIT); muriel keeps its own duration binary over the source's bands.
- **`muriel.aiism` per-rule suppression + cleared-candidates list.** Suppress individual rules and record a "do not chase" list of candidates already evaluated and cleared, so re-runs don't re-litigate settled calls.
- **`channels/polish.md` composition rules (23–27).** A second altitude above the tactile rules 1–22: one focal point per view, type-scale-as-ratio, 60/30/10 distribution, a numbered surface-elevation system, and the swap/squint/signature test battery. Paraphrased from [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) (MIT) — **with its low-opacity/muted-colour hierarchy lever dropped** (it conflicts with the 8:1 floor); the same hierarchy is rebuilt on weight + size + space.
- **`channels/diagrams.md` Mermaid zoom/pan/expand shell.** A runtime `.diagram-shell` viewport for client-side-rendered Mermaid — zoom (+/−/fit/1:1), drag-pan, pinch, and expand-to-full-window — so a large flowchart isn't an unreadable thumbnail. Theme-driven by `--mg-*` tokens; controls clear 8:1; `prefers-reduced-motion` safe.

### Changed

- **`fix(spatial)`** — CSS3D cards depth-sort by camera distance, fixing draw-order overlap in the spatial exemplars + gallery.
- **`pyproject` version** 0.12.0 → 0.13.0. No channel-count change (polish and diagrams are existing channels); no breaking changes — every addition is additive.

## [0.12.0] — 2026-05-24

**Polish discipline + the surfaces concept.** Two additions from a 2026-05-24 LLM-agent-skill audit of the wider Claude-skill ecosystem. (1) A new `channels/polish.md` — fourteenth output channel — codifies the UI micro-interaction + visual-detail rules that turn an OK interface into one that feels considered. 16 numbered rules mined verbatim from `thedavidmurray/claude-make-interfaces-feel-better` (archived MIT), with muriel's 8:1 floor added as a binding gate on top. (2) A new `vocabularies/surfaces.md` names the *surfaces* concept (composed-artifact archetypes that compose channels: decks, frames, cards, prototypes, articles, PRDs, dashboards, posters) and cites `nexu-io/html-anything` as the canonical external catalog; full surface implementation queued. The Sibling-skills table in SKILL.md gains davidmurray and html-anything entries; README "Related prior art" gains four new entries from the broader audit. Long-form notes: [`RELEASE_NOTES_v0.12.0.md`](RELEASE_NOTES_v0.12.0.md).

### Added

- **`channels/polish.md` — fourteenth output channel.** UI micro-interaction + visual-detail discipline: 16 numbered rules covering concentric border radius (`outer = inner + padding`), optical alignment, shadows-over-borders, image outlines, 40×40px hit area minimum, interruptible CSS transitions vs keyframe one-shots, split-and-stagger enter animations (~100ms between semantic chunks), subtle exit animations, contextual icon animations (exact `scale 0.25→1` + `opacity 0→1` + `blur 4px→0` with `bounce: 0`), `scale(0.96)` on press (never below `0.95`), skip-animation-on-page-load, never `transition: all`, `will-change` only on compositor-friendly properties, macOS font smoothing at root, `font-variant-numeric: tabular-nums` for dynamic numbers, `text-wrap: balance` for headings + `text-wrap: pretty` for body. Mined from [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archived 2026-05); rule values preserved verbatim because they're *tuned* (not arbitrary), with muriel's 8:1 contrast floor added as a binding gate on top — polish is additive, never a contrast excuse. Channel count: 13 → 14.
- **`vocabularies/surfaces.md`** — survey of the *surfaces* concept (composed-artifact archetypes that compose muriel's channels). Cites [nexu-io/html-anything](https://github.com/nexu-io/html-anything) (Apache-2.0, 4.7k★) as the canonical external catalog — ~75 surface skills grouped into nine families (decks / frames / cards / web prototypes / articles / office docs / dashboards / posters / specialized). Patterns named for future mining: typed frontmatter shape (`category` / `scenario` / `aspect_hint` / `featured` / `recommended` / `example_source_url`), "absolute rules per surface" as enforceable gates (`deck-swiss-international`'s `border-radius: 0` everywhere, 22 locked layouts S01–S22, 4 locked themes with no hex modification), CJK-first font stacks (`Inter Tight / Inter / Noto Sans SC / JetBrains Mono`), and the "inspired by" lineage chain shipped as a frontmatter field rather than buried in prose. Full surface implementation queued — the vocabulary names the concept so it's discoverable; the implementation should follow the first concrete brief that wants a surface.
- **`vocabularies/data-viz-platforms.md`** — also surfaced into the SKILL.md vocabularies list (shipped in v0.11.0 but never added to the index). Cross-platform charting design guides (Apple HIG / Google Material 3 / IBM Carbon / Vega-Lite / Observable Plot / FT Visual Vocabulary / Datawrapper Academy) with license posture spelled out per platform. Sibling to `channels/charts.md` (which covers chart *libraries*); this vocab covers platform *guides*.

### Changed

- **`SKILL.md` channels table** gains the polish row; channel count description updated from thirteen to fourteen.
- **`SKILL.md` Sibling-skills table** gains entries for `thedavidmurray/claude-make-interfaces-feel-better` (full port to `channels/polish.md`) and `nexu-io/html-anything` (surfaces concept → `vocabularies/surfaces.md`; full implementation queued).
- **`SKILL.md` channel reference map** gains rows for polish, surfaces vocab, and data-viz-platforms vocab.
- **`SKILL.md` aesthetic-vocabularies list** gains `vocabularies/surfaces.md` and `vocabularies/data-viz-platforms.md`.
- **`README.md`** updates: channel count fifteen → sixteen, polish bullet added to channels list, `html-anything` "Related prior art" entry rewritten to reflect the actual mining (was "worth tracking", now "surveyed in `vocabularies/surfaces.md` with patterns mined"). Four additional "Related prior art" entries added from the broader 2026-05-24 audit: `anthropics/skills` (official baseline positioning), `wrsmith108/visual-prompt-coach` (validates the 4-question constraint-elicitation intake shape), `dot-Justin/teenage-engineering-ui-ux-skill` (external precedent for the "inspired-by, not cloned" curator stance), and a "Skill-discovery indices" group entry (VoltAgent / sickn33 / travisvn).
- **`TODO.md`** gains active items: implement muriel-side `surfaces/` directory starting with `deck-swiss-international` / `frame-data-chart-nyt` / `pm-spec`; CJK-first font stack i18n support; promote polish rules into `muriel.critique` gates. Existing constraint-elicitation queue item replaced with a validated-by-visual-prompt-coach entry (4-question cap confirmed independently).

## [0.11.1] — 2026-05-24

**ECharts vocabulary + aiism cross-repo sync.** Two small additions that were authored in a parallel session alongside the v0.11.0 cut: a deep [`vocabularies/echarts.md`](plugins/muriel/skills/compose/vocabularies/echarts.md) covering ECharts dashboard / dark-theme work that doesn't fit the per-library quick-reference row in `channels/charts.md`, and `scripts/extract_aiism_rules.py` — a one-shot helper that lets `science-agent` consume muriel's `*_RULES` tables in its own JSON shape without forking the rule definitions. Sibling to v0.11.0's [`vocabularies/data-viz-platforms.md`](plugins/muriel/skills/compose/vocabularies/data-viz-platforms.md): platforms vocab surveys design *guides*, ECharts vocab covers a specific *library* deeply.

### Added

- **`vocabularies/echarts.md`** (358 lines) — deep ECharts vocabulary for dashboard / interactive / dark-theme work. Candor up-front about training-data under-representation (verify against upstream docs every time); five-block dark-mode baseline `setOption` override; `markArea` two-element pair shape + `markLine` playhead sync; the series-color contract bug; HTML5 `<audio>` playhead sync gotchas; option-tree diffing; multi-axis discipline; data-shape contract; renderer choice (canvas vs SVG); heatmap + visualMap "3D projected grid" pattern; live-verification protocol. Apache-2.0 substrate, pinned to `echarts@^5.4`.
- **`channels/charts.md` ECharts row** gains a one-line pointer to the new vocab for dashboard / interactive / dark-theme work that needs more than the quick-reference row.
- **`scripts/extract_aiism_rules.py`** — one-shot helper that loads muriel's `*_RULES` tables and emits them as JSON entries compatible with `science-agent`'s `aiism-rules.json` schema, preserving any non-muriel entries already in the target file. Defaults to `~/Documents/dev/science-agent/src/aiism-rules.json`; supports `--dry-run` and `--target=<path>`. Keeps the muriel-side rule definitions canonical while letting `science-agent` consume them in its own JSON shape.

## [0.11.0] — 2026-05-24

**Sibling, not subordinate.** Three new surfaces, each a sibling of something already in muriel rather than a new top-level concern. [`muriel.spatial.ridgemap`](muriel/spatial.py) is a sibling primitive to `grid()` — same module, same conventions, same brand floor — that scaffolds *scalar fields* the way `grid()` scaffolds *space*. The new [`.agents/skills/muriel`](.agents/skills/) broadcast symlink is a sibling install path to `.claude/skills/`, read natively by Codex CLI and as an alternate by Cursor / Gemini CLI / GitHub Copilot / OpenCode / Pi — one symlink, six harnesses. [`muriel.tools.impeccable_bridge`](muriel/tools/impeccable_bridge.py) wraps pbakaus/impeccable's 27-rule deterministic detector as an *optional* pre-scan for `muriel-critique`; it stays silent when Node / impeccable / network are missing, so the critique agent works identically with or without it. None of the three is a dependency; each is a peer. Long-form notes: [`RELEASE_NOTES_v0.11.0.md`](RELEASE_NOTES_v0.11.0.md).

### Added
- **`muriel.spatial.ridgemap(field, canvas, …)`** — stacked 1D slices of a 2D scalar field. Joy Division *Unknown Pleasures* / Harold Craft 1970 PSR B1919+21 lineage; sibling primitive to `grid()`. Zero-dep, duck-types numpy ndarray, brand defaults clear the 8:1 floor, occlusion fill on by default with `fill=None` for line-art mode. `python -m muriel.spatial --ridgemap` renders a deterministic pulsar-style demo.
- **`.agents/skills/muriel` broadcast symlink** — one symlink pointing to the canonical `plugins/muriel/skills/compose/` directory. Read natively by Codex CLI and as an alternate path by Cursor, Gemini CLI, GitHub Copilot, OpenCode, and Pi. Per-harness verification still TBD; rollout plan in [`HARNESSES.md`](HARNESSES.md).
- **`muriel.tools.impeccable_bridge`** — optional Python wrapper around `npx impeccable detect <target>` (pbakaus/impeccable's 27-rule deterministic anti-pattern detector, regex + Puppeteer, no LLM). Defensive JSON-shape normalisation; `format_markdown(result)` returns `""` when unavailable so callers paste it unconditionally and the section silently disappears.
- **`HARNESSES.md`** — top-level plan for cross-harness packaging across eleven AI agent harnesses (Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub Copilot, Kiro, OpenCode, Pi, Qoder, Rovo Dev, Trae). Mirrors [pbakaus/impeccable](https://github.com/pbakaus/impeccable)'s packaging matrix. P0 landed (the symlink); P1 (per-harness manifests + `./install.sh --harness`) and P2 (frontmatter universalism, marketplace submissions, critique-agent portability) queued.
- **`vocabularies/data-viz-platforms.md`** — survey of seven platform charting guides (Apple HIG, Google Material 3, IBM Carbon Charts, Vega-Lite, Observable Plot, FT Visual Vocabulary, Datawrapper Academy) with license posture spelled out for each (Apple proprietary, Material CC BY 4.0, Carbon Apache 2.0, Vega-Lite BSD-3, Plot ISC, FT MIT, Datawrapper per-page). Five-rule cross-platform consensus + divergence list. Sibling to v0.10.0's `channels/charts.md` (which covers JS chart libraries) — the vocab covers platform design *guides*, the channel covers chart *libraries*.
- **`examples/scrutinizer-ridgemap/`** — branded composition exemplar. A vesica-piscis scalar field whose row-wise ridges trace an eye outline; bottom half mirrored so the almond closes; pupil + iris core for the eyeball; rendered in Scrutinizer orange on a Blauch log-spaced concentric-ring scaffold.

### Changed
- **`muriel-critique` agent** can optionally invoke `python -m muriel.tools.impeccable_bridge` as a deterministic pre-scan on HTML / URL / project-directory artifacts. Output template grows an optional `## Deterministic pre-scan (impeccable)` section above `## Issues`; layering rule says don't re-derive pre-scan findings in `## Issues`. Silent and non-blocking when impeccable / Node are absent — the agent's primary description, workflow, and verdict rules are unchanged for the without-impeccable path.
- **README "Other AI harnesses" section** updated to reflect the landed `.agents/skills/` broadcast symlink and point at `HARNESSES.md` for verification status per harness.
- **`channels/web.md` impeccable footnote** updated to reflect impeccable Skill 3.1.1 (May 2026), its 27-rule deterministic detector, and the `muriel capture → npx impeccable detect → muriel-critique` pipeline.
- **`channels/spatial.md`** documents the ridgemap path alongside the existing perspective-grid path; queued: filled-iso-line, wireframe-protrusion, hachured-relief projections of the same scalar-field primitive.
- **`channels/science.md`** "Prior art / upstream" entry for Apple HIG — *Charting data*, cited by link + paraphrase per scholarly discipline (Apple-proprietary docs). Calls out Swift Charts' audio-graph accessibility as a distinctive contribution.

## [0.10.0] — 2026-05-19

**`muriel.aiism` rule cleanup: removed CC-BY-SA-4.0 content for commercial-use clarity.** Drops the 25 inline phrase/cluster/repeated-phrase rules that were attributed to Wikipedia "Signs of AI writing" and `ammil-industries/vale-signs-of-ai-writing` (both CC-BY-SA-4.0). Share-alike on those rules would have required any redistribution of muriel.aiism to remain CC-BY-SA-4.0, constraining commercial use of muriel and downstream consumers (science-agent, plugin shipments, etc.). Mirrors the parallel cleanup that landed in `science-agent` 0.4.0 ([commit 9574fd5](https://github.com/andyed/science-agent/commit/9574fd5)).

### Removed

- **9 significance-inflation phrases**: `phrase-testament-to`, `phrase-reminder-of`, `phrase-plays-a-role`, `phrase-underscores`, `phrase-stands-as`, `phrase-serves-as`, `phrase-rich-heritage`, `phrase-indelible-mark`, `phrase-contributes-to`.
- **4 prescriptive-narrator phrases**: `phrase-it-is-important`, `phrase-one-must`, `phrase-needless-to-say`, `phrase-worth-mentioning`.
- **4 throat-clearing temporal openers**: `phrase-recent-years`, `phrase-past-decade`, `phrase-todays-world`, `phrase-modern-era`.
- **1 anthropomorphized-research-verb**: `phrase-research-unveiled`.
- **1 sourceless-authority hedge**: `phrase-vague-attribution`.
- **4 cluster rules**: `cluster-padded-vocab`, `cluster-hedges`, `cluster-firstly-thirdly`, `cluster-significance-verbs`. `CLUSTER_RULES` is now empty.
- **2 Vale-style repeated-phrase rules**: `repeat-not-x-but-y`, `repeat-what-x-cleft`.

### Retained

- All 8 `HARD_ARTIFACT_RULES` (project-specific LLM-tooling residue detectors: `oaicite`, sandbox paths, ChatGPT URLs, knowledge-cutoff disclaimers, etc.).
- 12 project-specific `SINGLE_PHRASE_RULES`: `phrase-earn-their-keep`, `phrase-locus-of`, `phrase-unit-at-which`, `phrase-substrate-licenses`, `phrase-doing-its-share`, `phrase-observational-register`, `phrase-names-the-same-observation`, `phrase-the-hope-is-that`, `phrase-looking-into-the-corners`, `phrase-leaky-cursor-aside`, `phrase-not-just-but`, `phrase-regime`.
- 5 project-specific `REPEATED_PHRASE_RULES`: `repeat-load-bearing`, `repeat-structurally`, `repeat-materially`, `repeat-meaningfully`, `repeat-already-compound`.
- 1 `PROXIMITY_RULES` entry: `doubled-cleft`.
- All engine-level detectors (long-sentence, bold-density, em-dash-per-line).

### Migration notes

- Total rule count: 51 → 26.
- Module docstring updated to remove the CC-BY-SA-4.0 attribution claim. The remaining phrase tables are project-specific and inherit muriel's parent license.
- For users who want the Wikipedia/Vale patterns back, they're available under their original CC-BY-SA-4.0 terms at the upstream sources cited in earlier muriel versions; clone those lists directly into your own configuration if you can accept share-alike for your distribution.

## [0.9.0] — 2026-05-17

**Generate the palette, don't audit it.** Adds `muriel.palettes.generate_for_floor()` — an Adobe-Leonardo-style contrast-driven palette generator that produces 8:1-by-construction palettes against any brand background. Four theme palettes (Catppuccin Mocha + Latte, Nord Aurora + Frost) join the registry under a new "theme tier"; the terminal channel gains an animated-effects section (TerminalTextEffects); the v0.8.0 surfaces (README, SKILL.md, demo gallery) got synced, link-audited, and reorganized. README lede rewritten per independent review. Long-form notes: [`RELEASE_NOTES_v0.9.0.md`](RELEASE_NOTES_v0.9.0.md).

### Added
- **`muriel.palettes.generate_for_floor()` — contrast-floor-driven
  palette generation.** The named palettes above (Wong / IBM / Tol)
  are *audited* against the 8:1 floor after the fact. This function
  inverts the relationship: pick a background and a target contrast
  ratio, and the palette is generated *at* the floor by construction.
  Every output color is guaranteed by the algorithm — not by audit —
  to hit the floor against the chosen background.

  Lineage: [`adobe/leonardo`](https://github.com/adobe/leonardo)
  (Apache-2.0). Leonardo's core insight ported to muriel's stack:
  Python, zero external deps, routes through `muriel.oklch` (binary
  search on perceptual L for the target relative luminance, then on
  chroma for max sRGB-gamut saturation) and verifies with
  `muriel.contrast.contrast_ratio`. Direction auto-resolves to light
  on dark backgrounds and dark on light backgrounds; explicit
  `direction="light"|"dark"` available. Raises `ValueError` cleanly
  when the floor can't be reached (mid-tone bg with floor=10, etc.).
  CLI: `python -m muriel.palettes --generate --bg "#0a0a0f" --floor
  8 --n 6` prints the palette with verified contrast per color.
  Ships with `--selftest`.

  Verified output (dark bg, floor 8, n=6): all six hit 8.05–8.48:1.
  Verified output (light bg `#fafafa`, floor 8, n=6): all six hit
  8.05–9.16:1.

- **Catppuccin + Nord palettes added to `muriel.palettes`** as four
  new entries in the unified registry:
  `catppuccin_mocha` (14 accents, dark register — 14/14 clear 8:1 on
  `#0a0a0f`), `catppuccin_latte` (14 accents, light register —
  decorative-only, 0/14 clear muriel's 8:1 since they're designed
  for Latte's own `#eff1f5` base), `nord_aurora` (5 Aurora accents —
  2/5 clear 8:1 on dark), `nord_frost` (4 cool blues — 2/4 clear
  8:1 on dark). Both MIT. Both are *theme* palettes (aesthetic
  coherence + brand recognisability) versus the *data-viz* tier
  above (Wong / IBM / Tol — colorblind-tested, audited). Citations
  now honest about which colors actually clear muriel's floor, so
  agents pick the right tool: theme for fills + chrome + markers,
  data-viz for series, `generate_for_floor()` for guaranteed-8:1
  brand palettes against a specific bg. Module docstring rewritten
  to split into a two-tier framing.

- **`channels/terminal.md` — animated-effects section.** Cross-pollinates
  the terminal channel with the kinetic-typography vocabulary by
  documenting [`TerminalTextEffects`](https://github.com/ChrisBuilds/terminaltexteffects)
  (TTE, MIT, ~100 named effects). Expands the channel from static
  primitives (`bar_chart`, `sparkline`, `table`) to terminal-as-
  artifact for installer ceremonies, deploy banners, README hero
  GIFs. Anti-prescription notes when motion in static-replay contexts
  becomes decoration. Paired with a new row in
  `vocabularies/kinetic-typography.md` substrate-choices table —
  same kinetic-type rules (max contrast, strategic motion, no
  ambient noise), new runtime (ANSI cells instead of canvas).

### Changed
- **`muriel.contrast` + `muriel.oklch` module docstrings now cite
  [`color-js/color.js`](https://github.com/color-js/color.js)** (MIT,
  maintained by the CSS Color Module spec editors) as the
  spec-authoritative reference for the wider color-science ecosystem
  (APCA, non-sRGB gamuts, deltaE, every CSS Color 4 space).
  muriel's stdlib-only subset stays the path for the 8:1 enforcement
  floor; color.js is the recommended drop-down when more is needed.

## [0.8.0] — 2026-05-17

**The rigorous round-trip.** Closes loops: the design.md → brand.toml → tokens.json round-trip got honest (corpus audit + three importer fixes), got fully two-way (new DTCG exporter), and grew a new visual surface that wires into both ends (spatial perspective grids + Three.js exemplars). First release where a brand can come in from `awesome-design-md`, ship outward to any DTCG-aware downstream, and render type into felt space without leaving the toolkit. Long-form notes: [`RELEASE_NOTES_v0.8.0.md`](RELEASE_NOTES_v0.8.0.md).

### Added
- **`muriel.spatial` + `render_assets/` exemplars + `channels/spatial.md`
  — depth scaffolding for layered typography.** Closes a long-standing
  gap: muriel rendered figures and brand chrome well, but had no
  primitive for type-in-space — the Cooper VLW / Perspective Wall /
  Data Mountain lineage. Two coupled surfaces:
  - **Static side: `muriel.spatial`** — pure-Python SVG perspective
    grids. `grid("1pt"|"2pt"|"3pt"|"iso", BBox(...))` returns a
    `PerspectiveGrid` (frozen dataclass with `vanishing_points` and
    canvas-clipped `GridLine` tuples) with `.svg()` emit. Tron-style
    cyan-on-near-black defaults; Liang-Barsky line clipping;
    fade-to-horizon depth weighting on transversals;
    isometric branch for parallel axonometric. CLI: `python -m
    muriel.spatial --demo` (2×2 panel of all four modes), `--mode
    {1pt,2pt,3pt,iso}` for single mode at full canvas, `--selftest`.
  - **Interactive side: `render_assets/`** — Three.js + CSS3DRenderer
    exemplars sharing one helper lib (`_lib/spatial.js`,
    `_lib/spatial.css`). The two-renderer stack keeps WebGL grid /
    horizon / atmosphere on the GPU while DOM cards composite on top
    via CSS3D, so text stays selectable, copyable, and screen-reader
    addressable. Helpers: `createScene`, `Mountain`,
    `addFloorGrid`, `addHorizon`, `makePlane`, `FocusController`
    (click-to-focus animation), `startRenderLoop` (parallax +
    auto-orbit). Five exemplars across two brand families:
    `spatial-typography/` (Cooper VLW homage),
    `mindbendingpixels-mountain/` + `sciprogfi-agentchan-mountain/`
    (Data Mountain — Dumais et al. 2001), `perspective-wall/` +
    `sciprogfi-lux-mesh-wall/` (Mackinlay-Robertson-Card 1991). Single
    gallery page at `render_assets/index.html`.
  - **`channels/spatial.md`** — channel doc with the full lineage
    (Alberti 1435 → Dürer 1525 → Cooper VLW 1980s → Mackinlay 1991
    → Robertson 1993 → Dumais 2001 → Tron), the four-mode anti-
    prescription (when *not* to reach for perspective), palette-token
    table showing the demo defaults pass 8:1 on `#e6e4d2` × `#07070d`
    (15.42:1), and a worked example wiring the JS lib into an exemplar.
  Coordinate system is shared between the static and interactive sides
  by design — the queued `muriel.spatial.typeset_scene()` (in TODO)
  will close the loop: take a `PerspectiveGrid` plus a list of DOM
  blocks with anchor names (`("vp", "left", 3)` /
  `("grid", row, col, depth)`) and emit a runnable
  `<scene>/index.html` so a paper figure and a fly-through share their
  geometry by construction, not by hand-port.

- **`muriel.dtcg_export` + `muriel export-dtcg` — emit a brand.toml as
  W3C Design Tokens Community Group JSON.** Third leg of the muriel
  round-trip: `design.md → brand.toml → tokens.json`. With both
  halves a brand.toml pivots into the entire
  [style-dictionary](https://amzn.github.io/style-dictionary/)
  ecosystem (style-dictionary, theo, Figma tokens-studio, token-css,
  iOS / Android / Tailwind / CSS-vars pipelines downstream) without
  writing any downstream transformer.

  Maps every brand.toml v2 block onto its DTCG-canonical type group:
  `[colors]` → `color`, `[colors.aliases]` → DTCG alias tokens with
  `{color.foreground}` reference syntax, `[semantic.{state}]` →
  nested `color.semantic.{state}.{text|surface|border}`,
  `[viz.{categorical,sequential,diverging}]` → indexed
  `color.viz.{series}.{1,2,…}` (DTCG has no native array type),
  `[typography.scale.{role}]` → composite `typography` tokens with
  `fontFamily` / `fontWeight` / `fontSize` / `lineHeight` /
  `letterSpacing` fields, `[spacing]` + `[radii]` → `dimension`,
  `[motion.duration_*]` → `duration`, `[motion.easing_*]` →
  `cubicBezier` (parses both `cubic-bezier(a,b,c,d)` and CSS keywords
  `linear` / `ease` / `ease-in` / `ease-out` / `ease-in-out`),
  `[elevation]` → best-effort `shadow` parse with the raw CSS string
  preserved under `$extensions.muriel.elevation_raw`.

  Muriel-specific fields that DTCG doesn't model natively
  (`iconography`, `imagery`, `logo`, `voice`, `rules`,
  `provenance`, `a11y`, `motion.motion_preference`, typography
  `upper: true`) are preserved under `$extensions.muriel.*` so a
  future brand.toml round-trip importer can recover them.

  Pure Python — no jsonschema or DTCG validator dependency. Lazy
  `tomllib` import so the in-memory `to_dtcg(dict) → dict` mapper
  works on Python 3.10 too (file-based `export_dtcg(path)` requires
  3.11+ for stdlib `tomllib`). Ships with `DTCGError`, public
  `to_dtcg` + `export_dtcg`, comprehensive `--selftest`, and CLI
  via `muriel export-dtcg brand.toml [-o tokens.json]`. **End-to-end
  verified**: all 61 parseable awesome-design-md brands round-trip
  cleanly through `import → export` with zero failures.

### Fixed
- **`muriel.design_md_import` — three bugs surfaced by the new corpus
  audit, each lifting clean-parse rate against the 71-brand
  awesome-design-md corpus.** Before/after on the harness:
  parsed cleanly 48/71 → **61/71** (85%), parse errors 13 → **0**,
  brands with REAL bg/fg from source 6/48 → **61/61**, pass 8:1 on
  stated colours 0 → **48**, total WARNs 90 → **0**.
  - **Color-key mapping rewritten as a priority list
    (`STITCH_COLOR_PRIORITY`).** Old flat `STITCH_COLOR_TO_MURIEL`
    dict made the winner iteration-order-dependent and missed the
    most common keys in the actual corpus (`canvas` / `ink` / `body` /
    `primary`). New list is ordered — first stitch key found in
    priority order wins for each muriel role. Adds Anthropic-style
    canonical keys (`canvas`, `body`, `ink`), variants (`canvas-light`,
    `canvas-cream`, `canvas-night`, `surface-canvas-light`,
    `surface-canvas-dark`), and obvious synonyms (`bg`, `paper`,
    `text`, `text-primary`, `brand`). Fixes 42 brands that previously
    had BOTH bg and fg silently defaulted to muriel's `#0a0a0f` /
    `#e6e4d2`. Legacy flat-dict mirror retained for any external
    consumer.
  - **YAML anchor / ref detection scoped to value-start
    (`_ANCHOR_REF_RE`).** Old whole-line substring check matched
    `" *"` and `"& "` inside prose strings (Ferrari's
    `**near-black** (...)`, several others), false-positiving as
    unsupported YAML. Check moved into `_coerce_scalar` against an
    actual `^[&*]\\w[\\w-]*\\b` pattern at value-start, after quote
    stripping. Fixes ~4 parse errors.
  - **YAML block scalars (`|` / `>`) now supported via
    `_expand_block_scalars` preprocessing.** ~1/6 of corpus brands
    (Nike, NVIDIA, Ollama, opencode.ai, Renault, Replicate, Resend,
    Revolut, …) carry their brand summary as
    `description: |` followed by an indented continuation. Old parser
    bailed with "unexpected indent" on the continuation. New
    preprocessor inlines the block into a single synthetic
    `key: "..."` row with newlines round-tripped through a Private
    Use Area sentinel (U+E000 — chosen because `str.splitlines()` does
    not split on PUA codepoints, whereas U+2028 / U+2029 would).
    Handles literal (`|`) and folded (`>`) styles. Fixes ~9 parse
    errors.

### Added
- **`muriel.tools.corpus_audit` + `muriel import-corpus` — bulk-import
  a DESIGN.md corpus and report.** Runs the entire
  [awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
  corpus (71 brands incl. Stripe, Linear, Notion, Anthropic, OpenAI,
  Cohere, Webflow, Vercel, Figma, …) through
  `muriel.design_md_import.parse_design_md` and emits a per-brand
  report. Three output shapes: `--format summary` (terminal headline
  numbers + top WARN categories), `--format md` (release-blog
  markdown table — brand × bg × fg × contrast × 8:1 pass/fail), and
  `--format json` (machine-readable per-brand record for CI diff).
  Honest accounting: when the importer fills in muriel's defaults
  because the source spec lacks usable surface keys, the brand's
  bg/fg are marked `*` and contrast is reported `n/a` rather than
  pretending muriel's defaults are the brand's contrast. A
  `--fail-on {never,any-error,any-contrast-fail}` gate turns the
  harness into a CI check.
- **`muriel.design_md_import.parse_design_md(text, source=None)`.**
  Non-IO counterpart of `import_design_md` — parses a design.md
  string into the brand.toml dict shape without writing anything.
  Lets `corpus_audit` iterate 71 brands without spraying 71
  brand.toml files into the filesystem, and lets tests assert on
  parser output without temp-file scaffolding.
- **`muriel.patterns` — generative pattern primitives for backgrounds
  and texture.** Three deterministic primitives that cover the
  workhorse background surface (and unblock the queued
  `channels/raster.md` screenshot-designer `background()` arg):
  - **`dots`** — Bridson (2007) fast Poisson-disk sampling. Even visual
    density, no obvious tiling. For dot-grid meshes, scatter texture,
    particle carriers.
  - **`flow`** — value-noise vector field traced as short polyline
    streamlines, LIC-style (Cabral & Leedom 1993). For directional
    backgrounds and contour-suggestion texture.
  - **`grain`** — value-noise raster sampled at cell granularity into a
    small SVG `<pattern>` tile that repeats across the canvas. File
    size stays O(tile_cells²) regardless of canvas dimensions. For
    film-grain, paper-texture, subtle non-flat fill.

  Pure Python — no numpy, scipy, or Pillow. All randomness routes
  through `hashlib.blake2b` so same seed → byte-identical SVG across
  platforms and Python versions. Each primitive ships `bg` + `fg`
  parameters; overlay text validates against `bg` (the contrast
  anchor) through `muriel.contrast`. Ships with `DotField` /
  `FlowField` / `Grain` frozen dataclasses, `_value_noise2` /
  `_bridson` / `_trace_streamline` internals, `python -m
  muriel.patterns --demo` (1×3 panel of all three primitives),
  `--kind {dots,flow,grain}` for single-primitive render, and
  `--selftest`. Lineage: `css-doodle`, `glisp`, `curv`, `nannou`,
  `noc-book-2`.

## [0.7.1] — 2026-05-14

### Added
- **`muriel.layout` — bbox-aware annotation placement.** `place_label()`
  closes a catalogued 100%-fail-rate pattern: hand-coded inline label
  placement produced an overlap on *every* iteration of *every*
  figure-with-annotations task, and the cover-up — white-stroke halos
  behind text — was worse than the original sin (occlusion-as-priority,
  data falsified to make the label fit). The helper takes the text, its
  font size, an ordered list of candidate in-plot anchors, and an
  obstacle point-cloud (or bbox list), and returns the first
  collision-free placement. When every in-plot candidate collides it
  falls back, in order, to **safe-by-construction zones**: the nearer
  left/right margin (a label outside `plot_bbox` cannot overlap data by
  construction), then the caption. Every rejected candidate is recorded
  on the result with the reason. It never shrinks text and never emits a
  halo. Ships with `BBox` / `Anchor` / `Rejection` / `Placement`
  dataclasses, a `text_bbox()` metric estimator, `sample_polyline()` for
  densifying curves into obstacle clouds, a `Placement.svg_text()`
  emitter (stroke-free by contract), `python -m muriel.layout --demo`
  (renders the bbox-vs-geometry check as a worked SVG) and `--selftest`.
- **`vocabularies/declassified.md`.** The visual register of the
  document-not-meant-for-the-reader — FBI Vault / FOIA reading-room /
  Wikileaks / Stasi-files lineage. Six provenance values, two redaction
  grammars (gov-at-creation vs view-time censorship), exemption-code
  system, classification banners, decl stamps, case-file paratext,
  aging-as-era-distance, and a four-handed marginalia vocabulary. For
  fiction documents framed as released, worldbuilding bibles, or
  editorial pieces *about* secrecy.
- **`muriel.provenance` module + `[provenance]` brand.toml schema.**
  Records where a brand's tokens came from so a derived artifact can
  cite its source.
- **`muriel.aiism` — anti-AI-tell prose audit module.** Flags AI-tell
  vocabulary and constructions in prose; `regime` added to the loaded-
  vocabulary list.
- **`muriel.palettes` — colorblind-safe categorical palettes.** Wong /
  IBM / Tol ramps as an importable module.
- **Audience profiles for style guides.** Vocabulary becomes a brand
  parameter, so a guide can target a reader profile.
- **Typed front-matter schema across channels** (heatmaps,
  infographics, web, svg, diagrams, science, gaze) with worked
  exemplars; **`muriel-critique` channel-aware gates + P0 honesty
  probe**, codified as a CLI gate with a tools index; **diagrams**
  `engine_sectors_overlay` (Blauch isotropic-sectors cobweb) and
  `foveal_overlay` (Scrutinizer brand mark) primitives; social-card
  validation pass in the skill.
- **`vocabularies/muriel-brand.md`.** Canonical brand-identity spec for
  muriel itself — closes the irony gap of theming every other project
  from a documented brand while running on vibes for our own. Defines
  the six-bar mark with exact rect coordinates for full (with bar-6
  ascender) and inline (capped, no ascender) variants; lineage to
  Müller-Brockmann + Cooper VLW; color tokens matching
  `examples/muriel-brand.toml`; subpixel rendering floor at ~28-30px
  display width; wordmark conventions (`muriel` always lowercase,
  `built with muriel` as canonical attribution, Inter regular + semibold,
  no italic); drop-in HTML/SVG snippets for inline credit, block credit,
  and wordmark-only fallback. First production deployment of the inline
  form is the `inside_the_math` footer credit (psychodeli-webgl-port).

### Changed
- **Repackage as a Claude Code plugin.** `/plugin marketplace add andyed/muriel`
  + `/plugin install muriel@andyed-muriel` is now the canonical end-user
  install — no clone, no symlinks, `/plugin uninstall` reverses cleanly.
  `SKILL.md`, `channels/`, `vocabularies/`, `examples/` moved under
  `plugins/muriel/skills/compose/`; `agents/muriel-critique.md` moved under
  `plugins/muriel/agents/`. `.claude-plugin/marketplace.json` at repo root
  catalogs the single plugin. Cross-references inside the skill tree that
  pointed at the Python package or top-level `docs/` were rewritten to
  GitHub URLs (the plugin cache only copies the plugin root subtree, so
  `../muriel/...` no longer resolves at runtime). `install.sh` retained as
  the developer-checkout install path; symlinks now target the new
  `plugins/muriel/skills/compose/` location and the script refuses if the
  plugin install is already present, to avoid double-loading. Plugin
  invocation is namespaced `/muriel:compose`; the standalone install via
  `install.sh` continues to give the bare `/muriel`. Spec at
  [`docs/spec-plugin-packaging.md`](docs/spec-plugin-packaging.md).

## [0.7.0] — 2026-04-25

### Added
- **`vocabularies/katex.md`.** Names KaTeX as muriel's web math engine
  — MIT, CDN-clean, no bundler, pin `^0.16`. Documents the `.eq-block`
  pattern, `auto-render` configuration, color/emphasis with
  `\textcolor`, server-side rendering for stills, and integration with
  the marginalia channel and `channels/science.md` (KaTeX is for web,
  matplotlib + LaTeX is for paper). Reference exemplar: `inside_the_math`
  (psychodeli-webgl-port, shipped). Cross-referenced from `SKILL.md`'s
  vocabulary index and a new "Math — KaTeX" subsection in
  `channels/web.md`.
- **iblipper substrate role broadened.** `vocabularies/kinetic-typography.md`
  iblipper entry now covers both animated kinetic-type artifacts *and*
  single-frame social-media graphic stills where slogan-scale
  rhetorical typography is the work. Edit Message → export PNG covers
  the still path without IAP. SKILL.md vocab index updated to match.
- **`muriel import <design.md>`.** New subcommand ingests a Google
  Stitch [design.md](https://stitch.withgoogle.com/docs/design-md/)
  and produces a muriel `brand.toml`. Zero-dep: hand-rolled YAML
  frontmatter parser + TOML emitter for the subset muriel's
  brand.toml uses. Stitch colors → `[colors]` (accent /
  accent_decorative / background / foreground) plus unmapped roles
  into `[colors.named]` + `[colors.aliases]`; Stitch typography →
  `[typography.scale]` + family at body/mono/display level; Stitch
  rounded → `[radii]`; elevation/motion preserved; Stitch
  `contrast.minimum < 8.0` warns to stderr and is recorded under
  `[a11y.imported_min_contrast_ratio]` while muriel's 8.0 floor
  stays the gate; prose Components / Do's-and-Don'ts preserved as
  `[rules.imported_*]` strings. Export direction (toml → design.md)
  queued.
- **`channels/diagrams.md` + `muriel.tools.diagrams`.** Eleventh channel.
  Rhetorical-primitive diagrams as deterministic SVG. MVP ships
  `matrix(quadrants, axes, …)` (2×2 categorical decomposition) and
  `cycle(steps, …)` (3–8 step iterative process). Each generator
  writes hand-rolled SVG with brand-aware fallback to the OLED
  palette and carries an explicit *epistemic precondition* +
  *anti-prescription* in its docstring. JSON-spec CLIs at
  `python -m muriel.tools.diagrams.{matrix,cycle}`. Worked examples
  in `examples/diagrams/`. Catalog table in the channel doc names
  the queued primitives (comparison pair, funnel, stack, DAG,
  spectrum, pyramid, heat-grid).
- **FUI vocabulary expanded to peer parity.** `vocabularies/fui.md`
  now carries a substrate decision table, common-failures list,
  cross-vocabulary SDF alpha rule, and integration points across
  channels. New runnable single-file scaffold at
  `examples/fui-scaffold.html` demonstrates four primitives (data
  ticker, radial compass, Canvas waveform, staggered reveal),
  corner brackets, scan-line overlay, and `prefers-reduced-motion`
  fallback — all on the known-safe 8:1 palette and driven by
  `--mg-duration-reveal` / `--mg-ease-emphasis`. New "Sci-fi UI
  patterns" subsection in `channels/interactive.md` names the
  canonical stack and points at the scaffold.
- **`muriel-critique` agent: vision-model sharpening.** Adds a
  Visual Inventory step 0 (3–5 sentence structural describe-before-
  judge pass), a per-artifact-type workflow table (PNG/JPG → look;
  SVG → grep + rasterize; PDF → pages; HTML/animated → decline),
  honest-hedging rule on contrast (verbal floors over fake decimals
  unless computed), and two new cross-channel checks: text-rendering
  integrity (mangled glyphs, duplicated letters, Cyrillic-in-Latin)
  as `CRITICAL`, and occlusion/overlap as a layout-bug tell.
- **`muriel-critique` agent: scoped Bash for compute calls.** Agent
  now has `Bash` in its `tools` list, scoped via project
  `.claude/settings.json` (committed; `.gitignore` negated) to
  read-only invocations of `muriel.contrast`, `muriel.oklch`, and
  `cairosvg` across `python` / `python3` / `.venv/bin/python` /
  `uv run` prefixes. Lets the agent cite exact WCAG ratios on SVG
  artifacts and rasterize SVG → PNG for real visual audits instead
  of eyeballing XML.
- **`critique` extra in pyproject.toml.** New optional dependency
  group declaring `cairosvg>=2.7` for the rasterizer path. Rolled
  into the `all` convenience extra.
- **Top-level `TODO.md`** consolidating the previously-scattered
  roadmap (CHANGELOG, SKILL.md, commit messages, per-channel
  hints) into Active / Queued / Someday / Won't-do sections.

### Changed
- **Tone pass across `README.md`, `channels/interactive.md`,
  `channels/style-guides.md`, `channels/infographics.md`, and
  `vocabularies/fui.md`.** Removed "next-gen" / "highest-leverage" /
  "unlocks" softening; tightened explainer-mode openings on
  style-guides and infographics; replaced the territory-marking
  framing in infographics with direct positioning. Channel-doc
  headings remain mixed pending a later standardization pass.
- **`muriel/__init__.py` docstring** updated for the OKLCH module
  and lists eight modules (was seven).
- **Unused imports removed** from `muriel/contrast.py`,
  `muriel/typeset.py`, and `muriel/oklch.py` (`field`, `math`,
  `sys`, `Union` respectively).

## [0.6.0] — 2026-04-23

### Added
- **`muriel.oklch` module.** Stdlib-only OKLCH / OKLab conversion
  (Ottosson 2020 / CSS Color Module Level 4), CSS `oklch()` parser
  covering the full CSS 4 grammar (percentages, angle units, `none`,
  legacy commas, alpha tolerated-and-discarded), sRGB gamut check, and
  chroma-bisection clamp that preserves L and h. Roundtrip is
  bit-exact on sRGB integer channels; primaries match Ottosson's
  reference values to four decimals.
- **`contrast.parse_color` accepts `oklch(...)`.** Every existing
  contrast helper — `contrast_ratio`, `check_text_pair`, `audit_svg`
  — now accepts OKLCH inputs transparently via a lazy import.
  Out-of-gamut OKLCH is auto-clamped so hue and lightness are
  preserved instead of hard-clipping the channel.
- **CLI.** `python -m muriel.oklch <color>` inspects any color
  (hex / `rgb()` / named / `oklch()`) and reports hex, sRGB, OKLCH,
  and gamut status; `--clamp` additionally reports the chroma-clamped
  OKLCH and ΔC for out-of-gamut OKLCH inputs.
- **`brand.toml` schema v2** covering the full design-token surface:
  `[spacing]`, `[radii]`, `[elevation]` structural ramps;
  `[typography.scale]` named type scale (display, h1–h4, body, body_small,
  caption, label, mono); `[semantic.*]` `{text, surface, border}` trios
  replacing the ad-hoc `note/tip/warning/important` fields;
  `[viz]` categorical / sequential / diverging palettes;
  `[iconography]` + `[imagery]` (with `crop_policy` hook into smartcrop);
  `[logo]` variants (wordmark / monogram / stacked / horizontal) with
  clear-space and min-width rules; `[voice]` adjectives + say-yes /
  say-no; `[a11y]` floors (`min_contrast_ratio`, `min_hit_target_px`,
  `focus_ring_*`, `motion_reduce_policy`).
- **Brand-driven contrast floor.** `StyleGuide.audit_contrast()` now
  defaults to the brand's own `a11y.min_contrast_ratio` (falls back to
  muriel's universal 8.0) instead of requiring an explicit argument.
- **CSS vars emitter expansion.** `to_css_vars()` now emits the full
  token surface: semantic-state trios, spacing / radii / elevation
  ramps, motion durations + easings, the full type scale (size / weight
  / line-height / tracking per role), and a11y hooks.

### Changed
- `examples/muriel-brand.toml` and `examples/example-brand.toml`
  rewritten against v2, each populating every optional block.
- `examples/example-brand.toml` `named` and `viz.categorical` entries
  bumped to clear muriel's 8:1 floor (`wildflowers`, `tiedye`,
  `violet`); `accent_decorative` now actually fails 8:1 to match its
  role.
- `muriel/tools/venn.py` `_region_colors` ported off the v1
  `colors.{tip,warning,important}` fields to the v2
  `viz.categorical` palette with `semantic.*` fallback.

## [0.5.0] — 2026-04-18

First public release. The project was previously named `render`; this
release formalizes the rename in honor of Muriel Cooper (1925–1994) and
consolidates the codebase.

### Added
- **Cooper tribute** in the README, placed after the opening paragraph
  before Channels. Cites Reinfurt & Wiesenberger (MIT Press, 2017) and
  David Small's *Rethinking the book* (MIT PhD, 1999).
- **Four named vocabularies** under `vocabularies/`: FUI, Visible
  Language, PixiJS, Kinetic Typography — design grammars to borrow from
  rather than reinvent.
- **PixiJS vocabulary** is a curated subset of [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) (MIT). Upstream is the source of truth.
- **Anti-patterns sections** in every channel doc — negative rules that
  complement the positive universal rules. Lifted in spirit from
  pbakaus/impeccable.
- **Two-tier brand schema.** `[colors.aliases]` block in `brand.toml`
  routes semantic roles (text, text-muted, decorative, surface-*,
  semantic-*) to raw colors. Unblocks text-accent vs decorative-accent
  distinction that was needed for light palettes.
- **Motion token block.** New `[motion]` section in `brand.toml` with
  duration (instant/fast/normal/slow/reveal) and easing tokens. Consumed
  by kinetic-typography, interactive, and video channels.
- **`muriel/examples/gallery/`** — 7 worked examples mapping shipped
  figures to muriel channels, each with a thumbnail and a live-post link.
- **`muriel/examples/logos/`** — colophon hero mark (still + animated)
  reinterpreting Cooper's mitp colophon for "muriel."
- **ascii-charts fold.** `chart.py`, `typeset.py`, `gen_og_batch.py`,
  `docs/PERMUTE.md`, and `templates/` moved into muriel. Former
  ascii-charts repo now redundant.
- **`muriel.dimensions`** — 34 named size presets, 17 device footprints,
  5 paper sizes, `figsize_for()` helper for 7 academic venues.
- **`muriel.capture`** — Playwright responsive viewport-sweep capture.
- **`muriel.styleguide`** — `brand.toml` loader with contrast audit, CSS
  variable derivation, matplotlib rcparams derivation, ownership rules.
- **`muriel.stats`** — APA-style reporting helpers enforcing
  detection-limit framing for nulls, proper minus-sign typography, and
  leading-zero stripping.
- **`muriel.contrast`** — WCAG contrast audit module + CLI with exit
  codes for CI use. Enforces muriel's 8:1 text rule.

### Changed
- Python package renamed `render_assets` → `muriel`. A deprecation
  shim at `render_assets/__init__.py` re-exports from muriel with a
  `DeprecationWarning`; existing notebooks continue to work for one
  release cycle.
- Skill directory renamed `~/.claude/skills/render/` → `~/.claude/skills/muriel/`.
- `SKILL.md` frontmatter `name: render` → `name: muriel`.
- All `~/Documents/dev/render/` paths in docs and CLI help text updated
  to `~/Documents/dev/muriel/`.

### Removed
- Personal research artifacts from the public repo. `psychodeli-brand.toml`
  and word-fingerprints SVG fixtures moved to a private sidecar skill
  (`muriel-personal`) and replaced with synthetic `example-brand.toml` /
  `example-palette.svg` fixtures that exercise the same code paths.

### Deprecated
- `render_assets` Python import path. Will be removed in 0.7.0. Update
  imports to `from muriel import ...` when convenient.
