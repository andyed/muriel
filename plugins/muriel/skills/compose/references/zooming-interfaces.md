# Zooming interfaces — navigation across scale

Use when a collection, document space, map, timeline, or workspace is navigated
by changing position and scale. Read the [interactive channel](../channels/interactive.md)
and use [multiscale coordination](multiscale-coordination.md) for selection,
representation levels, and linked state. A zooming user interface (ZUI) is an
interaction model; a camera transform is only one implementation detail. For a
collection of images, start with [collections](collections.md): Wunderkammer
already has the camera, detail, and faceting behavior described here, and the
agent writes a collection document for it instead of building a new wall.

## Choose what zoom enables

Name the person's next useful action at each scale. They might survey a
collection, compare a subset, read an item, follow a relationship, then return.
Make those actions reachable without requiring camera skill. A flat list,
search result, or explicit inspector can be an equally important entry point.

| Choice | Use when | Main cost to examine |
|---|---|---|
| Continuous pan/zoom | Position or scale helps organize the material | Getting lost, targeting, and the work of returning |
| Semantic zoom | Different tasks need different representations of the same entities | Correspondence, threshold stability, and focus continuity |
| Overview plus detail | Location and fine detail must be available together | Screen space and correspondence between views |
| Local lens / focus+context | A local transformation is useful without leaving the larger view | Distortion, occlusion, and conflicts with interaction under the lens |
| Direct jump / search / portal | A known destination is distant or otherwise hard to reach | Loss of route context; need for an explicit return |
| Conventional list/detail | Spatial position adds little to the task | Whether a compact overview or relationship view would add value |

These are alternatives to compare and mechanisms to compose. ZUIs need not be
infinite canvases, 3D scenes, animated camera flights, or replacements for every
conventional control. State what space means: geography, ordered time,
hierarchy, similarity, authored arrangement, or packing. Proximity in an
embedding is an inferred relationship; adjacency in a packed grid may mean
nothing beyond efficient layout.

## Camera truth and input ownership

Keep the camera separate from scope, selected identities, preview, and pin.
Define the camera's coordinate system, extent, scale limits, and anchor policy.
For an affine camera, the anchor equation is in the coordination reference;
test off-center anchors and interrupted motion, not only centered button zoom.

- **Useful bounds.** Fit reveals the meaningful extent. On an axis whose content
  already fits, decide whether panning serves a task; do not allow an accidental
  blank destination by default. Padding may be deliberate space for editing.
- **True no-op at a limit.** If the clamped target scale equals the current
  scale, avoid re-anchoring, rewriting history, restarting animation, or clearing
  a fitted-state flag. A floating-point discrepancy should not cause drift.
- **Follow visible geometry.** If an animated camera is interrupted, use the
  currently displayed transform as the next gesture's origin, not its abandoned
  destination. The content must stay under the user's control.
- **Own one gesture at a time.** Pan, brush, item drag, lasso, pinch, and browser
  scrolling need an explicit arbitration policy. A second touch must not
  accidentally commit a one-pointer brush. Support cancellation and release
  outside the plot.
- **Equivalent actions.** Provide zoom controls, Fit, navigable records and
  direct inspection. Retain page/browser magnification and ordinary scrolling
  where the canvas does not own the gesture.

An edge gesture that changes from pan to zoom can be a useful experiment when
reversal and feedback make the new meaning clear. It is not a universal gesture
rule. Compare it with bounded pan; test diagonals, tiny collections, rapid
reversal, and the scale ceiling before adopting it.

## Preserve a place, not just a transform

Keep three forms of recovery distinct:

- **Fit / Home:** show the current scope's meaningful extent in the current
  viewport. It is a navigation intent, not necessarily a saved pixel transform.
- **Back:** restore the preceding meaningful context: scope, layout/order,
  focused identity, and camera as applicable. It must not silently broaden the
  selection or query just to make the view fuller.
- **Undo:** reverse a committed editing or selection action under the product's
  existing history model. Do not add hover frames or every animation frame.

Provide a persistent landmark, overview, named path, scale indicator, or reliable
return action appropriate to the information space. A world can contain records
yet show no useful cues at the current location and scale; navigation must still
offer a way out. Empty space may be meaningful, so judge the task rather than
maximizing pixel occupancy.

When a layout reflows, preserve identity and distinguish intentional movement
from camera motion. A fitted overview can refit after resize; a deliberately
positioned camera may preserve a relative anchor and scale. Avoid restoring a
raw transform from a large display onto a phone and claiming equivalent context.
If a saved view references changed data, disclose the mismatch.

## Reveal detail without changing commitment

Zoom can change the representation in place or trigger an inspector. These are
different mechanisms. A low-resolution image replaced by sharper pixels is
rendering level of detail. A thumbnail becoming a readable object with metadata
and actions is semantic change. A pane opening for a nearby item is scale-driven
details on demand; it need not select that item.

For automatic detail, define a pure decision from projected geometry:

1. Which candidates are actually visible, and what space remains unobscured?
2. Which footprint is sufficient to enter detail, and which lower threshold
   leaves it? Measure against the same geometry whether the pane is open or shut.
3. What keeps the current item stable when two candidates nearly tie?
4. Does the rule run continuously, at gesture completion, or after settling?
5. How does dismissal persist until the person changes context?
6. What happens to an explicit pin, keyboard focus, and the narrow-screen reader?

Automatic detail must not create a feedback loop in which opening a pane changes
the qualifying geometry, closes the pane, then qualifies again. It should not
move the camera unexpectedly or overwrite an explicitly chosen reference.
Keep a click or explicit action as a clear route from preview to commitment.

## Wunderkammer as an inspected implementation precedent

Source inspected at Clipwall commit `6ac1e70`, 16 October 2026. Clipwall was
the private predecessor of [Wunderkammer](https://github.com/andyed/wunderkammer/tree/v0.2.0),
and the files named here are public at its v0.2.0 tag. This is source and
contract evidence, not a new runtime or user study. Read
[`docs/PHILOSOPHY.md`](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/PHILOSOPHY.md),
[`docs/ARCHITECTURE.md`](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/ARCHITECTURE.md),
[`docs/ZOOM_DETAIL.md`](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/ZOOM_DETAIL.md),
[`wall/zoom-detail.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/zoom-detail.mjs), and
[`wall/viewport.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/viewport.mjs).

- **Survey / Review / Dive** use one corpus and scope evaluator. Layout and sort
  change presentation, while search and facets change membership.
- **Scale-driven detail** follows the preview path. The flat-wall rule uses
  projected size, separate open/close thresholds, and a sticky current item.
  The detail pane overlays a fixed stage; it does not move the camera.
- **Unobscured area** matters: selection of the preview candidate considers the
  space left by the detail rail, using its width whether currently open or not.
- **Spatial promotion** makes near items readable DOM cards. It does not also
  trigger the flat view's detail pane, which would duplicate information.
- **Persistent identity** survives texture tiers, DOM pooling, and filtered
  membership. Renderer residency is not the corpus or a saved selection.
- **Bounded navigation** avoids unproductive movement; a clamped zoom is a
  no-op. Fit and return context are product actions with explicit semantics.

Borrow these mechanisms selectively. Wunderkammer's threshold ratios, settle delay,
phone breakpoint, URL identity, and ownership of research notes belong to that
product. Its peer-study measurements are tied to its recorded corpora, commits,
hardware and tests; they are not general performance rankings or proof that a
3D presentation is better. The fuller source audit is in the muriel repository's
`research/clipwall-multiscale-case-study.md`.

## Faceting is adjacent, with its own contract

A facet declares a query over attributes; a brush is one way to author a query
or selection; a layout groups or positions its results; zoom navigates that
representation. A persistent selection can survive all of these. Distinguish
an attribute preview from committing a facet, and filter counts from counts of
selected records. OR within a facet and AND across facets is one common policy,
not an implicit universal rule. Multi-valued records and missing values require
explicit counting semantics.

Use [faceted exploration](faceted-exploration.md) when the task needs contextual
counts, searchable values, active-value retention, query history, and zero-result
recovery. It is based on the faceting implementation in Wunderkammer 0.2.0
and includes an independent acceptance fixture. Hierarchical facets, numeric ranges, server-side
queries, and missing-value policy require explicit host decisions. The Linked
Atlas habitat control remains a single categorical filter; use the dedicated
reference for the broader mechanism.

## Historical anchors and verification

Pad++ establishes a zooming-interface design and implementation precedent;
Space-Scale Diagrams make position and magnification explicit for analysis.
The overview/detail review distinguishes competing context mechanisms rather
than declaring a winner. [Pad++](https://doi.org/10.1145/192426.192435),
[Space-Scale Diagrams](https://doi.org/10.1145/223904.223934),
[overview/detail review](https://doi.org/10.1145/1456650.1456652).

Small's Virtual Shakespeare presents changing text representations and physical
navigation prototypes together; it also describes ambiguity in judging scale.
Use that as a design precedent, not a universal comprehension result.
[Small's paper](https://smg.media.mit.edu/library/small1996.html).

The repository's `research/multiscale-history.md` traces further relationships:
dynamic graphics, brushing, degree of interest, lenses, dynamic queries,
DataSplash, data-cube abstractions, semantic substrates, and declarative
selections. The [evaluation battery](multiscale-evaluation.md) supplies a ZUI
brief with observable return, identity, camera, and focus requirements. The
chart lab proves its narrower camera and selection contract; use a collection
fixture before claiming the full ZUI workflow passes.
