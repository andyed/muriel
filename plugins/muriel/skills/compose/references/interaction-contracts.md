---
reference: interaction-contracts
status: active
requires:
  canonical_state: required
  focal_task: required
output:
  kinds: [behavior-contract, state-matrix, flow-spec, interaction-test]
  registers: [app, web, native, service]
---

# Interaction contracts — behavior before surface

Use this reference when a human-visible interaction is not yet behaviorally
settled. It turns flows, component states, async feedback, and recovery into
implementation constraints that join the project's canonical state.

This is not a second state model and not a generic UX checklist. The calling
agent still owns product truth and architecture. Muriel makes the behavior
perceivable, reversible where appropriate, and testable before visual polish
conceals a gap.

## When to load

For building or auditing an application UI, load after the primary UI channel.
For a behavior-only consultation, task analysis may route here directly without
loading a production channel. Use when the visible slice contains one or more of:

- a multi-step flow or meaningful branch;
- async work, optimistic UI, background processing, or uncertain latency;
- destructive, reversible, save, publish, send, or payment behavior;
- drag and drop, gestures, direct manipulation, or multiple input modalities;
- unclear loading, disabled, empty, success, error, offline, or conflict states;
- a handoff where engineering would otherwise have to infer behavior.

Do not load for a purely typographic, spacing, or surface-detail change whose
behavior and state ownership are already verified.

For semantic zoom, linked displays, or brushing, use the specialized
[multiscale coordination contract](multiscale-coordination.md). It distinguishes
navigation, querying, hover, pinning, and selection, and defines how identity and
aggregate membership survive representation changes. Apply this reference's
general recovery and async rules through that same owner.

## Behavior-truth sequence

Before designing or changing a multi-step flow, use
[task analysis](task-analysis.md) to decide which steps the person should do at
all; derive this contract's transitions and acceptance journeys from it.

Resolve these in order:

1. **Goal** — what the user is trying to complete.
2. **Owner** — the canonical state, component, service, or platform path that
   owns the behavior.
3. **Transitions** — what enters, changes, exits, fails, recovers, and resumes.
4. **Feedback** — what the user perceives immediately and at eventual outcome.
5. **Protection** — what must be preserved, reversible, retryable, or confirmed.
6. **Proof** — the exercised paths and rendered states that establish the
   contract works.

If the owner is missing or contradictory, stop styling and resolve that product
or architecture question with the calling agent first.

## Applicable state matrix

Do not demand a fixed set of ten states from every component. A button does not
have an empty state; a data region may not have hover; a synchronous toggle
does not need a skeleton. Select states from the component's real capabilities
and data lifecycle.

Common state families:

- **Interaction:** default, hover, focus, pressed, selected, dragging.
- **Availability:** enabled, conditionally unavailable, read-only, permission
  blocked.
- **Async:** acknowledging, loading, backgrounded, cancelling, retrying.
- **Outcome:** success, recoverable error, terminal error, conflict, offline.
- **Content:** initial, empty, partial, stale, skeleton, populated.

For each applicable state, record:

| Field | Required answer |
|---|---|
| State | What the product calls this state |
| Canonical owner | Existing component/store/service/platform path |
| Entry | Trigger plus any guard or precondition |
| Visible feedback | Text, control, status, motion, haptic, or announcement |
| Available actions | What remains possible by keyboard, pointer, and touch |
| Exit | Success, cancellation, timeout, navigation, or another transition |
| Recovery | Retry, undo, resume, alternate path, or honest terminal state |
| Proof | Test, exercised flow, render, or accessibility assertion |

State names should match product/code vocabulary. Do not invent a visual-only
alias that obscures canonical state.

## Flow contract

Map the flow as behavior, not a row of screens:

```text
goal
  → entry / preconditions
  → trigger
  → acknowledgment
  → working state
  → decision or branch
  → outcome
       ↘ failure → recovery → resume or honest exit
```

Answer:

- What data or permission is required at entry?
- What is the shortest successful path?
- Which branches reflect real user decisions?
- What can fail, and who can recover it?
- What do Back, Cancel, Escape, reload, and repeated input do?
- What user work survives failure, navigation, or interruption?
- Can the user re-enter or resume without reconstructing context?

A flow with a happy path but no exit or recovery path is incomplete.

## Micro-interaction contract

Use this compact structure for a contained interaction:

```text
Trigger → Rules → Feedback → Loops / modes
```

- **Trigger** — user or system event, input modality, and preconditions.
- **Rules** — canonical state transition, guards, limits, and side effects.
- **Feedback** — immediate acknowledgment plus success, failure, and assistive
  technology output.
- **Loops / modes** — repetition, toggled modes, history-dependent behavior,
  cancellation, and reset.

Add two Muriel fields:

- **Integration** — the existing state/component path carrying the contract.
- **Proof** — the exact exercised transition and visible state that passed.

## Feedback and latency budgets

These are response-feedback budgets, not animation-duration tokens. Preserve
the project's measured performance data and Muriel's existing motion rules.

When timing or information-access costs may change the routine a person adopts,
use [microstrategies](microstrategies.md) to examine the interaction itself.
Keep that analysis distinct from the response-feedback budgets below.

| Observed delay | Required interaction response |
|---|---|
| Up to about 100 ms | Synchronous local acknowledgment; no spinner flash |
| About 100 ms–1 s <!-- motion-exempt: not-motion (latency budget) --> | Preserve layout; show local processing only if the delay is perceptible |
| About 1–10 s <!-- motion-exempt: not-motion (latency budget) --> | Show honest progress or indeterminate work; offer cancel when safe |
| Beyond about 10 s | Persist/background the job when possible; provide re-entry and completion status |

Rules:

- Acknowledgment means “input received,” not “operation succeeded.”
- Keep unrelated controls usable unless product truth requires a modal block.
- Never fake a percentage or completion estimate.
- Delay a spinner briefly when a fast path would otherwise produce a flash.
- Skeletons are for predictable content structure, not command execution.
- Preserve dimensions through loading transitions to avoid layout shift.
- Announce meaningful async status without flooding assistive technology.
- Test on realistic slow, failure, and offline paths; the source-code state
  alone does not prove the user sees feedback in time.

## Optimistic UI gate

Use optimistic UI only when all are true:

- success is highly likely under normal conditions;
- the action is reversible;
- the previous state can be restored exactly;
- rollback is understandable to the user;
- the failure path is implemented and exercised.

Do not use it by default for payment, publish, send, irreversible deletion,
permission changes, or operations with complex reconciliation.

On rollback:

1. restore the previous canonical state;
2. explain that the action did not complete;
3. preserve the user's work;
4. offer retry or a safe alternate path.

## Protect the user's work

- Preserve entered data across validation and recoverable network failure.
- Prefer undo for common reversible actions; confirm before rare irreversible
  ones. Do not stack confirmation and undo without a product-specific reason.
- Prevent duplicate side effects while still acknowledging repeated input.
- Make Back and Cancel semantics explicit and platform-consistent.
- Explain a conditionally unavailable action close to the control. Do not use
  low-opacity text; every text-bearing state still clears Muriel's 8:1 floor.
- Error copy states what happened, why when useful, and what the user can do
  next. Do not promise recovery the system cannot perform.

## Affordance and input parity

The visible signifier must match the actual behavior:

- draggable objects expose a handle or other discoverable signifier;
- gesture-only actions also have a visible and keyboard-accessible path;
- drag and drop supports selection, movement, confirmation, and cancellation
  without requiring a pointer;
- focus order follows the visible task order;
- state changes that are not visually obvious are announced accessibly;
- platform navigation and destructive-action conventions are preserved unless
  the product deliberately and visibly teaches a deviation.

Do not turn discoverability into decoration. A cue that suggests behavior the
component does not own is a false affordance.

## Continuity across states

Each state can look right while the sequence is wrong. Check the journey as a
sequence of frames, not a set of screenshots.

- **The next action stays put.** Actions that serve one goal sit together in a
  predictable place across idle, working, ready, failure, and return. If a
  target must move, the move is the point and is visible.
- **A control that changes meaning is guarded.** When Record becomes Download
  in place, a state change between pointer-down and activation must not turn
  the intended action into a different one.
- **One indicator, one quantity.** Playback position, recorded duration, job
  completion, and delivery are different quantities. Give each its own label
  and behavior; a control that seeks is not an indicator that reports work.
- **Results carry their revision.** Tag a result with the input and settings
  revision that produced it. A result for an older revision, a cancelled job,
  or a late completion never becomes the current Download or replaces the
  ready action.
- **Ready is not delivered.** Check the output at its destination: the file
  plays, with the expected crop and duration, where the platform put it.

Known sequence failures, with fixes and sources, are in
[flow patterns](flow-patterns.md). For a jury review of an implemented flow,
seat the [Walker](jury.md#the-roster); it is the seat that sees the sequence.

## Proof checklist

Exercise the applicable rows, not a ceremonial superset:

- [ ] shortest successful path;
- [ ] one realistic failure → recovery → resume path;
- [ ] Back, Cancel, Escape, or reload where relevant;
- [ ] rapid reversal and duplicate input;
- [ ] keyboard-only completion and visible focus;
- [ ] pointer and touch behavior where supported;
- [ ] slow, offline, stale, or conflict state where relevant;
- [ ] the whole journey walked in order: the next action stays put, and a
      control that changes meaning cannot misfire across the change;
- [ ] each progress or position indicator measures one labelled quantity;
- [ ] a stale, cancelled, or late result cannot become the current result;
- [ ] delivered output checked at its destination, not only "ready";
- [ ] optimistic rollback when used;
- [ ] preserved input/work after recoverable failure;
- [ ] reduced-motion behavior without loss of state feedback;
- [ ] rendered text contrast for every text-bearing state.

Record the result in the Muriel delta:

- **Decision** — the behavior or recovery choice that changed.
- **Integration** — the canonical owner and production path carrying it.
- **Proof** — the exercised transitions, assertions, and rendered states.

## Anti-patterns

Do not ship:

- a visual state that has no canonical behavioral owner;
- a disabled control whose enablement condition is unknowable;
- success styling before the operation has succeeded;
- an error that destroys input or offers no honest next step;
- a spinner that blocks unrelated work;
- one progress indicator standing for two quantities;
- a next action that relocates every time the state changes;
- a pipeline stage the person must trigger when nothing about their intent
  decides it;
- gesture-only behavior without a discoverable fallback;
- optimistic UI without a tested rollback;
- a fixed “all states” checklist applied to irrelevant components;
- animation timings imported as response-latency policy;
- feedback verified only in source, not in the exercised interface.

## Prior art and Muriel divergence

Adapted from
[`rastian/interaction-design-skills`](https://github.com/rastian/interaction-design-skills)
(MIT), especially its flow/recovery framing, response-time reference, and
Trigger → Rules → Feedback → Loops & Modes micro-interaction model.

Muriel deliberately keeps:

- canonical project state over a parallel design-state model;
- applicable states over a mandatory ten-state inventory;
- the 8:1 text floor over the source's WCAG-AA minimum and opacity-based
  disabled treatments;
- existing `muriel.motion` duration/easing/property rules over the source's
  generic motion bands;
- exercised implementation proof over handoff documentation alone.
