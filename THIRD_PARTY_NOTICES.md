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
