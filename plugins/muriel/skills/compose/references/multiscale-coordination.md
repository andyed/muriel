# Semantic zoom, linked displays, and brushing

Use this reference when the task needs people to move between scales, select a
subset in one representation, and inspect its meaning in another. Read the
[interactive channel](../channels/interactive.md) first. Use
[multiscale adapters](multiscale-adapters.md) for the host's rendering library
and [zooming interfaces](zooming-interfaces.md) for continuous canvases, spatial
collections, camera behavior, and navigation recovery.

Muriel's job is to design the representations **and their coordination**. Begin
with a real question: “Which observations make this cluster unusual, and does
that relationship persist over time?” A page of independently interactive
charts does not answer it until the relationships between their states are
defined, visible, and exercised.

The research lineage is documented in the repository's
`research/semantic-zoom-linked-views.md` and `research/multiscale-history.md`,
with a verified bibliography. The
contracts below are engineering and design
recommendations derived from that lineage. Their exact thresholds, gestures,
and layouts require calibration in the host; they are not experimentally
established constants. Open the [linked atlas](../examples/linked-atlas/index.html)
for the runnable teaching implementation and its model and interaction tests;
use [multiscale evaluation](multiscale-evaluation.md) to exercise the capability.

The core lineage is [Pad++](https://doi.org/10.1145/192426.192435) and
[space-scale diagrams](https://doi.org/10.1145/223904.223934) for representation
at scale; [brushing scatterplots](https://doi.org/10.1080/00401706.1987.10488204)
for coordinated selection; [Snap-Together](https://doi.org/10.1145/345513.345282)
for relational coordination; and [Vega-Lite](https://doi.org/10.1109/TVCG.2016.2599030)
for explicit selection semantics. These are design, formalism, and system
foundations. The [overview/detail review](https://doi.org/10.1145/1456650.1456652)
and [transition experiments](https://doi.org/10.1109/TVCG.2007.70539) help bound
claims: performance depends on tasks and conditions; neither motion nor an
additional view guarantees better analysis.

## 1. Choose the mechanism by the work

| Mechanism | What changes | Use when | Question to resolve |
|---|---|---|---|
| Geometric zoom | Magnification and visible extent | Spatial detail needs inspection | What remains a stable landmark? |
| Semantic zoom | Representation changes with usable scale | An overview and an item need different encodings | What becomes meaningful at each level? |
| Details on demand | Information about an indicated entity appears | Exact values or provenance are occasional needs | Does inspection require disturbing the viewport? |
| Drilldown | Dataset scope or hierarchy level changes | The task follows a parent/child relation | How are scope and the return path shown? |
| Overview + detail | Context and focus occupy separate regions | Location and detail must be compared | What navigation is linked, and in which direction? |
| Focus + context | Detail is embedded in surrounding context | A local lens helps a spatial task | Does distortion undermine metric comparisons or targeting? |
| Linked brushing | A selected subset is represented across views | Complementary attributes need comparison | What identity or relationship links the records? |
| Crossfiltering | A query changes other views' input populations | The task narrows a cohort | Does the originating view retain its full context? |

These can be combined, but each adds behavior the person must learn. A cluster
expanding into its members is semantic zoom if representation depends on
scale. Clicking it to replace the dataset is drilldown. A tooltip is details on
demand. Enlarging unchanged labels is geometric zoom. Describe the mechanism
accurately before claiming a semantic-zoom capability.

Give every view one analytic job and a reason to exist. A useful combination is
a distribution overview, an alternative projection, an exact record table, and
a pinned inspector. A second scatterplot with different axes can be valuable;
three copies of the same summary usually cannot justify their space.

## 2. Write the coordination contract before rendering

Record these decisions in the host's design note or implementation:

| Concern | Required declaration |
|---|---|
| Identity | Entity namespace, stable key, dataset version, duplicate-key policy |
| Selection universe | Whole dataset, eligible filtered records, or visible records |
| Selection meaning | Frozen IDs or a live predicate; empty and absent behavior |
| Relationship | Same entities, parent/child, membership, join, or another declared mapping |
| Viewport | Per-view domains/transform; explicit synchronization groups |
| Aggregation | Grouping fields, membership, denominator, overlap, missingness |
| Brush | Fields, units, bounds, operation, commit/cancel behavior |
| Preview and pin | Ephemeral inspection versus persistent reference |
| Filter | Which views and denominators it changes; how it is removed |
| Resolution | How simultaneous brushes combine across views |
| Recovery | Clear selection, clear filter, reset viewport, undo, restore |

One canonical state does not require a new global-store library. Join the host's
existing reducer, signals, query model, or controller. Keep renderer-local state
limited to drawing, hit testing, and an in-progress gesture. A possible shape:

```js
{
  dataVersion: 'observations-v3',
  revision: 17,
  filters: { category: null },
  selection: null, // or { kind: 'ids', ids: [] } or a typed predicate
  preview: null,   // { namespace: 'observation', id: 'o-31' }
  pin: null,
  viewports: { spatial: { x: [0, 100], y: [0, 100] } },
  brushes: {},     // authored predicates + provenance; not authoritative pixels
  interaction: { tool: 'brush', operation: 'replace' }
}
```

Selection, filter, pin, hover, and viewport are different state dimensions.
Panning does not change the selected entities unless the product explicitly
offers “select visible.” Hovering does not silently replace a pin. Clearing a
brush does not reset the viewport. Show these differences in the controls and
state readout, not only in variable names.

Expose named commands and read-only diagnostics for automated exercise. The
diagnostic snapshot should contain IDs, extents, level, counts, and revisions;
tests should also use the actual input routes. A debug API alone cannot prove
the visible controls work.

## 3. Design a representation ladder

For each level, specify the task, available evidence, mark semantics, allowed
actions, and transition criterion. Prefer a few consequential changes over
many cosmetic levels. A specimen ladder for an observation atlas:

| Level | Representation | Human question | Selection meaning |
|---|---|---|---|
| Overview | Stable spatial bins with counts and spread | Where are concentrations and exceptions? | Select members of a bin, or explicitly brush raw positions |
| Neighborhood | Individual marks plus restrained group context | Which observations form the apparent pattern? | Select stable observation IDs |
| Detail | Records with measured labels and available attributes | Which entity is this, and what supports its value? | Same IDs; inspect or pin without replacing the cohort |

The ladder need not end in cards, and every view need not change level at once.
A timeline may aggregate by time while a map groups by location. Declare each
view's semantic level and maintain the correspondence through identity.

**Measure the available screen space.** Use projected mark spacing, measured
label dimensions, plot area, overlap, and visible mark count. Raw zoom `k` is a
poor portable threshold: the same `k` produces different affordances after a
resize. For one-dimensional spacing, `pixelsPerUnit = plotWidth / domainSpan`.
For nonuniform or nonlinear layouts, measure projected bounds locally. Text
must meet Muriel's size and contrast rules; shrink the information budget
before shrinking prose below them.

**Use hysteresis.** Enter detail only when the footprint clears an upper
threshold; leave it below a lower threshold. Retain the current level in the
gap. For example, entering at 60 px and leaving at 45 px is an illustrative
policy to calibrate, not a perception result. Apply the rule to each adjacent
level and test oscillation, large jumps, and resize. If a collision budget is
exceeded, prioritize labels deterministically; do not continually reshuffle
them on every pointer movement.

**Preserve evidence across the boundary.** A coarse bin must retain its member
IDs or an exact membership predicate. An individual outlier must not vanish
from the analytic result because its label is hidden. Show the binning or
aggregation rule, count, units, missing values, and relevant uncertainty. A
mean alone can conceal a bimodal population; choose the overview statistic for
the task and provide inspection of its members.

## 4. Preserve navigation anchors and identity

For an affine world-to-screen transform `screen = k * world + t`, preserve the
world point below the zoom anchor `a`:

```text
worldAtAnchor = (a - t) / k
tNext         = a - kNext * worldAtAnchor
```

Apply independently to x and y after accounting for plot offsets. For scale
domains, use the inverse scale at the anchor and solve the new domain around
that value. Log scales require the scale's transform/inverse; geographic
projections and rotated cameras need their actual geometry. Bounds clamping
may prevent exact anchoring at an edge: make that constraint deliberate and
test the unconstrained invariant separately from the boundary policy.

At a semantic transition, maintain stable spatial landmarks, parent/member
relationships, selection, and pin identity. A transition may show a group
expanding toward members when the grouping supports that correspondence. Do
not morph unrelated entities into one another merely because their screen
positions are nearby. Make an immediate reduced-motion route equally legible.

When detail controls or labels appear, preserve keyboard focus by entity ID.
If a focused entity is no longer drawable, keep its inspector or transfer focus
to a named surviving control; do not drop it onto the document body. Back or
reset should restore a meaningful context. A persistent overview, named path,
or saved view can be more useful than an elaborate camera animation.

## 5. Treat brushing as a query with an explicit lifetime

Convert pointer coordinates through the current plot transform into data-space
bounds. Normalize drag direction, then evaluate membership against the declared
universe. Use one specified boundary rule; for contiguous bins, half-open
intervals avoid double inclusion, with an explicit final-domain endpoint rule.
Handle reversed scales, missing values, dates/time zones, log domains, and
degenerate extents. A zero-size drag may be a point pick or an empty brush; make
that gesture distinction explicit.

Store persistent extents in data coordinates. Reproject them on zoom and resize.
The screen rectangle is a view of the predicate, not the predicate itself. For
lassos and irregular projections, retain the proper geometry and coordinate
reference; an inverted bounding rectangle may not describe the drawn region.

For existing set `S` and current brush match set `B`:

| Operation | Result |
|---|---|
| Replace | `B` |
| Add | `S ∪ B` |
| Subtract | `S \ B` |
| Intersect | `S ∩ B` |

Take a snapshot `S₀` at gesture start. Each preview computes `operation(S₀, Bₜ)`.
Do not repeatedly compose against the previous preview: shrinking an additive
brush must remove points that were only inside an earlier preview. Commit once
on completion; Escape, pointer cancellation, or lost capture restores the
snapshot. Freeze the operation during the gesture unless mid-drag modifier
changes are an intentionally designed and tested feature.

**Absent is not empty.** `selection: null` means no active selection;
`{ kind: 'ids', ids: [] }` means an active selection matching nothing. Filtering
by the former leaves the eligible population; filtering by the latter returns
zero. Never use `ids.length === 0` as “show everything.” Disable Add/Subtract/
Intersect until a baseline exists, or document a precise initial-set policy.
“No brush” is not automatically the universal set for all operations.

**Choose snapshot or live semantics.** Frozen IDs keep a cohort stable if data
values change. A stored predicate reruns on new data and may select different
members. Neither is universally correct. Label the behavior, retain query
provenance, and define migration on dataset replacement. When compound
selection no longer equals the latest rectangle, show the operation history or
cohort summary; do not present that rectangle as the full selected set.

## 6. Coordinate views through meaning

Views of the same entities exchange stable keys, never array offsets, SVG
indices, screen coordinates, or display labels. Sorts, filters, and
virtualization must not change identity. Namespace IDs when distinct datasets
can contain the same key. Reject duplicate IDs or explicitly model occurrence
identity before enabling linking.

Views of related datasets need a declared relation. For customers and orders,
brushing customers might select their orders by a customer key; the reverse
mapping might select customers with **any** brushed order. These mappings are
not inverses, and counts describe different entity types. For many-to-many
relations, define deduplication and aggregation before counting. For
probabilistic matches, show uncertainty rather than asserting exact identity.
If no defensible relation exists, keep the views unlinked.

A brush in one projection is not a screen rectangle to copy into another.
Evaluate its predicate where it was authored, then project matching IDs in the
other view. If both views share a domain dimension, a meaningful range overlay
can also be drawn in each view's own scale. Shared time axes are useful for
temporal comparison; a map, scatterplot, and table can coordinate without a
shared coordinate system.

For aggregate mark `g` with eligible member set `Mᵍ` and selected set `S`, derive
`selectedCount = |Mᵍ ∩ S|`. Render none, partial, and full states distinctly, and
show the actual counts. Define whether “full” means all eligible or all original
members. A `3 of 12` label is more truthful than painting the entire bin as
selected. Overlapping groups cannot be summed as though they were a partition.
Aggregates based on samples must not imply complete membership.

Choose view query policy intentionally:

| Policy | Population shown | Useful effect |
|---|---|---|
| Highlight | Eligible records remain; selection changes emphasis | Preserves comparison with nonmembers |
| Filter | Only matching records feed the view | Makes the cohort inspectable |
| Context + subset | Both full and selected aggregate layers | Shows changed composition and denominator |
| Crossfilter except self | All relevant predicates except this view's own | Retains context for adjusting its filter |

Keep hover preview, keyboard focus, pinned inspection, and selected cohort
visually distinguishable. Use stable semantic color assignments plus outlines,
patterns, shape, labels, or selected-count marks. A pin outside the current
filter should say so; it should not disappear silently. A selected cohort
outside the viewport still exists and needs a visible count or return action.

## 7. Make input ownership, access, and recovery explicit

Dragging cannot simultaneously mean pan and brush. Provide a visible tool
switch or another unambiguous grammar, plus buttons for operations that would
otherwise depend on modifiers. Use pointer capture for drags; handle cancellation
and release outside the plot. Decide how a second touch changes or cancels a
gesture. Preserve ordinary page scrolling and browser zoom outside the intended
interaction surface.

Provide usable alternatives, not a sentence saying “keyboard supported”:

- Numeric/date bounds and category controls create the same predicates as a brush.
- Zoom buttons, a reset control, and navigable records support inspection without a wheel.
- A selectable table or structured list exposes the same eligible/selected IDs.
- Preview content is available by focus or explicit inspection, not hover alone.
- A visible operation control supports touch and single-pointer use without modifiers.
- Escape cancels a gesture; clear selection and reset viewport remain separate.

Keyboard equivalence and a single-pointer alternative to dragging are distinct
requirements. W3C's [dragging guidance](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
and [color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)
inform this implementation. Muriel's 8:1 text-contrast policy remains in force.
Small data marks need an accessible inspection path; expanding thousands of
overlapping hit targets does not create an intelligible interface.

Announce committed selection counts and level changes using a restrained status
region. Avoid narrating every pointer move. Use a manageable focus model rather
than thousands of tab stops. Test keyboard and touch completion of the actual
analytic question, browser magnification, reduced motion, and a narrow layout.
On narrow screens, a persistent cohort summary and explicit view switch can
preserve coordination when simultaneous display is impractical.

## 8. Keep rendering responsive without weakening semantics

Compute from a canonical snapshot, render the affected views, then expose a
consistent revision. Prevent programmatic view updates from re-emitting user
actions into a coordination loop. Use origin tags or adapter suppression with
cleanup, and guard no-op updates. A transaction should publish once even if
several dependent views update.

Coalesce input rendering to animation frames. Separate cheap brush/hover
feedback from expensive data queries. Culling, level of detail, and label
suppression reduce drawing cost; they must not silently reduce the population
being queried. Use a spatial index or worker when measured data size requires
one. A sampled visual overview needs explicit sampling semantics.

For asynchronous computation, send a request ID plus dataset and query/viewport
revision. Accept results only when the versions they depend on still match.
Abort superseded work when possible, but use version checking even with aborts.
Track dependencies precisely so an unrelated hover does not invalidate a long
query. A stale result may remain visibly marked while new work runs; never
present mixed revisions as a coherent current analysis.

Measure input-to-feedback, query completion, and settled render separately on
representative devices and datasets. Report distributions and the tested size.
“60 fps” does not establish correct brushing, exact counts, or usable analysis.

## 9. Verify invariants, then evaluate the human task

Use deterministic fixtures that include duplicate coordinates, zero matches,
missing values, boundary values, outliers, and partial aggregates. Derive
expected IDs independently of the renderer. Required checks for implemented
capabilities include:

| Invariant or behavior | Exercise |
|---|---|
| Anchored navigation | Compare the world point under an off-center anchor before/after zoom; test edge clamping separately |
| Representation continuity | Cross every level in both directions; pin and selection retain identity |
| Hysteresis | Oscillate around thresholds and resize through them without level chatter |
| Coordinate correctness | Brush after zoom, pan, resize, reversed-axis and transformed-scale changes |
| Selection algebra | Replace, union, subtract, intersect; shrink a gesture preview; cancel and undo |
| Empty semantics | Active zero matches filters to zero; clearing the brush restores absence |
| Aggregate truth | Partial/full/none membership and denominators remain correct at every level |
| Query scope | Offscreen selected IDs and filter-hidden pins remain accounted for |
| Coordination | All views agree on eligible and selected IDs for the same revision |
| Relationship mapping | One-to-many and many-to-many joins count the declared entity type without duplication |
| Event ownership | One drag creates one action; programmatic redraw cannot recurse |
| Async freshness | Delayed older results cannot overwrite a newer query or dataset |
| Recovery | Pointer cancellation, Escape, clear, reset, and restoration have their specified effects |
| Access | Equivalent bounds/selection via keyboard and non-drag pointer controls; visible focus and noncolor state |

The example's tests demonstrate its supported subset of this contract. They do
not establish capability for an unimplemented lasso, projection, streaming
dataset, or join. A rendered screenshot proves visible state at a moment; an
interaction test proves the exercised path; neither proves understanding.

For human evaluation, compare plausible alternatives on representative tasks:
find a cross-view outlier, explain a cluster's members, form and refine a
cohort, recover from a mistaken operation, and return to an earlier finding.
Compare task success, explanation errors, cohort errors, completion time,
recovery, and learning across repeated use. Observe whether people notice level
changes and understand partial aggregates. Test with the users and access needs
the product serves. Treat reduced workload, improved comprehension, and faster
analysis as hypotheses until those outcomes have relevant human evidence.
