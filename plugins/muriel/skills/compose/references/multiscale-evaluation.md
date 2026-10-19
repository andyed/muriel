# Evaluating semantic zoom, linked displays, and brushing

Use this battery when changing Muriel's multiscale guidance or building an
interface whose task depends on coordinated views. It tests whether the skill
produces useful working behavior across domains. A passing reference demo is
evidence for that demo; it does not establish that a future build, a different
dataset, or Muriel's general capability passes.

Read [the coordination contract](multiscale-coordination.md) for the design
mechanisms, [zooming interfaces](zooming-interfaces.md) for navigable spaces and
return paths, and [the adapters](multiscale-adapters.md) for host integration.
The [linked-atlas lab](../examples/linked-atlas/index.html) supplies one
inspectable implementation. The independent fixtures below deliberately cover
additional data shapes that the lab does not represent.

## Four kinds of evidence

Keep these separate in the handoff. A failure in one cannot be repaired by
accumulating passes in another.

| Evidence | What to exercise | What a pass establishes |
|---|---|---|
| Model | Small independent data oracles, predicates, ID joins, transforms, event ordering | The declared state and aggregation semantics hold for the tested cases |
| Browser interaction | Actual pointer, keyboard, focus, wheel, and touch routes; rendered state read back from the page | The UI invokes those semantics through the tested input paths |
| Rendered inspection | Relevant sizes and tiers, selection/filter combinations, empty/loading/error states, text/mark contrast | The inspected outputs are legible and communicate the intended state |
| Human task observation | Representative tasks with unfamiliar users; a comparison when claiming improvement | What those participants understood or accomplished under the observed conditions |

Calling a reducer from a browser console is model evidence. Synthetic pointer
events can exercise handlers but do not establish hit testing, pointer capture,
native scrolling, or physical touch acceptance. A screenshot does not establish
keyboard access. Automated accessibility checks do not establish screen-reader
comprehension. Record skipped and unavailable checks explicitly.

The repository includes focused checks for the linked-atlas implementation:

```sh
node --test tests/multiscale-coordination.test.mjs
node tests/multiscale-browser.mjs
```

The browser suite needs Playwright and its Chromium runtime in the test
environment. `PLAYWRIGHT_MODULE` can point to an existing installation, while
`BASE_URL` can supply an already-served lab. Otherwise the script starts and
stops its own loopback server. Set `SCREENSHOT_DIR` to retain captures for a
separate rendered inspection. Browser touch checks use Chromium input emulation;
physical-device and assistive-technology acceptance remain separate. These
checks exercise the reference lab, not all the independent briefs below.
The browser suite also checks its rendered HTML and SVG text against the painted
background at glyph locations, including SVG label backplates and halos, with
an 8:1 floor. Planted low-contrast fills and changed backgrounds verify that the
audit can fail. This audit is scoped to the lab's solid-color text; it does not
establish chart-mark contrast, native popup-menu contrast, or general image-text
accessibility.

## Run the capability battery

Run the build briefs below in fresh sessions against a recorded skill revision.
Give the agent the brief and fixture, with the required task and existing host
constraints. Keep the expected answers available to the evaluator. Require a
runnable artifact, its canonical-state description, and bounded evidence for
what was verified. Preserve the resulting artifacts and event traces, including
failed builds.

Evaluate the output, not the presence of vocabulary in its rationale. A response
that says "semantic zoom" while enlarging the same marks fails the relevant
task. A modest table with the required correspondence and recovery can pass a
linking task without using a prescribed library or visual form.

For each brief report **pass**, **fail**, or **not observed** against its listed
behaviors. Record the first reproducible counterexample and user consequence.
Do not turn mixed evidence into an invented quality score. Repeat fresh runs
when estimating reliability; report runs completed / runs attempted and the
number passing each behavior. Fix the fixture before comparing skill revisions
when a task or oracle proves ambiguous.

### A. Time-series cohort investigation

**Brief:** Build a small investigation surface for field observations. Let a
reader select a time window, compare its habitat composition, inspect individual
records, and retain a chosen record while changing the viewport and habitat
filter. An overview must retain temporal context. Use calendar day as the time
unit; brushing selects a half-open interval `[start, end)`.

| ID | Day | Habitat | Value |
|---|---:|---|---:|
| r1 | 1 | Coast | 10 |
| r2 | 2 | Ridge | 20 |
| r3 | 3 | Coast | 30 |
| r4 | 4 | Coast | 40 |
| r5 | 5 | Ridge | 50 |
| r6 | 6 | Coast | missing |
| r7 | 7 | Ridge | 70 |
| r8 | 8 | Coast | 80 |

**Required observations:**

- Brushing `[2, 5)` selects exactly `r2, r3, r4`. Day 5 is excluded. Reverse
  dragging produces the same set. Endpoint inclusion is visible in the range
  control or explanation.
- Filtering to Coast retains three selected IDs, reports two selected records
  in the current filter, and exposes five eligible records. The selected visible
  value mean is 35, computed from `r3, r4`; the selection denominator is not
  silently replaced by the total corpus size.
- The full Coast mean is 40 over four observed values, with one missing value
  separately accounted for. Missing does not become zero or disappear from the
  record count.
- Pin `r2`, then filter to Coast. The pin remains identifiable with its hidden
  status, or the interface explicitly asks to replace it. Hovering `r4` and
  leaving restores the pin; it does not commit a new selection.
- Zooming the main chart changes the viewport and representation as needed,
  while the overview retains the full temporal domain and the three selected
  identities survive. Resetting the viewport does not clear the selection.
- An empty brush has a visible zero-result state distinct from "no selection."
  Clearing the selection restores the declared unselected behavior.

### B. Document or image collection across scale

**Brief:** Build a collection browser for eight synthetic documents. At a broad
scale show two collections and their composition; at a middle scale expose
documents; close up, expose readable excerpts and metadata. Let a reader select
documents, cross a tier boundary, inspect one, and return to the original place.
Supply an equally capable linear route for keyboard use and small screens.

Use IDs `d1`–`d4` in collection A and `d5`–`d8` in collection B. Give `d2` and
`d6` the same title, "Survey notes," but different excerpts. Give `d4` a missing
thumbnail. Initially select `d2, d5, d8`; pin `d6`. Filter out `d8` in a later
step. The contents are fixtures, not an asserted semantic clustering result.

**Required observations:**

- Overview groups expose selection membership: A has 1/4 selected, B has 2/4.
  They cannot appear wholly selected. After filtering `d8`, show B's visible
  1/3 selected alongside the fact that one selected document is hidden.
- A tier change adds or replaces task-relevant representation: counts and
  summaries become recognizable document objects, then readable content.
  Enlarging thumbnails without adding meaningful content does not pass.
- Selecting or pinning either duplicate title identifies the correct ID and
  excerpt in every view. Array position and display title are not identities.
- Crossing the representation boundary back and forth preserves selected IDs,
  the pin, and the spatial anchor. If the focused DOM element is replaced,
  focus transfers to its semantic successor; it does not drop to the page body.
- Slow movement around a threshold does not flicker between tiers. Returning
  from detail restores enough location context to find the same neighborhood.
- The missing thumbnail has a usable identity and inspection route. Zooming
  does not trigger repeated unbounded image loads. Motion reduction preserves
  the state transition without requiring a flying camera.

**Bounded ZUI navigation and return extension:** Use the same collection as a
two-dimensional space, with world bounds `[0, 1600] × [0, 1000]`. Place collection
A near `(300, 300)` and B near `(1200, 700)`, with the document positions stored
in world coordinates. Start at a fitted overview; select `d2, d5, d8` and pin
`d6`. Record camera position, scale, focused entity, and navigation-history
length at each action. Declare the allowed scale interval and camera-boundary
policy before testing.

- **Anchored zoom:** Choose an off-center point that is away from world bounds.
  Zoom by a factor of two and back using pointer, keyboard, and any offered
  pinch route. The same world point remains at the same screen location within
  a stated rendering tolerance, such as one CSS pixel. Check both axes; a
  horizontal chart-domain change cannot satisfy this collection task. Boundary
  clamping is separately visible and tested, rather than treated as anchor
  preservation.
- **Fit and Back:** Pan to an asymmetric view, then inspect `d2`. Fit computes
  a camera that contains its declared target (document, collection, selection,
  or whole space). Back restores the recorded previous camera, including its
  offset and scale. They must produce distinct results in this fixture. Returning
  to the preceding location must not clear selection, change the pin, or replace
  a user's manually chosen camera with a newly fitted one.
- **Scale limits and history:** At minimum and maximum scale, repeat the
  outward zoom action. It is a true no-op: the camera, selection, preview, pin,
  focus, and history length remain unchanged. One continuous gesture creates
  the declared single navigation checkpoint, not one entry per input event.
  Back must not require traversing invisible no-op entries.
- **Reflow and intentional position:** Resize the host from a wide screen to a
  narrow one after an intentional pan. Preserve the declared world anchor or
  give a visible recovery action. Browser resize or delayed thumbnail arrival
  cannot silently refit the entire space. If the design offers a reflowing
  collection layout, record the world-to-entity correspondence before and
  after reflow and preserve the selected/pinned IDs; test reflow separately from
  camera navigation.
- **Preview and pin:** Crossing the close-up threshold may reveal `d2`'s content
  or initiate a preview under an explicit policy. It cannot pin `d2` merely
  because the camera approached it. `d6` remains pinned; zooming away removes
  a transient preview and restores the pinned detail. An explicit inspect/pin
  action remains available through keyboard controls.
- **Bounds and reachability:** Pan toward all four corners and apply repeated
  large wheel or key inputs. The camera remains finite and obeys the declared
  bounded or elastic policy. Every document, including those near the edges,
  can still be reached and inspected at a readable scale. The overview and a
  keyboard recovery control can return from an empty region without requiring
  knowledge of the offscreen coordinates.
- **Focus continuity:** Focus `d2`, cross every representation boundary, then
  return. Its semantic successor keeps focus and a visible indicator even if
  DOM nodes, canvas layers, or thumbnail representations change. If `d2` becomes
  unavailable, focus moves to an explained collection or navigation target.
  Virtualization cannot send focus to the page body or leave it on an invisible
  recycled object.

This extension tests navigation of a collection. It does not require a new
faceting runtime. When applying it to Wunderkammer, evaluate any existing filters
or collection membership behavior against their own declared task and data
contract; do not equate that behavior with camera movement.

### C. Heterogeneous linked data and non-bijective joins

**Brief:** Build a customer, order, and event investigation surface. Let a reader
select a customer, inspect the related orders and events, and compare tags. The
views have different units of analysis. Make unmatched data and count units
visible. A shared x-axis is neither required nor meaningful.

Customers are `c1, c2, c3`. Orders are `o1(c1, 10)`, `o2(c1, 30)`,
`o3(c2, 20)`, and `o4(no customer, 5)`. Events are `e1(o1)`, `e2(o1)`,
`e3(o2)`, `e4(o3)`, and `e5(unknown order)`. Tag A relates to `o1, o2`;
tag B relates to `o2, o3`.

**Required observations:**

- Selecting `c1` links to exactly two orders totaling 40 and three events. The
  second event on `o1` does not count its order amount again.
- Selecting both tags yields three distinct orders, not four. Any weighted or
  multiplicity-based metric is separately named and justified.
- Selecting `c3` yields no related orders and visibly empty target views.
  Clearing that selection restores all records; the two actions are distinct.
- `o4` and `e5` remain discoverable as unmatched records. A join cannot silently
  drop them while claiming to show the entire input dataset.
- The source entity and join direction are intelligible. Selecting event `e1`
  may link to `o1` and `c1`, but any expansion to sibling event `e2` is explicitly
  defined and visually distinguishable from the original selected entity.
- Sorting, filtering, and aggregate expansion do not change identity mapping.
  The rendered count labels name customers, orders, or events as appropriate.

### D. Geographic and temporal views with independent navigation

**Brief:** Build an observation map linked to a timeline and record list. Select
observations in either view, inspect their correspondence, and inspect a dense
map region without losing the global time context. The map has longitude and
latitude; the timeline has dates. Declare how multiple selections combine.

Use five records: `p1(-5, 0, day 1)`, `p2(0, 0, day 2)`,
`p3(5, 0, day 3)`, `p4(0, 5, day 4)`, `p5(5, 5, day 5)`.
Define the test rectangle as `-1 <= longitude <= 1` and `-1 <= latitude <= 6`,
which yields `p2, p4`. Define the time brush `[2, 4)`, which yields `p2, p3`.

**Required observations:**

- Replace produces the most recent set; add produces `p2, p3, p4`; intersection
  produces `p2`; subtracting the time set from the map set produces `p4`. Offer
  only operators the interface declares, and test each offered operator.
- Map navigation changes the map viewport without changing timeline scale or
  turning pan into selection. The selected IDs remain shared.
- Pixel-to-data conversion works when the plot begins away from the document
  origin, the page is scrolled, and the graphic is CSS-scaled. Nested transforms
  and SVG viewBox letterboxing must be covered when the host uses them.
- Small-screen interaction has an explicit way to choose navigation versus
  brushing. Touch scrolling outside the plot still works; multiple pointers
  do not silently commit the first pointer's unfinished selection.

## Adversarial interaction sequences

Run applicable cases against every built artifact, not only a purpose-built
test harness. A feature absent from the product is **not applicable**, with the
reason recorded; an offered but untested feature is **not observed**.

| Sequence | Observable invariant |
|---|---|
| Start a replacement brush, move outside the plot, press Escape | The prior committed set survives; transient geometry disappears; keyboard focus remains usable |
| Start a brush, then `pointercancel` / loss of capture / window blur | No unfinished selection commits; capture and temporary listeners are released |
| Draw a nonzero rectangle that contains no marks, then clear | Explicit empty selection and absence of selection remain distinguishable |
| Click or tap without crossing the drag threshold | The documented click action occurs; no accidental empty brush replaces the selection |
| Start from `{a,b}`; add `{b,c}`; subtract `{b}`; undo if offered | Sets become `{a,b,c}`, then `{a,c}`; undo restores exactly the preceding committed state |
| Preview A while B is pinned; move to empty space or another view | Preview clears through the shared path and B remains pinned |
| Change a filter while records are selected offscreen | Selection identity and visibility counts agree; filtered or offscreen records are not confused with deleted records |
| Change data revision during a pending brush | The gesture is cancelled or recomputed under an explicit policy; IDs from incompatible revisions cannot be committed silently |
| Issue request A, then B; resolve B before A | Visible results stay on B; a stale A response cannot repaint them or restore its selection |
| Change viewport while a selection overlay exists | The overlay reprojects from its declared domain or IDs; stale screen coordinates do not change meaning |
| Resize or cross a semantic tier while a child control has focus | Focus has a visible, relevant destination and remains operable |
| Remove a selected or pinned record from the data | The missing identity is explained or cleared according to a visible policy; another row cannot inherit it |

Async, deleted-data, and multi-pointer cases require host fixtures; a static
reference lab cannot establish them. Do not retrofit a fake loading spinner to
claim asynchronous verification.

## Narrow routing counterexamples

These briefs test restraint. Use fresh sessions and inspect the runnable result
or proposal; checking whether the agent mentions "brush" is not a valid test.

| Brief | Expected decision and evidence |
|---|---|
| "Fix the spacing of the already specified zoom buttons; behavior is approved" | Follow the host's settled control model; no new selection or linking system |
| "Show the latest total and its units on a status page" | A readable direct display; no invented exploratory canvas or selection state |
| "Add a date filter to this appointment form" | A conventional bounded input is sufficient unless a concrete distribution-comparison task is supplied |
| "Make this static publication figure readable when printed" | Work through the figure channel and print constraints; no interaction required to interpret the export |
| "The gallery's image magnifier must show the original pixels" | Geometric magnification preserves the requested content; semantic substitution is not imposed |
| "Build three independent operational controls with unrelated data" | Preserve independent state; shared appearance alone does not warrant cross-filtering |

For a paired positive test, add a genuine relationship task to the last brief:
"Choose a deployment and inspect its errors, hosts, and traces." The response
should then define correspondence and linked state. This tests whether routing
responds to task meaning rather than surface nouns.

## Human comparison when an outcome claim matters

The following is a study plan, not evidence that these mechanisms improve
performance. Start with observed workflow failures and a relevant existing
interface. Pick tasks that both conditions can complete, and preserve data,
labels, available information, and answer criteria across conditions.

1. **Define the claim and task before recruiting.** For example: find which
   habitat changed within a time window, recover a previously inspected record,
   or explain why an aggregate includes certain members. Decide which task
   tests correspondence, navigation, selection, or learning. Do not claim a
   general cognitive benefit from one successful task.
2. **Choose the comparison that addresses the mechanism.** Compare the host's
   current interface with the proposed one. If separating zoom from linking
   matters, use a targeted variant or staged comparison. Keep the baseline
   capable and equally polished; otherwise the result cannot isolate the
   mechanism. A factorial study is useful only when the research question and
   participant budget support it.
3. **Separate learning from practiced performance.** Capture unassisted first
   use, provide the same amount of instruction, then use parallel datasets for
   practiced trials. Counterbalance condition and task order. Use different
   values with comparable structure to reduce answer memorization. A delayed
   retention task is needed for a retention claim.
4. **Define denominators and failures.** Report correct task answers / assigned
   tasks, participants completing each condition / recruited participants,
   recoveries / induced recoverable errors, and condition-specific missingness.
   Measure elapsed time from an explicit start to an explicit completion. Report
   incomplete tasks and timeouts alongside time for successful tasks; do not
   hide them in a faster-successes-only mean.
5. **Observe the mechanism.** Record chosen IDs, operations, tier crossings,
   resets, accidental selections, backtracks, and help requests alongside task
   correctness. Think-aloud can reveal confusion but changes task timing; use
   a separate session or acknowledge that limit. Logs alone do not reveal why a
   person acted.
6. **Treat insight tasks carefully.** Collect an answer and its cited data.
   Define valid findings and scoring examples beforehand; blind raters to
   condition where practical. Report agreement, unsupported findings, duplicates,
   and findings per participant within a fixed observation period. Verbosity or
   number of interactions is not an insight measure.
7. **Recruit for the claimed population and input modes.** Include relevant
   domain experience and access needs. Test keyboard, screen reader, or touch
   with people who use them before making claims about their usability. Use
   pilot variance and a smallest meaningful effect to plan a comparative sample;
   a convenient small pilot supports defect discovery, not a universal ranking.
8. **Report uncertainty and scope.** Analyze paired observations as paired when
   appropriate, account for repeated tasks per participant, and report effect
   estimates with uncertainty. Predeclare primary outcomes and exclusions when
   testing a performance claim. Preserve contradictions: improved speed with
   worse accuracy or harder first use is a tradeoff, not an overall win.

## Evidence receipt

Attach a compact record to a completed evaluation:

```text
Skill and artifact revisions:
Brief, dataset version, and expected answers:
Host browser, viewport, device/input mode:
Model cases passed / failed / not observed:
Real input cases passed / failed / not observed:
Rendered states inspected and captures:
Human participants, assigned tasks, completed tasks (if any):
First reproducible defect and its consequence:
Claim supported by this evidence:
Unverified boundaries and next check:
```

Do not mark the battery complete merely because the reference example passes.
Keep a new failing build as a regression fixture when it exposes a transferable
skill or implementation defect.
