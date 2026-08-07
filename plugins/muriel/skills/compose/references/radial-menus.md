---
reference: radial-menus
status: experimental
requires:
  canonical_state: required
  measured_geometry: required
output:
  kinds: [radial-menu-contract, wedge-composition, interaction-test]
  registers: [app, game, web, native]
---

# Radial menus — stable targets and measured wedge typography

Use this competency for a pie, marking, or radial menu whose commands combine a
glyph with a short label and optional status, cost, or shortcut. It joins two
proven implementations:

- Psychodeli consumerUI contributes config-driven main/sub-pies, split rings,
  two-tone 24-grid glyphs, live-state accents, nested Back, and theme tokens.
- Pot Luck contributes invariant target geometry, radial keyboard movement,
  direct touch activation plus hold-to-preview, captions for consequences, and
  shape-aware type that gives the label and cost priority over ornament.

This is a visual and interaction competency, not a standalone engine. Keep each
product's state, commands, gating, and side effects in its canonical owner. A
future shared library may implement this contract; the contract does not require
either product to adopt a speculative common runtime.

## Use gate

Choose a radial menu when spatial recall or rapid directional selection is part
of the value, and the set is small enough to remain distinguishable. A useful
default range is three to eight primary wedges. Test beyond eight rather than
assuming that more radius creates more comprehension.

Prefer a linear menu when commands are unfamiliar, descriptions carry the
decision, order or comparison matters more than direction, or zoom and text
scaling would push the labels below the physical size floor. Do not hide a
destructive, legal, financial, or permission consequence inside an unlabeled
glyph or a gesture-only path.

## Shared contract

### State and architecture

- Accept config and emit intent. The renderer does not read application globals
  or mutate product state.
- Keep `open`, active wedge, submenu path, and input modality local to the menu
  instance. Command availability and on/off state remain canonical product data.
- Preserve one geometry primitive for every annular sector. Main rings, sub-rings,
  split bands, and decorative rails derive from it.
- Treat visual composition as a projection. Pretext handles measurement and line
  breaking; ordinary DOM, SVG, or a hybrid of both remains the semantic, focus,
  hit-test, and theme layer. Pretext does not require a canvas renderer.

### Target geometry

- Wedge boundaries do not move on hover, focus, selection, or live-state change.
  Emphasis changes paint, type, or an interior rail, never the target under the
  pointer. This preserves motor plans and prevents neighbor motion while aiming.
- Make every pointer target at least 40 × 40 physical px; prefer 44 × 44 for
  touch. Measure the narrowest useful part of the sector, not only its outer arc.
- Keep visual gaps smaller than hit gaps when safe: the interactive path owns the
  full stable sector while an inset paint path supplies the groove.
- Recompute composition after a real size, font, locale, item, or ring change.
  Do not poll layout in an animation loop.

### Information priority

Use this admission order:

1. command label;
2. exact cost, quantity, shortcut, or consequence when it changes the decision;
3. status glyph;
4. command glyph;
5. decorative material.

Status is shape, not wedge copy. Model it as a semantic token such as `on`,
`off`, `live`, `ready`, `warning`, or `locked`, render it through a consistent
status-glyph family, and preserve a natural-language `statusLabel` in the
accessible name and consequence caption. Do not print implementation phrases
such as `INPUT OFF`, or routine state words such as `ON`, `OFF`, `LIVE`, and
`READY`, inside the wedge.

Do not turn an exact decision value into a pictogram. `$350`, `1 AP`, `12.0 oz`,
inventory counts, heat changes, and shortcuts remain text because the magnitude
matters. A status glyph must differ by silhouette as well as color so the state
survives color-vision differences and monochrome rendering.

The accessible name and consequence caption keep the full source copy even when
the visible surface needs a shorter display label. If no legal glyph pocket
remains, hide the glyph. If no legal label clears the 16 px physical floor, move
the full choice to a linear sheet or another larger surface; do not silently
shrink it.

### Composition rhythm

Treat every peer wedge as one member of a ring, not as an isolated packing
problem. Select one label-size tier that every peer can legally render. A short
label does not become larger merely because it has spare chord width, and a
status marker does not make its neighboring label smaller. Wrap the longer
label, lower the shared tier, or move the command to a larger surface.

Keep a stable semantic order from the outer side of the stack inward:

1. optional status rail;
2. command-glyph rail;
3. one- or two-line command-label rail;
4. optional exact-value rail.

An absent optional rail may collapse, but the remaining rails never reorder or
run inline to exploit a local gap. In particular, do not append a status glyph
to the label or append an inventory count to the command name. The rail gap is a
measured constraint, not a literal space character or an accidental flex gap.
This stable grammar is more important than maximizing the mean font size.

### Input parity

- Pointer: moving over a wedge previews it; click or tap commits once.
- Touch/pen: a short tap commits. A hold may preview detail, but consume the
  synthetic click so preview cannot also trigger the action.
- Keyboard: Left/Right rotate around the current ring; Up/Down move between
  outer ring, inner ring, and hub; Home/End reach ring endpoints; Enter/Space
  commit; Escape backs out one submenu before closing.
- Keep one predictable tab entry into the instrument, then expose the active
  descendant or a roving focus item to assistive technology. Every actionable
  sector has a role, accessible name, availability, and current/pressed state.
- A submenu transition hands focus to the new ring; Back restores the wedge that
  opened it. Repeated input cannot land on a replacement wedge after the DOM
  swaps under the pointer.

## Pretext wedge compositors

Pretext earns its cost when labels, command glyphs, exact values, and status
glyphs need to share irregular or variable-width sectors. It is a layout engine,
not an output medium: use its
measurements and line ranges to render ordinary DOM, SVG, Canvas, or another
host-native surface. Native CSS/SVG alone is still better for a fixed one-word
label at a known size, and SVG `textPath` is better for a decorative group name
that intentionally follows an arc.

### Renderer choice

Choose the renderer from the host rather than from Pretext:

- **DOM content over SVG targets — recommended for the current Psychodeli and
  Pot Luck carriers.** Keep the stable SVG wedge paths as semantic and hit-test
  geometry. Place an absolutely positioned, `pointer-events: none` DOM layer
  above the wheel, then materialize the selected line fragments as spans and
  inline SVG glyphs. This keeps CSS typography, localization, selection, and
  browser inspection available without duplicating command state.
- **DOM-native wedges.** When the host already uses buttons, apply the same
  generated path or polygon as CSS `clip-path` and render the Pretext fragments
  inside each button. Verify clipped pointer hit-testing, focus indication, and
  non-overlapping tab order in every target browser before choosing this path.
- **SVG-native content.** Materialize fragments as SVG `<text>` and `<svg>` when
  the wheel already owns all visual content, exact viewBox scaling is valuable,
  or a single exportable vector artifact is the requirement.

Do not use `foreignObject` merely to claim DOM support. A normal positioned DOM
overlay is easier to theme and test, while the shared geometry can still map
each slot between viewBox coordinates and CSS pixels.

### Pipeline

1. **Load a named font before measurement.** Await `document.fonts.load()` for
   every weight and size tier. Do not use `system-ui`; canvas and DOM can resolve
   it differently on macOS.
2. **Declare rails before measuring copy.** Reserve separate status, command,
   label, and exact-value line boxes in that order. The compositor may collapse
   an absent optional rail; it may not place a glyph or value beside the label.
3. **Turn text rails into planning slots.** For horizontal copy, intersect each
   candidate label or value line box with the padded annular sector and keep a
   continuous interval whose corners and edge midpoints remain inside the
   wedge. For an arc-follow probe, use the guarded arc length at that label
   rail's radius. Do not wrap against a horizontal chord and bend the result
   afterward; that creates false line breaks and crowds the inner rails.
4. **Prepare text once per style tier.** Give Pretext the label words at their
   real named font and the exact value as its own unbreakable item. Command and
   status glyphs are fixed SVG pockets, not rich-inline text items.
5. **Search ring-wide tiers.** At each candidate physical label size, compose
   every wedge with one or two label lines. Accept the first tier for which the
   entire peer ring passes; never retain a larger local tier for an easier wedge.
6. **Apply hard gates before scoring position.** Reject overflow, missing label
   or value content, physical text below 16 px, text contrast below 8:1, a glyph
   below its legible minimum, or a rail gap below its declared minimum. Among
   survivors at the shared tier, score vertical balance and chord use.
7. **Materialize only the ring winner.**
   `materializeRichInlineLineRange()` provides fragments, widths, gaps, and
   source-item indices for the text rails. Turn those into DOM spans, SVG text,
   or Canvas draws. An arc-follow renderer may segment the winning fragments
   into graphemes only at this stage, then position each grapheme along the
   planned rail. Place the 24-grid glyphs in their fixed rails and keep the
   original item data for `aria-label` and captions.
8. **Close the loop against rendered truth.** After fonts and paint settle,
   measure the actual DOM or SVG fragments with `getBoundingClientRect()`. Reject
   a candidate whose rendered bbox crosses the padded wedge even when Pretext's
   predictive canvas measurement fitted. Also audit peer type variance, the
   minimum rendered gap between glyph and text rails, and the gap between a
   curved label and its exact-value rail.

Pin Pretext and preload fonts. The runnable
[`radial-menu-pretext.html`](../examples/radial-menu-pretext.html) example vendors
`@chenglou/pretext` 0.0.5 locally and compares a fixed midpoint stack with the
shape-flow compositor.

### Composition sketch

```js
const labelItems = label.split(/\s+/).map((word, index) => ({
  text: `${index ? ' ' : ''}${word}`,
  font: `800 ${sharedLabelSize}px Arial`,
  break: 'never',
}))

const prepared = prepareRichInline(labelItems)
let cursor = { itemIndex: 0, segmentIndex: 0, graphemeIndex: 0 }

for (const slot of labelRailSlots) {
  const range = layoutNextRichInlineLineRange(prepared, slot.width, cursor)
  if (!range) break
  render(materializeRichInlineLineRange(prepared, range), slot)
  cursor = range.end
}
```

The command and status glyphs are placed independently in their declared rails.
Pretext decides line breaks inside the label and exact-value rails; it does not
decide semantic order or use spare label width to pull glyphs inline.

Pretext permits a `break: 'never'` item to overrun an otherwise empty line. That
is useful for pills and unbreakable tokens, but an annular sector is a hard
boundary. After each range, reject the candidate when `line.width > slot.width`
and continue the search at a smaller type tier. Split a multi-word command into
atomic word items so wrapping can occur between words without producing
`Harves` / `t` or another mid-command fracture.

### Experimental per-grapheme bows and carrier selection

Curved command labels are a probe, not the radial-menu default. Use a shallow bow
only when a short label underuses the outer part of a sector. Value-dense rings
and multiword commands default to upright word lines; a literal circle is not an
upgrade when it makes the reader rotate the word mentally.

- Keep the complete command and state in the semantic SVG/DOM target. The
  positioned letter layer is visual projection and may remain `aria-hidden`.
- Let Pretext choose the shared type tier and word breaks against guarded arc
  length. Then segment the winning fragments with `Intl.Segmenter` and place
  graphemes individually; never rotate one rigid string around its midpoint.
- Preserve word spacing when materializing letters. Measure cumulative prefixes
  so font kerning survives, and reparameterize a line-to-arc blend by its local
  path speed. Naively interpolating Cartesian glyph centers contracts side-wedge
  words and makes pairs such as `Mo` and `Co` collide.
- Separate **path follow** from **letter turn**. The first blends positions from
  a horizontal rail to a circular rail. The second independently blends each
  letter from upright toward the local tangent. This makes restrained hybrids
  testable instead of coupling curvature to an unreadable 90-degree turn.
- Reverse traversal where necessary to keep lower-half letters upright. Start a
  command probe near 30% path bow and 10% orientation follow, then verify the
  actual production font. The reference wheel resolves this to about 2.4
  degrees of letter turn; the earlier 42-degree result failed visual reading.
- Keep command glyphs and routine-status glyphs upright on their own outer
  rails. Keep decision-changing exact values horizontal on a separate inner
  rail unless a product test establishes a better grammar.
- Compute label capacity from the arc before Pretext wraps. After DOM paint,
  reject any glyph bbox outside the wedge or any label/value collision. A legal
  horizontal endpoint may use two word lines; an illegal endpoint hard-stops
  rather than disappearing through clipping.
- Select the carrier from the content before styling it. Short command rings may
  use the shallow DOM bow. A ring where at least half the wedges carry exact
  values uses an upright stack. Preserve the full command in `aria-label` and
  the consequence caption; a shorter unambiguous `displayLabel` may protect the
  wedge, as `Connections` does for `Work Connections, $350`.

An arc variant expands only after real-use evidence shows equal or better
command recognition, acquisition time, and error rate than the horizontal
carrier. Fit and novelty alone do not establish the upgrade.

### iBlipper DOM precedent

iBlipper's `PretextRenderer.tsx` demonstrates the DOM path at production scale:
it waits for the named font, uses `prepareWithSegments()` and
`layoutWithLines()` to choose wrapping and font sizes, then renders normal React
`.pretext-chunk` and `.pretext-line` elements. After two animation frames it
reads each line's `getBoundingClientRect()` and records fill, visible fill, and
truncation from the actual DOM.

Carry its measurement-parity lessons into wedge work:

- measure the transformed text that CSS will paint (`uppercase` in iBlipper),
  not the pre-transform source string;
- budget for CSS `letter-spacing`, stroke, per-character wrappers, and other
  effects that Pretext's canvas measurement does not see;
- treat emoji and platform-substituted glyphs as a canary because their DOM
  extent can materially exceed canvas metrics;
- distinguish raw overflow from visible clipped area; clipping can protect the
  surface without proving that the composition is well fitted;
- keep the post-render audit even when the predictive fit usually agrees.

For a command wedge, prefer rejection and the next smaller legal composition to
clipping readable content. Clipping is appropriate for decorative trails, not
for a label, cost, shortcut, availability reason, or glyph needed to decide.

## Glyph grammar

- Author on a 24 × 24 grid with round joins/caps unless the product has another
  established family.
- Use one primary structural color and at most one live/accent element. The
  second tone carries state or meaning, not decoration.
- Verify at the real 18–24 px glyph size. Large-source beauty is irrelevant if
  the mark collapses in its wedge.
- Do not use emoji as the primary command grammar. Platform substitution changes
  weight, metrics, color, and sometimes meaning.
- Keep command and status glyphs upright. Horizontal command labels remain the
  default. An explicit per-grapheme arc probe may turn individual letters within
  a tested ceiling; never rotate the icon or a whole command string as one unit.

## Verification matrix

Exercise the real content, not lorem ipsum:

| Dimension | Minimum proof |
|---|---|
| Density | 3, 5, and 8 wedges; primary and nested/split ring |
| Copy | shortest label, longest production label, state/cost, disabled reason |
| Status grammar | no printed routine state words; glyph has shape + accessible name |
| Size | desktop plus phone-sized same-origin iframe at the target CSS width |
| Script | English plus one CJK or RTL canary when localization is in scope |
| Input | pointer preview/commit, short touch, hold preview, keyboard ring + depth |
| State | default, focus, selected/on, unavailable, locked, submenu, Back |
| Geometry | every visual bbox inside its sector; target paths byte-stable across focus |
| Type | named fonts loaded; every readable line at least 16 physical px; 0 px peer-label variance unless hierarchy is explicit |
| Rhythm | declared rail order preserved; measured glyph/text and label/value gaps do not collapse |
| Carrier | short-label bow and value-dense upright stack both exercised with the same semantic targets |
| Arc probe | path follow and letter turn tested independently; kerning preserved; path contraction prevented; per-letter rotation recorded |
| Contrast | in-browser effective foreground/background audit at least 8:1 |
| Behavior | one commit per activation; focus survives submenu swap and return |

For optimization work, measure more than fit. Log task-local acquisition time,
pointer corrections, wrong-wedge entries, hold cancellations, and keyboard step
count. Expand the Pretext path only if it improves fit or comprehension without
regressing acquisition or input parity.

## Stop conditions and fallbacks

Stop the radial approach or fall back to a linear surface when:

- any production label requires text below 16 physical px;
- more than one wedge needs a caption to identify the command itself;
- localization produces routine four-line labels or unstable abbreviations;
- narrow sectors fail 40 × 40 target geometry;
- focus order and visible radial order cannot be made to agree;
- the menu contains heterogeneous controls whose interaction cannot be expressed
  as inspect, commit, enter submenu, or Back.

Do not add animation, fisheye expansion, or arc-follow command text to compensate
for an information-architecture failure. An arc probe must still satisfy every
label, consequence, input, and fallback requirement above.
