# muriel

Importable Python assets for the [muriel](../muriel.md) skill. matplotlibrc blocks, APA-style reporting helpers, WCAG contrast audit, dimension constants, capture, and brand style guides — extracted from the [`channels/`](../channels/) subfiles so notebooks can `import` them instead of copy-pasting.

## Install

No required dependencies. Add the muriel repo to your `PYTHONPATH`:

```bash
export PYTHONPATH=~/Documents/dev/muriel:$PYTHONPATH
```

Or `pip install -e` it:

```bash
pip install -e ~/Documents/dev/muriel
```

Then `from muriel import ...` works from any Python environment. The old `render_assets` import path continues to work via a deprecation shim for one release.

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

See [`channels/science.md`](../channels/science.md) in the muriel repo for the full statistical reporting chapter.

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
