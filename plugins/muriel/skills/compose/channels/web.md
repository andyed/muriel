---
channel: web
status: active
requires:
  brand: optional
  audience: required
  reads:
    - muriel.contrast
    - muriel.dimensions
output:
  kinds: [html]
  registers: [blog, editorial]
peer_channels:
  - interactive
  - svg
  - infographics
---

# Web — editorial HTML and static capture

Use this channel for prose-led web artifacts, Marginalia pages, Markdown-to-HTML
or PDF pipelines, and browser-rendered stills. Use `interactive.md` when the
reader manipulates the artifact; use `polish.md` for tactile product UI.

## Purpose in the solution

Make the content hierarchy, reading path, responsive behavior, and export path
part of the implementation—not a decorative pass after the page works.

Before editing, tell the calling agent:

- **Purpose:** which reading or presentation problem this channel will solve.
- **Integration:** which existing content, component, or build path it will
  preserve.
- **Proof:** which rendered viewport, contrast audit, or export will verify it.

## Default workflow

1. Identify the audience, primary reading task, and destination: live page,
   self-contained HTML, PNG, or PDF.
2. Inspect the existing content and design tokens before choosing a visual
   register.
3. Put the core narrative inline. Use sidebars and margin notes only for
   optional depth.
4. Implement semantic HTML, a readable measure, responsive behavior, and
   keyboard-visible links and controls.
5. Render the real page, inspect at representative widths, and run the
   contrast audit.
6. Report the web decision that changed, the code or artifact carrying it, and
   the rendered evidence.

## High-leverage rules

- Keep body prose near `65–75ch`; never center-align paragraphs.
- Keep all text at Muriel's 8:1 floor. Demote with size, weight, and space—not
  opacity.
- Use a deliberate typeface and palette; avoid pure `#000`/`#fff`, default
  gradient heroes, and repeated-card filler.
- Keep essential content in the main flow. One optional aside per section is a
  useful ceiling.
- Preserve semantic heading order, landmarks, focus visibility, and reduced
  motion.
- Never hotlink placeholder imagery. Use local, generated, or embedded assets.
- Wait for fonts before capture and verify the actual DOM width rather than a
  screenshot crop.
- Animate `transform` and `opacity`, never layout properties.

## Choose the build path

| Need | Path |
|---|---|
| Editorial page with callouts | Marginalia HTML/CSS |
| Markdown that must fan out to HTML/PDF/DOCX | Pandoc + Marginalia Lua filter |
| Highly customized single-target explainer | `marginalia-md.js` + project build script |
| Browser page frozen to PNG | Playwright or `muriel.capture` |
| HTML converted to paged PDF | WeasyPrint |
| One portable file | Data-URI embedding, within a deliberate size budget |

### Minimal Marginalia setup

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.css">
<script src="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.js" defer></script>
```

Use `mg-` classes and `--mg-*` tokens. Pick one document theme—OLED dark or
warm editorial light—and keep figures in the same register.

### Verification

```bash
python -m muriel.contrast path/to/page.html
python -m muriel.capture https://example.com --dir captures/
weasyprint page.html page.pdf
```

Inspect at least one narrow and one wide viewport, keyboard traversal, console
errors, overflow, image loading, and final export dimensions.

## Load deeper only when needed

Read [`../references/web-recipes.md`](../references/web-recipes.md) only for
exact Marginalia syntax, Pandoc transforms, light-editorial tokens, capture
recipes, or data-URI implementation details. Do not load it for routine product
UI work.
