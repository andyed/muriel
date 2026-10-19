# Sparklines — a repertoire for evidence in context

Use when a word, value, row, place, or control benefits from seeing an ordered
sequence beside it. Read the host channel first: [charts](../channels/charts.md),
[web](../channels/web.md), [interactive](../channels/interactive.md), or
[terminal](../channels/terminal.md). A sparkline can carry history, variation,
rhythm, or a spatial profile; time is one possible horizontal coordinate.

Actively consider one when a current value conceals a meaningful trajectory,
people scan many entities, or a compact preview helps them decide where to look.
Choose for the question it exposes. An arrow answers direction; a sparkline can
also expose the path, interruption, or instability behind that direction.

This reference contains 48 task patterns, a mark vocabulary, implementation
contracts, and acceptance checks. These are design options, not a quota for
adding graphics. Their task benefits are hypotheses until evaluated in the host.

## Choose the reason before the mark

Complete: **Beside [anchor], show [measure over ordered domain] so the reader
can [judge or act]; compare against [reference]; disclose [scale and coverage].**

For example: beside a service name, show request latency over the last hour so
an operator can distinguish a persistent slowdown from a single spike; compare
with its objective; expose milliseconds, sampling interval, and missing samples.

Choose the reading operation:

| Need | What the compact sequence contributes | When to use something else |
|---|---|---|
| Context | Puts the path beside the current number or claim | Two values and a delta already answer the question |
| Comparison | Aligns trajectories across entities | Exact ranks or small differences need a table or larger chart |
| Triage | Makes bursts, gaps, drift, or reversals visible | Detection requires formal thresholds or a larger diagnostic view |
| Navigation | Previews where useful observations occur | Preview cannot be interpreted without axes or a legend |
| Control | Shows consequences beside the parameter being changed | The plot would conceal state or replace a needed numeric input |
| Continuity | Retains history as a view changes scale or detail | Aggregation changes the meaning without a visible explanation |

## 48 ways and reasons

Each row pairs a placement with a distinct question. Select or combine a few
that fit the task. The caveat is part of the pattern, not optional fine print.

### Reading and explanation

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 01 | Inline after a current value | Distinguish the same endpoint reached by steady growth, recovery, or a spike | State window and units beside the sentence |
| 02 | Beside a change claim | Show whether a reported increase was sustained or concentrated in one interval | Give the actual comparison dates |
| 03 | In a margin beside an event narrative | Locate a reversal relative to the described event | Mark the event; temporal alignment does not establish causation |
| 04 | Beside a quoted peak or record | Show how exceptional that value is within the available history | Disclose the record's observation window |
| 05 | In a methods or results table row | Reveal within-run evolution hidden by a single summary statistic | Identify the run and retain uncertainty elsewhere |
| 06 | Beside a place or route name | Show elevation or another ordered spatial profile before opening a map | Horizontal position means distance, not elapsed time |

### Scanning and comparing entities

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 07 | A history column in a metric table | Find rows whose recent behavior differs despite similar current values | Shared time window and comparable vertical domains |
| 08 | Beside ranked items | See whether a leader is established or briefly ahead | Ranking timestamp and chart window must agree |
| 09 | Beside experimental conditions | Compare learning or adaptation trajectories | Align trials deliberately; show participant counts |
| 10 | Beside cohorts | Locate when cohort trajectories diverge | Label elapsed-since-entry versus calendar time |
| 11 | Beside project or job rows | Distinguish steady progress from a late burst or prolonged stall | Define progress; changed scope can change the denominator |
| 12 | In a comparison shortlist | Compare volatility as well as endpoint magnitude | Use shared units/scales or explicitly label normalization |

### Monitoring and investigation

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 13 | Beside a live status value | Distinguish stable operation from recent oscillation | Show freshness; freeze and label a stale feed |
| 14 | Beside a limit or objective | See approach to a threshold before it is crossed | Keep the limit visible on a stable scale |
| 15 | In an incident list | Judge whether a breach was isolated, repeated, or sustained | Preserve breach duration during reduction |
| 16 | Beside recovery status | See whether a system has returned to its prior range | Include the pre-incident baseline and follow-up coverage |
| 17 | Beside queue depth | Separate accumulating backlog from short bursts | Depth and arrival rate are different measures |
| 18 | Beside a periodic process | Notice a changed cadence or a missed cycle | Use real time spacing and show observation gaps |

### Navigation and information scent

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 19 | Beside search results | Preview when a document or entity has activity relevant to a query | Explain what activity is counted and how query scope applies |
| 20 | Beside facet values | See temporal concentration before choosing a filter | Counts use the host's contextual-filter semantics |
| 21 | Above a timeline scrubber | Find bursts, quiet spans, or transitions worth inspecting | Provide numeric/keyboard seeking and a larger target |
| 22 | In a collection overview | Choose which record histories merit opening | Preserve entity identity when aggregating at low zoom |
| 23 | Beside map locations | Inspect local histories while retaining geographic context | Prevent overlap; keep time/scale shared across locations |
| 24 | Beside saved views or bookmarks | Preview the sequence each view will restore | Distinguish saved snapshots from refreshed live data |

### Controls and feedback

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 25 | Beside a parameter slider | Preview a response curve and the selected position | Label modeled output; do not imply it was observed |
| 26 | Beside a threshold control | Show which portions of history the threshold would classify | Preview must not silently commit the setting |
| 27 | Beside a time-window chooser | Show how trimming the window changes the apparent trend | Keep a larger-window reference available |
| 28 | Beside a smoothing control | Compare raw variation with the selected smoothing | Retain the raw signal and name the smoothing window |
| 29 | Beside an audio or media item | Preview an amplitude envelope to locate silence or bursts | Envelope is not a measure of perceived loudness or musical structure |
| 30 | Beside a simulation preset | Preview its time response before loading it | Use the same initial conditions; label simulation provenance |

### Data quality and analytical trust

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 31 | Beside a data-source name | Expose changes in ingestion volume | A zero count and an unobserved interval have different marks |
| 32 | Beside a reported rate | Show how its denominator changes over time | Keep numerator/rate and denominator separately named |
| 33 | Beside a sensor reading | Reveal dropouts or repeated-value plateaus | A flat trace alone does not prove a stuck sensor |
| 34 | Beside an aggregate statistic | Show time segments with incomplete coverage | Coverage is a separate measure, not value zero |
| 35 | Beside model evaluation rows | Expose drift in an explicitly measured error metric | Hold evaluation definitions consistent and report sample support |
| 36 | Beside a revised estimate | Show how successive published estimates changed | Horizontal axis is revision date; retain the underlying period |

### Planning and resource use

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 37 | Beside remaining capacity | Reveal whether consumption is accelerating | Forecast extensions must be visually distinct and qualified |
| 38 | Beside planned versus actual work | Locate when execution departed from a plan | Use the same scope and distinguish plan from observation |
| 39 | Beside inventory | See repeated depletion and replenishment cycles | Use steps when the state changes discretely |
| 40 | Beside resource utilization | Distinguish persistent pressure from brief peaks | Averages can conceal peaks; choose aggregation for the task |
| 41 | Beside elapsed job time | Show throughput changes that affect completion estimates | An estimate requires a model beyond the sparkline |
| 42 | Beside scheduled demand | Reveal peaks that compete for the same resource | Align time zones and distinguish booked from actual demand |

### Learning, recall, and coordination

| ID | Way | Reason to use it | Keep honest |
|---|---|---|---|
| 43 | Beside a practice exercise | Distinguish consistent improvement from variable performance | Comparable difficulty and scoring are prerequisites |
| 44 | Beside repeated attempts | Show whether errors recur at the same sequence position | Position is an ordered step, not a continuous time measure |
| 45 | In a handoff summary | Preserve the trajectory behind the current status | Include an as-of time and source link |
| 46 | Beside an annotation or pinned observation | Retain surrounding context when revisiting a notable point | Pin the point's identity and original window |
| 47 | In an overview-to-detail transition | Keep the same sequence recognizable as labels and detail appear | Maintain orientation, selected interval, and disclosed scale changes |
| 48 | Beside a linked-view selection | Compare the selected population's trajectory with its reference | Name both populations; hover preview and committed selection stay separate |

## Mark vocabulary

Sparklines belong to a broader family of word-scale graphics. A histogram,
boxplot, or categorical state strip can be a better answer; name it accurately
instead of calling every tiny chart a sparkline.

| Form | Use when | Encoding contract |
|---|---|---|
| Plain line | Ordered magnitude and trajectory matter | Connecting samples must be meaningful |
| Line with endpoint dot | The latest observed value is the anchor | Dot belongs to the last valid timestamp, not the right edge by default |
| Line with selected-point marker | A sentence, pin, or inspector refers to one observation | Selection identity survives sorting, filtering, and resizing |
| Line with extrema markers | Range or exceptional observations matter | Mark meaningful extrema; do not decorate every trace automatically |
| Line with baseline | Direction relative to a reference matters | Label the reference outside the tiny plot |
| Line with target band | Time spent inside a defined range matters | Explain who or what defines the range |
| Step line | Inventory, configuration, or another held state changes discretely | Define whether changes apply before or after the timestamp |
| Sparkbars | Counts or totals belong to discrete intervals | Zero baseline, consistent interval width, explicit aggregation |
| Diverging sparkbars | Signed deviations from zero matter | Shared zero and magnitude scale; sign is visible without color |
| Win/loss or event ticks | Occurrence, order, or streaks matter more than magnitude | Show unobserved intervals separately from negative outcomes |
| Observed line plus forecast | Future projection is explicitly part of the task | Mark the forecast boundary, use a distinct stroke, expose assumptions |
| Line with interval envelope | Uncertainty is material and still legible at this size | Name interval type; expand if the envelope obscures the signal |
| Paired traces | A single comparator is necessary | Shared units/domain, distinguish strokes, label outside the plot |
| Aligned small multiples | Several series need comparison | Shared domains; use explicit exceptions for shape-only comparison |
| Min/max envelope | Dense observations contain peaks that must remain visible | Encode bins as ranges; do not invent within-bin ordering |

## Scale, time, and data contracts

- **Choose the comparison.** Across rows, share horizontal domain, units, and
  vertical domain when comparing magnitude. For shape-only comparison, local
  ranges or indexed baselines are allowed if labeled; include actual values
  nearby. An unlabeled collection of auto-scaled lines invites false comparison.
- **Keep scale stable during monitoring.** Recompute a live domain deliberately,
  explain changes, and preserve threshold visibility. Do not make each new
  sample look equally dramatic. Disclose clipping and offer the full range.
- **Name horizontal meaning.** Time, distance, trial, rank, and revision are
  different coordinates. Preserve irregular time intervals. For calendar bins,
  specify time zone and boundary handling; compare equal windows where needed.
- **Separate absence from zero.** Break lines at missing intervals; show empty,
  insufficient, and stale states in text. One point is a point, not a trend.
  A constant series gets a flat trace on a disclosed domain, not a divide-by-zero
  workaround that implies a slope. Never interpolate across an outage silently.
- **Choose reduction for the question.** Bucket totals for counts, rates with
  their denominators, and extrema envelopes when excursions matter. Averages
  can erase incidents. Record the reducer and bin width. Render from canonical
  data; retain original samples for detail and accessibility.
- **Avoid invented geometry.** Sort by the true coordinate, resolve duplicate
  timestamps by a documented rule, and use linear or justified step segments.
  Decorative spline overshoot can invent peaks, negative values, or thresholds.
- **Keep forecasts and uncertainty explicit.** Historical variation, a target
  band, and a statistical interval mean different things. Small size does not
  justify collapsing them into the same shaded strip.

The surrounding sentence, row heading, column header, or caption may supply
measure, units, dates, reference, and scale policy. They need not be repeated
inside every plot. Earlier observations in a clearly labeled window can be the
comparison context for a trajectory question; add a target or peer only when
the task calls for one. Axes may disappear; semantics must remain available.

## Placement and interaction recipes

**Prose:** keep the anchor and graphic associated through wrapping. Reserve
dimensions before data loads. Start near the host line height and adjust width
to preserve the important shape; 80×20 px is an example, not a universal size.
Move to a margin or separate line when insertion damages reading rhythm. Keep
labels at the host's readable size rather than shrinking them into the graphic.

**Tables and lists:** align chart bounds and endpoints across rows; keep the
exact current value in its own numeric column. Declare scale/window policy in
the header. Sorting changes row order, not series identity or scale. Show an
explicit no-data state instead of inserting a synthetic flat line.

**Controls and navigation:** use a real button, link, or host control with a
40×40 px minimum target (prefer 44×44 for touch); the plot may be smaller inside
it. Opening detail preserves the entity/window, supports Escape or Back, and
restores focus. Provide keyboard and tap equivalents for pointer inspection.
A brush uses the canonical selected interval, with numeric start/end controls;
hover preview does not overwrite committed selection. For linked views, follow
the [coordination contract](multiscale-coordination.md).

**Live views:** show freshness and provide a stable observation window. Avoid
constant drawing animation or automatic announcements of every sample. Let
people pause inspection; expose the live/paused state. Follow the host's motion
rules and reduced-motion preference for deliberate transitions.

**Static export:** include the window and as-of time in nearby text; carry the
key interpretation and scale policy into print, PDF, and image alternatives.
An interactive tooltip cannot be the only explanation in an exported artifact.

**Accessible representation:** use an SVG accessible name/description or adjacent
text that states measure, window, key shape, current value, and important gaps.
If equivalent adjacent text already conveys the information, hide the redundant
graphic from assistive technology. Interactive graphics need a labeled native
control and accessible detail. Supply a data table when exact inspection is
part of the task. Never encode status or comparator identity only by hue.
Keep text at Muriel's 8:1 floor and strokes legible at actual display size.

## Implementation through the existing host

Use the chart library already present, or plain SVG for a few compact series.
Do not introduce a dashboard library for a table column. For many rows, use the
host's virtualization and stable entity keys; Canvas still needs accessible
DOM summaries and controls. Keep domain calculation, aggregation, labels, and
detail derived from the same canonical series.

A useful renderer boundary carries samples with coordinates and validity,
measure/unit, horizontal and vertical domains, reference values, gap policy,
reducer, freshness, and accessible summary. These are responsibilities to join
to the host's model, not a requirement to invent another state store.

Map valid coordinates into the plot's inner bounds; reserve space for stroke
caps and markers. Start a new segment after each gap. Handle empty, single-point,
and constant inputs before dividing by a domain span. Derive endpoint labels
from the last observed sample, not a forecast or padded interval. Resize by
recomputing geometry and reduction from source data, never by repeatedly reducing
an already reduced trace.

Muriel's current `muriel.chart.sparkline(values, label=...)` is a small Unicode
helper: one character per value, eight height levels, a local min/max domain,
and no timestamp, gap, or shared-domain parameters. Use it for finite, regularly
spaced, single-series shape previews with explicit nearby context. It does not
implement the richer patterns above. Do not pass missing values or claim shared
scale comparison by normalizing inputs: the helper normalizes them again.
Choose SVG or the host renderer when timing, gaps, shared domains, or interaction
matter. Terminal glyphs are lossy; retain the numerical summary.

## Acceptance and limits

For an implementation, inspect the rendered result in its actual sentence,
row, or control. A large standalone preview cannot establish inline legibility.

- Check narrow layouts, text zoom, light/dark surfaces, and export where used;
  labels must remain readable, anchors associated, and marks unclipped.
- Exercise zero, negative, constant, one-point, empty, gapped, irregularly
  spaced, stale, and spike-containing inputs appropriate to the domain.
- Compare rows with identical shapes but different magnitudes, and identical
  endpoints but different histories. Confirm the chosen scale supports the task.
- Inspect reduction against source samples, especially threshold crossings and
  extrema. Verify selected points and windows survive sorting and filtering.
- Exercise keyboard, touch, focus return, and reduced motion where interactive.
  Confirm the accessible summary describes the data actually shown.
- Ask whether removing the trace removes useful information. If it does not,
  use the value, delta, or sentence alone. If tiny geometry cannot support the
  decision, open a larger labeled chart or use a table.

These checks establish rendering, encoding, and interaction properties. Claims
about faster scanning, comprehension, memory, or reduced workload need a relevant
human task comparison. Evaluate the sparkline against a value/delta or larger
chart with the same data; measure interpretation errors as well as time.

## Lineage and evidence boundaries

- Edward Tufte, [Sparkline theory and practice](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/):
  design precedent for compact quantitative sequences integrated with words
  and numbers. This motivates contextual placement; it does not validate every
  application in this repertoire.
- Pascal Goffin, Wesley Willett, Jean-Daniel Fekete, and Petra Isenberg,
  [Exploring the Placement and Design of Word-Scale Visualizations](https://www.visdesignlab.net/publications/2014_infovis_placement-wsv/),
  IEEE TVCG 20(12), 2291–2300 (2014), DOI 10.1109/TVCG.2014.2346435:
  a design space and quantitative analysis of placement and text disruption.
  It informs the choice among inline, interline, margin, and overlay placements;
  it is not blanket evidence that sparklines improve reading performance.

The 48 task patterns and host contracts above are Muriel's design synthesis.
Treat new combinations as candidates to exercise and evaluate.
