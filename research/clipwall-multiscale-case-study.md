# Clipwall (now Wunderkammer): a precedent for zooming interfaces

Baseline inspection and bounded working-tree extension · 16 October 2026

The original inspection examined Clipwall, clean at private commit
`6ac1e70ecf035c1909412893429a7940517e18a4`, without changing that checkout or
establishing runtime acceptance. Subsequent showcase work implemented the
faceting extension described below in Clipwall's working tree. Those changes
are not part of the baseline commit. Clipwall has since been released as
[Wunderkammer](https://github.com/andyed/wunderkammer/tree/v0.2.0), and the
links below point to the files at its public v0.2.0 tag, which includes the
faceting extension. This record separates source
contracts, implementation evidence, and human outcomes that were not measured.

## Product structure

[README](https://github.com/andyed/wunderkammer/blob/v0.2.0/README.md), [architecture](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/ARCHITECTURE.md),
and [philosophy](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/PHILOSOPHY.md) agree on Survey / Review / Dive
over one corpus. Search and facets define their common scope. Flat review is a
first-class access path, and spatial presentation has to earn its cost by making
material reachable or relationships inspectable.

The scope evaluator in [`wall/context-clusters.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/context-clusters.mjs) supplies `state.filtered`
through `applyFilters()` in [`wall/wall.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/wall.mjs), using query, active facets, and
optional union branches. Facets use OR within a key and AND
across keys; presentation and sort do not redefine membership. Multiple display
occurrences of one multi-valued item remain one entity. These distinctions are
valuable to Muriel even when the host has different data or state machinery.

## Mechanisms worth carrying into Muriel

| Mechanism and inspected source | Design consequence | Transfer boundary |
|---|---|---|
| [Zoom detail decision](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/zoom-detail.mjs), [contract](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/ZOOM_DETAIL.md) | Projected footprint, hysteresis, and a sticky item make automatic inspection stable | Open above 0.5 / close at 0.4 of the free extent is Clipwall tuning, not a universal perceptual threshold |
| Same decision accounts for the rail even when closed | A new pane cannot change its own qualifying geometry and oscillate | Pane geometry depends on the host's overlay/reflow model |
| Zoom detail uses preview; explicit activation commits | Camera exploration can expose information without replacing a deliberate pin | Source contract, not a usability finding; narrow screens use another reader model |
| [Viewport](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/viewport.mjs) returns early when the clamped next scale is unchanged | A zoom limit is a real no-op, avoiding camera creep, fitted-state loss and needless work | Numerical tolerance belongs to the camera implementation |
| Current scope and viewport are separate in the architecture | Culling and rendering residency cannot silently change the selected universe | Dataset and durable identity rules vary by adapter |
| Spatial cards promote from pixels into live DOM | Semantic enrichment can coexist with a bounded DOM budget | Requires shared geometry, activation and focus identity; texture refinement alone is not semantic zoom |
| Fit versus custom camera restoration | Reflow can preserve a navigation intent rather than stale screen pixels | Test restoration on the receiving viewport and with changed data |
| Attribute previews preserve layout and membership | People can ask where an attribute occurs without rearranging the evidence | Preview, facet, sort and persistent lens need distinguishable controls |

The flat-wall zoom-detail contract evaluates after zoom settling, suppresses
reopening after explicit dismissal until context changes, and is disabled in
the spatial view and the narrow modal-reader layout. These policies prevent
duplicate detail and accidental commitment. They should inform Muriel's questions
before becoming defaults elsewhere.

## Bounded faceting extension in the working tree

The baseline's facet rail displayed the most frequent 24 values and redirected
the tail to global search, which did not search arbitrary properties. Its visible
counts were corpus totals. The new extension joins the canonical scope evaluator
and the existing attribute-preview path; it does not introduce a second query
model. The full contract and evidence are in
[Wunderkammer's faceting note](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/FACETING.md).

| Working-tree addition | Meaning and source |
|---|---|
| Local value search and progressive expansion | Search the complete facet vocabulary, show another 24 values, and retain active values even outside local search; [`wall/facet-model.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/facet-model.mjs) and [`wall/facet-rail.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/facet-rail.mjs) |
| In view / available counts | Current scope members versus members matching text, other facets, and frozen branches while omitting this facet's own restriction; [`wall/facet-model.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/facet-model.mjs) |
| Per-facet clear and removable active restrictions | Remove one value or facet without clearing unrelated text or frozen branches; rail and scope controls in [`wall/wall.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/wall.mjs) |
| Zero-result recovery | Preserve the actual restrictions and offer deliberate recovery instead of silently widening membership |
| Shared prefix preview | Attribute preview and scope use the same captured-date prefix semantics; [`wall/attribute-brush.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/attribute-brush.mjs) and [`wall/context-clusters.mjs`](https://github.com/andyed/wunderkammer/blob/v0.2.0/wall/context-clusters.mjs) |

Available is neither the final total after an OR-add nor its incremental gain.
Multi-valued records can contribute to overlapping categories, and “In view”
includes offscreen members of the working subset. Chip fill now uses
current/available, matching the visible denominator. Counts depend on canonical
entity identity; duplicate input records must be reconciled at the owning layer.

At this integration checkpoint, focused browser checks passed **15/15 in
25.77 s**. They exercised contextual counts, rare-value search, retained keyboard
focus through URL saving and camera changes, captured-prefix preview, phone
targets of at least 44 px, zero-result recovery, and an initially empty 3D scope
with a valid permalink and fresh restoration. A separate model, scope, attribute,
and permalink pass succeeded **36/36**; **2/2** deliberate facet mutations were
detected. These are distinct passes with overlap, not additive totals.

The public 297-image showcase passed five rendered desktop, spatial and phone
states with no script errors or failed assets. Measured facet/scope text contrast
was at least 8.528:1; the audit does not cover every text element in the app.
Its source data and all 297 image files remain byte-identical to the existing
public demo. The local static host also passed inline-link restoration and the
one-probe fallback for an absent snapshot service. See
[Wunderkammer's verification receipt](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/FACETING.md#implementation-verification)
for the combined-suite result and detailed limits. These checks establish the
exercised implementation paths, not a controlled evaluation of comprehension,
discovery speed, or workload.
Hierarchy, numeric ranges, server-side queries, and a new missing-value
classification remain outside this bounded extension.

## What the peer study contributes

[PEER_STUDY.md](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/PEER_STUDY.md) records a pinned-source study of
collection explorers, including VIKUS, PixPlot, Collection Space Navigator,
Embedding Atlas, Piling.js, and seajax/PivotViewer. It separates measured cases,
source evidence, and inference; [PRECEDENTS.md](https://github.com/andyed/wunderkammer/blob/v0.2.0/docs/PRECEDENTS.md)
records earlier descriptions and their later corrections. This is a useful
method as well as a set of precedents: inspect a concrete implementation, test
the same data and actions, then verify the mechanism producing a difference.

This Muriel task did not rerun that study, inspect every peer's current version,
or establish live licensing/performance claims. Its numerical rankings and
claims about missing peer features should remain attached to the original
commit, fixture and measurement conditions. No peer code was copied here.

## Consequences for this investment

The [ZUI reference](../plugins/muriel/skills/compose/references/zooming-interfaces.md)
adds camera bounds, direct jumps, Fit/Back/Undo, automatic detail, input ownership,
and identity through render tiers to the existing coordination guidance.
The [lab](../plugins/muriel/skills/compose/examples/linked-atlas/index.html)
demonstrates the narrower linked-analytics contract; it is not a replacement for
Wunderkammer's collection workflow. The [evaluation battery](../plugins/muriel/skills/compose/references/multiscale-evaluation.md)
includes transfer tasks for collections and zooming interfaces.

The [faceted-exploration reference](../plugins/muriel/skills/compose/references/faceted-exploration.md)
now carries the Clipwall contract, released in Wunderkammer, into reusable design guidance, with
host-selection criteria and an independent acceptance fixture. It keeps facet
queries distinct from camera navigation, attribute previews, and selected
cohorts. A single habitat filter in the reference lab remains a narrower example;
it does not exercise the whole faceting contract.
