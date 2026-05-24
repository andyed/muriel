# muriel v0.11.0 — sibling, not subordinate

*Released 2026-05-24.*

v0.9.0 made palette generation honest (8:1-by-construction). v0.11.0 adds three new surfaces, and each one is a **sibling** of something already in muriel rather than a new top-level concern. `muriel.spatial.ridgemap` joins `grid()` inside the spatial module under the same conventions. The `.agents/skills/muriel` broadcast symlink is a sibling install path to `.claude/skills/`. The new `muriel.tools.impeccable_bridge` wraps pbakaus/impeccable's deterministic detector as an *optional* pre-scan for `muriel-critique` — silent when absent, so the critique agent works identically with or without it. None of the three is a dependency; each is a peer. The rule running through the release is: **when an idea fits next to something already shipped, ship it as a sibling, not as a subordinate.**

---

## Headline 1 — `muriel.spatial.ridgemap()`

Where `grid()` scaffolds *space*, `ridgemap()` scaffolds *scalar fields*. Any source that yields one value per (x, y) — terrain DEM, gaze density, image luminance, attention map, audio spectrogram — feeds the same primitive, and the rendering choice (stacked 1D slices today; isolines / wireframe protrusion / hachured relief queued) is just which projection of the field you draw. First shipped projection is the Joy Division *Unknown Pleasures* stacked-1D-slice form, originally Harold Craft's 1970 PSR B1919+21 successive-period chart and ported to statistical density plots by Wilke's *ggridges* in 2016.

```python
from muriel.spatial import ridgemap
from muriel.layout import BBox

# field is any 2D iterable — list-of-lists, tuple-of-tuples, numpy ndarray.
# Each row becomes one ridge polyline.
rm = ridgemap(field, canvas=BBox(0, 0, 800, 600))
open("ridges.svg", "w").write(rm.svg())             # cream-on-near-black default
open("ridges-lineart.svg", "w").write(rm.svg(fill=None))  # no occlusion, every ridge visible
```

Pure Python, zero deps, duck-types numpy ndarray. Brand defaults clear the 8:1 floor (cream `#e6e4d2` on near-black `#0a0a14`, 15.42:1). Occlusion fill on by default — each ridge paints with a baseline-closed polygon so front ridges hide back ones, producing the iconic stacked-and-occluded look. `fill=None` switches to line-art mode (every ridge visible, useful when the back-to-front semantics aren't the point).

CLI:

```bash
python -m muriel.spatial --ridgemap                  # deterministic pulsar demo
python -m muriel.spatial --ridgemap --width 1600 --height 1000 -o pulsar.svg
python -m muriel.spatial --selftest                  # ridgemap assertions included
```

[`channels/spatial.md`](plugins/muriel/skills/compose/channels/spatial.md) grows a "ridgemap path" section alongside the existing perspective-grid section, plus a lineage table (Craft 1970 → Saville/Joy Division 1979 → Wilke 2016) and anti-prescriptions ("when row order is arbitrary, use a heatmap; when you need precise peak comparison, switch to `fill=None` or small multiples").

**Worked exemplar:** [`examples/scrutinizer-ridgemap/`](plugins/muriel/skills/compose/examples/scrutinizer-ridgemap/) — a vesica-piscis scalar field whose row-wise ridges trace an eye outline. Bottom half mirrored so the almond closes; pupil + iris core add the eyeball; rendered in Scrutinizer orange (#ff9933, 9.28:1) on a Blauch log-spaced concentric-ring scaffold (cmf_a=2.78).

Queued projections of the same primitive: filled-isoline bands (USGS / Imhof quadrangle register), wireframe protrusion from a grid (BYTE-cover / Tinney 3D mesh), hachured / halftone relief. One extractor stage, several emitters — the unifier is *scalar field → topology*. A future `channels/topography.md` will document the taxonomy before more emitters land.

## Headline 2 — `.agents/skills/muriel` broadcast symlink

One symlink, six harnesses. The repo now ships:

```
.agents/skills/muriel  →  ../../plugins/muriel/skills/compose
```

Git tracks it as a symlink (mode `120000`), not a copy — one canonical source, no duplication. Read **natively** by Codex CLI; read as an **alternate path** by Cursor, Gemini CLI, GitHub Copilot, OpenCode, and Pi. Six of the ten non-Claude harnesses gain a working install with zero additional packaging work.

Why this matters: until this release, muriel shipped natively only for Claude Code (plugin marketplace + `install.sh`). Every other harness got a one-paragraph "mirror the SKILL.md into `.<harness>/skills/muriel/`" hint in the README. The `.agents/skills/` convention — emerging as a convergent open standard for cross-harness skill discovery — closes most of that gap with one Unix symlink.

The full rollout plan lives in [`HARNESSES.md`](HARNESSES.md), modelled on impeccable's eleven-harness packaging matrix:

- **P0** (this release) — the broadcast symlink. Landed. Per-harness verification still TBD.
- **P1** (queued) — per-harness manifest generator (`.cursor-plugin/`, `.gemini-plugin/`, etc.); `./install.sh --harness <name>` for project-local discovery.
- **P2** (rolling) — SKILL.md frontmatter universalism (add `license`, `compatibility`, `metadata`, `allowed-tools` fields per the Agent Skills spec); marketplace submissions; critique-agent portability for non-Claude harnesses.

Critique-agent placement (`.agents/agents/muriel-critique.md` vs sibling location) is deferred to P1 because no harness has a documented convention for sub-agent definitions inside the broadcast skills dir.

## Headline 3 — `muriel.tools.impeccable_bridge`

[pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Skill 3.1.1, May 2026) ships a deterministic anti-pattern detector with twenty-seven rules across two categories (AI Slop + Quality) — `side-tab`, `border-accent-on-rounded`, `overused-font`, `gradient-text`, `ai-color-palette`, `nested-cards`, `monotonous-spacing`, `everything-centered`, `bounce-easing`, `dark-glow`, `icon-tile-stack`, `italic-serif-display`, `hero-eyebrow-chip`, `low-contrast`, `gray-on-color`, `line-length`, `cramped-padding`, `body-text-viewport-edge`, `tight-leading`, `skipped-heading`, `justified-text`, `tiny-text`, `all-caps-body`, `wide-tracking`, plus a few advisory rules. Runs in headless Chrome via Puppeteer, no API key required.

muriel's new `muriel.tools.impeccable_bridge` wraps `npx impeccable detect <target> --json` as an *optional* pre-scan for the `muriel-critique` agent:

```bash
python -m muriel.tools.impeccable_bridge https://example.com
# → ### Deterministic pre-scan — impeccable (3 findings)
#   | Rule | Severity | Where | What |
#   |---|---|---|---|
#   | `low-contrast` | high | .hero h1 | 2.1:1 on body bg |
#   …

python -m muriel.tools.impeccable_bridge --selftest
```

**Silent when unavailable.** `format_markdown(result)` returns `""` when Node, npx, network, or impeccable itself is missing — callers paste the output unconditionally and the section silently disappears. `verbose=True` (or `--verbose` on the CLI) re-enables the diagnostic line for debugging. The critique agent's description, primary workflow, and verdict rules are unchanged for the without-impeccable path; the integration is purely additive.

The shortest pipeline for a web artifact:

```
muriel capture <url> → muriel-critique invokes impeccable_bridge → vision model layers on top
```

`muriel-critique` covers what only a vision model can see (hierarchy, composition, brand voice, occlusion, perceptual issues, AI-tell beyond the named-ban list); impeccable covers what static rules can prove (contrast ratios, banned font families, line length, heading-level jumps, gradient text). The layering rule says don't re-derive impeccable's findings in the agent's own `## Issues` section — cite the pre-scan row and add only what static rules cannot detect.

## Side note — `vocabularies/data-viz-platforms.md`

New cross-platform charting vocab surveying seven platform guides with license posture spelled out per source (matters for citation discipline):

| Platform | License | Citable how |
|---|---|---|
| Apple HIG — *Charting data* | © Apple, all rights reserved | link + paraphrase only |
| Material Design 3 — Data viz | CC BY 4.0 | freely with attribution |
| IBM Carbon Charts | Apache 2.0 (code) / permissive docs | freely with attribution |
| Vega-Lite | BSD-3 | freely with attribution |
| Observable Plot | ISC | freely with attribution |
| FT Visual Vocabulary | MIT | freely with attribution |
| Datawrapper Academy | per-page; varies | link + paraphrase, check per article |

Closes with the **five-rule cross-platform consensus** (chart type from argument, hue not alone, motion serves readability, hierarchy via size + weight + position before colour, label every number) and the **divergence list** (contrast floor 4.5:1 vs muriel's 8:1, pie/donut tolerance, audio-graph parity, token discipline, animation budget). `channels/science.md`'s "Prior art / upstream" section gains an Apple HIG entry citing Swift Charts' audio-graph accessibility as a distinctive contribution.

## Compatibility

No breaking changes. Python 3.9+ as before. The `muriel.spatial.ridgemap` API is additive (the existing `grid()` signature is unchanged). The `muriel-critique` agent's primary workflow is unchanged for any artifact type that isn't HTML / URL / project-directory; for those types, the new pre-scan section is *optional* and conditional on impeccable being installed locally.

Pin against `muriel >= 0.10.0` if you depend on `muriel.spatial.ridgemap` or `muriel.tools.impeccable_bridge`. Pin against `>= 0.9.0` if all you need is the palette generator.

## Upgrade notes

```bash
pip install --upgrade muriel
# or the v0.11.0 wheel directly:
pip install https://github.com/andyed/muriel/releases/download/v0.11.0/muriel-0.11.0-py3-none-any.whl
```

The `.agents/skills/muriel` symlink is part of the repo; it doesn't ship in the Python wheel. Non-Claude-Code users who want the cross-harness install path should clone the repo (or download a release tarball) and let their harness discover the `.agents/skills/` tree from a project-local checkout — same model as the existing `install.sh` developer path for Claude Code.

If you're on Windows and the symlink doesn't resolve, that's a git-on-Windows issue with mode `120000` symlinks rather than a muriel issue — enable [`core.symlinks=true`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coresymlinks) in your local git config. Linux and macOS Just Work.

## Acknowledgements

- **[pbakaus/impeccable](https://github.com/pbakaus/impeccable)** (Apache-2.0) — for the deterministic detector this release wraps, and for the eleven-harness packaging matrix `HARNESSES.md` mirrors. Paul Bakaus did the discovery work for cross-harness skill distribution; muriel's plan is built on top of his.
- **Harold Craft / Peter Saville / Claus O. Wilke** — for the visual lineage `ridgemap()` borrows. Craft's 1970 pulsar profile chart through Saville's 1979 *Unknown Pleasures* sleeve through Wilke's 2016 *ggridges* R package is the same primitive, three times over.
- **Apple, Google, IBM, UW IDL, Observable, FT, Datawrapper** — for the platform charting guides surveyed in [`vocabularies/data-viz-platforms.md`](plugins/muriel/skills/compose/vocabularies/data-viz-platforms.md). The five-rule consensus they converge on is the strongest defence of muriel's own register when a reviewer pushes back.
