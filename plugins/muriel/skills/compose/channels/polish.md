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

# Polish — interaction and visual-detail discipline

Use this channel when an interface works but its hierarchy, focus, density,
motion, or tactile feedback is unclear. Polish is a design-engineering pass,
not decoration and not a substitute for fixing the interaction model.

If the interaction model itself is unresolved, run the behavior-truth gate
below before applying visual-detail rules.

## Purpose in the solution

Help the calling agent make the visible interaction model clearer and more
coherent while preserving canonical state, accessibility, and product logic.

Before editing, tell the calling agent:

- **Purpose:** the user-visible confusion or inconsistency to resolve.
- **Integration:** the existing component/state path the solution must join.
- **Proof:** the task flow and rendered states that will demonstrate success.

Do not produce a detached “Muriel verdict” and then hand the task back. Carry
the chosen visual and interaction constraints into the implementation plan,
code, tests, and rendered verification.

## Behavior-truth gate

Use this gate when the visible slice includes a multi-step or async flow,
destructive or reversible work, drag/gesture behavior, ambiguous component
state, or an error path:

1. Name the user's goal and the existing canonical state owner.
2. Map the applicable transitions, including cancel/back, failure, recovery,
   and resume. Do not require irrelevant states merely to complete a checklist.
3. Define immediate acknowledgment separately from eventual success or failure.
4. Exercise the happy path, one failure-and-recovery path, and rapid reversal or
   duplicate input before polishing the surface.

Read
[`../references/interaction-contracts.md`](../references/interaction-contracts.md)
for the state matrix, micro-interaction contract, latency budgets, optimistic
UI gate, and proof checklist. This reference resolves behavior; it does not
authorize a parallel state model.

## Default workflow

1. Name the focal task and walk it with keyboard and pointer before editing.
2. Identify whether the defect is behavioral, structural, compositional, or
   tactile.
3. If behavioral, apply the behavior-truth gate. Then fix the highest-altitude
   remaining problem: hierarchy → surface system → micro-motion.
4. Reuse canonical state and controls; do not create a parallel UI model.
5. Render real applicable states, including narrow layouts, focus, hover,
   pressed, loading, success, disabled, empty, and error where relevant.
6. Report the Muriel delta: changed decision, integrated implementation, and
   proof.

## Core constraints

### Structure and hierarchy

- Give every view one focal point.
- Use progressive disclosure when more than about seven peer choices compete.
- Build hierarchy with size, weight, position, and space—never illegible muted
  text.
- Use one intentional accent and a quiet numbered surface-elevation system.
- Preserve at least `40×40px` hit areas (`44×44px` when the product standard
  permits).
- Keep nested radii concentric: `outer = inner + padding`.
- Prefer optical alignment over geometric centering for asymmetric icons.

### Typography and surfaces

- Apply font smoothing once at the root.
- Use `text-wrap: balance` for headings and `pretty` for prose.
- Use tabular numerals only for values that update or align in columns.
- Use shadows for elevation and borders for separation or focus.
- Put local text plates behind text over unpredictable translucent backdrops;
  do not darken an entire glass panel to rescue a few labels.
- Keep every text-bearing state at the 8:1 floor.

### Motion

- Use transitions for interruptible state and keyframes for one-shot sequences.
- Never use `transition: all`; name exact properties.
- Animate compositor-friendly properties: `transform`, `opacity`, `filter`,
  and `clip-path`.
- Use `ease-out` to enter, `ease-in` to exit, and `ease-in-out` to reposition.
- Give each interaction one load-bearing motion.
- Gate hover behavior behind `(hover: hover) and (pointer: fine)`.
- Treat reduced motion as a design mode, not an afterthought.
- Use FLIP for reorders; do not animate `top`, `left`, `width`, or `height`.

## Composition check

Run these on the rendered output:

- **Task test:** can the primary action be found and completed without learning
  browser Tab order?
- **Squint test:** does the hierarchy remain legible when detail disappears?
- **Swap test:** what would remain unchanged if replaced by a generic template?
- **Signature test:** name five concrete elements expressing this product.
- **State test:** do applicable states, transitions, and recovery paths remain
  coherent?

## Verification

Run relevant project tests, inspect representative viewports, and audit text:

```bash
python -m muriel.contrast path/to/component.html
python -m muriel.contrast path/to/component.svg
```

Check console errors, overflow, focus order, target size, reduced motion, and
rapid interaction reversal. A rule applied in source but not verified in the
render is still a hypothesis.

## Load deeper only when needed

Read
[`../references/interaction-contracts.md`](../references/interaction-contracts.md)
when behavior, async feedback, recovery, or state ownership is unresolved.
Read [`../references/polish-rules.md`](../references/polish-rules.md) only when
the task needs exact CSS recipes, motion constants, the complete numbered rule
set, or a comprehensive audit. Do not load it for a single hierarchy or spacing
decision.
