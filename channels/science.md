---
channel: science
status: active
requires:
  brand: optional
  audience: required
  reads:
    - muriel.matplotlibrc_light
    - muriel.matplotlibrc_dark
    - muriel.stats
    - muriel.dimensions
    - muriel.contrast
output:
  kinds: [pdf, svg, png]
  registers: [paper, editorial]
peer_channels:
  - gaze
  - heatmaps
  - svg
  - diagrams
---

# Science — Paper Figures, Stats Reporting, Notebook Editorial

The research-communication channel. How to produce figures, statistical reports, and notebook prose that meet the standards of publishable research — empirically grounded, honestly framed, reproducibly generated, and readable at the sizes papers actually print.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map. Closely related: [channels/gaze.md](gaze.md), [channels/heatmaps.md](heatmaps.md), [channels/svg.md](svg.md).

## When to use

- Paper figures for CHI, ETTAC, CIKM, IUI submissions
- Research notebook editorial passes (explicit metric definitions, caption-first prose)
- Statistical reports (effect sizes with confidence intervals, null results framed as detection limits)
- LaTeX figure round-trip (matplotlib PDF/PGF → paper build)
- Pre-registration boilerplate and methods sections
- Blog posts that present empirical results (research explainers)

## matplotlib rcparams — OLED-compliant defaults

Matplotlib's out-of-the-box defaults are wrong for every constraint muriel enforces. Light background, thin sans-serif at default sizes that fail 8:1 contrast, 6×4 figsize too small for a paper, no units on ticks. A rcParams block at the top of every notebook fixes all of it in one place.

### Importable module (preferred)

The dark and light rcparams blocks are shipped as importable Python modules in [`muriel/`](../muriel/). Add the muriel repo to your `PYTHONPATH` (or `pip install -e ~/Documents/dev/muriel`), then:

```python
# Auto-apply on import — pick one palette per document
from muriel import matplotlibrc_dark    # OLED cream on near-black
# or
from muriel import matplotlibrc_light   # warm editorial (F explainer)

# Scoped to a single figure (no global side effect)
import matplotlib.pyplot as plt
from muriel.matplotlibrc_dark import PARAMS
with plt.rc_context(PARAMS):
    fig, ax = plt.subplots()
    # ...
```

Prefer the import path so updates to the rcparams stay in one place and propagate to every notebook on the next run. The rest of this section documents the raw blocks as they live in `muriel/matplotlibrc_dark.py` and `muriel/matplotlibrc_light.py`.

### Drop-in dark block (OLED palette)

```python
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    # Figure sizing — large enough that a paper figure doesn't need upscaling
    'figure.figsize':        (10, 6),
    'figure.dpi':             120,
    'savefig.dpi':            300,
    'savefig.bbox':          'tight',
    'savefig.transparent':    False,

    # Typography — readable at paper print sizes; never Light weight at small sizes
    'font.family':           'sans-serif',
    'font.sans-serif':       ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size':              14,
    'axes.titlesize':         16,
    'axes.labelsize':         14,
    'xtick.labelsize':        12,
    'ytick.labelsize':        12,
    'legend.fontsize':        12,
    'figure.titlesize':       18,
    'font.weight':           'regular',

    # OLED palette — matches muriel's universal rules
    'figure.facecolor':      '#0a0a0f',
    'axes.facecolor':        '#0a0a0f',
    'savefig.facecolor':     '#0a0a0f',
    'axes.edgecolor':        '#e6e4d2',
    'axes.labelcolor':       '#e6e4d2',
    'xtick.color':           '#e6e4d2',
    'ytick.color':           '#e6e4d2',
    'text.color':            '#e6e4d2',
    'grid.color':            '#3a3a4a',  # decorative ≥55/255 on dark bg
    'grid.linewidth':         0.6,
    'grid.alpha':             1.0,       # set color directly, don't fade via alpha

    # Axes — visible but not loud
    'axes.linewidth':         1.2,
    'axes.grid':              True,
    'axes.grid.axis':        'y',        # horizontal grid only by default
    'axes.axisbelow':         True,
    'axes.spines.top':        False,
    'axes.spines.right':      False,

    # Ticks — outside, proportional to signal
    'xtick.direction':       'out',
    'ytick.direction':       'out',
    'xtick.major.size':       5,
    'ytick.major.size':       5,
    'xtick.major.width':      1.2,
    'ytick.major.width':      1.2,

    # Lines and markers — thick enough to read through a PDF down-resize
    'lines.linewidth':        2.0,
    'lines.markersize':       7,
    'patch.linewidth':        1.0,

    # Legend — framed, no shadow, opaque background
    'legend.frameon':         True,
    'legend.framealpha':      0.9,
    'legend.edgecolor':      '#3a3a4a',
    'legend.facecolor':      '#0f1117',
})
```

### Light theme variant (for journal submissions that require white)

```python
mpl.rcParams.update({
    'figure.facecolor':      'white',
    'axes.facecolor':        'white',
    'savefig.facecolor':     'white',
    'axes.edgecolor':        '#1a1a2e',
    'axes.labelcolor':       '#1a1a2e',
    'xtick.color':           '#1a1a2e',
    'ytick.color':           '#1a1a2e',
    'text.color':            '#1a1a2e',
    'grid.color':            '#cccccc',
})
```

Keep every other setting. The palette flip is a two-dozen-line override, not a reset. Save both blocks as `~/Documents/dev/muriel/assets/matplotlibrc_dark.py` / `_light.py` and `import` whichever one fits the target medium.

## Plot readability rules

Codified from per-project feedback. Every rule exists because a specific plot failed in a specific way.

### Axes proportional to signal

- **Axis space should scale with the signal.** If the interesting variance is in a 10% range, don't waste 90% of the plot on empty y-axis. Zoom in. Let the reader see the difference.
- **Never use matplotlib's default figsize (6×4).** Too small for anything worth looking at. Set `figsize=(10, 6)` minimum; go larger for multi-series plots.
- **Reserve the bottom 20% for axis labels + units.** Cramming them causes the axis to eat the data.

### Fonts

- **No Light weight at small sizes.** 14pt Light is unreadable at paper print size regardless of contrast ratio (`feedback_thin_font_contrast.md`). Regular minimum; Bold for axis titles.
- **8:1 contrast on all text.** Compute the WCAG ratio between axis color and figure background. `#e6e4d2` on `#0a0a0f` passes. The `grid.color` `#3a3a4a` is decorative-only — fails as text.
- **Consistent type scale.** One font family per paper; one weight per element class. Don't mix Regular and Medium body labels in the same figure.

### Label every number

- **Axes need units.** `ms`, `%`, `px`, `°`, `$USD`, `fixations/trial`. Every number. No exceptions.
- **Legend entries need context.** "N=42, women only" beats "condition A".
- **Annotations beat floating numbers.** If a value matters enough to point at, add a text callout with an arrow — don't assume readers will find it in the legend.
- **Error bars need a key.** State what they represent (SEM, 95% CI, SD, IQR) in the caption or legend.

### Color

- **Sequential when the variable has order.** Viridis for time, cognitive load, any scalar. Never use rainbow — it's perceptually non-uniform and fails colorblind accessibility.
- **Diverging when the variable has a meaningful midpoint.** Red-white-blue (or equivalents) for effect sizes, correlations, changes from baseline.
- **Categorical when the variable has no order.** Tableau 10, Dark2, or a hand-picked palette. Max 8 categories; more becomes indistinguishable.
- **Color is redundant, not primary.** Always pair with shape, linestyle, or text labels. Pure color encoding fails for ~5% of readers.

## Statistical reporting

How to present numerical findings so they are precise, honest, and not over-claimed.

### Importable helpers (preferred)

Every template in this section is shipped as a function in [`muriel/stats.py`](../muriel/stats.py). Standard-library only — no numpy, scipy, or pandas required.

```python
from muriel.stats import (
    format_comparison, format_null, format_correlation,
    format_auc, format_chi2, format_exploratory,
    cohens_d, cohens_d_paired, fisher_ci,
    apa_number, format_p, format_ci,
)

print(format_comparison(
    "baseline", "treatment",
    mean_a=1.42, sd_a=0.12, n_a=127,
    mean_b=0.98, sd_b=0.11, n_b=127,
))
# baseline: M = 1.42 (SD = 0.12, n = 127). treatment: M = 0.98 (SD = 0.11,
# n = 127). Δ = −0.44, 95% CI [−0.47, −0.41], Cohen's d = 3.82, n = 254.

print(format_null(delta=0.03, ci_lo=-0.12, ci_hi=0.18, n=84))
# Not detected (Δ = 0.03, 95% CI [−0.12, 0.18], n = 84). The 95% CI
# excludes effects larger than 0.18; smaller effects may exist but cannot
# be resolved at this sample size.

print(format_correlation(r=0.34, n=62, p=0.007))
# r = .34, 95% CI [.10, .54], n = 62, p = .007
```

All formatters enforce: 95% CI paired with every point estimate, minus signs as U+2212 (proper typography), APA leading-zero stripping for probabilities and correlations, `p < .001` for tiny values (never `p = 0.000`), detection-limit phrasing for nulls, explicit exploratory labels.

The raw templates below still apply — they document *why* the formatters say what they say. Use the Python helpers in notebooks; use the templates when writing prose by hand.

### Effect sizes with confidence intervals

Minimum acceptable report for any empirical result:

```
The LF/HF index decreased from 1.42 to 0.98 (Δ = −0.44, 95% CI [−0.61, −0.27],
Cohen's d = 0.82, n = 127).
```

Not acceptable:

```
The LF/HF index significantly decreased (p < 0.05).
```

Bare p-values hide how large the effect was and how precisely it was measured. Always include:

- **Point estimate** (Δ, mean difference, slope, odds ratio, AUC, etc.)
- **Uncertainty interval** (95% CI is standard; SE is acceptable for raw quantities)
- **Standardized effect size** when comparing across units (Cohen's d, Hedges' g, η², Cliff's delta)
- **Sample size** (n, including n per group for between-subjects designs)

### Null results framed as detection limits

The hard rule from `feedback_empirical_not_truth.md`: **null results reflect instrument sensitivity, not ground truth.** Never write "there is no effect" — write "not detected at this granularity."

Template:

```
We did not detect a difference between conditions A and B (Δ = 0.03, 95% CI
[−0.12, 0.18], n = 84). The 95% CI excludes effects larger than 0.18; smaller
effects may exist but cannot be resolved at this sample size.
```

Note what the CI *excludes*, not just what it contains. A wide CI is a detection-limit statement, not a zero-effect claim.

### Pre-committed vs. exploratory analyses

Label them. Exploratory findings are hypotheses, not conclusions.

```
Exploratory: we observed a correlation between dwell time and phase 3 onset
(r = 0.34, 95% CI [0.11, 0.55], n = 62). This was not pre-registered and
should be interpreted as a candidate for replication.
```

### Copy-paste formulations

| Finding type | Template |
|---|---|
| Between-groups comparison | `Group A: M=X (SD=Y). Group B: M=X (SD=Y). Δ = Z, 95% CI [...], d = ...` |
| Within-subjects change | `Baseline M=X; follow-up M=X. Mean change Δ=Z, 95% CI [...], dz = ...` |
| Correlation | `r = 0.XX, 95% CI [a, b], n = N, p = ... (two-sided)` |
| AUC / classifier | `AUC = 0.XX, 95% CI [a, b], chance = 0.50, n = N` |
| Chi-squared | `χ²(df) = X, p = ..., Cramer's V = ..., n = N` |
| Logistic regression | `OR = X, 95% CI [a, b], p = ... (Wald)` |

## Notebook editorial pass

From `project_notebooks_v2_editorial.md`: research notebooks need explicit metric definitions before any interpretive prose. Readers shouldn't have to infer what "performance" means from context.

### The rule

**Before using any metric in prose, define it inline with units and direction.**

Bad:

```
Performance improved in the new condition.
```

Good:

```
The primary outcome — time to first fixation on the target AOI, measured in
milliseconds from trial onset — decreased from M=842 ms (SD=210) in the
baseline condition to M=671 ms (SD=185) in the treatment condition.
```

The second version tells the reader:

- What the metric is
- What units it's measured in
- What direction "improvement" means
- The magnitude of the change
- The variability of the measurement

### Caption-first writing

Write the figure caption *before* writing the surrounding prose. The caption is the self-contained summary the reader scans first — it should answer "what am I looking at?" and "what's the takeaway?" without depending on the body text.

**Template:**

```
Figure N. [WHAT is plotted] across [CONDITIONS]. [KEY FINDING in one sentence].
[METHODS: n, error bars, filter criteria]. [TECHNICAL NOTE if needed].
```

**Example:**

```
Figure 1. Mean LF/HF pupil index across trial positions 1–10 for satisficer
and optimizer sub-populations. Cognitive load decreased with position for
both groups (ANOVA main effect of position, p < 0.001), but did not differ
between groups (position × group AUC = 0.43 for discrimination, χ² p = 0.77).
Error bars are 95% CIs; n = 84 trials per position. Data preprocessed with
Jayawardena RIPA2 filter (see Methods §2.3).
```

~90 words. Tells you exactly what you're looking at and what it means. Body prose can add context, interpretation, and references without re-explaining the figure.

## LaTeX / BibTeX bridge

For paper submissions, matplotlib figures need to round-trip into a LaTeX build.

### Export for LaTeX

Prefer PDF over PNG for vector precision:

```python
fig.savefig('figures/lfhf_trajectory.pdf', bbox_inches='tight', pad_inches=0.1)
```

Or PGF for native LaTeX text rendering (matches the paper's font automatically):

```python
mpl.use('pgf')
mpl.rcParams.update({
    'pgf.texsystem': 'xelatex',
    'font.family':   'serif',
    'text.usetex':    True,
    'pgf.rcfonts':    False,
})
fig.savefig('figures/lfhf_trajectory.pgf')
```

Include in LaTeX:

```latex
\begin{figure}
  \centering
  \input{figures/lfhf_trajectory.pgf}
  \caption{...}
  \label{fig:lfhf_trajectory}
\end{figure}
```

### BibTeX hygiene

Keep a single `references.bib` per paper. Use `pandoc-citeproc` or `natbib` for consistent formatting. Common mistakes:

- Missing DOIs — add them; reviewers check
- Wrong title capitalization — use `{CamelCase}` to preserve case
- `@misc` entries for real papers — use `@article` or `@inproceedings`
- Missing year field on preprint citations

## Recipes for current projects

### AdSERP fixation-phase plot (F-pattern decomposition)

Bands showing survey/evaluate phases over a SERP screenshot. Per `project_f_pattern_decomposition.md`.

```python
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import polars as pl

fix = pl.read_csv('trial.tsv', separator='\t').filter(
    pl.col('FixationIndex').is_not_null()
)

fig, ax = plt.subplots(figsize=(12, 7))
ax.imshow(plt.imread('serp.png'), alpha=0.55)  # desaturated background

# Phase bands
survey_end_x = fix.filter(pl.col('t_ms') < 2000)['x'].max()
ax.add_patch(Rectangle((0, 0), survey_end_x, 50,
                       color='#e6a817', alpha=0.3, label='Survey phase (0–2s)'))
ax.add_patch(Rectangle((0, 50), fix['x'].max(), 50,
                       color='#50b4c8', alpha=0.3, label='Evaluate phase (2s+)'))

# Numbered fixations sized by duration
for i, row in enumerate(fix.iter_rows(named=True)):
    ax.scatter(row['x'], row['y'], s=row['duration_ms']*2,
               c='#e6e4d2', edgecolors='#0a0a0f', linewidths=1.5, zorder=10)
    ax.annotate(str(i+1), (row['x'], row['y']), color='#0a0a0f',
                ha='center', va='center', fontweight='bold', fontsize=9)

ax.set_xlabel('Screen x (px)')
ax.set_ylabel('Screen y (px)')
ax.set_title('Trial 042 — Survey/Evaluate F-pattern decomposition')
ax.legend(loc='upper right')
plt.tight_layout()
fig.savefig('trial-042-phases.pdf', bbox_inches='tight')
```

### Pupil LF/HF trajectory with CI ribbon (ETTAC 2026)

Per `project_lfhf_orthogonality.md` and `project_ettac2026.md`.

```python
import numpy as np
import matplotlib.pyplot as plt

positions = np.arange(1, 11)
lfhf_mean = np.array([1.42, 1.38, 1.30, 1.21, 1.14, 1.08, 1.03, 1.00, 0.99, 0.98])
lfhf_ci95 = np.array([0.12, 0.11, 0.10, 0.09, 0.09, 0.09, 0.10, 0.10, 0.11, 0.12])

fig, ax = plt.subplots(figsize=(10, 6))
ax.fill_between(positions, lfhf_mean - lfhf_ci95, lfhf_mean + lfhf_ci95,
                color='#50b4c8', alpha=0.25, label='95% CI')
ax.plot(positions, lfhf_mean, color='#50b4c8', linewidth=2.5,
        marker='o', markersize=8, label='LF/HF pupil index')

ax.axhline(1.0, color='#8a8aa0', linestyle='--', linewidth=1, alpha=0.6)
ax.text(10.1, 1.0, 'baseline', color='#8a8aa0', fontsize=11, va='center')

ax.set_xlabel('Trial position')
ax.set_ylabel('LF/HF pupil index (ratio)')
ax.set_xticks(positions)
ax.set_title('Cognitive load decreases with trial position (n = 84/position)')
ax.legend(loc='upper right', frameon=True)
plt.tight_layout()
fig.savefig('lfhf-trajectory.pdf', bbox_inches='tight')
```

### Small multiples of scanpaths by condition

The small-multiples principle (see Visualization principles in the top-level index) applied to gaze data.

```python
fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True, sharey=True)
conditions = ['easy', 'medium', 'hard', 'novel', 'repeat', 'catch']
for ax, cond in zip(axes.flat, conditions):
    trial = fix.filter(pl.col('condition') == cond)
    ax.scatter(trial['x'], trial['y'], s=trial['duration_ms']*1.5,
               c=trial['t_ms'], cmap='viridis',
               edgecolors='#0a0a0f', linewidths=0.8)
    ax.set_title(f'{cond} (n = {len(trial)})')
    ax.set_xlim(0, 1920)
    ax.set_ylim(1080, 0)  # flip y for screen coordinates
fig.suptitle('Fixation scanpaths by task condition', fontsize=18)
fig.supxlabel('Screen x (px)')
fig.supylabel('Screen y (px)')
plt.tight_layout()
fig.savefig('scanpath-small-multiples.pdf', bbox_inches='tight')
```

### Effect-size forest plot

For meta-analytic or multi-condition summaries.

```python
fig, ax = plt.subplots(figsize=(10, 7))
labels = ['Satisficer vs optimizer', 'Novel vs repeat', 'Hard vs easy',
          'Ambient light effect', 'Hour-of-day effect']
effects = [0.03, 0.82, 1.41, 0.15, 0.08]
ci_lo   = [-0.12, 0.61, 1.18, -0.04, -0.09]
ci_hi   = [0.18, 1.03, 1.64, 0.34, 0.25]

y = np.arange(len(labels))
ax.errorbar(effects, y, xerr=[np.subtract(effects, ci_lo), np.subtract(ci_hi, effects)],
            fmt='o', color='#50b4c8', ecolor='#50b4c8', elinewidth=2, capsize=5,
            markersize=9)
ax.axvline(0, color='#8a8aa0', linestyle='--', linewidth=1)
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Cohen's d (95% CI)")
ax.set_title('Effect sizes across conditions — forest plot')
ax.invert_yaxis()
plt.tight_layout()
fig.savefig('effect-forest.pdf', bbox_inches='tight')
```

## Workflow

1. **Import rcparams** at the top of every figure-producing notebook (`from muriel.matplotlibrc_dark import *`)
2. **Write the figure caption first** — what is this, what's the takeaway — before touching the plotting code
3. **Code the figure to match the caption claim exactly** — not more, not less
4. **Print contrast ratio and effective figsize** before saving, to catch silent regressions
5. **Save as PDF or PGF** (not PNG) for LaTeX round-trip
6. **Write prose that adds context** referencing the figure, don't re-explain what's on screen
7. **Every numerical claim in prose must be traceable** to a table or figure in the same notebook
8. **Run an editorial pass before sharing**: define every metric, frame nulls as detection limits, pair every p-value with effect size + CI

## Anti-patterns to reject

- **Default matplotlib figsize.** Always override.
- **Bare p-values.** Always pair with effect size.
- **"No effect" phrasing.** Use "not detected at this granularity."
- **Unlabeled axes.** Every number has a unit.
- **Rainbow colormap.** Use viridis or a paired diverging scale.
- **Light-weight fonts at small sizes.** Regular minimum.
- **Alpha-faded gridlines.** Set color directly; alpha fails on PDF re-render.
- **Figure without caption.** Caption is non-optional for any research artifact.
- **Prose before metric definition.** Define first, interpret second.
- **Tier-collision in stacked text.** Multi-tier figures (`suptitle` / per-axes `set_title` / `fig.text` annotations / `figcaption`) cramp into each other when y-positions are typed as bare literals — the gaps don't scale with `fig_h` or with a panel's actual aspect. Express every tier's y as a function of `fig_h` (e.g. `y_title = 1 - 0.40 / fig_h`), and either render at draft + final aspect to confirm no two tiers' bbox y-extents overlap, or use `constrained_layout=True` and let the engine resolve. The Mona Lisa Laplacian and falloff-curve figures (peripheral-color blog) are the worked examples.
- **Terminology drift inside the same figure.** A channel called *BY* in the legend and *YV* in the inline annotation forces the reader to translate. Pick one name per quantity per figure; if the field has two conventions (castleCSF *YV* vs HCI *BY*), reconcile before drawing and put the cross-walk in the docstring, not the figure.

## Anti-patterns

- **Don't report a point estimate without a 95% CI.** Every number paired with an interval.
- **Don't say "not significant."** Say "not detected at this granularity" and state the CI upper bound that you've excluded.
- **Don't use gradient fills in bar charts.** Gradients distort perceived value; solid fills are readable.
- **Don't pluralize "data" both ways in one paper.** Pick "data are" or "data is" once and commit.

## Prior art / upstream

- [K-Dense scientific-agent-skills — matplotlib](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/matplotlib/SKILL.md) (MIT). Pure guidance doc: OO interface default, `constrained_layout=True`, viridis/cividis, ban rainbow/jet, 72/150/300 DPI by medium. Muriel's rcparams and figures already enforce the same principles with project-specific palettes and importable helpers. Worth skimming before adding new recipes — if it's conventional matplotlib opinion, check there first to avoid reinventing. One alternative worth knowing: K-Dense prefers `constrained_layout=True` over `tight_layout()`; both work, `constrained_layout` handles suptitle / colorbar edges more gracefully on multi-panel figures.
- [K-Dense — statistical-analysis](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/statistical-analysis/SKILL.md) (MIT). Test-selection guide, assumption checks via `scipy.stats` + `statsmodels` + `pingouin` + `pymc`, APA reporting. Overlaps [`muriel/stats.py`](../muriel/stats.py) on output formatting but goes deeper on test selection. Read when the question is "which test?" not "how do I report the number?"
- [K-Dense — scientific-critical-thinking](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/scientific-skills/scientific-critical-thinking/SKILL.md) (MIT). GRADE system, Cochrane Risk of Bias, bias taxonomy (Cognitive / Selection / Measurement / Analysis / Confounding). Useful vocabulary when an editorial pass needs to name *why* a claim is weak, not just flag it.
