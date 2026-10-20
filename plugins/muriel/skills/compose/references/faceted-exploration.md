# Faceted exploration

Use facets when people need to discover or refine a collection through named
attributes: source, author, topic, format, date, or another meaningful dimension.
Read the [interactive channel](../channels/interactive.md); combine this contract
with [multiscale coordination](multiscale-coordination.md) for linked views and
[zooming interfaces](zooming-interfaces.md) for spatial collections. Faceting
changes the working subset; zoom changes the view of that subset. For a
collection of images, start with [collections](collections.md); Wunderkammer's
facet rail already implements this contract.

## 1. Choose a suitable host and task

Begin with an exploration question, such as “Find material from either of these
topics, restrict it to one source, then compare the available alternatives.”
Facets help when attributes provide recognizable entry points and the person
may not know the exact query in advance. A useful facet exposes choices and
their consequences, rather than merely putting a filter field on screen.

| Host condition | Design consequence |
|---|---|
| Reliable named categorical attributes | Offer value controls with explicit combination rules |
| Many rare values | Provide local value search and incremental expansion |
| Multi-valued attributes | Count unique entities and explain overlapping groups |
| Meaningful hierarchy | Specify ancestor/descendant semantics before adopting a hierarchical widget |
| Continuous quantity | Consider a range control or brush instead of thousands of categorical chips |
| Sparse or inferred metadata | Expose missingness/provenance; do not treat labels as complete ground truth |
| Existing server-side query system | Obtain results and count contexts from that system, with consistent versions |
| Small loaded collection | A local model can implement the same semantics without a search service |

Avoid adding every available field. Choose dimensions that help the task and
have understandable value vocabularies. Exact identifiers usually belong in
lookup. Similarity, text search, and facets can coexist, but must disclose their
different matching rules. Measure actual query and render costs before moving
work to an index or worker; no universal collection-size cutoff is implied.

## 2. Declare the scope algebra

The common contract here is **OR within a facet, AND across facets**, combined
with global text by AND. Multiple tags on an item are membership facts; selecting
two tags asks for either tag under this contract. A task requiring both needs
an explicit different operator, not a silent reinterpretation.

Keep one authoritative evaluator. Results, facet counts, linked displays,
accessible summaries, history, and exports must use its interpretation of
strings, dates, ranges, hierarchy, missing values, and permissions. A local
renderer must not implement a second approximation of the query.

Let `U` be eligible canonical entity IDs after fixed access/data boundaries;
`B` a deliberate base subset; `T` the global text matches; and `P_f` the matches
for the selected values of facet `f`. With no selection, `P_f = U`.

```text
Working subset R = B ∩ T ∩ all P_f
Facet context E_f = B ∩ T ∩ all P_g where g ≠ f
Value membership V_f,v = entities matching value v in facet f

Current(f,v)   = |R ∩ V_f,v|
Available(f,v) = |E_f ∩ V_f,v|
```

“Available” omits **only the current facet's own restriction**. It retains
global text, all other facets, and the deliberate base subset. This disjunctive
count exposes alternatives while one value is selected. Do not confuse it with
the final result count after a click, the number newly added, or a corpus total.
With overlapping values, those numbers can differ substantially.

Name the counts visibly. Wunderkammer uses **In view / available**; “In view” means
the current working subset, including offscreen items. A host may prefer
“Current / available” to avoid camera ambiguity. Give the accessible name the
facet, value, both counts, and any additional corpus context. If a fill encodes
current/available, its numeric denominator must match; handle `0 / 0` explicitly.
Selection has its own pressed/checked state and a visible noncolor cue.

An absent base subset and an explicit empty subset are different states. For
frozen unions, `null` can mean the whole eligible corpus while `[]` means no
members. Removing a facet must not widen an empty or restricted base. Likewise,
cross-dataset relationships need declared joins; equal display labels do not
establish entity identity.

## 3. Make identity, overlap, and missingness accountable

Use stable IDs independent of sorting, rendering, grouping, or array position.
Require one canonical record per entity, or reconcile duplicate IDs before
counting. If distinct occurrences are the intended unit, name that unit and
use occurrence IDs consistently. Counts of entities and occurrences are not
interchangeable.

Deduplicate repeated values within a record. An entity appearing in multiple
groups or overlapping frozen branches counts once per value. Counts across
different values need not sum to the working-set size: one entity can belong
to several. Preserve exact membership for aggregate inspection.

Absent, empty, unknown, and an explicit label such as “Unclassified” may mean
different things. Declare whether missing values get a selectable bucket. Do
not silently synthesize one or count a missing field as matching every selected
value. Clearing a facet normally restores records with that field missing.
If a single observed value exists, the facet can still distinguish records
with that value from records without it; “one value” alone does not prove the
control is useless.

Dates and hierarchical labels require shared matching semantics. For example,
a year prefix may match several monthly values; count the entity once even if
several values match. Declare time zones and range boundaries when applicable.
Catalog frequencies can rank controls, but current counts require current data
and query evidence. Mark approximations or stale revisions explicitly.

## 4. Search value labels without changing the global query

Local value search navigates a facet's vocabulary. It changes which controls
are offered, not scope, camera, layout, or the saved query. A global query
searches the host's declared content fields. A property can supply facet values
without appearing in those fields, so redirecting local search to global search
can make a legitimate value unreachable.

Use a bounded initial list plus incremental expansion. Search the complete
facet catalog, not only the rendered page. Keep deterministic ordering while
counts update; continually reranking under the pointer can change the intended
target. Dates may deserve chronological order. Preserve the focused search
input and its selection while updating options.

Always retain a route to selected values, including those outside the current
local search, below the display limit, absent from the refreshed catalog, or
currently matching nothing. An active-filter summary with independent removal
controls can provide that route. Distinguish “no matching value labels” from
“no records match the active scope.” Clearing local text fixes only the former.

## 5. Separate preview, commitment, and recovery

Hover or keyboard focus can preview where a value's members occur. Declare
whether preview highlights current results or contextual candidates. Preview
must not mutate scope, reorder evidence, move the camera, or write history.
Click/activation commits an explicit query change. A persistent lens or pinned
inspection is separate state. Provide touch and keyboard paths to inspection.

Make removal granular: remove one value, clear one facet, clear global text,
and reset the whole scope are different commands. Clearing facets preserves
unrelated text and base-subset constraints. Show active restrictions even when
the rail is collapsed or a zero-result state replaces the wall.

Keep zero-result states truthful and recoverable. Retain controls for removing
the responsible restriction, Back, and an explicit broader reset. Never silently
drop a constraint to populate the screen. Active zero-count values remain
removable. Decide explicitly whether unselected zero-count options are disabled
or selectable, and communicate their status without color alone.

Record deliberate scope changes through the host's history path. Restoring a
query must restore the same operator and base boundary; a frozen set must not
turn into a live predicate. Local option-search text can remain transient unless
the product deliberately makes it part of restoration. Preserve logical focus
after removing a control and announce committed results without narrating every
pointer movement. Native focused controls own Enter, Space, and text-editing
keys; document shortcuts must not intercept their actions. URL saving and
camera-history updates must preserve unchanged controls and their focus.
Follow Muriel's text size and 8:1 contrast requirements.

## 6. Use an independent acceptance fixture

Start with this synthetic table, not values copied from the implementation:

| ID | Source | Topic values | Search text |
|---|---|---|---|
| A | Print | Archive, Review, Archive | study |
| B | Print | Archive | study |
| C | Print | Review | study |
| D | Web | Review | study |
| E | Print | missing | study |
| F | Print | Review | other |

With text `study`, Source `Print`, and Topic `Archive`, expect IDs **A,B**.
Topic Archive is `2 / 2`; Review is `1 / 2`. Adding Review yields **A,B,C**,
not four records. Clearing Topic yields **A,B,C,E**. With Topic Review instead,
Source Web is `0 / 1`; adding Web yields **A,C,D**. The repeated Archive on A
must not inflate a count. A frozen base of A,B excludes C after any facet clear;
an explicit empty base remains empty.

In a separate fixture, add more values than one display page, including a rare
property-only value absent from global search fields. Reach it by local search
and by expansion. Retain an active value excluded by local option text. Test a
restored value missing from the catalog, date-prefix overlap, duplicate-ID
rejection/reconciliation, and a no-match query with granular recovery.

Browser checks must use real controls and verify keyboard focus, narrow-screen
access, preview without mutation, count labels, history, and restoration. Change
presentation and camera position without changing IDs or counts. Delay an old
server response and ensure its counts cannot replace a newer revision. These
checks establish exercised behavior; human understanding requires observing
whether people can explain the counts, form intended subsets, and recover.

## Sources and implementation status

Ka-Ping Yee, Kirsten Swearingen, Kevin Li, and Marti Hearst's **Faceted Metadata
for Image Search and Browsing** (CHI 2003, pp. 401–408) describes Flamenco's
category navigation and query previews. Its study analyzed 32 participants
using 35,000 art images and found strong preference for the faceted interface;
it did not show faster task times. Its hierarchical interface and study setting
do not validate every flat multi-select design. Metadata and claims were checked
against CrossRef and the [primary paper](https://courses.ischool.berkeley.edu/i247/f05/readings/Yee_Flamenco_CHI03.pdf),
[DOI](https://doi.org/10.1145/642611.642681), on 16 October 2026.

Official [Elastic filter documentation](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/filter-search-results)
illustrates omitting a facet's own restriction for its alternatives;
[Algolia faceting](https://www.algolia.com/doc/guides/managing-results/refine-results/faceting)
and [refinement lists](https://www.algolia.com/doc/api-reference/widgets/refinement-list/js)
document value search and disappearing selected values. These are implementation
precedents, not human-effectiveness evidence or dependency recommendations.

**Implemented host reference:** Wunderkammer's
[`wall/facet-model.mjs`](https://github.com/andyed/wunderkammer/blob/v0.3.0/wall/facet-model.mjs),
[`wall/facet-rail.mjs`](https://github.com/andyed/wunderkammer/blob/v0.3.0/wall/facet-rail.mjs), and
[`docs/FACETING.md`](https://github.com/andyed/wunderkammer/blob/v0.3.0/docs/FACETING.md) implement and describe the contextual
counts, reachable values, and recovery contract. The source was inspected on
16 October 2026, before Clipwall was released as Wunderkammer. At the
integration checkpoint, focused browser checks passed 15/15
in 25.77 s; a separate model/scope/attribute/permalink pass succeeded 36/36, and
two deliberate facet mutations were both detected. These passes overlap and
must not be summed. The public 297-image showcase passed desktop, spatial and
phone smoke checks, with no script errors or failed assets and a minimum
measured facet/scope text contrast of 8.528:1. Wunderkammer's
[`docs/FACETING.md`](https://github.com/andyed/wunderkammer/blob/v0.3.0/docs/FACETING.md#implementation-verification)
records the combined-suite receipt and measurement boundaries. No controlled
evaluation of the faceting benefit is established. Treat this contract and
fixture as reusable guidance; copying the host component does not complete another product's integration.
