---
reference: annular-interfaces
status: experimental
requires:
  canonical_state: required
  declared_polar_semantics: required
  measured_geometry: required
output:
  kinds: [annular-interface-contract, polar-instrument, interaction-test]
  registers: [app, game, web, native, installation]
---

# Annular interfaces — polar meaning before sci-fi chrome

Use this competency when concentric rings, sectors, spokes, or a central subject
carry an interface's actual information or interaction. **Annular interface** is
Muriel's working umbrella, not a claim that the industry has one settled name
for every circular screen.

The familiar terms name narrower things:

- a **pie, ring, or radial menu** uses direction to select a command;
- a **polar plot or plan-position instrument** uses angle and radius as data
  axes;
- a **dial or annular gauge** maps progress or a bounded value to arc length;
- a **cyclic timeline** maps phase or time around a period;
- a **sunburst** maps hierarchy depth to radius and sibling weight to angle;
- a **reticle** establishes a subject, tolerance, or aiming relationship around
  a centre and may not be interactive at all.

The [Science Fiction & Fantasy Stack Exchange
discussion](https://scifi.stackexchange.com/questions/214058/what-is-the-name-of-this-sci-fi-circular-interface-seen-on-computers-and-hologra)
calls its examples ring or radial menus. That is accurate only when the sectors
are commands. FUI screens often combine several of the other structures in one
frame. Classify each ring by what it means before borrowing the silhouette.

## Use gate

Choose an annular composition when at least one polar relationship is native to
the task:

- direction, bearing, orientation, or phase is primary;
- distance from a subject matters;
- the domain is genuinely cyclic;
- a centre-and-periphery relationship is part of the mental model; or
- recursive containment benefits from a radial overview.

Prefer a Cartesian chart, table, linear timeline, list, or conventional control
when order and comparison are linear, exact cross-item comparison dominates,
the centre has no stable meaning, or the circle would merely decorate unrelated
readouts. A sci-fi register does not make polar geometry truthful.

## Start with a semantic declaration

Before drawing, write down the meaning of angle, radius, rings, centre, and
motion. A compact host-owned model is enough:

```js
const polarContract = {
  angle: {
    meaning: 'bearing',
    domain: [0, 360],
    zero: 'north',
    direction: 'clockwise',
    unit: 'degrees',
  },
  radius: {
    meaning: 'range',
    domain: [0, 100],
    unit: 'km',
  },
  center: { meaning: 'sensor origin' },
  rings: [
    { id: 'range-gates', role: 'axis', source: 'range scale', update: 'static' },
    { id: 'contacts', role: 'data', source: 'canonical tracks', update: 'event' },
    { id: 'sweep', role: 'feedback', source: 'scan phase', update: 'animation' },
  ],
}
```

The product owns the values and effects. The annular renderer accepts the
contract and projects it into paths, labels, hit regions, and a linear
alternative. It does not infer meaning from color, visual proximity, or a
clockwise animation.

## Shared geometry contract

- Use one polar transform and one annular-sector primitive. Data marks,
  interaction targets, rails, focus paint, and export paths derive from them.
- Keep semantic geometry immutable across hover, focus, selection, alarm, and
  live-state changes. Emphasis changes paint, stroke, a halo, or an interior
  rail; the point, sector, angle, and radius stay put.
- Separate the **data path**, **paint path**, and **hit path**. A generous target
  may surround a precise contact or thin arc without changing what the mark
  means.
- Declare the angular zero, direction, radial domain, clamping behavior, and
  whether the centre is data-bearing or a dead zone.
- Reserve foreground lanes for labels and callouts before adding ornamental
  rings. A ring that exists only to fill space loses to readable evidence.
- Measure the rendered result in screen coordinates. Perspective, SVG viewBox
  scaling, and responsive layout can invalidate clearance that passed in world
  coordinates.

## Signal, context, and decoration

Every visible layer belongs to exactly one tier:

1. **Signal** — the subject, selected value, alarm, command, or comparison the
   user is here to read or act on.
2. **Context** — axes, range gates, history, uncertainty, thresholds, or
   provenance needed to interpret the signal.
3. **Decoration** — texture or authored atmosphere with no claimed data or
   control meaning.

Signal and context require a named source, unit when applicable, update rule,
and accessible equivalent. Decoration is `aria-hidden`, pointer-inert, and may
not resemble an enabled control. Never promote decoration into context with a
plausible-looking number.

Use this admission order when the circle becomes crowded:

1. selected subject and consequence;
2. axis meaning, units, and current value;
3. data marks and uncertainty;
4. thresholds, history, and comparison guides;
5. ornament.

## Ring grammar

### Centre

The centre establishes the frame: sensor origin, current object, pivot, cycle
state, or menu hub. Give it one dominant meaning. If the centre alternates
between summary, button, label, and decoration without an explicit mode change,
the surrounding rings lose their reference.

### Angle

Angle may encode a categorical direction, a measured bearing, hierarchy share,
or cyclic time. Do not mix those meanings on one rail. When two angular systems
must coexist, distinguish them with separate scales and explicit labels rather
than relying on color alone.

### Radius

Radius may encode range, depth, lane, magnitude, or interaction distance. Area
grows quadratically, so a radial extent is not automatically a perceptually
honest magnitude. For exact comparison, show the number and provide a linear
view; for area-proportional partitions, compute area rather than only radius.

### Rings and sectors

Give each ring one job. Sibling rings may share a scale, but a ring should not be
simultaneously an axis, progress indicator, menu, and alarm. A sector that can be
clicked has an action, state, accessible name, and stable target. A sector that
only depicts a zone is pointer-inert.

## Typography and callouts

- Keep decision text screen-upright by default. Arc-follow labels are suitable
  for short group names, scale captions, or an explicit tested probe—not for
  exact values or sentences.
- Give every important number its label and unit: `Bearing 042°`, `Range 63 km`,
  `Cycle 18%`. A bare `042` is set dressing.
- Preserve one physical type floor across responsive states. If SVG scaling
  would make embedded labels smaller than 16 px, hide those labels and expose a
  16 px or larger HTML summary rather than pretending they remain readable.
- Anchor callouts to real data marks and keep their leader lines pointer-inert.
  The callout may leave the circle; its target geometry may not move to make room.
- Keep complete source copy in the semantic tree even when a shorter visible
  label protects the ring.

Load [`radial-menus.md`](radial-menus.md) when commands must share a wedge with
labels, glyphs, status, or exact values. Its rail order and Pretext compositor
are stricter than a general instrument needs.

## Motion has an owner

FUI motion should explain state, not certify futurism.

- A sweep belongs to sampling phase or search progress.
- A rotating bearing rail belongs to orientation or a selected frame.
- A pulse belongs to a new sample, alarm, or confidence change.
- A trail belongs to history and must declare its time window.
- A reveal belongs to mode entry or evidence arrival.

Do not rotate several rings at unrelated speeds unless each has an independent,
readable variable. Keep targets stable while feedback moves. Pause, reduced
motion, background-tab throttling, and deterministic capture must preserve the
current values and selection.

## Input and accessibility

- Pointer hover may preview a mark; click or tap pins it. Pointer exit restores
  the pinned selection rather than clearing the user's context.
- Give one predictable keyboard entry to the instrument. Map keys to declared
  semantics: Left/Right may step by bearing, Home/End by range extrema, and
  Enter may pin. Do not copy radial-menu depth navigation into a sensor display
  unless Up/Down genuinely means hierarchy or radius.
- Provide a linear list or table over the same canonical records. It is both an
  accessible representation and the responsive fallback—not a second dataset.
- Make touch targets at least 44 × 44 physical px. When the scaled circle cannot
  hold them, make the linear surface primary and the circle illustrative.
- Announce selected identity, state, labeled values, and consequence. Do not
  narrate decorative ticks or every animation frame.

## Case 1 — radial command selector

Angle is a discrete command. Radius is normally dead-zone plus acquisition
distance, but may explicitly become submenu depth or a continuous argument.
The important measurements are acquisition time, wrong-wedge entries, label
fit, target stability, and one activation per input. The complete contract and
runnable comparison live in [`radial-menus.md`](radial-menus.md) and
[`radial-menu-pretext.html`](../examples/radial-menu-pretext.html).

## Case 2 — FUI sensor-fusion instrument

Angle is bearing, radius is range, the centre is the simulated sensor origin,
and each contact is one canonical record. Range gates are context. The scan
sweep is sampling feedback. Confidence changes the contact glyph's interior
mark, not its coordinates or target. The selected contact is mirrored into a
linear inspector and contact list.

[`annular-fui-console.html`](../examples/annular-fui-console.html) is the runnable
second case. It uses deterministic simulated telemetry, declares both polar
axes on the surface, supports pointer preview and pinning plus keyboard bearing
steps, freezes under reduced motion, and exposes a local audit object for path
stability, target size, semantics, and responsive fallback checks.

This case borrows the FUI register without becoming a radial menu. The user does
not choose a wedge; they inspect a spatial measurement.

## Renderer choice

- **SVG** for polar axes, annular sectors, contact marks, and stable hit paths.
  It keeps geometry inspectable and scales cleanly.
- **HTML** for inspectors, controls, exact values, and the linear equivalent.
  It preserves ordinary focus, responsive layout, and readable type.
- **Canvas2D** for dense trails, sweeps, or waveforms that redraw every frame.
  Keep semantic targets in DOM/SVG rather than rebuilding accessibility in a
  bitmap.
- **WebGL/Three.js** only when depth, particles, or projection is part of the
  information contract. A circle does not by itself earn a GPU.

## Verification matrix

| Dimension | Minimum proof |
|---|---|
| Semantics | angle, radius, centre, ring roles, units, and update owners declared |
| Geometry | one polar transform; data and target positions stable across state |
| Data truth | real source named, or deterministic synthetic data labeled as simulated |
| Density | sparse, expected, and worst-case records; overlap and occlusion checked |
| Type | every readable line at least 16 physical px; exact values labeled |
| Targets | every action at least 40 × 40 px; prefer 44 × 44 for touch |
| Input | pointer preview/pin, keyboard semantic steps, touch path, recovery |
| State | default, preview, pinned, warning, unavailable, paused, reduced motion |
| Responsive | desktop instrument plus linear phone fallback over the same records |
| Motion | each moving layer has an owner; pause and deterministic capture work |
| Contrast | text at least 8:1; decorative dark-screen strokes at least 55/255 |
| Behavior | no duplicate commits, no state inferred from animation or proximity |

## Stop conditions

Fall back to a linear or Cartesian surface when:

- the angle or centre cannot be named without inventing a metaphor;
- users need precise comparison across many radial lengths or areas;
- label fit depends on sub-16 px text or routine mental rotation;
- interactive marks cannot keep 44 px targets without overlapping neighbors;
- several rings change independently but their update ownership cannot be
  explained;
- the linear equivalent is consistently clearer and the circle adds no spatial
  task advantage.

Do not add rings, scan lines, random counters, or orbiting particles to rescue an
unresolved information model.

## Lineage

- Don Hopkins's [Pie Menu Cookbook](https://donhopkins.com/home/piepaper/cookbook.html)
  defines the directional-command case and distinguishes angle from distance.
- Microsoft's [Surface Dial interaction
  guidance](https://learn.microsoft.com/en-us/windows/uwp/ui-input/windows-wheel-interactions)
  documents a real radial controller whose menu, rotation, click, context, and
  occlusion have distinct semantics.
- In a [conversation about film
  interfaces](https://www.pushing-pixels.org/2012/06/01/the-craft-of-screen-graphics-and-movie-user-interfaces-conversation-with-jayse-hansen.html),
  Jayse Hansen describes researching the real information a character would
  need; the useful lesson is that circles and random text do not substitute for
  an information model.
