# Declassified — released, leaked, seized, discovered

**When to reach for it.** When an artifact is framed as *not originally meant for the reader* — released after the fact, leaked against the issuer's wishes, seized as evidence, or recovered from an archive. The visual register of the released document carries weight a clean rendering of the same prose can't: it tells the reader the document has *survived* something. FBI Vault, FOIA reading-room PDFs, the Pentagon Papers, the Mitrokhin archive, Wikileaks cables, the Stasi files, and the Snowden cache all share the same typography of release — black bars, exemption codes, classification banners, marginalia, scan damage. Borrow it deliberately.

Use it for:

- **Speculative-fiction documents** framed as recovered, leaked, or seized — sciprogfi-web's `type: document` nodes are the canonical case.
- **Worldbuilding bibles** when an in-universe document needs to feel like an artifact, not a stat block.
- **Editorial pieces** that *are* about classification, secrecy, surveillance, or the FOIA process — let the form match the topic.
- **Forensic walkthroughs** where the visible redaction itself is the point ("the bar is over the agent's name; here's why we know").

Don't reach for it when:

- The document is not framed as released. A working memo, a marketing post, or a research paper presented straight should not cosplay as classified. Aesthetic-only declassification reads as costume and erodes the grammar.
- The audience can't tell the artifact is *fictional*. Real declassified-document conventions are read as authentic government output by some readers; pair fictional uses with explicit framing (in-universe filename, narrative wrapper, or visible disclaimer).
- The content is fine on its own. If the prose stands without the paratext, the paratext is decoration.

## Lineage and grammar

The grammar is narrow, well-codified, and recognized at a glance:

- **Classification banner.** Top and bottom of every page. "TOP SECRET", "SECRET", "CONFIDENTIAL", "SENSITIVE BUT UNCLASSIFIED", "FOR OFFICIAL USE ONLY", "UNCLASSIFIED". Compartments append (`//SCI`, `//NOFORN`, `//ORCON`, `//REL TO USA, FVEY`). Banner colors track sensitivity (red for TS, blue for SECRET in some traditions; banner-only color is sufficient — don't tint the whole page).
- **Declassification stamp.** Diagonal red overprint: "DECLASSIFIED", "DECLASSIFIED IN PART", "RELEASED IN FULL", "APPROVED FOR PUBLIC RELEASE". Includes release date, authority code, and case number. This is what marks a document as *available* — without it, the page is still pretending to be classified.
- **Case-file identifier.** Top-right or top-left: `OHC-2033-IMM-407 // PAGE 4 OF 12`. Stable across pages, anchors the document in a system. If your document doesn't have a case-file ID, invent one — the absence is more conspicuous than a fake.
- **Redaction bars.** Solid black rectangles that occlude text but preserve the *bounding box of the redacted span*. Length is informative — "REDACTED" replacing a whole paragraph reads differently than a 3-character bar inside a sentence. Margin annotation cites the exemption: `(b)(7)(C)`, `(b)(1)`, etc.
- **Exemption legend.** Footer or final page: lists what each `(b)(...)` code means in plain English. Without the legend, the codes are noise; with it, the document teaches the reader to read its own redactions.
- **Page paratext.** Sequential numbering, sometimes a routing line ("FILE COPY", "ROUTED TO: ___", date stamps), sometimes a header carrying agency / case / subject. Lower-end documents have less; higher-classification documents have more.
- **Aging artifacts.** Scan moiré, edge wear, dog-ears, staple shadows, dust specks, photocopier streaks, carbon-paper bleed. Aging is *substrate damage* — paper, ink, scanner roller — not a sepia filter.
- **Marginalia.** Handwritten annotations from readers along the way: blue pen for an analyst, red pen for an adversary or surveillance reader, pencil for an archivist. Marginalia is whose hands the document passed through; it tells a story the document itself doesn't.

The 8:1 contrast rule still applies: redaction-code labels, classification banners, page numbers, exemption legends, and marginalia text all need to clear 8:1 against their backgrounds. Aging artifacts may not — they're the substrate, not the message.

## Provenance vocabulary

Six values, each with a different visual signature. Pick one per document and let the rest of the styling follow.

| Value | Story | Visual cues |
|---|---|---|
| `foia` | Government-sanctioned release through formal records request. The cleanest variant. | Crisp scan, full paratext intact, neat redaction bars w/ exemption codes, declassification stamp w/ release date + authority, exemption legend in footer. |
| `leak` | Released against the issuer's wishes. Less polished, often photographed pages rather than scanned. | Original classification banner *still present* (no decl stamp), partial or sloppy redactions, occasional white-out, sometimes annotated by the leaker. May include screen glare, finger occlusion, or off-axis photography artifacts. |
| `seizure` | Physical document recovered through raid, warrant, or war-zone capture. | Battle / water / fold damage, foreign-language stamps, military or court evidence markings, chain-of-custody numbering, sometimes stapled or paper-clipped to a cover sheet. |
| `discovery` | Archival find — declassified by time, recovered from estate, museum, or library. | Heavy paper aging (yellowing, foxing, edge browning), archive paratext (acquisition #, finding-aid reference), original classification stamps marked *cancelled*, museum/archive label adhesive ghosts. |
| `open` | Published willingly by the source. The "manifesto" register. | Minimal or no paratext, no redactions, signed/dated by author, cover-sheet typography (issue number, distribution list). The *typography* signals self-published-but-formal — broadsheet, samizdat, technical-report covers. |
| `seized-annotated` | A copy of a public document captured by an adversary, with their marginalia and routing stamps over the original. | Original document is clean (it was public); overlay carries red-pen threat assessment, surveillance routing stamps ("REVIEWED BY: ___"), highlighting, sometimes a translation ribbon down the side. |

These are visual *registers*, not technical truth claims. A fictional `leak` doc isn't actually leaked; it's framed as if it were, and its styling has to back the framing.

## Two redaction grammars — keep them separate

Black-bar styling collapses two distinct stories that need to read differently:

1. **Government redaction at creation.** Done by the issuer (or a reviewer) before release, citing a legal exemption. Solid black bar, length ≈ original text length, exemption code in the right margin: `(b)(7)(C)`. The reader knows *something specific* was removed by an *identified authority* under a *cited rule*. Use a `redact` shortcode / class for this.
2. **View-time censorship.** Done by the *display environment* — a Clean Net filter, a regional firewall, a corporate compliance overlay. The text was once visible to *some* readers and is now blocked from *this* reader. Often rendered as `█` characters (the original glyph count is preserved as a tell), and the overlay tooltip names the censor. Use a `censor` shortcode / class for this.

These can coexist on the same page (a leaked document re-suppressed by a Clean Net filter), but they should not share visual language. Government redaction is a property of the document; view-time censorship is a property of the reader's environment.

## FOIA exemption codes

The five-or-six codes a reader will see often enough to recognize. Use these in fiction; invent parallel codes only when the universe explicitly diverges.

| Code | Meaning |
|---|---|
| `(b)(1)` | Classified national-security information. |
| `(b)(3)` | Specifically exempted by another statute. |
| `(b)(4)` | Trade secrets or commercial/financial info from a person. |
| `(b)(5)` | Inter/intra-agency memoranda — privileged deliberation. |
| `(b)(6)` | Personnel/medical files — clearly unwarranted invasion of privacy. |
| `(b)(7)(A)` | Law enforcement records — interferes with enforcement. |
| `(b)(7)(C)` | Law enforcement records — personal privacy. |
| `(b)(7)(D)` | Law enforcement records — confidential source. |
| `(b)(7)(E)` | Law enforcement records — techniques and procedures. |
| `(b)(7)(F)` | Law enforcement records — endangerment of life or safety. |

Render the code in the right margin opposite the bar, in a smaller monospace face. Always include the exemption legend somewhere on the page (footer or final page), or the codes don't teach.

## Aging as era-distance

Aging is *time elapsed between issue date and view date*, not absolute calendar time. A document dated 2026 viewed inside a 2026 era surface should look fresh; the same document re-rendered inside a 2033 era surface should carry seven years of substrate damage. This composes naturally with era-progression CSS already in use (sciprogfi-web's `2024-2026.css` → `2035.css`) — the aging filter is *a function of `view_year - issue_year`*, not of `issue_year` alone.

Three intensity tiers:

- **Tier 0 (`Δ ≤ 1 year`)** — fresh. Crisp scan, clean edges, full ink density, minimal artifacts.
- **Tier 1 (`Δ 2–7 years`)** — used. Light scan grain, soft edge wear, occasional dust spec, mild ink density loss. Marginalia from intermediate readers becomes plausible here.
- **Tier 2 (`Δ ≥ 8 years`)** — archival. Yellowing, foxing, visible photocopier streaks, edge browning, possible coffee ring or staple-shadow geometry. Original classification stamps may be cancelled (red overstrike on TOP SECRET).

Implementation: an SVG paper-grain overlay at 4–10% opacity (tier-scaled), an edge-wear mask at the page perimeter, and an optional yellow-tint blend on tier 2 (≤ 8% opacity, on the *paper* layer only, never on text — text must clear 8:1 always). For sciprogfi-web specifically, the `(view_year - issue_year)` calculation can use the existing `intrusion` system as a proxy — older docs in higher-intrusion eras inherit higher aging tiers.

## Marginalia conventions

Marginalia tells the story of *who read this document along the way*. Three hands cover most cases:

- **Red pen** — adversarial reader. Surveillance state, opposing analyst, intercept reviewer. Used for threat assessment, target identification, action-required circling. Renders as a slightly off-rotation handwritten note in a red ink color (e.g., `#a8242b`). Always 8:1 against the paper.
- **Blue pen** — friendly analyst. Internal reviewer, allied agency, the document's own staff. Used for clarification, citation, follow-up question. Renders as a more controlled handwritten note in dark blue (`#1c3a6e`).
- **Pencil** — archivist or scholar. Cataloguing, dating, source attribution, finding-aid reference. Most restrained of the three — short, often abbreviated, often in the bottom margin. Renders as a soft graphite gray.

Each annotation should be *positioned* relative to a specific span of text (right margin opposite a paragraph, between two paragraphs, or in a bottom-margin block). Floating annotations not anchored to content read as decoration.

A typewriter strikethrough is the fourth hand: when the *original document* was edited at issue time, render `~~struck text~~` with a red horizontal line at half-stroke through the original text in the document's own face. This is different from marginalia — it's a property of the document at issue, not a later reader's annotation.

## Simulating handwriting — making marginalia *look* handwritten

A cursive font in a margin reads as fake unless it carries the irregularities of an actual hand. The grammar of handwriting differs from print along five dimensions; reproducing them is what separates "rotated cursive text" from a marginalia note that someone wrote.

### 1. Font selection

System handwriting fonts (Bradley Hand, Marker Felt, Comic Sans MS, Segoe Print) are *available* but not *consistent* across platforms — a cursive fallback chain produces a different effective face on every reader's device. Two better options:

- **Hosted webfonts.** Pick a face with handwriting authenticity, broad glyph coverage, and a license that ships with the artifact. Defaults that work well in declassified contexts:

  | Font | Hand | License | Notes |
  |---|---|---|---|
  | [Caveat](https://fonts.google.com/specimen/Caveat) | informal ballpoint | OFL | Most legible at small sizes; the safe default. |
  | [Kalam](https://fonts.google.com/specimen/Kalam) | rounded marker / fine pen | OFL | Excellent for blue-pen analyst notes; reads slightly more deliberate than Caveat. |
  | [Architects Daughter](https://fonts.google.com/specimen/Architects+Daughter) | print-letter handwriting | OFL | Good when the marginalia is technical or schematic (engineer's hand). |
  | [Shadows Into Light Two](https://fonts.google.com/specimen/Shadows+Into+Light+Two) | quick scrawl | OFL | Best for adversarial red-pen notes — has tension. |
  | [Reenie Beanie](https://fonts.google.com/specimen/Reenie+Beanie) | hurried cursive | OFL | Use sparingly — the irregularity reads as agitated, fits surveillance contexts. |
  | [Permanent Marker](https://fonts.google.com/specimen/Permanent+Marker) | thick felt-tip | OFL | Reserve for emphatic single-word callouts (`URGENT`, `STOP`). |

- **Custom scanned handwriting.** For a single-author voice across a large corpus (a fictional analyst whose marginalia recurs across many documents), trace handwriting samples and bake into a webfont via [Calligraphr](https://www.calligraphr.com/) or hand-craft an SVG font. Higher activation cost; pays back when the *same hand* appears across dozens of documents.

Pair the font choice with a stack: `font-family: 'Caveat', 'Bradley Hand', 'Marker Felt', cursive;`. The system fallbacks degrade gracefully when the webfont fails to load.

### 2. The visual grammar of handwriting (vs print)

Five things printed text does *not* do, but handwriting always does:

- **Per-character drift.** Letters don't sit on a perfect baseline; they drift up-and-down by a fraction of a pixel. Larger drift on words at line breaks.
- **Per-character rotation.** Each glyph rotates by a small random angle (±1.5° typical, ±3° for hurried notes).
- **Ink saturation variability.** Pen pressure changes; the same pen reads darker at the start of a stroke and lighter at the end. Ballpoints leave gaps; felt-tips bleed.
- **Word-level rotation.** A word may tilt as a unit before the writer corrects course on the next word.
- **Line-to-line drift.** Lines aren't parallel. They slope (usually up-and-to-the-right for right-handed writers; down-and-to-the-right for left-handed). The slope changes between paragraphs.

Apply these in layers — over-applying any one looks like a stylization gimmick; the cumulative effect of three at low intensity reads as authentic.

### 3. CSS recipes

The minimum baseline (works without JS):

```css
.marginalia {
  font-family: 'Caveat', 'Bradley Hand', cursive;
  font-size: 1.05rem;
  line-height: 1.4;
  /* Word-level rotation — irregular per note, not page-wide */
  transform: rotate(-0.6deg);
  /* Slight ink bleed via tiny outward text-shadow */
  text-shadow: 0 0 0.4px currentColor;
  /* Soften ink-into-paper interaction */
  mix-blend-mode: multiply;
}

/* Vary rotation per hand so identically-typed paragraphs look like
   different hands wrote them. */
.marginalia[data-hand="red"]    { transform: rotate(-0.6deg); }
.marginalia[data-hand="blue"]   { transform: rotate( 0.4deg); }
.marginalia[data-hand="pencil"] { transform: rotate(-0.3deg); }
```

Baseline drift via per-character spans (works without JS if you accept generated markup, or use a small render-time helper):

```html
<aside class="marginalia hand-jitter">
  <span style="--y:-0.4px">T</span><span style="--y:0.3px">a</span>...
</aside>
```

```css
.hand-jitter span { display: inline-block; transform: translateY(var(--y, 0)); }
```

A more authentic ink-bleed via SVG filter (apply via CSS `filter`):

```html
<svg width="0" height="0" style="position:absolute">
  <filter id="ink">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="3"/>
    <feDisplacementMap in="SourceGraphic" scale="0.6"/>
  </filter>
</svg>
```

```css
.marginalia { filter: url(#ink); }
```

`scale="0.6"` is just enough to roughen the glyph edges; `scale > 1` reads as drunk, not as written. The filter has a real cost — fine on marginalia (small text spans), avoid on body copy.

### 4. Pen-color authenticity

Generic CSS color names (`red`, `blue`) read as digital, not as ink. Use realistic ink palettes — and verify each clears the brand's contrast floor against paper.

| Pen | Hex | Notes |
|---|---|---|
| Ballpoint blue | `#1c3a6e` | The single most common ink in 20th-century institutional documents. 9:1 on `#f9f5e8`. |
| Felt-tip blue | `#1f4dba` | Brighter, slightly purplish — late-century markers. |
| Ballpoint red (correction) | `#7a0e14` | The "red pen" of evaluators. 8.3:1 on cream. |
| Felt-tip red (declass stamp) | `#5a0c0c` | Very dark, almost burgundy — what looks "official". |
| Pencil graphite | `#3d3d3b` | Cool gray, not warm. 8.6:1 on cream — borderline; verify. |
| Sharpie / permanent black | `#0a0a0a` with slight bleed | Use 1.5px text-shadow for the bleed-through-paper effect. |
| Highlighter yellow | `#fff263` at 0.4 alpha | Rare in declassified docs; prefer underline over highlight. |
| Carbon-paper purple (typewriter) | `#3a2a4a` | When the document itself is a carbon copy, body ink shifts here. |

The 8:1 contrast rule still applies — verify each pen color against the paper tier in use. Tier-2 (yellowed) paper changes the math; precompute and store per-tier ink colors rather than reusing tier-0 values.

### 5. Compositional grammar

Marginalia *is* placement — a note in the wrong spot reads as decoration:

- **Anchored, not floating.** Every note refers to a specific span in the body. Use the right margin opposite that span on wide layouts; use a flush block immediately after the span on narrow layouts.
- **Connector marks** are optional but powerful. A small SVG line or arrow from the margin note to the underlined or circled span in the body sells the annotation. Render the arrow in the same ink color as the marginalia.
- **Underlines and circles in the body itself.** Same hand, same ink — `<u class="hand-mark" data-hand="red">` for an underline or a small SVG circle drawn over the relevant phrase. The marginalia note then references "the circled phrase."
- **Length matches voice.** Single word = exclamation (`Confirmed.` `Sus?` `URGENT`). Single sentence = analyst comment. Multi-line = staff review. A handwritten paragraph in the margin always reads as theatrical; if the note is long, break it into two anchored notes at different positions.
- **Attribution is a tell.** Initials and date in parens (`— JL 4/82`) signal institutional handwriting culture. Without attribution, the reader doesn't know whose hand they're seeing — fine for ambient atmosphere, weaker for narrative weight.

### 6. Channel-specific implementations

| Channel | How to render handwriting |
|---|---|
| **Web / HTML** | CSS recipe above. Webfont via `@font-face` (self-host the OFL files, don't hot-link Google Fonts in production-quality artifacts). Use `font-display: swap` so absent webfont falls back gracefully. |
| **SVG** | `<text>` with custom font, per-`<tspan>` `dy` for baseline drift, `transform="rotate(N)"` per-character. Apply `<feTurbulence>` + `<feDisplacementMap>` filter for ink-roughened edges. Vector-faithful at any scale; preferred for printable artifacts. |
| **Raster (Pillow)** | Load handwriting font via `ImageFont.truetype()`. Draw each character separately at slightly randomized rotation (use `Image.new` for the glyph, rotate, paste). Apply `ImageFilter.GaussianBlur(0.6)` to the marginalia layer for ink bleed. Composite over paper grain via `Image.alpha_composite`. |
| **Print (PDF)** | Same as web; weasyprint and Prince both honor `@font-face` and CSS `transform`. SVG filters do not survive print rasterization in some pipelines — use baked-in jitter via per-span markup instead of `filter: url(#ink)`. |
| **Video** | Animate the *writing* of the note: progressive `clip-path: inset(0 100% 0 0)` reveal at ~5 chars/sec for the writing motion. Marginalia appearing fully-formed reads as overlay, not as performed annotation. |

### 7. Anti-patterns

- **Don't use Comic Sans for "casual" handwriting.** It's recognizable as a font; it pulls the reader out of the artifact.
- **Don't render every marginalia note at the same rotation.** Multiple notes in the same hand should share *style* (rotation range, ink color, font) but not exact transform — they were written at different sittings.
- **Don't make handwriting too jittery.** Per-character rotation > ±3° crosses into "shaky-hand" territory and reads as drunk or distressed. Default range: ±1.5°.
- **Don't use stroke effects (`-webkit-text-stroke`) on marginalia.** Real handwriting has uneven ink density; outline strokes look stenciled.
- **Don't render handwriting at body-text size.** Marginalia is typically a touch larger than body (1.05–1.15× body size) so the cursive shapes remain legible. Smaller sizes turn into blur.
- **Don't use multiple webfonts for different hands.** One handwriting font, varied by ink color and rotation, reads as different hands. Stacking fonts reads as a typography demo.
- **Don't auto-generate marginalia.** Each note should anchor to specific content with specific authorial intent. Procedurally placed notes ("a random note every 200 words") read as noise.
- **Don't ignore line-height.** Handwriting needs more vertical breathing room than print — `line-height: 1.4` minimum, `1.6` better. Tightly packed handwriting reads as a wall of cursive.

## Cross-channel translation

Declassified is substrate-aware. Each output channel implements the grammar with the materials it has:

- **Web ([`channels/web.md`](../channels/web.md)).** CSS-driven. Classification banner = `<header>` + `<footer>` with sticky position. Redaction bar = inline `<span class="redact">` with `data-exemption` attribute and `::after` for the code label. Paper grain = SVG noise filter applied as `background-image` on the page surface. Marginalia = positioned absolute or floated, with rotation transforms. Aging = CSS filter chains (`sepia()`, `contrast()`, mask gradients).
- **SVG ([`channels/svg.md`](../channels/svg.md)).** Vector-native. Banners as text on rect; redaction bars as filled rects; aging as `<feTurbulence>` + `<feDisplacementMap>` filters. Paper grain renders crisply at any zoom — preferred when the artifact will be enlarged or printed.
- **Raster ([`channels/raster.md`](../channels/raster.md)).** Pillow + typeset. Compose layers: paper-grain noise (PIL.ImageFilter), text layer, redaction layer (filled rects), banner/stamp layer, marginalia layer. Use this when the deliverable is a single PNG (social card, in-fiction screenshot of a printed page). PIL's `Image.composite` handles the layering; `ImageDraw.rectangle` produces clean redaction bars.
- **Document (paged HTML or PDF).** Pandoc + weasyprint route from [`channels/web.md`](../channels/web.md). Paged-media CSS (`@page`, `@page :first`, running headers/footers) maps directly onto classification banners and case-file paratext. `page-break-before: always` between sections.

## Frontmatter schema

Suggested shape for projects adopting this vocabulary. Fields are optional unless noted.

```yaml
declassified: true                         # required to opt the document into the register
provenance: leak                           # foia | leak | seizure | discovery | open | seized-annotated
classification:                            # original classification at issue
  level: SECRET                            # TOP SECRET | SECRET | CONFIDENTIAL | SBU | FOUO | UNCLASSIFIED
  compartments: [NOFORN, ORCON]            # optional — appended after //
casefile:
  id: OHC-2033-IMM-407                     # stable identifier across pages
  pages: 12                                # total page count for "PAGE x OF y" rendering
  agency: "OHC // Strategy Directorate"    # issuing body
  subject: "Immune-system thesis (draft)"  # subject line
declassification:                          # only when provenance ∈ {foia, discovery}
  date: 2034-01-15
  authority: "OHC-DECL-AUTH-04"
  release_type: "RELEASED IN FULL"         # IN FULL | IN PART | DENIED IN PART
exemptions:                                # only when redactions are present
  - code: "(b)(7)(C)"
    plain: "Personal privacy in law-enforcement context"
  - code: "(b)(1)"
    plain: "Classified national-security information"
seizure:                                   # only when provenance == seizure
  recovered_from: "Lagos node, 2034-04-02"
  custody: "OHC Evidence Locker / case 2034-LAG-117"
marginalia:                                # optional — also doable inline via shortcode
  - hand: red
    anchor: paragraph-3
    text: "TGT confirmed — request authorization to act."
```

The schema is suggestive, not enforced. A web project may flatten these into top-level keys if its templating prefers; a paper project may carry only `declassified`, `provenance`, and a single case-file string.

## Anti-patterns

- **Don't mix the two redaction grammars in one shortcode.** Government-redaction-at-creation and view-time-censorship are different stories. Use distinct classes/shortcodes (`redact` vs `censor`) so a future author can compose them deliberately.
- **Don't use redaction for emphasis or surprise.** Bars on a punchline read as a meme. Redact only what an in-universe authority would redact, for an in-universe reason.
- **Don't put redaction bars over text the reader still needs to follow the document.** Leave enough surrounding context that the rest of the page makes sense; over-redaction breaks comprehension and is a tell that the document is fake.
- **Don't skip the exemption legend.** Codes without legend are noise. The legend is what makes the redaction *legal-feeling* instead of mysterious.
- **Don't tint the whole page sepia and call that aging.** Aging is substrate damage — grain, edges, scan moiré — not a color filter. A sepia layer over crisp text is a costume, not a register.
- **Don't render marginalia in a body-text font.** Marginalia is *handwriting* — different face, slight rotation, ink color, irregular tracking. If it looks like the document's body type, it reads as part of the document, not as a reader's note.
- **Don't put aging or redaction artifacts under text without checking 8:1.** Paper grain at 8% opacity will not break text contrast; the same grain at 25% will. Audit every text-bearing role over the aged surface.
- **Don't apply the register to documents the universe says are public.** A manifesto issued openly by its author has no FOIA history and no redactions. Use `provenance: open` and let the manifesto layout do its job — the register is wrong here.
- **Don't fake real-world classification systems for non-fiction work.** "TOP SECRET" on a marketing piece is a bad joke; "DRAFT — INTERNAL" is the honest equivalent. Reserve the actual government grammar for fiction or for pieces that are themselves *about* declassification.

## Reference exemplars

- **FBI Vault** — `vault.fbi.gov`. The canonical reference for FOIA-released US federal documents. Note the consistent paratext, exemption-code marginalia, and case-file headers. Particularly useful are the multi-decade case files (Hoover-era memos through 1990s investigations) — the same grammar, applied across substrate generations from typewriter carbons to photocopies to native PDFs.
- **National Security Archive (GWU)** — `nsarchive.gwu.edu`. Curated declassified collections with editorial framing. Good source for how *historians* present declassified material — captions, source notes, finding aids.
- **Wikileaks Cablegate** — leak-register reference. Documents retain original classification banners, no decl stamps, tabular metadata strip at the top. Different aesthetic from FOIA; closer to raw issue-time formatting.
- **The Pentagon Papers (NARA digital release)** — multi-volume document with mixed declassification status across pages. Useful reference for how declassification stamps interact with original classification banners ("TOP SECRET" with diagonal "DECLASSIFIED" overstamp).

These are visual references, not citation sources for the fictional projects that borrow the grammar. Read them to learn the form, then build new artifacts that *are* the form, not pastiches of specific real documents.

## Related

- [`channels/web.md`](../channels/web.md) — CSS implementation, paged-media for HTML/PDF, marginalia tokens.
- [`channels/svg.md`](../channels/svg.md) — vector implementation with `<feTurbulence>` aging, scalable paper grain.
- [`channels/raster.md`](../channels/raster.md) — Pillow compositing of layered substrates for single-PNG deliverables.
- [`channels/style-guides.md`](../channels/style-guides.md) — `[provenance]` table on `brand.toml` is unrelated naming-collision; brand-token provenance ≠ document-register provenance.
- [`vocabularies/fui.md`](fui.md) — sci-fi UI grammar; pairs naturally with `seized-annotated` overlays where the surveilling system is itself an FUI surface.
