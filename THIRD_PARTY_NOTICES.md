# Third-Party Notices

muriel incorporates work from the projects listed below. Their license terms
are reproduced in full as required.

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

muriel's own contribution is the deterministic Python generators, the
epistemic-precondition / anti-prescription gate on each diagram, the 8:1
contrast floor (stricter than the source's WCAG AA), and integration with
muriel's brand tokens. The source's typefaces and colour system were **not**
adopted.

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
