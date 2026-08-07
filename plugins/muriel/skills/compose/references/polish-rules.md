---
channel: polish
status: active
requires:
  brand: optional
  audience: optional
  reads:
    - muriel.contrast
output:
  kinds: [css, tsx, html]
  registers: [app, blog, editorial]
peer_channels:
  - web
  - interactive
  - charts
---

# Polish rules — UI micro-interaction + visual-detail discipline

Load this detailed reference only when the compact polish channel points to an
exact rule or the task needs a comprehensive implementation or audit pass.

The frontend-polish channel: the codified design-engineering rules that turn an OK interface into one that feels considered. Concentric border radius. Optical alignment. Scale on press. Tabular numbers. Interruptible transitions. The small things that compound.

This is **distinct from sibling channels**:

- [`channels/web.md`](../channels/web.md) covers editorial HTML, Marginalia, Pandoc, and static capture — the *prose* surface.
- [`channels/interactive.md`](../channels/interactive.md) covers live demos where the reader moves parameters — the *exploratory* surface.
- This channel covers UI polish — the *tactile* surface that any frontend benefits from regardless of its higher-level purpose.

Structurally mined from [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archived 2026-05). The 16 rules below are ported and tightened for muriel's brand floor; per-rule citations live inline. Mining stance follows muriel's curator pattern — port the discipline, not the React component code.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to use

- Building or reviewing UI components (buttons, cards, dropdowns, modals)
- Implementing animations, hover states, shadows, borders, typography micro-details
- Reviewing AI-generated frontend code for "feels off" without obvious cause
- Adding tactile feedback (scale on press, hover lift)
- Closing the gap between "renders correctly" and "feels considered"
- Triggers: *"make it feel better"*, *"polish this"*, *"feels off"*, *"jarring"*, *"loose"*

If the work is data viz, use [`channels/charts.md`](../channels/charts.md). If it's a live demo, use [`channels/interactive.md`](../channels/interactive.md). If it's prose-rendering HTML, use [`channels/web.md`](../channels/web.md).

## Workflow

1. **Identify the surface.** Is it a button, card, list item, modal, navigation? Different surfaces apply different subsets of rules.
2. **Apply universal rules** (1–4 below) — they hit nearly every interface.
3. **Apply surface-specific rules** from the matching section (Typography / Surfaces / Animations / Performance).
4. **Run the validation checklist** before declaring done.
5. **Audit any text element with `muriel.contrast`** if brand tokens are in play — the 8:1 floor still binds; polish is additive, never a contrast excuse.

## Universal rules

The four that hit almost every interface. Numbered for citation.

### 1. Concentric border radius

When nesting rounded elements, the outer radius must equal the inner radius plus the padding between them:

```
outer_radius = inner_radius + padding
```

Mismatched radii on nested elements is the single most common thing that makes interfaces feel off. If padding exceeds `24px`, treat the layers as separate surfaces and choose each radius independently — the strict math stops mattering at that scale.

```css
/* Good — concentric */
.card        { border-radius: 20px; padding: 8px; }  /* 12 + 8 = 20 */
.card-inner  { border-radius: 12px; }

/* Bad — same radius on both */
.card        { border-radius: 12px; padding: 8px; }
.card-inner  { border-radius: 12px; }
```

### 2. Optical over geometric alignment

When geometric centering looks off, align optically. Three common cases:

- **Button with text + trailing icon:** `icon-side padding = text-side padding − 2px` so the icon doesn't appear pushed too far out.
- **Play-button triangle:** shift `2px` right of geometric center — the triangle's visual mass sits left of its bounding box.
- **Asymmetric icons (stars, arrows, carets):** fix in the SVG itself when possible; fall back to `margin-left: 1px` adjustments only if the SVG can't be edited.

### 3. Shadows over borders for depth

For buttons, cards, and containers using a border to suggest elevation: prefer a three-layer `box-shadow` over a solid border. Shadows adapt to any background via transparency; solid borders don't survive background changes or image fills.

**Exception:** dividers (`border-b`, `border-t`, side borders for layout separation) and form-input outlines (for focus accessibility) stay as borders. The shadow-over-border rule is for *elevation*, not *separation*.

```css
:root {
  --shadow-border:
    0 0 0 1px rgba(0, 0, 0, 0.06),
    0 1px 2px -1px rgba(0, 0, 0, 0.06),
    0 2px 4px 0 rgba(0, 0, 0, 0.04);
  --shadow-border-hover:
    0 0 0 1px rgba(0, 0, 0, 0.08),
    0 1px 2px -1px rgba(0, 0, 0, 0.08),
    0 2px 4px 0 rgba(0, 0, 0, 0.06);
}

/* Dark mode — simplify to a single white ring */
[data-theme="dark"] {
  --shadow-border:       0 0 0 1px rgba(255, 255, 255, 0.08);
  --shadow-border-hover: 0 0 0 1px rgba(255, 255, 255, 0.13);
}
```

### 4. Minimum 40×40px hit area

Interactive elements need a hit area of at least `40×40px` (WCAG 2.5.5 recommends `44×44`; `40` is the minimum muriel accepts). If the visible element is smaller (a `20×20` checkbox), extend with a pseudo-element. **Never let two interactive hit areas overlap** — shrink the pseudo-element rather than have collisions.

```css
.checkbox {
  position: relative;
  width: 20px;
  height: 20px;
}
.checkbox::after {
  content: "";
  position: absolute;
  inset: -10px;       /* extends to 40×40 */
}
```

## Typography rules

### 5. `text-wrap: balance` on headings

Headings and short text blocks (≤6 lines on Chromium, ≤10 on Firefox) get even line distribution with `text-wrap: balance`. The balancing algorithm is computationally expensive — on body paragraphs it's silently ignored.

```css
h1, h2, h3 { text-wrap: balance; }
```

### 6. `text-wrap: pretty` on body text

For paragraphs longer than the balance threshold, `text-wrap: pretty` runs a slower algorithm that favors typography over performance. Result: fewer orphans without the line-count cap.

```css
p, .article-body { text-wrap: pretty; }
```

Decision table:

| Scenario | Property |
|---|---|
| Headings, titles, short text (≤6 lines) | `text-wrap: balance` |
| Body paragraphs, descriptions | `text-wrap: pretty` |
| Code blocks, pre-formatted text | Neither — leave default |

### 7. macOS font smoothing at the root

Apply once on `<html>`. Other platforms ignore these properties, so the rule is safe to ship universally.

```css
html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

Never apply per-element — inconsistent smoothing reads as heavier text in some places and thinner in others, which is more distracting than no smoothing at all.

### 8. Tabular numbers for dynamic values

Counters, prices, timers, table columns of numbers, animated number transitions — all use `font-variant-numeric: tabular-nums` to prevent layout shift as digits change.

```css
.counter, .price, table td.numeric { font-variant-numeric: tabular-nums; }
```

**Don't** use tabular-nums on static display numbers, phone numbers, zip codes, version strings, or decorative large numerals — the proportional spacing reads better when the value isn't changing. (Some fonts like Inter widen the `1` glyph under tabular-nums; verify in the project's font before shipping.)

## Surface rules

### 9. Image outlines

Add a subtle `1px` inset outline to images. Creates consistent depth across a design system without affecting layout (outlines don't add to box dimensions).

```css
img {
  outline: 1px solid rgba(0, 0, 0, 0.1);
  outline-offset: -1px;
}
[data-theme="dark"] img {
  outline-color: rgba(255, 255, 255, 0.1);
}
```

### 17. Local text scrims over translucent surfaces — never a panel-wide dark plate

When text sits on a translucent / backdrop-blurred surface (a frosted popup, a glass card over live content, an overlay on a visualization) and needs contrast against whatever shows through, **darken behind the text only** — per-line caption plates or a glyph-hugging scrim. Do **not** drop a large opaque/dark fill behind the whole content block to buy contrast.

A hard-edged dark plate sitting *inside* a translucent panel reads as a **dark box floating in fog**: it re-introduces the nested-container problem (rule 1) the glass surface was supposed to avoid, doubles the visible container count, and muddies the very blur that made the surface feel like glass. It's the lazy contrast fix — the box just moved inward.

Opaque media (album art, thumbnails, avatars) already carry their own contrast — let them sit **directly** on the translucent surface. Only the text needs help, so only the text gets a backing.

```css
/* Bad — panel-wide scrim: a dark box floating in the frosted panel */
.card { background: radial-gradient(120% 100% at 50% 40%, rgba(6,7,16,.86), transparent); }

/* Good — card is layout-only; selective darkening hugs each text line */
.card   { background: none; }
.title,
.artist { background: rgba(6,8,13,.9);          /* near-opaque so 8:1 holds over any backdrop */
          padding: 3px 13px; border-radius: 10px;
          -webkit-box-decoration-break: clone;   /* per-line plates when the line wraps */
          box-decoration-break: clone; }
```

The plate opacity is a **contrast decision, not a taste one**: compute it against the *brightest* the backdrop can get — a near-white highlight in a visualization, not the calm frame in front of you. A translucent plate that looks fine over the current view can dip below 8:1 for light text over a bright highlight. Push alpha toward `0.9` (≈12:1 even over pure white) rather than leaving it pretty-but-failing at `0.75` (~7.9:1 for dim text over white). Hide empty plates (`:empty { display: none }`) so missing metadata doesn't leave a floating dark pill.

## Animation rules

### 10. Interruptible transitions for interactive state, keyframes only for one-shot sequences

CSS *transitions* interpolate toward the latest state and retarget mid-animation. CSS *keyframe animations* run on a fixed timeline and restart from the beginning if re-triggered. Pick by intent:

| | Transitions | Keyframes |
|---|---|---|
| Interruptible | Yes — retargets | No — restarts |
| Use for | Interactive state changes (hover, toggle, drawer) | One-shot sequences (enter animations, loading spinners) |

A drawer using keyframes for open/close snaps on rapid toggling. A drawer using transitions smoothly reverses mid-flight.

### 11. Split + stagger enter animations

Don't animate a single container. Break enters into semantic chunks and stagger:

- Title → description → CTA buttons, ~100ms between groups.
- For hero titles, consider splitting into individual words at ~80ms stagger.
- Combine `opacity` + `translateY(12px)` + `filter: blur(4px)` for the enter effect.

```css
.stagger-item { opacity: 0; transform: translateY(12px); filter: blur(4px); animation: fadeInUp 400ms ease-out forwards; }
.stagger-item:nth-child(1) { animation-delay:   0ms; }
.stagger-item:nth-child(2) { animation-delay: 100ms; }
.stagger-item:nth-child(3) { animation-delay: 200ms; }
@keyframes fadeInUp { to { opacity: 1; transform: translateY(0); filter: blur(0); } }
```

### 12. Subtle exit animations

Exits should be quieter than enters — the user's focus is already moving to the next thing. Small fixed `translateY(-12px)` over `150ms` ease-in, not a full-height slide-out. Exception: when spatial context matters (a card returning to a list, a drawer to a screen edge), slide the full distance.

Never remove the exit entirely — popping out of existence loses the user's place.

### 13. Contextual icon animations — exact values, never deviate

When icons appear/disappear contextually (hover toolbars, state-change toggles), animate with `opacity` + `scale` + `blur`. Use **exactly these values**:

- `scale`: `0.25` → `1` (never `0.5`, never `0.6`)
- `opacity`: `0` → `1`
- `filter`: `blur(4px)` → `blur(0px)`
- Motion: `{ type: "spring", duration: 0.3, bounce: 0 }` — **bounce must be `0`**, never `0.1` or higher

If the project has `motion`/`framer-motion` in `package.json`, use `AnimatePresence` with these values. If not, keep both icons in the DOM (one absolutely positioned, one in flow) and cross-fade via CSS transitions with `cubic-bezier(0.2, 0, 0, 1)` — don't add a motion dependency just for icon swaps.

The exact values are tuned: smaller scale values feel jarring, bounce > 0 reads as gimmicky, opacity-only feels lifeless.

### 14. Scale on press: exactly `0.96`, never below `0.95`

A subtle scale-down on click gives buttons tactile feedback. Always `scale(0.96)`. **Anything below `0.95` reads as exaggerated** — past that threshold the button feels like it's collapsing rather than depressing.

```css
.button { transition-property: scale; transition-duration: 150ms; transition-timing-function: ease-out; }
.button:active { scale: 0.96; }
```

Not every button needs this. Provide a `static` prop on the button component to disable scale for cases where the motion would be distracting (form submits inside dense layouts, primary-action buttons that already have other feedback).

### 15. Skip enter animations on page load

For animation systems that fire on mount (Framer Motion's `AnimatePresence`, etc.), use `initial={false}` so default-state elements don't animate in on first render. Icons that match the current state on page load shouldn't pop in — only state *changes* should animate.

**Caveat:** don't apply this to staged page-enter sequences (rule 11). If `initial={false}` would skip the entire intentional entrance, the rule doesn't apply.

## Performance rules

### 16. Never `transition: all`; `will-change` only for compositor-friendly properties

Two coupled performance rules:

- **`transition: all` is banned.** Always specify exact properties: `transition-property: scale, opacity, filter`. The shorthand forces the browser to watch every property for changes — causes unintended transitions on color/padding/shadow and prevents browser optimizations. Tailwind's `transition` shorthand has the same issue; use `transition-[scale,opacity,filter]` bracket syntax instead. `transition-transform` is fine — it expands to `transform, translate, scale, rotate` specifically.
- **`will-change` only for GPU-compositable properties** — `transform`, `opacity`, `filter`, `clip-path`. Never `will-change: all`. Never on `background-color`, `padding`, `top/left/width/height` — they can't be GPU-composited so the hint accomplishes nothing while costing a compositing layer in memory. Only add `will-change` when you observe first-frame stutter; modern browsers optimize most cases on their own.

| Property | GPU-compositable? | `will-change` worth it? |
|---|---|---|
| `transform`, `translate`, `scale`, `rotate` | Yes | Yes |
| `opacity` | Yes | Yes |
| `filter` (blur, brightness) | Yes | Yes |
| `clip-path` | Yes | Yes |
| `background-*`, `border-*`, `color` | No | No |
| `top`, `left`, `width`, `height` | No | No |

## Motion axes — easing, scale, budget

Rules 18–22 cover the axes rules 10–16 leave open. Paraphrased from All-The-Vibes/ATV-Design's `emil-design-eng-inspired` (MIT). `muriel.motion` enforces the mechanical ones — `validate_properties`, `easing_for`, `validate_scale`. muriel's duration **binary** (`muriel.motion`: utility ≤ 100 ms / cinematic ≥ 1500 ms) deliberately overrides the source's 100–500 ms bands — don't import those.

### 18. Easing curve follows direction

The curve encodes the physical model the user applies to the motion. Pick by where the element is going, not by taste:

| Direction | Curve | Why |
|---|---|---|
| Entering / user-triggered (modal mount, toast in, click response) | `ease-out` | decelerates to rest — catches up to where the user expects it |
| Leaving (modal dismiss, toast out) | `ease-in`, or linear under 150 ms | accelerates away; exit is less load-bearing |
| Repositioning on-screen / system-scheduled (list reorder, reflow) | `ease-in-out` | accelerates from one rest position, decelerates into the next |

**Never `ease-in` for an entrance** — acceleration-on-appear reads as the element *avoiding* the user. `muriel.motion.easing_for("enter"|"exit"|"move")` returns the curve.

### 19. Entrance scale floors at `0.95` — never from `0`

Distinct from press feedback (rule 14). A mounting modal/popover scales `0.95 → 1` while opacity goes `0 → 1`: opacity carries "wasn't here, now is," scale carries depth. From `0` it reads as a black hole opening; from `0.95` it's a card stepping forward. Set a popover's `transform-origin` toward its anchor (Radix exposes `--radix-*-transform-origin`) so it doesn't appear unanchored. `muriel.motion.ENTRANCE_SCALE_FLOOR` / `validate_scale()`.

### 20. Gate `:hover` behind pointer capability; carry touch presses with opacity

```css
@media (hover: hover) and (pointer: fine) { .card:hover { /* … */ } }
```

An unconditional `:hover` fires on tap on touch devices and sticks until the next tap ("stuck hover"). On touch there's no hover preview, so the press itself must carry weight — pair the `:active` scale (rule 14) with a brief opacity dip (`0.85` for ~80 ms).

**Reduced motion is a dial, not a kill switch.** `prefers-reduced-motion: reduce` means "don't parallax/slide me across the viewport," not "freeze everything." muriel brands pick the response via `[a11y].motion_reduce_policy`: the default `collapse-to-zero`, or the softer `reduce` (shorten to ~100 ms, drop transforms to identity, keep opacity). Either way, decorative/background motion goes.

### 21. One load-bearing motion per interaction

A single click/tap/drag-end should produce **one** motion that carries meaning. If a click opens a modal *and* slides a sidebar *and* fades a backdrop *and* repositions a tooltip, the user can't tell which is the consequence of their action. Pick the most informative (usually the modal entrance) and play the rest silently — instant opacity, no transforms.

### 22. Reorders and expands use FLIP, not animated layout

Rule 16 bans animating layout properties; FLIP is the technique that replaces them. To move an element to a new position, don't animate `top`/`left`/`height` — snapshot **F**irst and **L**ast positions, **I**nvert the delta with a `transform`, then transition the transform to identity (**P**lay). For accordions, prefer letting content settle into place; if height must animate, animate `max-height` with a generous ceiling and accept it's less crisp than FLIP.

## Composition rules — hierarchy, distribution, surface system

Rules 1–22 are *tactile* detail — the feel of a single element. Rules 23–27 are one altitude up: how elements compose so a build doesn't read as AI-generated. This is the layer that separates a Linear/Vercel/Stripe dashboard from a template. Paraphrased from [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) (MIT) — **with its low-contrast hierarchy lever removed** (see rule 24); the rest is 8:1-safe as written.

### 23. One focal point per view

Every screen has one thing the user came to do. That element dominates — through **size, weight, position, or surrounding space** (not low-contrast neighbors — see rule 24). When everything competes equally, nothing leads and the layout reads as a parking lot. Before building, name the focal element; make it win; demote the rest deliberately. The failure mode is *flatness* — same size, weight, spacing everywhere — which is the single biggest "this was generated" tell.

### 24. Type scale is a ratio — demote with weight, size, and space, never with low contrast

Pick a ratio and step it: `~1.2` (dense/calm), `~1.25` (most product UI), `~1.333` (expressive). From a 14–16px body that yields a *visibly* distinct scale, not 15/16/17 mush. A 14px base at 1.25: `caption 11 · body 14 · h4 16 · h3 18 · h2 22 · h1 28 · display 44+`. Round to whole px and to the spacing grid.

Weight does more hierarchy work than size: a single 14px size holds three tiers through weight alone (`600` value / `500` label / `400` meta).

**The 8:1 carve.** The source skill builds a fourth lever — demoting secondary/muted/disabled text via *low opacity and muted color* (`secondary`/`muted`/`faint` tiers at e.g. slate-600/400/200). **muriel does not import that lever** — a muted tier at slate-400 on white is ~3:1 and violates the 8:1 floor (`~/CLAUDE.md` — readable text has no contrast exception; only logotypes/decorative lettering do, per WCAG 1.4.3). Build the *same* hierarchy with the three contrast-safe levers — **weight, size, and space** — and keep every text tier, including metadata and disabled-state labels, at ≥8:1. Disabled controls signal state through cursor, border, and fill, not by dropping text below floor.

### 25. 60/30/10 distribution — one accent, color means something

A dominant neutral surface (~60%), a secondary tone (~30%), and ~10% accent. Color is a scarce resource: gray builds structure, color *communicates* (status, action, identity). One intentional accent beats five low-commitment tints. Keep **one hue across surfaces** and shift only lightness — different hues per surface fragments the space. Decorative gradients and unmotivated color are noise; remove them or make them mean something. (The accent still clears 8:1 anywhere it carries text.)

### 26. Surface elevation is a numbered system, whisper-quiet

Surfaces stack — dropdown above card above page — via a numbered lightness scale, each step only a few percent: dark mode base → +7% → +9% → +12%; light mode stays light and adds shadow per rule 3. You should *feel* the step, not see it (the squint test, rule 27). Specifics:

- **Sidebars:** same background as the canvas + a subtle border, not a different color — different colors split the UI into "sidebar world" and "content world."
- **Inputs:** slightly *darker* than their surroundings, not lighter — inset surfaces receive content; a darker fill says "type here" without a heavy border.
- **Dropdowns/popovers:** exactly one level above their parent surface, or the layering collapses.

This is the surface-token side of the brand floor: text on every elevation step must still clear 8:1, so verify against the *lightest* step a given text color lands on.

### 27. Composition test battery — run before showing

Higher-altitude analogues to the validation checklist; run them on the rendered output, not the CSS:

- **Swap test** — mentally swap the typeface for the default and the layout for a standard template. Anything that wouldn't change is where you defaulted.
- **Squint test** — blur your eyes: hierarchy still legible (what's above what, where sections divide), and *nothing* jumps out harshly? Quiet structure, clear focal point.
- **Signature test** — point to five specific elements expressing this product's identity. "The overall feel" doesn't count.

If a screen fails these, the fix is composition (rules 23–26), not more micro-polish.

## Anti-patterns at a glance

| Mistake | Fix |
|---|---|
| Same border radius on parent and child | `outer = inner + padding` |
| Icons look off-center | Optical adjustment (icon-side padding −2px, or fix SVG directly) |
| Hard 1px borders for elevation | Three-layer `box-shadow` |
| Jarring enter animations | Split into semantic chunks, stagger at ~100ms |
| Dramatic exit animations | Small `translateY(-12px)`, `150ms` ease-in |
| Icon swaps that pop without animation | `scale 0.25→1` + `opacity 0→1` + `blur 4px→0`, spring `bounce: 0` |
| Buttons with no press feedback | `scale(0.96)` on `:active`, never below `0.95` |
| Numbers that shift layout as they update | `font-variant-numeric: tabular-nums` |
| Text rendering heavy on macOS | `-webkit-font-smoothing: antialiased` at root |
| Headings with orphaned words | `text-wrap: balance` |
| Body paragraphs with orphans | `text-wrap: pretty` |
| Page-load animations on default-state elements | `initial={false}` on the AnimatePresence boundary |
| `transition: all` or `transition` shorthand | `transition-property: scale, opacity` (or Tailwind bracket syntax) |
| `will-change: all` or `will-change: background-color` | Only on `transform`, `opacity`, `filter`; only when stutter is observed |
| `ease-in` on a modal/popover entrance | `ease-out` for entrances; reserve `ease-in` for exits (rule 18) |
| Entrance scaling from `scale(0)` | Floor at `scale(0.95)`; let opacity carry the appear (rule 19) |
| Unconditional `:hover` (sticks on touch) | Gate behind `@media (hover: hover) and (pointer: fine)` (rule 20) |
| One click firing several competing motions | One load-bearing motion; play the rest silently (rule 21) |
| Animating `top`/`left`/`height` to reorder | FLIP (transform-based), or `max-height` for accordions (rule 22) |
| Tiny hit areas on small icon buttons | Extend with `::after { inset: -10px }` to 40×40 minimum |
| Panel-wide dark scrim to make text readable on a translucent surface | Transparent container; near-opaque per-line plates behind the text only — opaque media sits directly on the glass |
| Flat layout — everything one size/weight, no focal point | Name the focal element; make it win via size/weight/space (rule 23) |
| Hierarchy built by dimming text (muted/disabled tiers below 8:1) | Demote with weight + size + space; keep every tier ≥8:1 (rule 24) |
| Five tints spread evenly / one accent on everything | 60/30/10, one intentional accent, one hue shifting only lightness (rule 25) |
| Different background color for the sidebar | Same canvas + subtle border; elevation via whisper-quiet lightness steps (rule 26) |
| Inputs lighter than their surroundings | Inputs slightly darker — inset surfaces receive content (rule 26) |

## Validation checklist

Before declaring a UI surface done, walk through these:

- [ ] Nested rounded elements use concentric radius math
- [ ] Icons and asymmetric shapes are optically centered, not geometrically
- [ ] Elevation uses layered `box-shadow`, not solid borders
- [ ] Images carry a subtle `1px` inset outline
- [ ] Text over translucent/blurred surfaces uses local per-line plates (computed for 8:1 over the brightest backdrop), not a panel-wide dark scrim
- [ ] Interactive elements have ≥40×40px hit area (no overlapping hit areas)
- [ ] Enter animations are split + staggered (~100ms between groups)
- [ ] Exit animations are subtle (small `translateY`, shorter duration than enter)
- [ ] Contextual icon swaps use the canonical `scale 0.25→1` + `opacity` + `blur` recipe with `bounce: 0`
- [ ] Buttons have `scale(0.96)` on press (with `static` opt-out where appropriate)
- [ ] Default-state elements don't animate on page load (`initial={false}`)
- [ ] No `transition: all` anywhere — exact properties only
- [ ] `will-change` only on compositor-friendly properties, only when first-frame stutter is observed
- [ ] Easing matches direction — enter `ease-out`, exit `ease-in`, on-screen move `ease-in-out`
- [ ] Entrance scale floors at `0.95` (not `0`); `:hover` gated behind `@media (hover: hover) and (pointer: fine)`
- [ ] One load-bearing motion per interaction; reorders/expands use FLIP, not animated layout
- [ ] macOS font smoothing applied once at root
- [ ] Dynamic numbers use `tabular-nums`
- [ ] Headings use `text-wrap: balance`; body uses `text-wrap: pretty`
- [ ] One named focal point per view; hierarchy demotes with weight/size/space, never with sub-8:1 muted text (rules 23–24)
- [ ] ~60/30/10 distribution, one accent, one hue shifting only lightness (rule 25)
- [ ] Surface elevation is a whisper-quiet numbered scale; sidebar = canvas; inputs darker (rule 26)
- [ ] Passes the composition battery — swap / squint / signature (rule 27)

## Brand-floor reminder

Polish is additive — it never excuses a contrast violation. Any text element in the polished UI still has to clear muriel's 8:1 floor:

```bash
python -m muriel.contrast audit-svg path/to/component.svg
python -m muriel.contrast audit-html path/to/component.html
```

Hover and focus states are particularly likely to drop below 8:1 — verify both rest and hover states explicitly. Shadows-over-borders (rule 3) interact with this: hover-shadow color must clear floor against whatever sits beneath.

## See also

- [`channels/web.md`](../channels/web.md) — editorial HTML, marginalia, the prose surface where polish rules apply to readable content
- [`channels/interactive.md`](../channels/interactive.md) — live demos with parameter sliders, where the polish rules apply to the controls
- [`channels/charts.md`](../channels/charts.md) — data viz, where polish applies to tooltips, axis labels, hover states
- [`agents/muriel-critique.md`](../../../agents/muriel-critique.md) — runs the polish validation checklist as part of critique when artifacts target the `app` register

## Prior art

- [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archived May 2026) — Source for rules 1–16. The mathematical-precision framing (`outer = inner + padding`, exact `0.96` press value, exact `0.25` icon scale, `bounce: 0`) is preserved verbatim because the values are tuned, not arbitrary.
- [All-The-Vibes/ATV-Design](https://github.com/All-The-Vibes/ATV-Design) `emil-design-eng-inspired` (MIT) — Source for rules 18–22 (easing-by-direction, entrance scale floor, hover-gating, motion budget, FLIP), itself a clean-room paraphrase of [emilkowalski/skill](https://github.com/emilkowalski/skill). muriel keeps its own duration binary and `0.96` press value over the source's bands and `0.97`.
- [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) (MIT, Damola Akinleye) — Source for rules 23–27 (composition: focal point, type-scale ratio, 60/30/10, surface-elevation system, test battery). muriel **drops the source's low-opacity/muted-color hierarchy lever** — it conflicts with the 8:1 floor — and rebuilds the same hierarchy on weight + size + space. Its polish/motion section (concentric radius, tabular-nums, easing, hit area, etc.) was *not* imported: muriel rules 1–22 already cover it, more precisely.
- [Material Design 3 Motion](https://m3.material.io/styles/motion) — Tangentially related; muriel intentionally does not adopt Material's broader motion vocabulary.
- [Apple HIG — Motion](https://developer.apple.com/design/human-interface-guidelines/motion) — Read-only reference; cited by paraphrase per scholarly discipline (Apple-proprietary docs).
