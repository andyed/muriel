---
channel: gaze
status: active
requires:
  brand: optional
  audience: required
  reads:
    - muriel.matplotlibrc_light
    - muriel.matplotlibrc_dark
    - muriel.dimensions
output:
  kinds: [pdf, svg, png]
  registers: [paper, editorial]
peer_channels:
  - heatmaps
  - science
---

# Gaze Plots — Scanpath / Fixation Visualization

The vision-science specialty channel. Photoshop has nothing here; matplotlib has primitives but no eye-tracking idioms. muriel keeps the canonical recipes alongside the [heatmap](heatmaps.md) and [science](science.md) channels.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## Plot types

| Plot | What it shows | Best for |
|---|---|---|
| **Scanpath** | Numbered fixations connected by saccade lines | Single trial, qualitative inspection |
| **Bubble scanpath** | Same, but circle radius = fixation duration | Single trial, duration emphasis |
| **Heatmap** | Gaussian density over all fixations | Aggregate across trials/users |
| **AOI timeline** | Horizontal bands showing which AOI is fixated when | Sequential / phase analysis |
| **Saccade rose** | Polar histogram of saccade directions | Reading vs. scanning detection |
| **Fixation duration histogram** | Distribution of fixation durations | Cognitive load comparison |
| **Approach-retreat plot** | Cursor distance to gaze over time | Mouse-gaze coupling studies |

## Tooling
- **`typeset.render_heatmap()`** — already shipped (Tobii-style topographic). See [channels/heatmaps.md](heatmaps.md).
- **Matplotlib + `Circle` patches** — scanpath/bubble scanpath. Set `figsize` large per the readability rule; never default.
- **D3 + SVG** — interactive scanpath with hover-to-inspect, brush-to-filter. Pairs with linked-displays principle.
- **Custom Canvas2D + `requestAnimationFrame`** — playback with timeline scrubber.

## Patterns
- **Numbered fixations** use circles with the index inside; size scales with duration. 8:1 contrast on the number.
- **Saccade lines** at low alpha (~0.4) so overlapping paths don't black out the underlying stimulus.
- **Background stimulus** desaturated to 0.6–0.7 (`feedback_plot_readability.md`) so gaze marks pop without losing context.
- **Color encodes time, not user.** Sequential colormap from start (cool) to end (warm). Categorical color is for AOIs.
- **Always overlay on the actual stimulus**, not a blank canvas. The whole point is showing *where on the page* attention went.
- **AOI rectangles in `<rect class="aoi">`** with marginalia-themed stroke so they re-theme on light/dark switch.

## Recipe patterns

Common shapes these plots take in research work:

- **Phase-segmented scanpath** — fixation sequence over a task screenshot, colored by task phase (e.g. survey vs. evaluate).
- **Approach-retreat** — cursor (x,y) vs. gaze (x,y) over time, distance line below.
- **Load-trajectory** — cognitive-load index (pupil, LF/HF, whatever your proxy) over trial position, with a secondary categorical overlay.
- **Task-replay** — model predictions vs. actual fixations, frame by frame, for peripheral rendering / saliency / attention-model validation.

See [channels/science.md](science.md) for worked code examples with the muriel rcparams defaults.

## Data formats
- **Tobii-native:** TSV with `Timestamp, GazePointX, GazePointY, FixationIndex, FixationDuration`
- **Polars idiom:**
  ```python
  import polars as pl
  fix = pl.read_csv('trial.tsv', separator='\t').filter(pl.col('FixationIndex').is_not_null())
  ```
- **Action-sequence format** (e.g. Mind2Web): task actions with bounding boxes; scanpath = saccade through bbox centers

## Anti-patterns

- **Don't color fixations by user identity.** Use time (sequential colormap) or AOI (categorical) instead — user-as-color doesn't generalize across sample sizes.
- **Don't show a scanpath without the stimulus** as background. Gaze points without referent are meaningless.
- **Don't rely on matplotlib default figsize** (6×4) for gaze plots. They need room — 10×6 minimum.
- **Don't draw AOI borders below the 3:1 decorative-contrast floor.** Invisible borders = invisible AOIs.
