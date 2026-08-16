---
channel: readme
status: partial-mvp
requires:
  brand: optional
  audience: required
  reads:
    - muriel.capture
    - muriel.squint
    - muriel.contrast
    - muriel.aiism
output:
  kinds: [png, svg, txt]
  registers: [blog, social]
peer_channels:
  - diagrams
  - dimensions
  - svg
  - terminal
---

# README — repo front pages on a renderer you don't control

A README is a visual artifact rendered by a hostile, non-configurable renderer, read once, at a glance, on a family of backgrounds, by someone deciding whether to close the tab. That is a composition problem, not a documentation problem — and it is the reason this is a channel rather than a style note.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to use
- A repo front page, GitHub profile README, or org landing README
- Release notes and `CHANGELOG` headers that render on the same surface
- Any markdown whose final renderer is GitHub, GitLab, or Gitea rather than your own CSS
- Auditing an existing README that "looks fine" to the person who wrote it

**Not** for: docs sites (you control the CSS there — use [`web.md`](web.md)), in-app help, or prose quality on its own. `muriel.aiism` already audits markdown prose independent of this channel.

## Purpose in the solution

Make the badge budget, asset theming, first-screenful hierarchy, and diagram-vs-prose call part of the artifact — not a decorative pass after the words are right.

Before editing, tell the calling agent:

- **Purpose:** which orientation failure this fixes — a reader who can't tell what the project is, whether it works, or where to start.
- **Integration:** which existing sections, assets, and anchors survive.
- **Proof:** which rendered capture, squint ladder, and contrast audit verify it.

## The renderer contract

GitHub sanitizes README HTML. Most of what designers reach for is stripped silently — the markdown renders, your styling just isn't there. Write against the surface that actually survives.

**Survives:**

| Feature | Use it for |
|---|---|
| `<picture>` + `<source media="(prefers-color-scheme: dark)">` | Theme-paired images. The one indispensable primitive. |
| `<img width height align>` | Sizing and float. `width` is the only layout control you get. |
| `<details>` / `<summary>` | Progressive disclosure — long install matrices, full option tables. |
| `> [!NOTE|TIP|IMPORTANT|WARNING|CAUTION]` | Native alert callouts, themed by GitHub. Five types, no more. |
| ` ```mermaid ` fences | Diagrams rendered natively, no image asset, diffable in git. |
| `$…$` / `$$…$$` | LaTeX math via MathJax. |
| Tables, footnotes (`[^1]`), task lists, `<kbd>`, `<sub>`, `<sup>` | Structure without HTML. |

**Stripped:** inline `style=`, `<style>` blocks, `<script>`, `<font>`, `class=`. There is no CSS escape hatch. An artifact that needs specific type or color must arrive as an image.

**Gotchas that bite:**

- **The README's first screenful is not the page's first screenful.** On a repo landing page it sits below the file browser. Your hero arrives after a scroll, and the reader arrives already impatient.
- **"Dark mode" is a family, not a color.** GitHub ships light, dark, dark dimmed, and two high-contrast themes. An image baked with a `#0d1117` background bands visibly against dark dimmed. Transparent backgrounds or `<picture>` pairs; never a hardcoded page color.
- **Images from outside the repo are camo-proxied and cached hard.** Relative repo paths update when you push; proxied ones can serve stale for a long while. Prefer relative paths for anything you'll iterate on.
- **SVG rendered through `<img>` resolves fonts against the reader's machine.** `font-family="Helvetica Bold"` is a macOS-shaped assumption; Linux and Windows substitute and the metrics drift out of your canvas. Any SVG with type in it ships as outlines, not `<text>` — see [`svg.md`](svg.md).
- **Renaming a heading breaks every anchor pointing at it,** including inbound links from issues and other repos.
- **Mobile is one narrow column.** Wide tables and wide diagrams squeeze or scroll. Check it; don't assume it.

## Default workflow

1. Name the reader and the one decision they're making. Everything else is subordinate.
2. Read the existing README and inventory what's load-bearing: anchors, assets, badge semantics.
3. Decide the first screenful — what is this, does it work, where do I start. Three answers, above everything else.
4. Set the badge budget before writing badges (below).
5. Choose diagram or prose per section, with the anti-prescription gate applied.
6. Render the real page, squint it, audit contrast on both themes.
7. Report the decision that changed, the file carrying it, and the rendered evidence.

## High-leverage rules

- **Badges are status signal, not a dependency manifest.** Budget 3–5: license, version/release, build, and at most one more. A wall of badges is the highest-contrast mass on the page, so it becomes the focal point by default — the eye lands on your toolchain instead of on what the project is. Dependencies belong in a table further down, where they're readable.
- **Every badge must clear 8:1 against both theme families,** and against its own label half. Shields' `-000` and pale custom colors fail on one side or the other; a black badge on dark dimmed has no edge at all.
- **One focal asset above the fold, or none.** Two competing heroes read as zero.
- **Prefer a mermaid fence to an image** when the content is structural. It diffs, it re-themes for free, and it can't go stale against the code the way an exported PNG does. Reach for a rendered asset when the geometry is real — see [`diagrams.md`](diagrams.md).
- **Don't add a diagram because READMEs have diagrams.** The anti-prescription gate applies here as everywhere: if the paragraph is already clear, the diagram is decoration with a maintenance cost.
- **Alt text is mandatory on every image,** and it carries meaning rather than naming the file. On a link-wrapped image the alt text *is* the accessible name.
- **Never render running text as an image.** Display lettering — a wordmark, a single logo glyph — is exempt under WCAG 1.4.3 and may ship as an asset. Prose, link text, and section headers may not: image text is unsearchable, unselectable, invisible to Ctrl-F, and untranslatable. The reader looking for your project name on their own screen should find it.
- **Screenshots get the same treatment as any raster artifact.** Real content, no lorem, no fake data, captured at retina and sized down. See [`raster.md`](raster.md) and [`terminal.md`](terminal.md).

### Theme-paired assets

The one recipe worth memorizing. `<picture>` survives the sanitizer and GitHub honors it:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/architecture-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/architecture-light.svg">
  <img alt="Three-stage pipeline: capture, squint, critique." src="docs/architecture-light.svg" width="720">
</picture>
```

Both renders are first-class palettes, not inversions — reduce saturation on the dark one rather than flipping channels. Both clear 8:1. The `<img>` fallback carries the alt text and the width.

## Verification

The README channel's distinguishing move is that the artifact is *renderable*, so the hierarchy claim is testable instead of arguable. Capture the live page logged-out at both schemes, then blur it.

```bash
python -m muriel.capture https://github.com/OWNER/REPO --dark --full-page --dir captures/
python -m muriel.capture https://github.com/OWNER/REPO --light --full-page --dir captures/
python -m muriel.squint captures/github-com-owner-repo-desktop.png
python -m muriel.contrast docs/architecture-dark.svg
python -m muriel.aiism README.md
```

Read the squint ladder against one question: **at the blur where all text has dissolved, what is the largest, highest-contrast mass?** If the answer is the badge row, the budget is wrong. If the answer is nothing — a uniform gray field — the page has no hierarchy and the reader has no entry point.

Also capture at `--tiers mobile` and confirm no table or diagram scrolls horizontally.

### The Stranger pass

[`../references/jury.md`](../references/jury.md) defines the Stranger seat: reads once, brief withheld, answers *what is this for, what is the one number, where do I click.* That is verbatim the README's job, which makes it the highest-yield single audit on this channel. It is also the only seat that can catch a README that is well-made and about the wrong thing.

Run it against the rendered capture, not the markdown source. The source reads in authoring order; the render reads in reading order, and the gap between those is where READMEs fail.

## Structural AI tells

*(Queued — see [`TODO.md`](../../../../../TODO.md). The rules below are the spec; `muriel.aiism` is the host.)*

`muriel.aiism` already audits markdown prose sentence by sentence. README tells are different in kind — they're **structural**, and they survive a prose pass untouched because every individual sentence is fine:

- Emoji-prefixed section headers, especially the full set: 🚀 Quick Start, ✨ Features, 📦 Installation, 🤝 Contributing, 📝 License.
- A table of contents on a file short enough to scroll.
- Feature lists that arrive in threes, each with a bolded lead-in.
- A "Why *X*?" section that restates the description.
- A Roadmap of unchecked boxes with no dates and no commits behind them.
- Badge count above the budget — the manifest-as-signal failure, machine-countable.
- Section headers in a fixed canonical order with no section carrying project-specific content.

This is the same "tasteful default" trap [`devibe`](../../../../../muriel/devibe.py) catches in CSS, in a different medium: nothing is wrong, and nothing is anyone's decision. The fix is never to delete the section — it's to make it carry something only this project could say.

## Prior art

- **[aza-ali/github-readme-crisp-links](https://github.com/aza-ali/github-readme-crisp-links)** (MIT). Source of the renderer-contract observations here: that GitHub strips inline `style=`, `<style>`, and `<font>`, and that an `<a>` whose only descendant is an `<img>` has no text node for Primer's CSS to underline — the mechanism every shields.io badge row already relies on. Their `<picture>` + `prefers-color-scheme` handling is adopted directly. **Not adopted:** the technique's headline use — rendering project names as gradient SVG wordmarks to defeat link underlines. It converts link text into unsearchable, unselectable image text, which is the running-text prohibition above, and the gradient-wordmark register is itself a generic-template tell. Their measure-then-size approach also assumes a macOS Helvetica Bold that the reader's browser will not have; if you do ship SVG type, bake outlines.
