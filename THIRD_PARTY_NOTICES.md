# Third-Party Notices

muriel incorporates work from the projects listed below. Their license terms
are reproduced in full as required.

## Acknowledged inspiration not incorporated

### SVG Wave

[`anup-a/svgwave`](https://github.com/anup-a/svgwave) made layered SVG-wave
generation approachable and directly inspired the decision to add
`muriel.patterns.wavefield()`.

No SVG Wave source code, assets, dependencies, algorithms, UI, presets, or
generated files are copied, translated, vendored, imported, or linked into
muriel. The Muriel primitive is an independent Python implementation based on
seeded harmonic synthesis, caller-supplied normalized series, and a standard
Catmull-Rom-to-cubic interpolation construction.

This separation is deliberate: SVG Wave's repository `LICENSE` prohibits
commercial use and modification, while its `package.json` declares ISC. This
notice credits the project as inspiration; it does not claim that its code is
licensed for incorporation into Muriel.

---

## diagram-design

The layout proportions and conventions for the `layer_stack`, `pyramid`, and
`swimlane` diagram generators (`muriel/tools/diagrams/layer_stack.py`,
`muriel/tools/diagrams/pyramid.py`, `muriel/tools/diagrams/swimlane.py`) —
band/tier/lane heights, the linear-taper and proportional-width rules, lane
dividers and handoff emphasis, label placement, and the single-focal-accent
convention — are adapted from the `diagram-design` Claude Code skill.

- Source: https://github.com/cathrynlavery/diagram-design
- Adapted: 2026-05 (diagram-design relicensed to MIT)
- Upstream re-checked: 2026-08-13 — the three adapted references (`type-layers.md`,
  `type-pyramid.md`, `type-swimlane.md`) are unchanged since the adaptation, so this
  notice still describes what muriel carries. Upstream has grown substantially
  elsewhere; the delta is summarised in the README's "Related prior art" entry.

muriel's own contribution is the deterministic Python generators, the
epistemic-precondition / anti-prescription gate on each diagram, the 8:1
contrast floor (stricter than the source's WCAG AA), and integration with
muriel's brand tokens. The source's typefaces and colour system were **not**
adopted.

Two verification ideas were adapted from the same repository (upstream commit
`dc1ace4`, 2026-09-19) on 2026-09-24:

- **Accessible-SVG lint rules** — `muriel/tools/diagrams/_a11y.py::lint_a11y`
  re-implements the rule set of `scripts/lint-skin.py::lint_accessible_svgs`
  (with `scripts/test-lint-a11y.py` as the fixture model): skip
  `aria-hidden="true"` SVGs; require `role="img"`, a four-number viewBox with
  positive size, `<title>` as the first child, a `<desc>`, slug-prefixed
  non-duplicate ids, and `aria-labelledby` naming the title then the desc. The
  60-character title bound follows `skills/diagram-design/scripts/self_check.py`.
- **Slopegraph conventions** — `muriel/tools/diagrams/comparison_pair.py` follows
  `references/type-line.md` (slopegraph variant): one scale shared by both
  axes, a run narrower than the plot is tall, dots and printed values at both
  ends, no gridlines, muted lines plus one weighted accent, and labels bound to
  their series by `data-*` attributes. The shared-scale and no-jitter checks in
  `tests/test_diagram_comparison_pair.py` follow `scripts/verify-slopegraph.py`.
  The label-spreading policy (labels move, endpoints never do) and the trace
  form are muriel's own.
- **Relative-error fidelity check** — `tests/test_diagram_fidelity.py` checks
  proportional funnel widths as *relative* error against the values, the
  framing of `scripts/verify-treemap.py`'s area-fidelity invariant, applied to
  bar width instead of cell area.
- **Motion contract** — the static-first rule, the none / reveal / step / loop
  modes with reveal as the only autoplay, the 3 s decorative-loop floor, and the
  8-step / 2-per-step / 12-item sequence budget follow `references/animation.md`
  and ADRs 0001 / 0003. They land in `references/polish-rules.md` (rules 28–29)
  and `muriel/motion.py` (`validate_mode`, `validate_flash_rate`,
  `validate_sequence_shape`). The upstream clock tokens and pinned controller
  were not adopted.
- **Diagram guidance** — behaviour-first pattern routing, the generator
  admission rule, callout discipline, the global node/arrow budget, and the
  redraw degrade ladder in `channels/diagrams.md`, plus the per-element removal
  test in `agents/muriel-critique.md`, paraphrase `references/semantic-patterns.md`,
  `references/output-spec.md`, `references/primitive-annotation.md`, and the
  skill's SKILL.md.

The code is muriel's own (ElementTree rather than the source's `HTMLParser`,
and wired into `muriel diagram-check`); no source files were copied.

```
MIT License

Copyright (c) 2025 Cathryn Lavery

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ui-ux-pro-max corpus

The CSV reference data under `muriel/uipromax/data/` (`colors.csv`,
`typography.csv`, `ui-reasoning.csv`, `ux-guidelines.csv`, `styles.csv`,
`charts.csv`, `icons.csv`) is a **verbatim** port of the `ui-ux-pro-max` skill's
data files — product-type colour sets, font pairings, UI-reasoning rules, UX
guidelines, design styles, chart taxonomy, and an icon index.

- Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Via: https://github.com/All-The-Vibes/ATV-Design (`skills/ui-ux-pro-max/`)
- Adapted: 2026-06 (both upstreams MIT)

muriel's own contribution is the accessor layer (`muriel/uipromax/__init__.py`)
and the **8:1 contrast re-gate**: the colour sets target WCAG 3:1/AA, so each is
measured against muriel's universal 8:1 floor via `muriel.contrast`. The data
itself is unchanged; muriel adds no colours. The source palettes' interactive
pairs (`On Primary`, `On Accent`, destructive, muted-on-muted) are reported as
sub-8:1 and **not adopted** as compliant — only the body-text pairs that clear
8:1 are surfaced as muriel starting points. A copy of the upstream MIT license
also ships at `muriel/uipromax/LICENSE.txt`.

```
MIT License

Copyright (c) 2024 Next Level Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## emil-design-eng-inspired (motion principles)

The motion-quality axes added to `muriel/motion.py` (compositor-safe property
set, easing-by-direction, entrance scale floor) and to
`plugins/muriel/skills/compose/channels/polish.md` (rules 18–22) are paraphrased
from the `emil-design-eng-inspired` skill — itself MIT-licensed original prose
that the ATV-Design authors wrote as a clean-room paraphrase of Emil Kowalski's
`emil-design-eng` skill.

- Source: https://github.com/All-The-Vibes/ATV-Design (`skills/emil-design-eng-inspired/`)
- Lineage: paraphrases https://github.com/emilkowalski/skill (MIT as of 2026-06-21; it carried no license when muriel first adapted via ATV-Design's clean-room paraphrase)
- Adapted: 2026-06 (ATV-Design MIT)

muriel's own contribution is the programmatic enforcement (`validate_properties`,
`easing_for`, `validate_scale`) and the integration with muriel's existing
polish rules. muriel deliberately **does not adopt** the source's duration
*bands* (100–500 ms) — they fall in `muriel.motion`'s uncanny zone, where the
forced utility (≤ 100 ms) / cinematic (≥ 1500 ms) binary overrides them — and
keeps its own tuned `0.96` press-scale value over the source's `0.97`.

```
MIT License

Copyright (c) 2026 atv-design contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## vibecoded-design-tells (devibe rules)

The rule table in `muriel/devibe.py` — the design-tell catalogue (shadcn
defaults, AI-purple, gradient text, the cream + serif + sage "tasteful default",
neon glow, emoji-as-icons, the hero + three-card skeleton) and their regex
signatures — is **derived** from the `vibecoded-design-tells` project: a
Reddit-mined ranking of the visual tells of AI-built sites (3.2M posts / 3,033
on-topic comments across 47 subreddits), with a standalone scanner
(`skill/scripts/devibe_scan.py`) and catalogue (`skill/references/tells.md`).

- Source: https://github.com/JCarterJohnson/vibecoded-design-tells
- Adapted: 2026-06 (MIT)

muriel's own contributions: (1) the data-source severities are **re-ranked** to
muriel's `info`/`warn`/`error` triple, with the cream + serif + sage combination
elevated to `error` because it is the look muriel — and Claude's house style
generally — is most likely to emit on autopilot; (2) an **8:1 contrast
cross-check** the source scanner has no equivalent of — colour tells that capture
a concrete hex are measured against muriel's 8:1 floor via `muriel.contrast` on
muriel's two canonical backgrounds (`#ffffff`, `#0a0a0f`), so a default colour
that *also* fails accessibility is reported as such; (3) integration as a critique
gate (`muriel/critique.py`, check 5) on HTML artifacts. muriel deliberately does
**not** vendor the project's harvested Reddit text or quote banks — those are
public Reddit content belonging to their authors; only the rule logic is derived.

```
MIT License

Copyright (c) 2026 Carter Johnson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## baoyu-infographic (dense-modules module vocabulary)

The module vocabulary and high-density-guide recipe in
`plugins/muriel/skills/compose/channels/infographics.md` — the seven typed
module archetypes (Option Array, Scale/Gauge, Anatomy Callout, Use-Case
Matrix, Diagnostic Checklist, Pitfall Panel, TL;DR Block), the
every-module-carries-concrete-data density rule, and the text-placement
conventions (module-count subtitle, badge-framed module headers, data values
oversized in the accent color) — are adapted from the `dense-modules` layout
definition in the `baoyu-infographic` skill of the `baoyu-skills` collection.

- Source: https://github.com/JimLiu/baoyu-skills (`skills/baoyu-infographic/references/layouts/dense-modules.md`)
- Adapted: 2026-07 (MIT)

muriel's own contribution is the re-cast from prompt spec to **content
contract** — each module declares structured-input minimums (item counts,
required numerics, stated consequences) that a deterministic SVG panel
builder can refuse to render below — plus genre-neutral renamings of the
source's buying-guide-specific module names. Two source rules are
deliberately **not** adopted: the shrink-text-and-eliminate-whitespace
density rule (it conflicts with muriel's 18px type floor and 8:1 contrast
floor — density comes from module count and data specificity instead), and
emoji quality indicators (muriel renders drawn ✓/✗ glyphs). The source's
raster generation pipeline (prompt-to-image via image-gen backends) is not
used in any form — muriel's lane is deterministic SVG.

```
MIT License

Copyright (c) 2026 Jim Liu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
