# Gaze Plots — Scanpath / Fixation Visualization

The vision-science specialty channel. Photoshop has nothing here; matplotlib has primitives but no eye-tracking idioms. Render keeps the canonical recipes alongside the [heatmap](heatmaps.md) and [science](science.md) channels.

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map.

## Plot types

| Plot | What it shows | Best for |
|---|---|---|
| **Scanpath** | Numbered fixations connected by saccade lines | Single trial, qualitative inspection |
| **Bubble scanpath** | Same, but circle radius = fixation duration | Single trial, duration emphasis |
| **Heatmap** | Gaussian density over all fixations | Aggregate across trials/users |
| **AOI timeline** | Horizontal bands showing which AOI is fixated when | Sequential analysis, OSEC phases |
| **Saccade rose** | Polar histogram of saccade directions | Reading vs. scanning detection |
| **Fixation duration histogram** | Distribution of fixation durations | Cognitive load comparison |
| **Approach-retreat plot** | Cursor distance to gaze over time | Mouse-gaze coupling (per `project_recgaze_analysis.md`) |

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

## Recipes the current projects need
- **AdSERP scanpaths** — fixation sequence over a SERP screenshot, colored by phase (survey/evaluate per F-pattern decomposition)
- **RecGaze approach-retreat** — cursor x/y vs gaze x/y over time, distance line below (for IUI 2027 / CIKM 2026 papers)
- **Pupil LF/HF trajectory** — cognitive load index over trial position, with sat/opt overlay (ETTAC 2026)
- **Mind2Web replay** — peripheral rendering predictions vs actual gaze fixations, frame by frame

See [channels/science.md](science.md) for worked code examples of these plots with the Render rcparams defaults.

## Data formats
- **Tobii-native:** TSV with `Timestamp, GazePointX, GazePointY, FixationIndex, FixationDuration`
- **Polars idiom** (per user's preferences):
  ```python
  import polars as pl
  fix = pl.read_csv('trial.tsv', separator='\t').filter(pl.col('FixationIndex').is_not_null())
  ```
- **Mind2Web format:** action sequence with bounding boxes; scanpath = saccade through bbox centers
