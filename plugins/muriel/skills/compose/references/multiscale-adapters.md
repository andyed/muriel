# Multiscale adapters — join the host's state

Read after [multiscale coordination](multiscale-coordination.md) when choosing or
integrating a renderer. These are integration recipes, not another framework.
Use the project's installed library version and canonical query/state paths.
The [Linked Atlas](../examples/linked-atlas/index.html) implements the invariant
core in native ES modules; the library-specific snippets below are sketches to
adapt and test in the host, not validated drop-in adapters.

## Choose the smallest useful substrate

| Host | Good fit | Work still owned by the product |
|---|---|---|
| DOM / SVG with D3 | Custom spatial grammar, moderate mark counts, explicit gestures | Canonical selection, representation levels, aggregate membership, accessible controls |
| Vega-Lite | Declarative linked analytical views, reproducible chart specifications | Cross-dataset identity, application state bridge, accessible workflows, semantic-level orchestration |
| ECharts | Existing dashboards with dataZoom/brush and many chart types | Stable ID mapping, filter/viewport distinction, feedback-loop protection |
| Canvas / WebGL | Dense scenes, large fields, expensive geometry | Hit testing, spatial indexes, semantic DOM companion, data-space predicates |
| Existing native UI | A native product with established navigation and accessibility | Translate the same contract into its state and input system; no web rewrite required |

Do not choose by an invented universal row-count cutoff. Measure the actual mark
geometry, labels, visible subset, query cost, hardware, and update cadence.

## D3: gestures are adapters, scales are derived

D3 brush extents and selections use SVG coordinates. Invert the current scales
before dispatching a domain query. `brush.move` can generate brush events;
`sourceEvent` identifies the underlying input event. Choose an explicit guard
for renderer-driven synchronization. [D3 brush](https://d3js.org/d3-brush).

Sketch for a one-dimensional selection brush, with the host supplying `dispatch`,
`xDetail`, and the current selection operation:

```js
let reflecting = false;
const brush = d3.brushX().on('end.model', (event) => {
  if (reflecting) return;
  if (event.selection === null) {
    dispatch({type: 'selection.clear'});
    return;
  }
  const bounds = event.selection.map(xDetail.invert).map(Number).sort((a,b) => a-b);
  dispatch({type: 'selection.query', field: 'time', bounds,
    operation: selectedOperation(), source: 'detail'});
});

function reflectBrush(pixelBounds) {
  reflecting = true;
  try { brushGroup.call(brush.move, pixelBounds); }
  finally { reflecting = false; }
}
```

This immediate synchronization guard does not cover a transition scheduled to
emit events later. Prefer immediate reflection during input. If transitions are
necessary, retain an origin/revision token for their full lifetime. For live
brushing, dispatch a pending predicate during movement and one commit at the
end; preserve the starting selection for set composition and cancellation.

Keep an untransformed base scale. D3's `rescaleX` / `rescaleY` derive display
scales from a zoom transform. `zoom.transform` emits events and does not enforce
scale/translation extents; validate restored transforms or use the constrained
convenience operations. [D3 zoom](https://d3js.org/d3-zoom).

If the brush group is inside a transformed group, establish its local coordinate
frame explicitly. Never invert once through the scale and again through the
same zoom. Resize updates scale ranges, gesture extents, and projected brush
geometry together; retain the data-domain query. Assert the same selected IDs
after a CSS resize, nonzero SVG viewBox origin, and browser device-scale change.

## Vega-Lite: specify selection and scale resolution independently

Current selection parameters support `point` and `interval`, with `global`,
`union`, or `intersect` resolution across repeated views. Projection over
aggregated fields is limited to its defining view. Interval projections over
binned/time-unit fields remain continuous. [Selection parameters](https://vega.github.io/vega-lite/docs/selection.html).

Make the intended role explicit in the spec. For example, a scatter view can
highlight members of a region while retaining the rest as context:

```json
{
  "params": [{"name": "region", "select": {
    "type": "interval", "encodings": ["x", "y"], "resolve": "global"
  }}],
  "mark": "point",
  "encoding": {
    "x": {"field": "time", "type": "quantitative"},
    "y": {"field": "value", "type": "quantitative"},
    "size": {"condition": {"param": "region", "empty": false, "value": 100},
             "value": 30}
  }
}
```

Here `empty: false` belongs to the consuming predicate. Explicitly add the
host's accessible status and controls; size is only a supplementary selection
cue. A filtering consumer instead uses a filter transform, which changes its
population and denominator. Check whether that consumer should show all records
or zero records when the brush is inactive. [Parameter predicates](https://vega.github.io/vega-lite/docs/predicate.html).

An interval bound to scales controls navigation. It is not automatically a
selected cohort. Use separate parameters for navigation and selection; resolve
scale sharing independently of selection sharing. [Scale binding](https://vega.github.io/vega-lite/docs/bind.html),
[scale resolution](https://vega.github.io/vega-lite/docs/resolve.html).

If the surrounding application owns selection, use a documented public View API
bridge and a defined origin guard. Avoid a React state copy plus a Vega signal
copy that can disagree. Do not rely on undocumented compiler-generated signal
names as a cross-version protocol. For a one-way specification, the Vega view
can itself be the single owner; choose ownership deliberately. [Vega View API](https://vega.github.io/vega/docs/api/view/).

## ECharts: translate indices at the data boundary

ECharts exposes input events and actions through `on` and `dispatchAction`.
Actions can update linked chart state; explicit event handling is also available.
[Event and action guide](https://echarts.apache.org/handbook/en/concepts/event/).

Keep a stable `id` alongside each source record and a revisioned mapping from
each rendered series index to that ID. Resolve reported indices against the
exact dataset that produced the event. Sorting, filtering, transforms, and
aggregation can change index meaning. For aggregate marks, resolve to member
IDs or a documented predicate rather than selecting the bin's display index.

Treat `dataZoom` and `brush` as separate product actions. Review `dataZoom`'s
filtering mode before interpreting a view as a fixed-population viewport. Route
selection feedback through guarded actions or derived styling; do not bounce
events between charts indefinitely. Avoid recreating options on each pointer
move when an overlay or a bounded style update suffices.

Read the installed version's [brush options](https://echarts.apache.org/en/option.html#brush),
[dataZoom options](https://echarts.apache.org/en/option.html#dataZoom), and
[API](https://echarts.apache.org/en/api.html) before wiring payloads. These pages
are dynamically rendered; the event guide alone does not verify every version's
brush payload shape. Test your chosen series types with a known-ID fixture.

## Canvas / WebGL: selection belongs to data

Convert client coordinates into the plot's CSS coordinate system, then through
the inverse camera/scale. Device-pixel ratio belongs to raster resolution; do
not apply it a second time to DOM pointer positions. For rotated/perspective
scenes, use the actual inverse transform or ray intersection rather than a
bounding-box approximation. Keep clipping, axis inversion, and logarithmic
domains in the same transform used for drawing.

Build the spatial index from stable data, or invalidate a screen-space index
whenever its transform changes. A bounding rectangle can produce candidates
for a lasso, but final membership needs the polygon predicate. GPU picking IDs
map back to entity IDs; they are not persistent identities themselves.

Use separate budgets for visible marks, semantic labels, accessible DOM
elements, and data queries. Rendering fewer marks must not silently reduce the
selection universe. If interaction uses sampled data or approximate queries,
label that scope, keep exact and approximate results distinct, and reconcile
without presenting an estimate as a completed exact selection.

Retain keyboard focus independently of pooled visual nodes. A focused or pinned
entity needs a stable DOM inspection route even when its mark is offscreen or
represented by an aggregate. Provide a list/table and the same named actions
through ordinary controls; do not make thousands of marks individual tab stops.

## Adapter acceptance

For the chosen host, verify a small fixture before optimizing:

1. A gesture and its form/keyboard equivalent return the same IDs.
2. The same IDs survive sorting, resizing, zooming, and representation changes.
3. Programmatic reflection emits no new user commit or infinite event loop.
4. Clear and an active zero-match query remain distinguishable.
5. A stale query response cannot replace a newer accepted result.
6. Filtering and panning have the stated effect on counts and hidden selection.
7. Destroy/remount removes old listeners and preserves only intended state.

Use the [evaluation fixtures](multiscale-evaluation.md) for independent expected
answers. A library's built-in brush or animation proves neither these invariants
nor a benefit to the analyst.
