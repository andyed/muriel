# Style guides — brand tokens as importable schema

A style guide is a brand's design tokens — colors, typography, assets, ownership rules — serialized so Render can import them and use them in any channel without reinventing them and without violating "this brand is owned by X repo, don't regenerate here" rules.

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map. Related: [`raster.md`](raster.md) for asset generation, [`web.md`](web.md) for marginalia CSS tokens, [`science.md`](science.md) for matplotlib rcparams.

## Why this exists

Every Andy project that ships visuals has a design voice. Scrutinizer's vision-science overlays, Psychodeli+'s 10-ring copperplate wordmark, marginalia's dark OLED palette, iBlipper's kinetic typography, the F-pattern explainer's warm editorial, render's own cream-on-near-black. Until now, each of those lived in its own ad-hoc form — CSS custom properties here, Python constants there, a CLAUDE.md rule somewhere else — and Render had no principled way to import one.

A style guide schema fixes that: one file per brand, one loader, one dataclass-tree in memory. When `/render` gets a task in the context of a brand, it loads the brand.toml, inherits the tokens, and respects the rules.

## Schema: `brand.toml`

A brand.toml has six top-level tables. Only `[meta]` (with `name`) and `[colors]` (with `background` + `foreground`) are required. Everything else is optional.

```toml
[meta]
name             = "Psychodeli+"           # required
slug             = "psychodeli-plus"
version          = "1.0.0"
owner_repo       = "psychodeli-brand-guide"
owner_path       = "~/Documents/dev/psychodeli-brand-guide"
canonical_source = "templates/shared-styles.css"
ownership_rule   = "psychodeli-brand-guide owns all Psychodeli image generation. Never rebuild elsewhere."

[colors]
background       = "#0a0a0f"              # required
foreground       = "#e6e4d2"              # required
# optional extras, all mapping to marginalia --mg-* conventions
background_2     = "#0f1117"
foreground_muted = "#b0b0c4"
accent           = "#50b4c8"
accent_ink       = "#7dd4e4"
note             = "#50b4c8"
tip              = "#66bb6a"
warning          = "#e6a817"
important        = "#ff8282"

[colors.rings]
# Brand-specific: a ring gradient for a layered-border effect.
# Keys are arbitrary names; values are {color, width_px}.
r10 = { color = "rgba(0,0,0,0.75)", width_px = 76 }
r1  = { color = "#91d7f8",          width_px = 6  }

[colors.accents]
# Named accent palette beyond the semantic defaults.
deepsea     = "#50b4c8"
wildflowers = "#dc64a0"
tiedye      = "#ff7f00"

[typography]
display_family              = "Nunito"
display_weight              = 900
display_line_height         = 1.2
display_letter_spacing_em   = -0.04
body_family                 = "Helvetica, Arial, sans-serif"
mono_family                 = "'SF Mono', Menlo, Monaco, monospace"
paint_order                 = "stroke fill"  # for multi-stroke text rendering

[assets]
# Paths are relative to meta.owner_path.
wordmark_template    = "templates/logo-wordmark.html"
monogram_template    = "templates/monogram-p-plus.html"
fractal_fill_default = "sources/bg-wildflowers.jpg"
fractal_fills        = ["sources/bg-wildflowers.jpg", "sources/bg-forcefield.jpg"]

[dependencies]
google_fonts = ["Nunito:wght@900"]

[export]
# Commands the owner repo provides; Render invokes these rather than
# re-implementing asset generation.
cmd_all      = "npm run export"
cmd_wordmark = "npm run export:wordmark"

[rules]
# Reserved booleans are enforced by StyleGuide.rules.check(operation).
never_modify_sources                     = true
never_rebuild_image_generation_elsewhere = true
brand_owner                              = "psychodeli-brand-guide"
# Non-reserved extras pass through into rules.custom{}.
one_font_treatment_per_app               = true
```

## Loading a style guide

```python
from render_assets.styleguide import load_styleguide

sg = load_styleguide("examples/psychodeli-brand.toml")
sg.meta.name                      # → 'Psychodeli+'
sg.colors.background              # → '#0a0a0f'
sg.colors.accent                  # → '#d2b06a'
sg.colors.rings["r1"].color       # → '#91d7f8'
sg.colors.rings["r1"].width_px    # → 6
sg.typography.display_family      # → 'Nunito'
sg.assets.wordmark_template       # → 'templates/logo-wordmark.html'
sg.rules.never_rebuild_image_generation_elsewhere  # → True
```

The returned `StyleGuide` is a frozen dataclass, safe to pass between functions without anyone mutating its tokens mid-operation.

## Respecting brand ownership

Brand rules aren't advisory — they're enforced:

```python
try:
    sg.rules.check("regenerate-wordmark")
except RuleViolation as exc:
    # Handle the rule: e.g., invoke the owner's export pipeline instead
    print(exc)
    # → "Operation 'regenerate-wordmark' is owned by psychodeli-brand-guide
    #    and cannot be performed here. Use the owner's export pipeline instead."
```

Operations that trip `never_rebuild_image_generation_elsewhere`:
- any name containing `wordmark`, `monogram`, `logo`, `favicon`, `brand-asset`, `app-icon`, `regenerate-image`

Operations that trip `never_modify_sources`:
- `modify-source`, `filter-source`, `blur-source`

Call `sg.rules.check(operation)` at the top of any handler that might generate brand-owned artifacts. It raises `RuleViolation` with a clean message pointing at the owner's export pipeline. Consumers should catch and redirect — not catch and ignore.

## Derived outputs

The `StyleGuide` can produce several ready-made formats for downstream channels:

### matplotlib rcparams

```python
import matplotlib as mpl
mpl.rcParams.update(sg.to_matplotlibrc())
```

Returns a dict identical in shape to [`render_assets/matplotlibrc_dark.py`](../render_assets/matplotlibrc_dark.py)'s `PARAMS`, but populated from the brand's background / foreground / accent tokens instead of Render's hardcoded defaults.

### CSS custom properties

```python
print(sg.to_css_vars(prefix="--brand-"))
```

Emits a `:root { ... }` block with every defined color as a custom property. Ring stops render as `--brand-ring-{name}` (both color and width), named accents as `--brand-accent-{name}`. Use `prefix="--mg-"` to target marginalia overrides.

### WCAG contrast audit

```python
for role, ratio, passes in sg.audit_contrast(required=8.0):
    mark = "✓" if passes else "✗"
    print(f"  {mark} {role:<20} {ratio:5.2f}:1")
```

Audits every text role and named accent against `colors.background` using the WCAG 2.1 formula from [`render_assets/contrast.py`](../render_assets/contrast.py). Good pre-flight before shipping a brand.toml.

## CLI

```bash
# Describe a style guide
python -m render_assets.styleguide examples/psychodeli-brand.toml

# Emit CSS custom properties
python -m render_assets.styleguide examples/render-brand.toml --css

# Emit CSS with a custom prefix (e.g., to override marginalia)
python -m render_assets.styleguide examples/render-brand.toml --css --css-prefix '--mg-'

# Run a contrast audit (exit 1 if any role fails)
python -m render_assets.styleguide examples/render-brand.toml --contrast
```

## Shipped examples

- [`examples/psychodeli-brand.toml`](../examples/psychodeli-brand.toml) — the Psychodeli+ brand as captured from `~/Documents/dev/psychodeli-brand-guide/templates/shared-styles.css`. Read-only mirror; the canonical source is still the CSS file in the brand-guide repo. Includes the 10-ring gradient, six named section accents, Nunito 900 display typography, wordmark/monogram template paths, export pipeline commands, and the hard ownership rules.
- [`examples/render-brand.toml`](../examples/render-brand.toml) — Render's own cream-on-near-black OLED palette as a style guide. Mirrors the constants baked into `render_assets/matplotlibrc_dark.py` and the universal rules in `render.md`. Useful as the default brand for any render operation not targeting a specific project.

## When to write a new brand.toml

- A project has a coherent design voice documented anywhere (CSS custom properties, CLAUDE.md rules, a Figma file, a design spec)
- Multiple Render operations in a session should inherit the same tokens (blog hero + paper figure + social card, all in brand palette)
- The brand has ownership rules that should be enforced (e.g., "don't regenerate assets here")
- You want contrast/a11y auditing on the whole palette with one command

## When to skip

- One-off operations without a reusable palette
- The brand's tokens are already available in a form Render natively consumes (e.g., marginalia's `--mg-*` custom properties — those work directly without a style guide wrapper)
- You're sketching and don't know the final palette yet

## Where a brand.toml should live

Two patterns:

1. **Inside the owner repo.** The brand.toml lives alongside the canonical source (CSS, CLAUDE.md, Figma exports). Render imports it by absolute path: `load_styleguide("~/Documents/dev/psychodeli-brand-guide/brand.toml")`. One source of truth, no drift risk. Preferred when you have write access to the owner repo.

2. **Inside the render/examples/ directory.** Read-only mirror committed to the render repo. Fast to iterate, no cross-repo coordination, but requires manual sync when tokens change in the owner repo. Preferred for reference examples or brands whose owner repos you don't control.

The shipped Psychodeli example uses pattern 2 — a mirror committed under `render/examples/` because psychodeli-brand-guide already has its own canonical source and we don't want to add files to it unilaterally.

## Schema extensions

The schema is intentionally small. Reserved keys (listed above) have documented semantics and are enforced by the loader. **Non-reserved keys are preserved** in the raw parse and accessible via:

- `sg.rules.custom` — extra keys under `[rules]`
- `sg.dependencies` — the whole `[dependencies]` table, free-form
- `sg.export` — the whole `[export]` table, free-form

Use these for brand-specific conventions that don't fit the canonical schema. If multiple brands start using the same extension, promote it to a reserved key in a future loader version.
