# muriel tools index

Channel docs (`channels/*.md`) tell you *how* to make a particular kind of artifact. This index tells you what *importable Python utilities and CLI tools* muriel ships, indexed by what they do — so when you need a screen size constant, an APA-formatted *p*-value, or a contrast audit, you don't have to remember which file it's in.

Part of the [muriel](SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to read this

When you're about to reinvent something. Before writing your own contrast helper, color-conversion function, paper-figure rcparams, or critique checklist — check here first. Most of muriel's friction comes from rebuilding what already exists.

## Tools by purpose

### Color & contrast

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **WCAG contrast audit** | `from muriel.contrast import audit_svg, contrast_ratio, check_text_pair` | `python -m muriel.contrast file.svg [--required 8.0]` | Verifying every text role in an SVG passes the 8:1 floor; pre-commit hooks; CI gates. Exit codes: 0 pass / 1 fail / 2 usage. |
| **OKLCH color science** | `from muriel.oklch import to_oklch, perceptual_distance` | `python -m muriel.oklch '#5B3EB8'` | Converting hex to perceptual color space; computing perceptual distance between two colors; understanding why two near-hex colors look different to the eye. |
| **Color palettes** | `from muriel.palettes import CATEGORICAL_WONG, CATEGORICAL_IBM, CATEGORICAL_TOL` | — | When a chart needs a colorblind-safe categorical palette; when a brand hasn't shipped its own. |

### Sizes & dimensions

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Dimension registry** | `from muriel.dimensions import REGISTRY, figsize_for, Size, Device, PaperSize` | `python -m muriel.dimensions` | Picking pixel dimensions for social cards (`og-image`, `x-card`, `ig-square`), device frames (`iphone_15_pro`, `macbook_pro`), paper sizes (A4, US Letter), or matplotlib `figsize` for academic venues (CHI, ACM, IEEE, PNAS, Nature, LNCS). |

### Statistics & reporting

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **APA stats helpers** | `from muriel.stats import format_p, format_ci, format_correlation, format_auc, format_chi2, format_comparison, format_null, format_exploratory, cohens_d, cohens_d_paired, fisher_ci, apa_number` | — | Formatting *p*-values with APA leading-zero stripping; computing Cohen's *d* with proper denominator; assembling CIs in U+2212-minus form; framing nulls as detection limits. |

### Matplotlib defaults

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Editorial light rcparams** | `from muriel.matplotlibrc_light import rcparams; rcparams()` | — | Cream-background paper figures aligned with the F-explainer / AdSERP register. |
| **OLED dark rcparams** | `from muriel.matplotlibrc_dark import rcparams; rcparams()` | — | Dark-mode paper figures with the OLED palette. |

### Critique & verification

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Critique gate** | `from muriel.critique import critique_artifact, CritiqueReport` | `python -m muriel.critique path/to/figure.{svg,png,pdf} [--audience eye-tracking-researcher --channel science]` | Pre-ship verification of any rendered artifact. Runs automated checks (8:1 contrast for SVG, dimension target match, P0 honesty probe — flags stock-emoji and unattributed narrative numeric claims), reads channel front-matter ([`channels/SCHEMA.md`](channels/SCHEMA.md)) to enforce `requires.audience: required` per channel, produces a Markdown critique report with the muriel manual checklist, and exits with a status code that slots into pre-commit hooks. **The recurring `/muriel critique` pattern, codified.** |

### Generation & rendering

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Text + asset rendering (Pillow)** | `from muriel.typeset import render_text, render_asset, generate_from_manifest` | — | Pillow-based raster text rendering with shadow/blur; templated app store icons / Fire TV banners / promo cards. Templates ship for `amazon-icon`, `tvos-topshelf`, `play-feature`. |
| **Responsive web capture** | `from muriel.capture import capture_responsive` | `python -m muriel.capture <url>` | Playwright-driven viewport-sweep screenshot capture (mobile / tablet / desktop tiers). Optional dependency. |
| **Hero shot composition** | `from muriel.tools.heroshot import compose` | — | Layered hero-shot rendering with shadow, glass panel, vignette. |
| **Smart crop** | `from muriel.tools.smartcrop import crop` | — | Saliency-aware cropping for promo / thumbnail generation. |
| **Tilt-shift** | `from muriel.tools.tilt_shift import apply` | — | Apply tilt-shift focus blur to a raster image. |
| **Venn diagrams** | `from muriel.tools.venn import draw_venn2, draw_venn3` | — | Two- or three-set Venn diagrams via matplotlib_venn. |
| **Diagrams** | `from muriel.tools.diagrams import ...` | — | Generic schematic diagram primitives (flowcharts, schemas). |

### Brand & style guide

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Brand schema loader** | `from muriel.styleguide import load_brand, derive_css_tokens, derive_matplotlibrc` | — | Reading `brand.toml`; deriving CSS custom-property tokens for marginalia; deriving matplotlib rcparams from brand colors / typography. See [`channels/style-guides.md`](channels/style-guides.md). |

### Quick chart helpers

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Quick chart builders** | `from muriel.chart import bar, line, scatter` | — | Lightweight chart constructors with muriel rcparams and contrast-safe color choices baked in. |

### Diagnostics

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Doctor** | `from muriel.doctor import check_environment` | `python -m muriel.doctor` | Verifying optional dependencies (Pillow, matplotlib, Playwright, matplotlib_venn) are reachable; pre-commit setup. |
| **Warmup** | `from muriel.warmup import warm_caches` | `python -m muriel.warmup` | Pre-loading font caches, palette data, dimension registry — useful in CI to avoid cold-start cost on first render. |

## When *not* to use these

These are deterministic, reproducible primitives. If the task is:

- **AI image generation** — wrong tool. Muriel is data-driven SVG/raster, not generative.
- **Hand-drawn or freeform diagrams** — use Excalidraw / Figma; muriel is for "if the data could drive it, it should."
- **Real-time interactive demos** — see [`channels/interactive.md`](channels/interactive.md) for the WebGL / D3 / pretext substrates; the python tools above don't ship runtime interactivity.

## Adding a new tool

When a recurring pattern shows up across more than two artifacts:

1. Implement as a focused module under `muriel/` (or `muriel/tools/` for non-essential utilities).
2. Standard-library-first; optional dependencies guarded by `try/except ImportError` with a graceful skip.
3. CLI entry point via `python -m muriel.<name>` for tools where a one-off invocation is useful.
4. Add a row to this index — purpose, import, CLI, "use when."
5. If the tool changes how a channel is built, also update the relevant `channels/*.md`.

## See also

- [`SKILL.md`](SKILL.md) — top-level index, universal rules, channel map.
- [`channels/`](channels/) — format-specific recipes (raster / vector / web / interactive / video / terminal / heatmaps / gaze / science / dimensions / style-guides / infographics).
- [`vocabularies/`](vocabularies/) — aesthetic grammar references (FUI / Visible Language Workshop / PixiJS / Kinetic Typography).
