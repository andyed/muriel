# Style guides — brand tokens as importable schema

A style guide is a brand's design tokens — colors, typography, spacing, radii, elevation, motion, iconography, imagery, logo lockups, voice, and accessibility floors — serialized so muriel can import them and use them in any channel without reinventing them and without violating "this brand is owned by X repo, don't regenerate here" rules.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map. Related: [`raster.md`](raster.md) for asset generation, [`web.md`](web.md) for marginalia CSS tokens, [`science.md`](science.md) for matplotlib rcparams.

## Why this exists

Every project that ships visuals has a design voice — OLED dashboard, copperplate wordmark, editorial marginalia, kinetic typography, warm light-mode explainer, cream-on-near-black. Each of those typically lives in its own ad-hoc form — CSS custom properties here, Python constants there, a CLAUDE.md rule somewhere else — and without a schema, muriel has no principled way to import one.

A style guide schema fixes that: one file per brand, one loader, one dataclass-tree in memory. When muriel gets a task in the context of a brand, it loads the brand.toml, inherits the tokens, and respects the rules.

## Schema v2

A brand.toml has up to 17 top-level tables. Only `[meta]` (with `name`) and `[colors]` (with `background` + `foreground`) are required. Every other block is optional — populate the ones your brand actually cares about.

```toml
[meta]
name             = "Acme Research"
slug             = "acme-research"
version          = "2.0.0"
owner_repo       = "acme-brand-guide"
owner_path       = "<brand-guide-repo>"
canonical_source = "tokens.css"
ownership_rule   = "Acme brand assets are owned by acme-brand-guide; do not regenerate elsewhere."

# ── Colors: raw palette + free-form named accents + rings + aliases ──
[colors]
background        = "#0a0a0f"       # required
foreground        = "#e6e4d2"       # required
background_2      = "#0f1117"
background_3      = "#1a1a24"
foreground_muted  = "#b0b0c4"
accent            = "#50b4c8"
accent_ink        = "#7dd4e4"
accent_decorative = "#d4a574"       # decorative only (exempt from 8:1 text rule)

[colors.named]
deepsea     = "#50b4c8"
wildflowers = "#ff8fc8"

[colors.rings]
r1 = { color = "#91d7f8", width_px = 6 }

[colors.aliases]
text             = "foreground"
text-muted       = "foreground_muted"
surface-primary  = "background"
decorative       = "accent_decorative"

# ── Semantic states: UI feedback as {text, surface, border} trios ──
[semantic.success]
text    = "#66bb6a"
surface = "#0f1a10"
border  = "#66bb6a"

[semantic.error]
text    = "#ff8282"
surface = "#1a0f0f"
border  = "#ff8282"

# (+ warning, info — same shape)

# ── Data-viz palettes ──
[viz]
categorical = ["#e6e4d2", "#50b4c8", "#66bb6a", "#e6a817", "#ff8282"]
sequential  = ["#0a0a0f", "#2a3a5a", "#7ba2c8", "#e6e4d2"]
diverging   = ["#ff8282", "#e6e4d2", "#50b4c8"]

# ── Typography: font stacks + named type scale ──
[typography]
display_family              = "Nunito, Helvetica, sans-serif"
display_weight              = 900
display_letter_spacing_em   = -0.04
body_family                 = "Helvetica, Arial, sans-serif"
mono_family                 = "'SF Mono', Menlo, monospace"

[typography.scale]
display    = { size = 72, weight = 900, line_height = 0.95, tracking_em = -0.04 }
h1         = { size = 48, weight = 900, line_height = 1.05 }
h2         = { size = 32, weight = 700, line_height = 1.10 }
h3         = { size = 24, weight = 700, line_height = 1.20 }
h4         = { size = 20, weight = 600, line_height = 1.25 }
body       = { size = 17, weight = 400, line_height = 1.60 }
body_small = { size = 15, weight = 400, line_height = 1.50 }
caption    = { size = 13, weight = 400, line_height = 1.40 }
label      = { size = 12, weight = 700, line_height = 1.20, tracking_em = 0.08, upper = true }
mono       = { size = 14, weight = 400, line_height = 1.60 }

# ── Structural tokens ──
[spacing]
xxs = 2; xs = 4; sm = 8; md = 16; lg = 24; xl = 40; xxl = 64; huge = 96

[radii]
sm = 6; md = 12; lg = 20; pill = 9999

[elevation]
low  = "0 1px 3px rgba(0,0,0,0.35)"
mid  = "0 6px 18px rgba(0,0,0,0.45)"
high = "0 18px 56px rgba(0,0,0,0.60)"

# ── Motion ──
[motion]
duration_fast     = 120
duration_normal   = 240
duration_slow     = 480
easing_default    = "cubic-bezier(0.2, 0.0, 0.2, 1.0)"
easing_emphasis   = "cubic-bezier(0.4, 0.0, 0.2, 1.0)"
motion_preference = "respect-prefers-reduced-motion"

# ── Iconography & imagery ──
[iconography]
family        = "phosphor"
stroke_px     = 1.5
default_size  = 20
sizes         = [16, 20, 24, 32, 48]

[imagery]
style       = "muted-duotone"
treatments  = ["cream-wash", "amber-tint"]
crop_policy = "preserve-faces"   # wires into smartcrop

# ── Logo: four variants + clear-space + min-width ──
[logo]
clear_space_em = 1.5
min_width_px   = 120

[logo.wordmark]
svg = "sources/logo-wordmark.svg"
png = "renders/logo-wordmark.png"

# (+ [logo.monogram], [logo.stacked], [logo.horizontal] — same shape)

# ── Voice: adjectives + do/don't examples for editorial ──
[voice]
adjectives = ["technical", "warm", "cited", "restrained"]
say_yes    = ["Lead with the data.", "Cite primary sources."]
say_no     = ["No hype language.", "No exclamation points."]

# ── Accessibility floors ──
[a11y]
min_contrast_ratio   = 8.0
min_hit_target_px    = 44
focus_ring_color     = "accent_ink"   # raw-name, hex, or [colors.named] key
focus_ring_width_px  = 3
motion_reduce_policy = "collapse-to-zero"

# ── Ownership rules ──
[rules]
never_modify_sources                     = true
never_rebuild_image_generation_elsewhere = true
brand_owner                              = "acme-brand-guide"
```

## Loading a style guide

```python
from muriel.styleguide import load_styleguide

sg = load_styleguide("examples/example-brand.toml")

# Meta
sg.meta.name                                # → 'Acme Research'

# Colors
sg.colors.background                        # → '#0a0a0f'
sg.colors.resolve_alias("text")             # → '#e6e4d2'
sg.colors.named["wildflowers"]              # → '#ff8fc8'

# Semantic states
sg.semantic["success"].text                 # → '#66bb6a'
sg.semantic["error"].surface                # → '#1a0f0f'

# Data viz
sg.viz.categorical                          # → ('#e6e4d2', '#50b4c8', ...)
sg.viz.sequential[-1]                       # → '#e6e4d2'

# Type scale
sg.typography.scale["h1"].size              # → 48
sg.typography.scale["h1"].weight            # → 900
sg.typography.scale["label"].upper          # → True

# Structural
sg.spacing["md"]                            # → 16
sg.radii["pill"]                            # → 9999
sg.elevation["high"]                        # → '0 18px 56px rgba(0,0,0,0.60)'

# Motion
sg.motion.duration_normal                   # → 240
sg.motion.easing_default                    # → 'cubic-bezier(0.2, 0.0, 0.2, 1.0)'

# Iconography / imagery
sg.iconography.default_size                 # → 20
sg.imagery.crop_policy                      # → 'preserve-faces'

# Logo
sg.logo.wordmark.svg                        # → 'sources/logo-wordmark.svg'
sg.logo.clear_space_em                      # → 1.5

# Voice
sg.voice.adjectives                         # → ('technical', 'warm', ...)
sg.voice.say_no                             # → ('No hype language.', ...)

# A11y
sg.a11y.min_contrast_ratio                  # → 8.0
sg.a11y.min_hit_target_px                   # → 44
```

`StyleGuide` is a frozen dataclass — safe to pass between functions without anyone mutating tokens mid-operation.

## Respecting brand ownership

Brand rules aren't advisory — they're enforced:

```python
try:
    sg.rules.check("regenerate-wordmark")
except RuleViolation as exc:
    print(exc)
    # → "Operation 'regenerate-wordmark' is owned by acme-brand-guide
    #    and cannot be performed here. Use the owner's export pipeline instead."
```

Operations that trip `never_rebuild_image_generation_elsewhere`:
- any name containing `wordmark`, `monogram`, `logo`, `favicon`, `brand-asset`, `app-icon`, `regenerate-image`

Operations that trip `never_modify_sources`:
- `modify-source`, `filter-source`, `blur-source`

Call `sg.rules.check(operation)` at the top of any handler that might generate brand-owned artifacts. Catch `RuleViolation` and redirect to the brand's `[export]` commands instead.

## Derived outputs

### matplotlib rcparams

```python
import matplotlib as mpl
mpl.rcParams.update(sg.to_matplotlibrc())
```

Emits a rcparams dict with brand colors wired in, type sizes drawn from `typography.scale["body"]` and `typography.scale["h2"]`, and — when `viz.categorical` is populated — the default color cycle bound to the brand's categorical palette.

### CSS custom properties

```python
print(sg.to_css_vars(prefix="--brand-"))
```

Emits a `:root { ... }` block covering **every** token: raw colors, named accents, ring stops, semantic states (text / surface / border per state), spacing, radii, elevation shadows, motion durations + easings, the full type scale (size + weight + line-height + tracking per role), and a11y hooks (focus-ring color + width, min-hit-target).

Use `prefix="--mg-"` to target marginalia overrides, though colors may not map 1:1.

### WCAG contrast audit

```python
for role, ratio, passes in sg.audit_contrast():
    mark = "✓" if passes else "✗"
    print(f"  {mark} {role:<22} {ratio:5.2f}:1")
```

Audits every text-bearing role — raw colors (`foreground`, `foreground_muted`, `accent`, `accent_ink`), named accents, and semantic-state `text` colors — against `colors.background`. Default threshold is `sg.a11y.min_contrast_ratio` (8.0 unless overridden). Pass `required=4.5` to audit against WCAG AA instead.

## CLI

```bash
# Describe a style guide
muriel styleguide examples/muriel-brand.toml

# Emit CSS custom properties
muriel styleguide examples/example-brand.toml --css

# Emit CSS with a custom prefix (e.g., to override marginalia)
muriel styleguide examples/example-brand.toml --css --css-prefix '--mg-'

# Contrast audit (exit 1 if any role fails the brand's a11y floor)
muriel styleguide examples/example-brand.toml --contrast

# Override the brand's own threshold
muriel styleguide examples/example-brand.toml --contrast --required 4.5
```

## Shipped examples

- [`examples/muriel-brand.toml`](../examples/muriel-brand.toml) — muriel's own cream-on-near-black OLED palette as a style guide. Demonstrates every v2 block (colors + semantic + viz + full type scale + spacing/radii/elevation + motion + iconography + imagery + logo + voice + a11y). Mirrors the constants in `muriel/matplotlibrc_dark.py` and the universal rules in `SKILL.md`. The canonical reference for the schema.
- [`examples/example-brand.toml`](../examples/example-brand.toml) — a fictional "Acme Research" brand with four logo variants, ring gradient, four named brand accents, `preserve-faces` crop policy, and hard ownership rules. Shows how a non-muriel brand would structure its own tokens.

## When to write a new brand.toml

- A project has a coherent design voice documented anywhere (CSS custom properties, CLAUDE.md rules, a Figma file, a design spec)
- Multiple muriel operations in a session should inherit the same tokens (blog hero + paper figure + social card, all in brand palette)
- The brand has ownership rules that should be enforced (e.g., "don't regenerate assets here")
- You want contrast / a11y auditing on the whole palette with one command

## When to skip

- One-off operations without a reusable palette
- The brand's tokens are already available in a form muriel natively consumes (e.g., marginalia's `--mg-*` custom properties — those work directly without a style guide wrapper)
- You're sketching and don't know the final palette yet

## Where a brand.toml should live

Two patterns:

1. **Inside the owner repo.** The brand.toml lives alongside the canonical source (CSS, CLAUDE.md, Figma exports). muriel imports it by absolute path: `load_styleguide("<brand-guide-repo>/brand.toml")`. One source of truth, no drift risk. Preferred when you have write access to the owner repo.

2. **Inside the muriel/examples/ directory.** Read-only mirror committed to the muriel repo. Fast to iterate, no cross-repo coordination, but requires manual sync when tokens change in the owner repo. Preferred for reference examples or brands whose owner repos you don't control.

## Imagery `crop_policy` — the smartcrop hook

`[imagery].crop_policy` is muriel's declarative way of saying "when this brand has its images cropped, which hard-avoids should be active." Values:

| Value | smartcrop behavior |
|---|---|
| `"energy-only"` | Edges + saturation scoring only (v0.1 default; no extras needed) |
| `"preserve-faces"` | `--faces on` — requires `pip install muriel[faces]` |
| `"preserve-text"` | `--text on` — requires `pip install muriel[text]` |
| `"preserve-both"` | Both detectors on — requires both extras |

smartcrop reads the loaded brand's `imagery.crop_policy` as its default, so channel handlers don't need per-call flags — the brand declares its policy once.

## Schema extensions

The schema is intentionally bounded. Reserved keys (the ones listed in this document) have documented semantics and are enforced by the loader. Non-reserved keys are preserved in:

- `sg.rules.custom` — extra keys under `[rules]`
- `sg.dependencies` — the whole `[dependencies]` table, free-form
- `sg.export` — the whole `[export]` table, free-form
- `sg.colors.named` — free-form brand accent dictionary

Use these for brand-specific conventions that don't fit the canonical schema. If multiple brands start using the same extension, promote it to a reserved key in a future loader version.

## Anti-patterns

- **Don't put raw hex values at the component level.** Route through `colors.aliases` so a theme switch or brand refresh propagates.
- **Don't conflate semantic states with the raw palette.** `note/tip/warning/important` go under `[semantic.*]` as `{text, surface, border}` trios, not as fields in `[colors]`. The audit tool cares about the distinction — text-bearing semantic colors must clear `a11y.min_contrast_ratio`.
- **Don't invent ad-hoc role names.** Use the four-layer decomposition: brand / neutral / semantic / extended (data viz). Keep aliases to this vocabulary.
- **Don't ship a `brand.toml` without an `ownership_rule`** — even "free to use for any output" is a rule worth stating explicitly.
- **Don't use the `display_*` fields and leave `[typography.scale]` empty.** The scale is what gets consumed by matplotlib / CSS / raster; the top-level `display_*` fields are metadata only.
- **Don't set `min_contrast_ratio` below 8.0 without a written reason.** The 8:1 floor is muriel's universal rule — relaxing it per-brand should be a deliberate, documented choice.
