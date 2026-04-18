# Heatmaps — Smooth Gaussian Density Overlays

Tobii-style topographic heatmaps from fixation data. The aggregate counterpart to scanpath visualization — same data, averaged across trials.

Part of the [muriel](../muriel.md) skill — see the top-level index for mission, universal rules, and channel map. Related: [channels/gaze.md](gaze.md) for individual-trial scanpaths.

## `typeset.render_heatmap()`

```python
from typeset import render_heatmap

heatmap = render_heatmap(
    fixations,              # list of {'x', 'y', 'd'} dicts
    canvas_size=(400, 800), # output dimensions
    radius=18,              # blob radius (controls bin coarseness)
    blur=8,                 # gaussian blur after binning
    colormap="pink",        # "pink" (Tobii-style), "heat", or (r,g,b) tuple
    background="serp.png",  # optional background image path
    desaturate=0.7,         # background desaturation (0=color, 1=gray)
    bg_opacity=0.35,        # background layer opacity
    output="heatmap.png",   # save path (None to just return Image)
)
```

## How it works

Fixations are binned into a coarse grid, then large gaussian blobs are stamped at each bin center (weighted by fixation count/duration). Density is quantized into 8 bands to create visible topographic contour plateaus, then softened with a light blur so band edges aren't pixelated. Result: discrete rounded peaks that merge where they overlap, like contour islands on a topo map.

## Key parameters

- **`radius`** controls blob size and bin coarseness. Smaller = more granular topology. 12–20 is the sweet spot for aggregate data.
- **`blur`** controls post-stamp smoothing. Keep low (6–10) to preserve topo feel. Too high washes out the contour structure.
- **For sparse data** (<500 fixations), increase radius to 30+ so individual blobs are visible.
- **For dense data** (>10K fixations), the contour banding is what creates the topo feel — without it, density saturates everywhere.

## Colormaps

- **`"pink"`** — monochrome magenta with gamma-corrected two-stop ramp: light pink → hot pink → deep magenta. Alpha ramps fast and saturates early. Tobii-style.
- **`"heat"`** — yellow → red → dark red.
- **`(r, g, b)`** tuple — monochrome with custom tint. Use the project's accent color for theme consistency.

## Generation script

`attentional-foraging/scripts/generate_explainer_heatmaps.py` — loads all 2,776 AdSERP trials, filters by phase/behavior, generates `f-decomposition.png` and `f-dissection.png` for the explainer page. Good starting point for any new aggregate heatmap work.

## Anti-patterns

- **Don't use `jet` or `rainbow` colormaps.** They introduce false discontinuities and fail colorblind tests. Use perceptually-uniform maps (`viridis`, `magma`, `inferno`).
- **Don't show a heatmap without its colorbar** — the colorbar carries units, N, and the range.
- **Don't aggregate across trials without stating `N`** in the caption. Heatmap density without N is ambiguous.
- **Don't apply a Gaussian kernel without recording the σ / bandwidth** in the figure metadata or caption.
