# muriel v0.9.0 — generate the palette, don't audit it

*Released 2026-05-17.*

The v0.8.0 release made the brand-token round-trip honest (corpus audit, three importer fixes, DTCG export). This release makes **palette generation** honest the same way. The seven named data-viz palettes shipped before this release (Wong, IBM, Tol × 5) pass muriel's universal 8:1 floor on a near-black background because their authors hand-picked saturations that happen to work. The new [`muriel.palettes.generate_for_floor()`](https://github.com/andyed/muriel/blob/main/muriel/palettes.py) inverts the relationship: pick a brand background and a contrast floor, and the palette is generated *at* the floor by construction. Every output color is guaranteed by the algorithm — not by audit — to clear the floor against your specific bg.

Alongside the generator, four widely-known theme palettes joined the registry — Catppuccin Mocha + Latte and Nord Aurora + Frost — under a new "theme tier" honestly tagged with their 8:1 footprint. The terminal channel gained an animated-effects section pulling kinetic typography into the terminal cell grid. The v0.8.0 release surfaces (README, SKILL.md, demo gallery) got synced to current reality, link-audited, and reorganized to lead with the spatial channel.

---

## Headline — `muriel.palettes.generate_for_floor()`

Adobe Leonardo's core insight, ported to muriel's stack:

```python
from muriel.palettes import generate_for_floor
from muriel.contrast import contrast_ratio

p = generate_for_floor("#0a0a0f", floor=8.0, n=6)
# → ['#ff78af', '#f68d15', '#98b300', '#00bfa8', '#0fafff', '#c092ff']

all(contrast_ratio(c, "#0a0a0f") >= 8.0 for c in p)
# → True
```

Pure Python, zero external deps. Routes through `muriel.oklch` (binary search on perceptual L for the WCAG target relative luminance, then on chroma for max sRGB-gamut saturation) and verifies with `muriel.contrast.contrast_ratio`. Direction auto-resolves to light on dark backgrounds and dark on light backgrounds; explicit `direction="light"|"dark"` available. Raises `ValueError` cleanly when the floor can't be reached (mid-tone bg + floor=10, etc.).

CLI:

```bash
muriel.palettes --generate --bg "#0a0a0f" --floor 8 --n 6
muriel.palettes --generate --bg "#fafafa" --floor 8 --n 6
muriel.palettes --generate --bg "#0a0a0f" --floor 4.5 --n 8   # WCAG AA
```

Output per-color with verified contrast inline, so the agent can copy the hex codes straight into a brand.toml with confidence.

Lineage: [`adobe/leonardo`](https://github.com/adobe/leonardo) (Apache-2.0).

## Theme palettes — Catppuccin + Nord

Four new entries in `muriel.palettes`:

| key | colors | 8:1 vs `#0a0a0f` | notes |
|---|---:|---:|---|
| `catppuccin_mocha` | 14 | **14/14** | Dark register. Among popular theme palettes, the only major one where every accent clears muriel's universal floor on a near-black canvas. |
| `catppuccin_latte` | 14 | 0/14 | Light register. Decorative-only against muriel's standard backgrounds — designed for Latte's own `#eff1f5` base. Use as fills, markers, chrome. |
| `nord_aurora` | 5 | 2/5 | Red + orange clear 8:1; the muted yellow, green, purple are decorative-only. |
| `nord_frost` | 4 | 2/4 | The two lighter teals clear 8:1; the deeper Frost blues are decorative-only. |

`muriel.palettes` is now an 11-palette registry organized into two tiers:

- **Data-viz tier** (Wong / IBM / Tol × 5) — colorblind-tested, audited for 8:1 against muriel's standard backgrounds. Reach when encoding categorical series in scientific figures.
- **Theme tier** (Catppuccin × 2 / Nord × 2) — aesthetic-first, brand register, *not* colorblind-tested. Reach for editorial / UI / brand chrome / decorative fills.
- **And the generator** — for brand-bg-specific 8:1-by-construction palettes.

Citations now tell the truth per palette per standard bg, so an agent picks the right tool from one read of `citation(name)`.

Both MIT.

## Terminal channel — animated effects

New section in [`channels/terminal.md`](https://github.com/andyed/muriel/blob/main/plugins/muriel/skills/compose/channels/terminal.md) and matching row in [`vocabularies/kinetic-typography.md`](https://github.com/andyed/muriel/blob/main/plugins/muriel/skills/compose/vocabularies/kinetic-typography.md) document [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects) (MIT) as the substrate for terminal-as-artifact moments — installer ceremonies, deploy banners, README hero GIFs. Same kinetic-typography rules (max contrast, strategic motion, no ambient noise, rehearsed emotional vocabulary), new runtime (ANSI cells instead of canvas).

Anti-prescription specific to this substrate: *don't animate text the reader needs to re-read. Once captured as a GIF, the GIF replays on every page load; if it's still saying something on the third replay, you over-animated.*

## color.js citation in `muriel.contrast` + `muriel.oklch`

Both module docstrings now cite [`color-js/color.js`](https://github.com/color-js/color.js) (MIT, by the CSS Color Module spec editors) as the spec-authoritative reference. It covers what muriel's stdlib subset doesn't: APCA / WCAG 3 draft ratios, non-sRGB gamuts, delta-E, every CSS Color 4 space. muriel stays the path for the 8:1 enforcement floor; color.js is the drop-down when you need more.

## Site + doc polish (consequences of v0.8.0)

- **README link audit.** 11 broken paths repathed to `plugins/muriel/skills/compose/...` and `plugins/muriel/agents/...` (artifacts of the plugin-packaging move that the v0.7-era doc text predated). 4 broken `github.com/andyed/muriel/...` URLs in the demo page repathed for the same reason. All 21 local refs + 9 GitHub URLs now resolve.
- **README critique-agent install section rewritten.** The old `ln -s ~/Documents/dev/muriel/agents/...` instructions pointed at a path that no longer existed (the file moved with the plugin packaging). Anyone following created a broken symlink. Replaced with the truth: the subagent ships with the muriel plugin and is loaded automatically by both install paths.
- **PyPI badge → GitHub Release badge.** muriel ships v0.8.0+ wheels via GitHub Releases; PyPI is not yet published. Badge now auto-tracks the latest tag.
- **muriel.mindbendingpixels.com bullet** added to README Showcase as the primary landing page (Scrutinizer demoted to its rightful spot as a downstream consumer).
- **Demo gallery reorganized** to lead with `Spatial` paired against `Typography` (drop-cap × log-polar cortical grid) — the headline pair of the design-history-aware register. 10 cards, one per channel, with 5 stale Science cards retired per the "one canonical exhibit per channel" frame.
- **Demo Install section** now leads with `/plugin install muriel@andyed-muriel`, then the wheel-from-Release pip line, then the developer-clone install.
- **README + SKILL.md** synced to twelve output channels (was eleven — spatial was missing); Diagrams entry credits the shipped Mermaid → SVG/ASCII and TeX → SVG (MathJax) bridges; Style-guides cross-ref names the v0.8.0 DTCG round-trip.

## Try it

```bash
# Generate a guaranteed-8:1 brand palette
muriel.palettes --generate --bg "#0a0a0f" --floor 8 --n 6

# Use a theme palette (knows its own 8:1 footprint)
python -c "from muriel.palettes import palette, citation; \
  print(palette('catppuccin_mocha', n=6)); \
  print(citation('catppuccin_mocha'))"

# Swatch sheet — all 11 palettes
python -m muriel.palettes --swatches /tmp/swatches.svg
```

## Upgrade notes

**No breaking changes.** Strictly additive — new function, new palette constants, new doc sections. The two-tier docstring rewrite preserves every previously-public name (`WONG`, `IBM`, `TOL_BRIGHT`, etc.) verbatim.

Python 3.10 still supported for everything in this release. Python 3.11+ continues to be required for file-based `muriel.dtcg_export.export_dtcg(path)` (stdlib `tomllib`).

## Verified

```
python -m muriel.palettes --selftest        # passes (8 invariants)
python -m muriel.patterns --selftest        # still passes
python -m muriel.spatial --selftest         # still passes
python -m muriel.dtcg_export --selftest     # still passes
python -m muriel.palettes --swatches OUT.svg  # 11 rows render cleanly
```

## Credits — sources of inspiration

Same MIT-first preference as v0.8.0.

### MIT (new this release)

- [`catppuccin/catppuccin`](https://github.com/catppuccin/catppuccin) — Mocha + Latte flavors lifted into `muriel.palettes`. Soothing pastels designed for syntax-highlighting + UI theming.
- [`nordtheme/nord`](https://github.com/nordtheme/nord) — Aurora + Frost subsets lifted into `muriel.palettes`. The Arctic, north-bluish palette.
- [`ChrisBuilds/terminaltexteffects`](https://github.com/ChrisBuilds/terminaltexteffects) — TTE, documented in `channels/terminal.md` as the animated-terminal substrate.
- [`color-js/color.js`](https://github.com/color-js/color.js) — spec-authoritative color-science reference cited in `muriel.contrast` + `muriel.oklch`.

### Apache-2.0 (new this release)

- [`adobe/leonardo`](https://github.com/adobe/leonardo) — algorithm + framing for `generate_for_floor()`. Leonardo's idea is the one that does the work: palettes generated at a target contrast ratio, not generated freely and audited. The muriel function is a Python port scoped to the OKLCH + WCAG-2.1 substrate.

### Continuing credits from v0.8.0

awesome-design-md, three.js, css-doodle, glisp, nannou, noc-book-2, style-dictionary, theo, W3C Design Tokens Community Group format — all from the v0.8.0 release notes. Still in play.

## What's next

- **Wire `generate_for_floor()` into `muriel.styleguide`** so a brand.toml can declare `viz.categorical.from_contrast_floor = { bg = "background", floor = 8.0, n = 8 }` and have the palette materialize at load time, brand-bg-aware.
- **Round-trip integration**: import a corpus brand → `generate_for_floor` from its accent color against its canvas → export as DTCG. Closes the corpus → rigor → downstream loop end-to-end.
- **Demo-page card** for `generate_for_floor()` — the "type the contrast you want; we'll find the colors" moment.
- **Catppuccin's Frappé + Macchiato flavors** (currently shipping only Mocha + Latte) if the two-flavor coverage proves insufficient for any project.
- **Sankey diagram primitive** — the queued TODO item now has confirmed substrate options (`floweaver` MIT for Python-side, `d3-sankey` BSD-3 via Node bridge for the algorithm port).
