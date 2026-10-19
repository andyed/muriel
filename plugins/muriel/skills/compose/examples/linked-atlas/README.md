# Field atlas: a linked, multiscale interaction lab

A working reference for semantic zoom, coordinated views and brushing. The
analytic task is to locate high detection counts, compare their habitat
composition, and inspect the observations behind the pattern. All 192 records
are deterministic **synthetic data** across a fictional 32-day survey. This is
an interaction example; it supplies no ecological evidence.

Serve this directory over HTTP; ES modules cannot reliably load from `file://`:

```sh
cd plugins/muriel/skills/compose/examples/linked-atlas
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765`. Nothing is downloaded, bundled or sent to a server.
The server serves the local files. Use a different port if 8765 is occupied.

From the repository root, run the pure model tests:

```sh
node --test tests/multiscale-coordination.test.mjs
```

The companion `tests/multiscale-browser.mjs` exercises rendered interaction when
Playwright and Chromium are available. See that script for its runtime flags.

## A five-minute exploration

1. In **Exact selection**, keep elapsed days 12–22 and detections 60–100, then
   apply the selection. The table, habitat summaries and overview all show the
   same selected IDs.
2. Zoom in repeatedly. The detail view changes from aggregate cells to records
   to nonoverlapping record labels, while the whole-study overview keeps its
   original domain. A representation change never changes membership.
3. Filter to **Shore**. Selected records outside the filter remain selected; the
   state strip reports visible and hidden counts. **Reveal selection** removes
   the filter and fits all selected IDs.
4. Choose **Add**, **Subtract** or **Intersect** and make another selection.
   Selection is a persistent set of record IDs. The operation's result appears
   while dragging; pointer release commits it, and Escape cancels it.
5. Pin a table record. Hover a visible dot to preview another record. Leaving
   restores the pin. **Undo** restores a committed selection, viewport, filter
   or pin change. **Reset all** starts over and can itself be undone.

## Mechanisms and explicit policies

`model.mjs` is the only owner of analytic state. `app.mjs` dispatches user
intent and derives all views from that state; there are no chart-to-chart event
relays. The HTML controls and pointer gestures call the same reducer.

| State | Meaning | Survives |
|---|---|---|
| `viewport` | A continuous elapsed-day interval for the detail camera | Selection operations |
| `selection` | `null` means inactive; an empty `Set` means an active empty result | Zoom, pan, filter, representation changes |
| `filter` | Eligible habitat, independent of selected membership | Zoom and selection changes |
| `pin` | Durable record identity for inspection | Filter and viewport changes, even when hidden |
| `preview` | Temporary record inspected by hover | Ends on pointer leave or a committed action |
| `pending` | Uncommitted gesture, including its source and data extent | Ends on commit, cancellation or semantic control change |

A brush evaluates record membership in **data coordinates**, including both
rectangle boundaries, against the current habitat filter. Replace, union,
subtraction and intersection use an empty baseline when selection is inactive.
For example, intersecting an inactive selection produces an active empty set.
Clearing selection restores `null`, not an empty set. A click/tap with less than
4 CSS pixels displacement cancels; it cannot accidentally clear a cohort.

Every persistent semantic change ends a pending gesture. While a gesture is
active, the committed selection and viewport stay unchanged. Cancellation by
Escape, pointer cancellation, lost capture, an additional pointer, window blur
or resize discards the draft. Pointer capture allows release outside the plot.
One completed gesture is one undo step; temporary previews are never history.
History retains the most recent 30 commits. Wheel events that change the camera
are discrete viewport commits in this small reference and consume individual
undo steps. Bounded zoom/pan requests that leave the camera unchanged do not
consume history or clear previews; an unfinished gesture still ends. Repeated
zoom input at the minimum or maximum scale cannot accumulate anchor drift.

The full-domain overview counts eligible observations in fixed one-day bins;
its vertical domain remains 0–6 surveys and its horizontal domain remains
0–32 elapsed days. A dashed rectangle is the detail camera, not the selection.
The detail y-domain stays 0–100 detections per ten minutes. Habitat summaries
use all eligible records across the whole study, with explicit selected/total
denominators, regardless of the detail camera. The table shows every eligible
record in the detail window and marks membership separately. No selection
silently filters a view.

## Semantic zoom and stable identities

Projected horizontal spacing is `plot width / visible record count`. It is a
small occupancy heuristic, not a claim that this approximates every visual
collision. Hysteresis prevents rapid level changes around a threshold:

| Current level | Transition |
|---|---|
| Aggregate | Enter records at ≥10 px/record; enter labels directly at ≥42 |
| Records | Return to aggregate below 7 px/record; enter labels at ≥42 |
| Labels | Return to records below 30 px/record; return directly to aggregate below 7 |

These thresholds are explicit design parameters for this task and dataset.
They are not universal perceptual constants. Labels use deterministic collision
checks; all records remain available in the accessible table. When the viewport
or responsive layout changes, occupancy is re-evaluated without changing IDs.

Aggregate cells use globally anchored time bins and a 20-detection grid. Time
bins are 2, 4, 8, 16 or 32 days wide: the renderer measures the widest total/total
label in the active font, then selects the smallest bin width that fits that
label plus padding at the current projected scale. Narrow screens therefore
retain readable counts by showing coarser groups. The width is shown beside the
chart. Using total/total as the measurement bound prevents selection changes
from triggering rebinning. Across widths, bins retain member IDs, total count
and selected count; cyan cell height is the selected fraction. The last bin includes the maximum domain endpoint. Cells are computed
from the full eligible population and clipped to the camera, so a partially
visible cell still reports its **whole-cell** denominator. That policy is stated
beside the chart. Aggregates never receive invented record identities and
cannot hide a partial selection behind a binary highlight.

Zoom preserves the data coordinate beneath its anchor, except when the domain
boundary or minimum width clamps the camera. Buttons zoom at the center; wheel
zoom in Navigate mode uses the pointer. The minimum viewport width is 0.75 days.
Input coordinates use the inverse SVG screen transform, so CSS scaling,
letterboxing and nonzero SVG origins do not require screen-pixel guesses.

## Access and recovery

On narrow screens, section links jump to the detail plot, exact controls, records
and selection state. The exact controls repeat the current selected/visible/hidden
counts with a recovery link; no sticky overlay covers the plot or controls.

Visible controls provide keyboard and touch equivalents for brushing, set
operations, habitat filtering, zoom, pan, clearing and undo. The exact selection
form accepts finite, bounded numerical values; both interval ends are inclusive.
Table pin buttons expose pressed state. A removed focused row transfers focus
to the labelled scroll region. There is no automatic animation; the stylesheet
also honors reduced motion. Text uses the example brand's near-black, cream and
high-contrast cyan colors, a 16 px minimum, and 44 px controls.

The SVGs provide a visual overview with descriptive alternatives. The table and
numeric controls are the nonvisual exploration path; hundreds of decorative
marks are not forced into the Tab order. Live announcements occur on completed
actions rather than every pointer movement. Color is paired with fill/outline
selection treatment, explicit counts and table membership text.

`window.linkedAtlas.snapshot()` returns a detached diagnostic snapshot with
serialized IDs, camera, pin/preview, semantic level and plot geometry. It
provides no writable alternate state route. Pure exports are independently
usable without DOM or renderer dependencies.

## Verification boundaries

The pure tests use explicit small fixtures and seeded varied sets to check
selection algebra, aggregate membership conservation, invalid data exclusion,
closed boundaries, hidden selections, pin/preview restoration, semantic
hysteresis, anchor-preserving zoom, coordinate round trips, cancellation and
undo. The browser companion checks actual controls and pointer paths separately.
Implementation tests do not establish human comprehension, analytic accuracy,
learning speed or accessibility with every screen reader. Those remain tasks
for appropriate user evaluation.

`inside` and `aggregate` exclude missing, nonnumeric, nonfinite and out-of-domain
x/detection values; they never coerce `null` to zero. Invalid aggregate bin widths
raise `RangeError`. Extents require exactly two finite values per supplied axis,
normalize reversed endpoints and clamp to the known domain. Stable record IDs
are a dataset precondition. The generated dataset satisfies it; a host adapter
must validate uniqueness before using the model with other data.

This is a focused reference, not a production chart framework. It has no remote
data, asynchronous query races, spatial indexing, streaming updates, persisted
state or collaborative editing. Large-data hosts need adapters and performance
budgets while preserving the same selection and camera semantics.
