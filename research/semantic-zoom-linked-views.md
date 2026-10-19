# Semantic zooming, linked displays, and brushing: evidence and build direction

Research intake · 16 October 2026

Muriel should be able to design and build an interface where a person can find
a pattern at one scale, identify its members, compare those members in another
representation, refine the cohort, and return to the original context. This
requires representation design, query semantics, navigation, and recovery to
work together. Polished transitions and multiple charts alone do not establish
that capability.

The [practical coordination reference](../plugins/muriel/skills/compose/references/multiscale-coordination.md)
translates this intake into implementation decisions and falsifiable checks.
The [renderer adapters](../plugins/muriel/skills/compose/references/multiscale-adapters.md)
connect the contract to host libraries. The runnable teaching artifact is
`examples/linked-atlas/index.html`; its tests verify the behavior actually
implemented there. They do not constitute a study of human analytic benefit.
The [working history and related-concepts map](multiscale-history.md) expands
the lineage to early statistical systems, zooming interfaces, dynamic queries,
fisheye views, lenses, typography, data abstraction, and spatial substrates.

## Evidence classification

- **Design precedent:** A system or technique establishes an implementable
  possibility. It does not establish universal usefulness.
- **Formal model:** A representation, algebra, or mathematical model supports
  reasoning within its assumptions. Its optimum need not optimize human work.
- **Empirical evidence:** Observed outcomes concern the tested tasks, people,
  devices, and conditions. Transfer requires a defensible argument or a study.
- **Synthesis:** A review or heuristic framework organizes a field. Its component
  studies can disagree, and its guidelines have different evidential bases.
- **Muriel inference:** A concrete design or engineering recommendation proposed
  here. Test its implementation; evaluate human outcomes separately.

This is a selected evidence ledger, not a systematic review or a claim to cover
all contemporary visualization research. It deliberately favors primary papers
that clarify the mechanisms and their boundaries.

## Muriel synthesis — Compare: how to build the capability

**Question.** What should Muriel provide so these techniques become coherent,
testable interactions in different host products?

| Option | Supports | Cost or unresolved question |
|---|---|---|
| Library-specific recipes | Fast adoption in a matching stack | State semantics and recovery can diverge between recipes |
| A shared production framework | Reusable executable ownership and rendering | Imposes architecture before cross-domain transfer has been demonstrated |
| A common contract, working lab, and host adapters | Inspectable behavior, independent fixtures, and integration with existing state | Each host still needs an implemented adapter and task-level evaluation |

**Decision.** Use the third option. The criteria are identity correctness,
navigation continuity, accessible operation, canonical host ownership, and
observable proof. One explicit state contract supports both linked visual
feedback and equivalent non-drag controls. Keeping camera, query, selection,
preview, and pin separate also preserves the boundary needed for
[faceted exploration](../plugins/muriel/skills/compose/references/faceted-exploration.md).
The native lab makes the contract executable without requiring a new framework.

**Proof and limits.** The lab exercises aggregate-to-record-to-label changes,
shared cohorts, set operations, cancellation, recovery, responsive rendering,
and anchored one-dimensional navigation. Model and browser tests check those
mechanisms. The evaluation battery specifies transfer to documents, relational
data, maps/timelines, and a two-dimensional ZUI; those broader capability trials
and human-benefit comparisons remain unrun. Library adapters are integration
sketches. The [Clipwall case study](clipwall-multiscale-case-study.md) separates
the inspected baseline from the subsequent local faceting extension and its
model, browser and rendered-state checks. Neither is a human-benefit benchmark.

## 1. Representation at scale

**Bederson and Hollan (1994), _Pad++: A Zooming Graphical Interface for Exploring
Alternate Interface Physics_.** Design precedent. The paper describes objects
whose rendering changes with viewing size and distinguishes this from simple
magnification. Its implementation also uses visibility bounds, spatial indexing,
refinement during navigation, and background loading. Read the Description and
Efficiency sections and the procedural-object example. [Primary paper](https://www.cs.umd.edu/projects/hcil/pad%2B%2B/papers/uist-94-pad/uist-94-pad.pdf),
[DOI](https://doi.org/10.1145/192426.192435).

**Muriel consequence.** Author a representation ladder before implementing a
camera: group statistics at overview, members at an intermediate scale, exact
entity information when there is room. State what task each level enables.
Measure the projected footprint. Treat threshold hysteresis and label budgets
as engineering policies to test, rather than attributing chosen pixel values
to the paper. Pad++ is a lineage for implementation and design; it does not
prove that Muriel's ladder improves comprehension or navigation.

**Furnas and Bederson (1995), _Space-Scale Diagrams: Understanding Multiscale
Interfaces_.** Formal representation and design precedent. The paper represents
space and magnification together to inspect navigation paths and scale-dependent
representations. Its semantic-zoom section explicitly shows the representation
changes and their transition points. [Primary paper, especially semantic zoom
and Figure 11](https://www.cs.umd.edu/projects/hcil/pad%2B%2B/papers/chi-95-spacescale/chi-95-spacescale.pdf),
[DOI](https://doi.org/10.1145/223904.223934).

**Muriel consequence.** Make a transition table that shows each level, its
entry/exit condition, corresponding objects, and information gained or lost.
Capture the same selected cohort on both sides of every threshold. Test
continuity by identity and world position, not resemblance alone. This paper
supports analyzing a multiscale design explicitly; it does not supply a
universal number of levels or a universally optimal zoom trajectory.

## 2. Context, zoom, and comparison are distinct design choices

**Cockburn, Karlson, and Bederson (2008), _A Review of Overview+Detail, Zooming,
and Focus+Context Interfaces_.** Research synthesis. The review distinguishes
spatially separated overview/detail, temporally separated zooming, integrated
focus/context, and cue-based techniques. It separates low-level acquisition
evaluations from higher-level search and comprehension. The evidence does not
produce one universally superior mechanism. [Primary paper, Sections 3–7](https://faculty.cc.gatech.edu/~stasko/7450/Papers/cockburn-surveys08.pdf),
[DOI](https://doi.org/10.1145/1456650.1456652).

**Muriel consequence.** Select a technique for a specified task and test a
credible alternative. Keeping an overview visible may help orientation while
costing space and comparison time. A lens may preserve context while distorting
metric judgments or target geometry. Distinguish semantic zoom, drilldown,
details on demand, and geometric zoom in implementation and evaluation. The
publication date discrepancy is recorded in the verification table below;
this ledger follows the paper's printed December 2008 citation.

**van Wijk and Nuij (2003), _Smooth and Efficient Zooming and Panning_.** Formal
model with a preference experiment. The authors derive camera paths under a
metric based on estimated perceived velocity and explore preferred speed and
zoom/pan tradeoff settings. Section 6 describes 26 experienced computer users
adjusting animations of an unfamiliar Mars map. This is not an experiment
establishing better analytic decisions. [Primary paper](https://vanwijk.win.tue.nl/zoompan.pdf),
[author institution record](https://research.tue.nl/en/publications/smooth-and-efficient-zooming-and-panning/),
[DOI](https://doi.org/10.1109/INFVIS.2003.1249004).

**Muriel consequence.** Use a principled path when distant camera movement
benefits from showing context, but make it interruptible and provide an
immediate reduced-motion route. Separately verify anchor-preserving direct
zoom, bounded navigation, and final camera state. Do not call an animation
human-optimal because it minimizes a mathematical path criterion.

## 3. Brushing is a family of selection operations

**Becker and Cleveland (1987), _Brushing Scatterplots_.** Technique and design
precedent. The publisher abstract describes coordinated effects across a
scatterplot matrix, several brushing operations, and transient, lasting, and
undo paint modes. This establishes that brushing has operation and persistence
semantics, rather than being synonymous with a rectangle. The primary abstract
was read; a complete full-text study appraisal was not conducted. [Publisher
record and abstract](https://www.tandfonline.com/doi/abs/10.1080/00401706.1987.10488204),
[DOI](https://doi.org/10.1080/00401706.1987.10488204).

**Muriel consequence.** Define the selected universe, the query, its lifetime,
and the effect of each operation. Keep absent selection separate from an active
selection with no matches. Compose replace/add/subtract/intersect against a
gesture-start snapshot. Retain data-space predicates and stable IDs through
rendering changes. These precise state rules are our implementation contract;
the source does not validate every rule or modern input mapping.

**Satyanarayan, Moritz, Wongsuphasawat, and Heer (2017), _Vega-Lite: A Grammar of
Interactive Graphics_.** Language/system contribution. Selections combine
input processing, selected data, and inclusion predicates; they can drive
highlighting, filtering, or scale domains. Multi-view resolution includes
distinct composition policies. The evaluation uses examples to demonstrate
expressiveness and specification concision. [Primary paper, Sections 4–5 and
Figures 8–11](https://vis.csail.mit.edu/pubs/vega-lite.pdf),
[author page](https://vis.mit.edu/pubs/vega-lite/),
[DOI](https://doi.org/10.1109/TVCG.2016.2599030).

**Muriel consequence.** Represent an interaction as an explicit query and name
its effect. A highlight predicate, a filter predicate, and a viewport extent
can share machinery while retaining different meanings. Decide how multiple
brushes resolve, including whether a view excludes its own predicate when
showing context. The paper's grammar is evidence for an architecture and
design space, not proof that any generated dashboard is usable. Consult current
official library documentation before translating the 2017 syntax into code.

## 4. Multiple views need justified relationships

**Wang Baldonado, Woodruff, and Kuchinsky (2000), _Guidelines for Using Multiple
Views in Information Visualization_.** Heuristic synthesis grounded in workshop
discussion and the authors' design experience. The eight guidelines address
when multiple views are worthwhile and how to manage their costs. The paper
explicitly includes parsimony, complementarity, self-evidence, and attention
management. This is guidance, not a randomized test of eight independent
causal effects. [Primary paper](https://www.cs.loyola.edu/~lawrie/CS774/S06/research/p110-wang_baldonado.pdf),
[DOI](https://doi.org/10.1145/345513.345271).

**Muriel consequence.** Assign each view a distinct analytic job. Make the
relationship visible through consistent cohort marking, exact counts,
meaningful scope labels, and inspectable membership. Assess the display and
attention cost of each additional view. An extra panel should answer an
additional question or make a consequential comparison easier; “linked” alone
is insufficient justification.

**North and Shneiderman (2000), _Snap-Together Visualization: A User Interface
for Coordinating Visualizations via Relational Schemata_.** System/conceptual
model with an initial evaluation. The paper coordinates actions through keys
and relational joins. Different data relationships support different actions,
including linked selection and drilldown. Read Sections 2.2–2.4, including the
one-to-one and one-to-many cases. [Primary conference paper](https://www.cs.umd.edu/~ben/papers/North2000Snap.pdf),
[DOI](https://doi.org/10.1145/345513.345282).

**Muriel consequence.** Name the entity and relation before linking views. A map
of customers and a table of orders require a customer-to-order relation, with
explicit direction and count semantics. A selected ID is not a global concept
without a dataset namespace. A single shared coordinate system is unnecessary;
shared meaning is necessary. Do not silently transfer the performance claims
of the separate 2000 journal article into this conference paper or a new task.

**Hurley (2000), _Graphical Selection of Data Views_.** Generalization of linked
selection. The primary abstract describes linking displays of different but
related datasets and an extensible system for such relationships. It directly
addresses the boundary of same-table brushing. Only the primary abstract and
bibliographic metadata were examined here; no detailed claims about its
implementation or evaluated performance are made. [Publisher record and
abstract](https://www.tandfonline.com/doi/full/10.1080/10618600.2000.10474899),
[DOI](https://doi.org/10.1080/10618600.2000.10474899).

**Muriel consequence.** Permit linked views across entity types when the
relationship is justified and inspectable. Explicitly choose any/all semantics,
deduplicate many-to-many matches, retain missing-link information, and label
counts with the entity type. A reverse mapping is not necessarily the inverse
of the forward mapping. Our detailed join and uncertainty rules are engineering
inferences, not claims tested by this abstract.

## 5. Continuity should preserve the data relationship

**Heer and Robertson (2007), _Animated Transitions in Statistical Data Graphics_.**
Design principles with two controlled experiments. The paper examines
transitions among statistical charts and finds benefits for appropriately
designed transitions in its graphical-perception tasks. It also discusses
misleading correspondence, distraction, timing, and the difficulty of comparing
changing displays. [Primary paper](https://sites.stat.columbia.edu/gelman/communication/HeerRobertson2007.pdf),
[author page and metadata](https://idl.uw.edu/papers/animated-transitions),
[DOI](https://doi.org/10.1109/TVCG.2007.70539).

**Muriel consequence.** Animate a correspondence the data supports. If a group
splits into members, preserve the membership relation and readable selected
counts. If an entity disappears because of filtering, distinguish that from
deletion. Keep animation optional and interruptible; compare an immediate or
static transition when it is credible. Neither animation smoothness nor these
experiments establishes faster analysis for every semantic-zoom design.

## 6. The build contract this evidence motivates

The following are Muriel-specific recommendations. They are not quotations or
claims that the cited authors tested this combined architecture.

1. **One semantic state, multiple projections.** A canonical model owns data
   version, selection, filters, preview, pin, and per-view navigation. Views
   derive their content and emit domain actions. Render adapters do not become
   competing stores of analytic truth.
2. **Selection survives representation.** Stable entity IDs and exact aggregate
   membership carry a cohort through bins, points, labels, tables, and detail.
   Rendering may cull marks; queries still cover their declared universe.
3. **The selected set has provenance.** Preserve the brush fields, bounds,
   operation, and snapshot/live policy. A geometric mark alone cannot explain
   a compound selection. Active empty results remain distinguishable from the
   absence of a query.
4. **Navigation and filtering stay distinguishable.** A zoomed view changes the
   camera; a filter changes the eligible population. If the product deliberately
   couples them, give the mode a visible name and a clear return path.
5. **Level changes are representation decisions.** Measure usable screen space,
   use entry/exit thresholds, disclose aggregation, and retain a stable anchor.
   The values are product policies, calibrated with data and target devices.
6. **Aggregate states are exact.** A bin containing 3 selected records out of 12
   is partially selected. Counts name their denominator and entity type. A
   sampled or approximate overview is labeled accordingly.
7. **Time is part of correctness.** An old network or worker result cannot replace
   newer analysis. Track the dataset and dependency revisions; update related
   views coherently and mark stale data when it remains visible.
8. **Access reaches the same query.** Form bounds, visible operation controls,
   structured records, and zoom controls should dispatch the same commands as
   gestures. Noncolor cues, stable focus, and restrained status announcements
   make the state inspectable beyond pointer hover.

W3C's current explanatory guidance for
[Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
and [Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)
was checked for the access recommendations. These are standards explanations,
not experiments proving usability. In particular, a keyboard path and a
single-pointer alternative to dragging solve distinct requirements. Muriel's
8:1 text-contrast target is a project policy, not a threshold derived from the
visualization papers.

## 7. Evaluation and honest capability claims

Start with three kinds of proof, and report them separately:

| Claim | Suitable evidence | What it does not establish |
|---|---|---|
| Selection and coordination are correct | Deterministic ID-set, coordinate, aggregate, and revision tests | Comprehension or usefulness |
| The interaction can be operated | Actual pointer, keyboard, touch, resize, cancellation, and recovery paths | Skill acquisition across users |
| The design helps the analytic task | Representative human tasks, outcomes, errors, explanations, and repeated use | General benefit outside the tested population and task |

A meaningful task sequence is: locate an unusual group; select it; identify its
members in another view; compare their temporal distribution; exclude a subgroup;
explain the resulting cohort; undo an error; return to the original context.
Include partial aggregates, empty matches, and entities hidden by navigation or
filters. Test a plausible baseline, such as explicit detail inspection plus
linked highlights, before attributing a benefit to automatic semantic changes.

Measure cohort accuracy, interpretation errors, task success, completion time,
recovery, and whether people notice and understand the representation changes.
Use enough repeated tasks to examine learning and distinguish it from first-use
discoverability. Predefine the relevant contrasts and retain uncertainty. Avoid
claiming reduced cognitive load merely because fewer clicks were recorded.

Implementation performance needs its own evidence: input-to-feedback latency,
query completion, render completion, data size, and tested device. Culling can
improve frame time while corrupting selection if visible marks are confused
with the full query universe. An impressive frame-rate figure does not close
the analytic correctness or human-evaluation questions.

## Bibliographic verification ledger

The companion [`semantic-zoom-linked-views.bib`](semantic-zoom-linked-views.bib)
contains ten core academic records plus sixteen historical records documented
in the [working history](multiscale-history.md). Titles, full author lists, DOIs, publication
venues, and supplied volume/issue/pages were checked against CrossRef records
and primary papers or author/publisher pages on 16 October 2026. CrossRef records
were fetched directly; unavailable initial responses were retried successfully.

| BibTeX key | Status | Verification and disambiguation |
|---|---|---|
| `BedersonHollan1994Pad` | Verified | CrossRef title plus subtitle; author PDF; UIST 1994, pp. 17–26. Not the six-author 1996 journal version. |
| `FurnasBederson1995SpaceScale` | Verified | CrossRef authors, DOI, pp. 234–241; full title from primary paper and ACM record. |
| `CockburnKarlsonBederson2008Review` | Verified; date discrepancy recorded | Printed paper says December 2008, volume 41(1), Article 2, 31 pages. CrossRef dates it 15 January 2009. Uses printed year consistently here and in BibTeX. |
| `vanWijkNuij2003ZoomPan` | Verified; page discrepancy recorded | CrossRef verifies title/authors/DOI; author PDF and institution record identify 2003 and pp. 15–22. CrossRef says 15–23. Uses the author institution's range. |
| `BeckerCleveland1987Brushing` | Verified | CrossRef and publisher: 1987, 29(2), pp. 127–142. The 2012 online posting date is not the publication year. |
| `SatyanarayanEtAl2017VegaLite` | Verified | All four authors; TVCG 23(1), pp. 341–350, January 2017. DOI contains 2016; this is not a CHI 2017 paper. |
| `WangBaldonadoEtAl2000MultipleViews` | Verified | CrossRef and primary paper; preserve compound family name Wang Baldonado; AVI 2000, pp. 110–119. |
| `NorthShneiderman2000Snap` | Verified | CrossRef and conference PDF, pp. 128–135. Distinct from _Can users construct and operate coordinated visualizations?_ in IJHCS, DOI 10.1006/ijhc.2000.0418. |
| `Hurley2000Selection` | Verified; abstract-level appraisal | CrossRef and publisher: 2000, 9(3), pp. 558–581. The 2012 online posting date is not the publication year. |
| `HeerRobertson2007Transitions` | Verified | CrossRef and author page: TVCG 13(6), pp. 1240–1247. Primary paper gives Robertson's middle initial G.; retained in bibliography. |

No human evaluation of the new Muriel guidance or example is established by
this intake. The useful immediate advance is a research-grounded contract that
can be built, inspected, and challenged with concrete tasks.
