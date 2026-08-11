# muriel

Importable Python assets for the [muriel skill](../plugins/muriel/skills/compose/SKILL.md). matplotlibrc blocks, APA-style reporting helpers, WCAG contrast audit, dimension constants, capture, brand style guides, and deterministic SVG patterns — extracted from the [`channels/`](../plugins/muriel/skills/compose/channels/) subfiles so notebooks can `import` them instead of copy-pasting.

## Install

No required dependencies. Add the muriel repo to your `PYTHONPATH`:

```bash
export PYTHONPATH=/path/to/muriel:$PYTHONPATH
```

Or `pip install -e` it:

```bash
pip install -e /path/to/muriel
```

Then `from muriel import ...` works from any Python environment. The old `render_assets` import path continues to work via a deprecation shim for one release.

## Tools by purpose

A quick index of every importable utility and CLI muriel ships, so you don't rebuild a contrast helper, color-conversion, or APA formatter that already exists. The most-used modules are documented in detail below; the channel/vocabulary recipes that drive them live in the skill at [`plugins/muriel/skills/compose/`](../plugins/muriel/skills/compose/).

### Color & contrast

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **WCAG contrast audit** | `from muriel.contrast import audit_svg, contrast_ratio, check_text_pair` | `python -m muriel.contrast file.svg [--required 8.0]` | Verifying every text role in an SVG passes the 8:1 floor; pre-commit hooks; CI gates. Exit codes: 0 pass / 1 fail / 2 usage. |
| **OKLCH color science** | `from muriel.oklch import to_oklch, perceptual_distance` | `python -m muriel.oklch '#5B3EB8'` | Converting hex to perceptual color space; computing perceptual distance between two colors. |
| **Color palettes** | `from muriel.palettes import CATEGORICAL_WONG, CATEGORICAL_IBM, CATEGORICAL_TOL` | — | A chart needs a colorblind-safe categorical palette and the brand hasn't shipped its own. |

### Sizes & dimensions

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Dimension registry** | `from muriel.dimensions import REGISTRY, figsize_for, Size, Device, PaperSize` | `python -m muriel.dimensions` | Picking pixel dimensions for social cards (`og-image`, `x-card`, `ig-square`), device frames (`iphone_15_pro`, `macbook_pro`), paper sizes (A4, US Letter), or matplotlib `figsize` for academic venues (CHI, ACM, IEEE, PNAS, Nature, LNCS). |

### Statistics & reporting

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **APA stats helpers** | `from muriel.stats import format_p, format_ci, format_correlation, format_auc, format_chi2, format_comparison, format_null, format_exploratory, cohens_d, cohens_d_paired, fisher_ci, apa_number` | — | Formatting *p*-values with APA leading-zero stripping; computing Cohen's *d*; assembling CIs in U+2212-minus form; framing nulls as detection limits. |

### Matplotlib defaults

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Editorial light rcparams** | `from muriel.matplotlibrc_light import rcparams; rcparams()` | — | Cream-background paper figures for long-form explainers and light-themed posts. |
| **OLED dark rcparams** | `from muriel.matplotlibrc_dark import rcparams; rcparams()` | — | Dark-mode paper figures with the OLED palette. |

### Critique & verification

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Critique gate** | `from muriel.critique import critique_artifact, CritiqueReport` | `python -m muriel.critique path/to/figure.{svg,png,pdf} [--audience … --channel …]` | Pre-ship verification of any rendered artifact: 8:1 contrast (SVG), dimension-target match, P0 honesty probe (stock-emoji + unattributed numeric claims), per-channel audience enforcement. Exits with a CI-friendly status code. The recurring `/muriel critique` pattern, codified. |

### Generation & rendering

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Text + asset rendering (Pillow)** | `from muriel.typeset import render_text, render_asset, generate_from_manifest` | — | Pillow raster text with shadow/blur; templated app-store icons / Fire TV banners / promo cards. |
| **Responsive web capture** | `from muriel.capture import capture_responsive` | `python -m muriel.capture <url>` | Playwright viewport-sweep screenshots (mobile / tablet / desktop). Optional dependency. |
| **Hero shot composition** | `from muriel.tools.heroshot import compose` | — | Layered hero-shot rendering with shadow, glass panel, vignette. |
| **Smart crop** | `from muriel.tools.smartcrop import crop` | — | Saliency-aware cropping for promo / thumbnail generation. |
| **Tilt-shift** | `from muriel.tools.tilt_shift import apply` | — | Tilt-shift focus blur on a raster image. |
| **Venn diagrams** | `from muriel.tools.venn import draw_venn2, draw_venn3` | — | Two- or three-set Venn diagrams via matplotlib_venn. |
| **Diagrams** | `from muriel.tools.diagrams import ...` | — | Generic schematic primitives (flowcharts, schemas, layer stacks, pyramids, swimlanes). |
| **Quick chart helpers** | `from muriel.chart import bar, line, scatter` | — | Lightweight chart constructors with muriel rcparams and contrast-safe colors baked in (the Terminal-channel renderer). |

### Brand, diagnostics & maintenance

| Tool | Import | CLI | Use when |
|---|---|---|---|
| **Brand schema loader** | `from muriel.styleguide import load_brand, derive_css_tokens, derive_matplotlibrc` | — | Reading `brand.toml`; deriving CSS tokens / matplotlib rcparams from brand colors. |
| **Doctor** | `from muriel.doctor import check_environment` | `python -m muriel.doctor` | Verifying optional deps (Pillow, matplotlib, Playwright, matplotlib_venn) are reachable. |
| **Warmup** | `from muriel.warmup import warm_caches` | `python -m muriel.warmup` | Pre-loading font caches / palette data / dimension registry in CI to avoid cold-start cost. |

**When *not* to use these:** AI image generation (muriel is data-driven SVG/raster, not generative), hand-drawn/freeform diagrams (use Excalidraw / Figma), or real-time interactive demos (see the skill's `channels/interactive.md`).

## matplotlibrc_dark — OLED palette

Cream on near-black. Matches muriel's universal OLED rule. Default for blog posts on dark sites, dark-themed project figures, paper figures destined for a dark slide deck.

```python
from muriel import matplotlibrc_dark   # auto-applies on import

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
ax.set_xlabel('x (units)')
ax.set_ylabel('y (units²)')
fig.savefig('demo.pdf')
```

Scoped to one figure (no global side effect):

```python
import matplotlib.pyplot as plt
from muriel.matplotlibrc_dark import PARAMS
with plt.rc_context(PARAMS):
    fig, ax = plt.subplots()
    ...
```

## matplotlibrc_light — warm editorial palette

Matches the [Attentional Foraging F-pattern explainer](https://andyed.github.io/attentional-foraging/explainer/). Warm cream `#fafaf8` background, Georgia serif body, amber accents. Use for long-form explainers, paper drafts in light review UIs, blog posts on light-themed sites.

```python
from muriel import matplotlibrc_light
```

For journal submissions requiring pure-white backgrounds, override the cream values:

```python
from muriel.matplotlibrc_light import PARAMS, apply
PARAMS.update({
    'figure.facecolor':  'white',
    'axes.facecolor':    'white',
    'savefig.facecolor': 'white',
    'grid.color':        '#cccccc',
})
apply()
```

**Pick one palette per document.** Don't mix dark and light figures in the same paper or post.

## stats — APA-style reporting helpers

Effect sizes, confidence intervals, and phrasing helpers that enforce the rules in `channels/science.md`.

```python
from muriel.stats import (
    format_comparison, format_null, format_correlation,
    format_auc, format_chi2, format_exploratory,
    cohens_d, cohens_d_paired, fisher_ci,
)
```

### Between-groups comparison

```python
print(format_comparison(
    "baseline", "treatment",
    mean_a=1.42, sd_a=0.12, n_a=127,
    mean_b=0.98, sd_b=0.11, n_b=127,
))
# baseline: M = 1.42 (SD = 0.12, n = 127). treatment: M = 0.98 (SD = 0.11,
# n = 127). Δ = −0.44, 95% CI [−0.47, −0.41], Cohen's d = 3.82, n = 254.
```

### Null result framed as a detection limit

```python
print(format_null(delta=0.03, ci_lo=-0.12, ci_hi=0.18, n=84))
# Not detected (Δ = 0.03, 95% CI [−0.12, 0.18], n = 84). The 95% CI
# excludes effects larger than 0.18; smaller effects may exist but cannot
# be resolved at this sample size.
```

### Correlation with Fisher z CI

```python
print(format_correlation(r=0.34, n=62, p=0.007))
# r = .34, 95% CI [.10, .54], n = 62, p = .007
```

### AUC with CI

```python
print(format_auc(auc=0.43, n=168, ci_lo=0.36, ci_hi=0.50))
# AUC = 0.43, 95% CI [0.36, 0.50], chance = 0.50, n = 168
```

### Chi-squared

```python
print(format_chi2(chi2=0.09, df=1, n=168, p=0.77, cramers_v=0.02))
# χ²(1) = 0.09, p = .770, Cramer's V = .02, n = 168
```

### Exploratory label

```python
corr = format_correlation(r=0.34, n=62)
print(format_exploratory(corr))
# Exploratory: r = .34, 95% CI [.10, .54], n = 62. Not pre-registered;
# candidate for replication.
```

## Rules the helpers enforce

- Every point estimate is paired with a 95% CI
- Every null result uses "not detected at this granularity" phrasing and states what the CI *excludes*, not just what it contains
- Effect sizes are reported with sample size
- Exploratory findings are explicitly labeled
- Minus signs render as U+2212 (proper typography), not ASCII hyphen
- Leading zeros stripped from probabilities and correlations (APA convention)
- p-values below 0.001 render as `p < .001`, never `p = 0.000`

See [`channels/science.md`](../plugins/muriel/skills/compose/channels/science.md) in the muriel repo for the full statistical reporting chapter.

## contrast — WCAG audit helper

Standard-library-only module for computing WCAG 2.1 contrast ratios and auditing SVG files against muriel's 8:1 rule.

### As a module

```python
from muriel.contrast import (
    contrast_ratio, check_text_pair, audit_svg,
    RENDER_8, WCAG_AAA, WCAG_AA, WCAG_AA_LARGE,
)

# Single pair
contrast_ratio("#e6e4d2", "#0a0a0f")
# → 15.42

check_text_pair("#8a8aa0", "#0a0a0f", required=RENDER_8)
# → CheckResult(fg=(138,138,160), bg=(10,10,15), ratio=5.85,
#                required=8.0, passes=False, wcag_tier='AA')

# Whole SVG
entries = audit_svg("examples/example-palette.svg")
# prints a formatted audit table and returns a list of SelectorEntry
```

### As a CLI

```bash
# Audit one SVG against muriel's 8:1 rule
python -m muriel.contrast examples/example-palette.svg

# Multiple files in one run
python -m muriel.contrast examples/*.svg

# Custom threshold (e.g. WCAG AA 4.5:1)
python -m muriel.contrast some.svg --required 4.5

# Override background (auto-detects .bg class by default)
python -m muriel.contrast light-mode.svg --background '#ffffff'
```

Exit status: `0` if every text rule clears the threshold, `1` if any fail, `2` on usage errors. Slots into a pre-commit hook or CI check.

### What it classifies as text vs decorative

Class selectors are matched against substring hints:

- **Text hints** (treated as body text, subject to the rule): `title`, `subtitle`, `heading`, `body`, `caption`, `label`, `kicker`, `footer`, `header`, `model`, `response`, `prompt`, `closer`, `callout`, `quote`, `pull`, `note`, `aside`, `margin`, `badge`, `footnote`, `mark`, `highlight`, `code`, `mono`, `stat`, `dropcap`, plus muriel-specific `out-m`, `out-r`, `apple-m`, `apple-r`.
- **Decorative hints** (exempt): `bg`, `background`, `rule`, `divider`, `border`, `frame`, `axis`, `grid`, `tick`, `shadow`, `glow`, `vignette`, `path`, `shape`, `line`, `icon`, `arrow`, `marker`, `vignette`.
- **Ambiguous**: anything else — checked conservatively (better to audit than silently skip).

Text hints beat decorative hints when both match. Add more hints to `_TEXT_HINTS` / `_DECORATIVE_HINTS` in the module if your project has its own class vocabulary.

### Limitations

- CSS parser is minimal — handles `<defs><style>` blocks with flat rules. Does not handle `@media`, nested rules, or inline `fill=` attributes on individual `<text>` elements. For SVGs that use inline fills, add a `<style>` block with equivalent classes first.
- sRGB only — no P3, Rec.2020, or Oklab color spaces.
- Alpha channel is ignored (assumes opaque text on opaque background).

## Dependencies

- **matplotlibrc_*** — matplotlib (any recent version)
- **stats** — standard library only. Uses normal approximations (z = 1.96 for 95% CI) accurate for n ≥ 30. For exact t-distribution CIs at small n, compute upstream with scipy and pass the endpoints directly into the formatters.
- **contrast** — standard library only. `re`, `xml.etree.ElementTree`, `dataclasses`, `argparse`.
