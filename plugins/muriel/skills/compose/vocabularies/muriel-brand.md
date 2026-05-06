# muriel — brand identity

The canonical spec for muriel's own visual mark, wordmark, color tokens, and credit conventions. Inward-facing: this is muriel's `brand.toml` for itself.

Until this doc existed, muriel theme'd every other project from a documented brand and ran on vibes for its own. The favicon at [`docs/favicon-512.png`](https://github.com/andyed/muriel/blob/main/docs/favicon-512.png) was the only canonical artifact, and every "built with muriel" credit anywhere had to be reverse-engineered from the rendered PNG. That's the exact failure muriel exists to prevent. This file fixes it.

## Lineage and grammar

The mark is **six rectangles in typographic-block rhythm**, descending from Müller-Brockmann's Swiss grid tradition and Muriel Cooper's Visible Language Workshop discipline (see [`vocabularies/visible-language.md`](visible-language.md) for the full lineage). The six bars represent a wordmark abstracted to vertical strokes — three "capital-height" chunky bars (1, 2, 5) on the main baseline, two "x-height" bars (3, 4) floating on a secondary baseline, one tall narrow accent stroke (6) on the right edge that may extend above as an ascender (favicon scale) or cap to bar-1 height (inline scale).

**The mark is generated, not drawn.** It always renders from these exact rect coordinates. Don't trace it from a screenshot. Don't redraw it for each context. Use the snippets below.

## Color tokens

These match `examples/muriel-brand.toml` and override nothing — they're the canonical values for any muriel-own surface.

| Token | Hex | Use | Contrast on `#0a0a0f` |
|---|---|---|---|
| `background` | `#0a0a0f` | OLED near-black surface | — |
| `foreground` | `#e6e4d2` | cream — primary fill for the mark and wordmark | 15.4:1 |
| `accent` | `#50b4c8` | cyan — text-safe brand accent for hover, links, highlights | 8.2:1 |
| `accent-ink` | `#7dd4e4` | higher-contrast cyan for inks/strokes | 11.7:1 |

The mark itself fills with `foreground`. Cyan accent is reserved for interactive states or highlights; never as the primary mark color (it's a secondary brand color, not the brand's voice).

## The mark — full form (favicon scale)

For favicons, OG cards, hero placement, anywhere the mark gets ≥32px of display height. Bar 6 carries an ascender (~22% above bar 1's top) — the right-edge accent that gives the mark its character. **Cannot be used inline in text** because the ascender breaks line-height.

```html
<svg viewBox="0 0 100 54" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="muriel">
  <g fill="#e6e4d2">
    <rect x="0"  y="12" width="22" height="42"/>  <!-- bar 1: capital, baseline -->
    <rect x="26" y="14" width="17" height="40"/>  <!-- bar 2: capital, baseline -->
    <rect x="47" y="26" width="10" height="14"/>  <!-- bar 3: small, x-height float -->
    <rect x="61" y="18" width="7"  height="22"/>  <!-- bar 4: medium, x-height float -->
    <rect x="72" y="14" width="15" height="40"/>  <!-- bar 5: capital, baseline -->
    <rect x="91" y="0"  width="9"  height="54"/>  <!-- bar 6: accent, ascender -->
  </g>
</svg>
```

**Anatomy.** Two baselines. Bars 1, 2, 5 sit on the **main baseline** (y=54). Bars 3, 4 float together on the **x-height baseline** (bottom at y=40 — fourteen units above the main baseline). Bar 6 ascends from main baseline to viewBox top — its height (54) is 1.29× bar 1 (42), the ascender accent that distinguishes the mark.

## The mark — inline form (capped, no ascender)

For inline credits, footers, anywhere the mark must fit within a text line. Bar 6 capped to chunky-bar height — the ascender is sacrificed for line-height conformance. Use this whenever the mark renders alongside text in a flowing line.

```html
<svg viewBox="0 0 100 42" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="muriel">
  <g fill="#e6e4d2">
    <rect x="0"  y="0"  width="22" height="42"/>
    <rect x="26" y="2"  width="17" height="40"/>
    <rect x="47" y="14" width="10" height="14"/>
    <rect x="61" y="6"  width="7"  height="22"/>
    <rect x="72" y="2"  width="15" height="40"/>
    <rect x="91" y="0"  width="9"  height="42"/>
  </g>
</svg>
```

The two-baseline rhythm (bars 3, 4 floating together) is preserved. Only bar 6's ascender is removed.

## Sizing — the subpixel rendering floor

Below ~30px of display width, the narrow bars (4, 6) start to subpixel and antialias to fuzzy hairlines. The minimum sizes that render crisply:

| Variant | Min display width | Min display height | Why |
|---|---|---|---|
| Full mark (with ascender) | 56px | 30px | Bar 4 (w=7) at this scale = 3.9px wide, renderable solid |
| Inline mark (no ascender) | 28px | 12px | Same threshold for bar 4 |
| Below floor | — | — | Drop the mark; use wordmark only with optional accent dingbat |

If the available display size is below the floor, **don't shrink the mark — drop it**. A wordmark-only credit reads cleaner than a mark rendering as fuzz.

## Wordmark conventions

- **Spelling.** `muriel` — always lowercase. The brand name is set in lowercase in every context including title positions. The library is `muriel`, not "Muriel" or "MURIEL."
- **Phrase.** `built with muriel` — canonical attribution form. Lowercase throughout. The verb is "built with," not "powered by," "made with," or "rendered by."
- **Font.** Inter (or system fallback `-apple-system, 'Segoe UI', system-ui, sans-serif`). Regular weight (400) for "built with"; semibold (600) for the "muriel" word so the brand name reads as the load-bearing token.
- **Sizing.** Match the surrounding text size. The credit doesn't shout.
- **Italic — no.** muriel is editorial, not kinetic. Roman only.

## Drop-in: inline "built with muriel" credit

Self-contained — paste anywhere inside any HTML page on a dark background. Clip the text-domain link to where the muriel project actually lives.

```html
<style>
  .muriel-credit {
    display: flex; align-items: center; gap: 8px;
    margin: 1rem auto 0; width: fit-content;
    text-decoration: none; user-select: none;
    opacity: 0.78; transition: opacity 0.2s ease;
  }
  .muriel-credit:hover, .muriel-credit:focus { opacity: 1; }
  .muriel-credit .muriel-mark rect { fill: #e6e4d2; }
  .muriel-credit .muriel-wordmark {
    font-family: -apple-system, 'Inter', 'Segoe UI', system-ui, sans-serif;
    font-size: 11px; font-weight: 400; color: #e6e4d2;
  }
  .muriel-credit .muriel-wordmark strong { font-weight: 600; }
</style>
<a class="muriel-credit" href="https://muriel.mindbendingpixels.com/"
   target="_blank" rel="noopener" aria-label="Built with muriel">
  <svg class="muriel-mark" viewBox="0 0 100 42" width="32" height="14"
       xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
    <rect x="0"  y="0"  width="22" height="42"/>
    <rect x="26" y="2"  width="17" height="40"/>
    <rect x="47" y="14" width="10" height="14"/>
    <rect x="61" y="6"  width="7"  height="22"/>
    <rect x="72" y="2"  width="15" height="40"/>
    <rect x="91" y="0"  width="9"  height="42"/>
  </svg>
  <span class="muriel-wordmark">built with <strong>muriel</strong></span>
</a>
```

Contrast on `#0a0a0f` background at 0.78 opacity: 9.4:1 on cream — passes the 8:1 floor.

## Drop-in: block "built with muriel" credit (full mark)

For pages with more vertical space — README hero, About pages, project credits sections. Mark stacks above the wordmark, ascender visible.

```html
<style>
  .muriel-block-credit {
    display: flex; flex-direction: column; align-items: center; gap: 10px;
    margin: 2rem auto 0; width: fit-content;
    text-decoration: none; user-select: none;
  }
  .muriel-block-credit svg rect { fill: #e6e4d2; }
  .muriel-block-credit .label {
    font-family: -apple-system, 'Inter', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px; font-weight: 400; color: #e6e4d2;
    letter-spacing: 0.02em;
  }
  .muriel-block-credit .label strong { font-weight: 600; }
</style>
<a class="muriel-block-credit" href="https://muriel.mindbendingpixels.com/"
   target="_blank" rel="noopener" aria-label="Built with muriel">
  <svg viewBox="0 0 100 54" width="60" height="32"
       xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
    <rect x="0"  y="12" width="22" height="42"/>
    <rect x="26" y="14" width="17" height="40"/>
    <rect x="47" y="26" width="10" height="14"/>
    <rect x="61" y="18" width="7"  height="22"/>
    <rect x="72" y="14" width="15" height="40"/>
    <rect x="91" y="0"  width="9"  height="54"/>
  </svg>
  <span class="label">built with <strong>muriel</strong></span>
</a>
```

## Wordmark-only fallback (when no mark fits)

Use when display constraints rule out even the inline form (extreme micro-scale: below 28px wide, or in any context where SVG isn't supported). The mark's *meaning* still reads through the wordmark + association.

```html
<a href="https://muriel.mindbendingpixels.com/" target="_blank" rel="noopener"
   style="font-family: -apple-system, 'Inter', system-ui, sans-serif;
          font-size: 11px; font-weight: 400; color: #e6e4d2; opacity: 0.78;
          text-decoration: none;">
  built with <strong style="font-weight: 600;">muriel</strong>
</a>
```

## Don'ts

- **Don't redraw the mark by tracing the favicon.** Use the rect coordinates above. Hand-tracing leads to subtly-wrong proportions.
- **Don't add color to the bars.** Cream `#e6e4d2` only. The mark is monochrome; brand differentiation comes from typographic discipline, not chromatic noise.
- **Don't stretch or distort.** The viewBox aspect ratio is fixed (100:54 full, 100:42 inline). Always set `width` and `height` proportionally.
- **Don't use the mark as a watermark or repeating pattern.** The mark is a typographic identity, not decoration.
- **Don't capitalize "muriel"** — even at the start of a sentence. Recast the sentence if the lowercase reads awkward.

## Reference exemplars

- **Favicon set:** [`docs/favicon-{16,32,180,512}.png`](https://github.com/andyed/muriel/tree/main/docs/) — light variant (cream background); [`docs/favicon-dark-{16,32,180,512}.png`](https://github.com/andyed/muriel/tree/main/docs/) — dark variant (cream bars on near-black).
- **Inside the Math footer credit:** `psychodeli-webgl-port/inside_the_math/index.html` — first production deployment of the inline form; landed the canonical inline coordinates after several iterations.

## Versioning

This spec is the **v1** canonical mark. Breaking changes (rect coordinates, color tokens, naming conventions) require a versioning step here and migration guidance for existing consumers.
