# Task observation — connect methods to evidence

Use when evaluating a workflow, interpreting an interaction trace, specifying
instrumentation for a design question, or checking whether a task model explains
actual use. Pair with [task analysis](task-analysis.md); implementation details
still belong to the host product. Loading this reference does not authorize
deploying analytics or collecting new user data.

## Contents

- [Research lineage](#research-lineage)
- [Specify the observation](#specify-the-observation)
- [Keep transformations inspectable](#keep-transformations-inspectable)
- [Observe dynamic and asynchronous state](#observe-dynamic-and-asynchronous-state)
- [Interpret traces](#interpret-traces)
- [Evaluate the outcome](#evaluate-the-outcome)

## Research lineage

Hilbert and Redmiles distinguish selecting events, abstracting higher-level
events, and recoding a stream for analysis. Context matters: the same input may
mean different things in different states, and a task cannot always be inferred
from lower-level activity. Sequence comparison needs expert interpretation and
an adequate model of expected behavior.
[Manuscript, §§3.2–3.4, 4.2, 4.5.5](https://ics.uci.edu/~dfredmil/publications/J006-HR00.pdf).

Edmonds's Uzilla couples assigned tasks, completion criteria, instructions,
hints, surveys, and browser/page events. DOM identity distinguishes controls and
alternate browser operations. Task, page, user, and behavior reports support
analysis, with a skilled analyst still needed. Its reference-path feature used
a recorded session; multiple optimal paths were a proposed extension. The paper
explicitly connects the instrumentation to Hilbert and Redmiles's taxonomy.
[Uzilla, pp. 194–196, 198](https://link.springer.com/content/pdf/10.3758/BF03202542.pdf).

Edmonds, White, Morris, and Drucker's MLogger captures within-page events with
structural context. The paper distinguishes aggregation by class from identity
by ID and notes the fragility of positional DOM paths. Dynamic state and task
boundaries remain challenges. Its deployment had unassigned visitors; inferred
task success or interest cannot establish their intentions. The hover example
admits competing explanations.
[Instrumenting the Dynamic Web, §§4.2, 5, 7](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/edmondsjwe2007.pdf).

The rest of this reference applies that lineage to asynchronous interfaces and
agent evaluation; those extensions are Muriel's, not the papers'.

## Specify the observation

Begin with a question that could change the design. “Do people successfully
return to the object after inspecting a source?” is useful. “Collect every click”
does not specify an analysis.

Declare the task's provenance: assigned, participant-stated, analyst-inferred,
or unknown. Identify an observable attempt boundary and outcome, and state
their limitations. Opening an export panel may be exploration, not an intention
to save. Clicking Download establishes an activation, not correct delivery.

Choose evidence appropriate to the question:

| Question | Evidence | Boundary |
|---|---|---|
| Was the action available and did it produce the intended state? | State/DOM inspection, input trace, render, focused test | Does not establish that a person would discover it |
| Which route was followed? | Ordered events with stable identities and relevant context | Missing events can make routes ambiguous |
| Was the result correct? | Domain check or delivered-artifact inspection | A success toast alone is insufficient |
| What did the person expect or understand? | Relevant explanation, prediction, or task behavior from a person | Logs alone do not reveal an internal belief |
| Did a revised method help? | Comparable task conditions and outcomes, with method checks | Do not equate fewer recorded actions with improvement |

Reuse existing traces when sufficient. Add the minimum instrumentation needed
to distinguish hypotheses; prefer scoped identities and state to raw document
contents or typed input. Record sampling, exclusions, redaction, capture errors,
and retention constraints that affect interpretation. Traceability does not
require unrestricted permanent capture of private material.

## Keep transformations inspectable

Maintain a chain from source observations to analytical conclusions:

```text
Captured input and state
  → selected observations for this question
  → abstracted semantic episodes
  → recoded sequence for comparison
  → interpreted method and outcome, with alternatives
```

Define the transformations, rather than presenting derived labels as raw fact.
For example, `source_inspected` overclaims if its rule only detects an opened
viewer. Use `source_view_opened`, then establish inspection through appropriate
additional evidence. Multiple input sequences may legitimately map to the same
semantic action; preserve their modality when modality is relevant.

A compact observation record might contain these fields. Adapt names to the
host's canonical events rather than introducing a competing analytics schema:

```text
event_id, sequence, timestamp, clock_basis
actor_kind: human | automation | system | unknown
task_instance_id, attempt_id, task_goal_source
build_or_snapshot_id, route, input_modality
object_id, control_id, relevant_state_before, relevant_state_after
request_id, input_revision, result_revision
event_type, capture_status
```

An abstraction record should identify its rule/version, contributing event IDs,
context required, and unobservable or ambiguous parts. Keep method inference in
a separate field with its evidence and competing explanation. Do not invent
missing event IDs or exact timestamps to make a reconstruction complete.

Before interpreting a report, check a few derived episodes against their source
events and rendered states. Include one alternative successful route and one
ambiguous or incomplete sequence. A classifier that always emits a task label
can conceal the most important uncertainty.

## Observe dynamic and asynchronous state

DOM position is not durable identity when rows reorder, virtualize, or change
representation. Prefer an existing stable domain identity plus action identity.
Record enough state to distinguish the same control acting on different
objects or revisions. If that identity is unavailable, narrow the claim instead
of matching by coincident screen coordinates.

Separate activation, request acceptance, work progress, settlement, result
availability, and user-visible delivery. For example:

```text
record_activated(take-7)
capture_completed(take-7)
encode_started(take-7, settings-revision-3)
preview_settings_changed(settings-revision-4)
encode_completed(take-7, settings-revision-3)
```

This synthetic trace does **not** establish that the current preview has a
ready matching file. A product test should verify that a stale result cannot
silently become the current download. A progress event also needs a referent:
playback position in seconds differs from encoding work fraction. Do not merge
them into a generic `progress` measure without preserving meaning.

Use attempt and request identity to distinguish a retry from duplicate event
delivery. Check ordering and clock basis before computing durations. Concurrent
work can overlap; summing task intervals can overstate elapsed time. Report
observed duration, blocking wait, and uncertain idle time separately where the
analysis requires them.

For interruption, keep resumed work associated with its original context when
the evidence permits. Do not classify an open task as abandoned simply because
the recording window ended. Mark it incomplete or censored and state the rule.

## Interpret traces

Compare meaningful episodes and outcomes before demanding an exact click path.
A deviation can indicate an incomplete model, a legitimate alternate method,
exploration, recovery, or a product problem. Use the event stream to locate
questions, then inspect the context that distinguishes them.

| Observed | Competing explanations | Useful discriminating evidence |
|---|---|---|
| Menu opened repeatedly | Comparing options; forgotten choice; missing command; accidental closure | Current task, menu state, choices, relevant observation or participant account |
| Long pause after activation | Blocking work; reading; checking; interruption; capture gap | Request timing, available actions, visible state, capture health |
| Several parameter reversals | Exploration; overshoot; misunderstanding; deliberate comparison | Intended outcome, continuous response, later retained choice |
| Back used after source access | Successful return; wrong source; lost context | Restored query/object/focus and subsequent task outcome |
| Download activation without artifact evidence | Delivery attempted; blocked; saved elsewhere; unobserved | Platform delivery result and independently inspected output where available |

Do not equate cursor position with gaze, hover with interest, rereading with
confusion, or path length with cognitive load. An agent's fluent explanation
does not turn these interpretations into measurements.

## Evaluate the outcome

State denominators and observation units. Exposed users, task attempts,
completed attempts, sessions, events, and files answer different questions.
Distinguish not attempted, attempted without observed completion, explicit
failure, and verified completion. Avoid interpreting all noncompletion as
abandonment or dislike.

For comparisons, report task and data equivalence, experience/practice, device
and input method, system latency, assistance, and build provenance insofar as
they could explain the difference. Keep pilot observations, model predictions,
agent walkthroughs, and human evaluations separate. Counterbalance repeated
tasks when learning or order can affect a human comparison.

Inspect success quality and recovery alongside time. Define what would refute
the expected benefit, and revise the model when a successful alternate method
appears. Leave genuine ambiguity unresolved. These practices make an observation
useful for design without pretending that instrumentation supplies intent.
