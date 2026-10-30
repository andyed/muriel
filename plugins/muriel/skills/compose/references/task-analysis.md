# Task analysis — design the work before arranging the controls

Use before designing or changing a multi-step flow: several stages serve one
outcome, more than one route is legitimate, or the work can fail, be
interrupted, or need a return. A settled styling change does not need a task
model.

This operationalizes the task framing in
[human capabilities](human-capabilities.md). Put its output in the existing
[design synthesis](design-synthesis.md) record, at the depth that can change the
decision. A narrow problem fits in a paragraph.

## Contents

- [Frame the activity](#frame-the-activity)
- [Model goals and methods](#model-goals-and-methods)
- [Inspect knowledge and coordination](#inspect-knowledge-and-coordination)
- [Walk first use](#walk-first-use)
- [Change the method](#change-the-method)
- [Choose analytical depth](#choose-analytical-depth)
- [Carry the model into proof](#carry-the-model-into-proof)

## Frame the activity

Name the outcome in the person's terms. "Get a usable video of this moment"
lets recording, encoding, and delivery change. "Click Prepare video" has already
mistaken an implementation step for a goal. "Make art" is too broad to settle
an export interaction.

Note where the goal came from: the user, an assigned task, observed work, a
requirement, or your own hypothesis. A plausible persona is not evidence.

Define one concrete task instance: starting state and materials, the outcome
and how you would see it was reached, what must survive the task, what the
person is told versus assumed to know, and the variants that matter, including
rare consequential ones.

Keep three success criteria apart. A valid file can be delivered with the wrong
crop, or without the moment the person wanted. Technical completion, task
correctness, and experienced value need different evidence. For open-ended
creative work, protect exploration and revision; define milestones without
claiming one optimal result.

## Model goals and methods

Decompose the outcome into subgoals whose completion changes what the person
can do next. The goal hierarchy is not the screen hierarchy: one screen can
serve several goals, and one goal can span screens or tools.

For each consequential subgoal, write a method: preconditions, steps (ordered
or conditional), information used, visible consequences, and how it ends. Stop
decomposing where more detail cannot change this decision. "Inspect the
evidence" is too coarse if the disputed work is finding a source, opening it,
locating the passage, and getting back.

```text
Goal: resume a change with its evidence available
  Establish what changed and what remains open
  Find the relevant object
  Inspect supporting source material
  Return to the object and resume work

Method: inspect a single source
  Requires: source identity and destination are available
  Open the source; locate the relevant material; check it
  Return with object identity, query, and reading position preserved

Method: inspect one of several sources
  Reveal membership; distinguish candidates; select a source
  Continue with the single-source method

Selection rule:
  If one source is available, use the direct route
  If several sources are available, use the member-selection route
  If no source is available, say so; do not pretend success
```

This is GOMS-informed pseudocode, not executable NGOMSL or a timed model. The
rule describes the design; whether a person notices the condition and picks
that method is a separate question.

Give competing methods the same start and success criterion. Include
shortcuts, keyboard and assistive routes, and routes people already use
successfully. A longer route may buy verification, learning, control, or
exploration; not every departure from the designer's route is an error.

Inspect each selection rule. What makes this method the right one? Can the
person perceive that condition where they choose? Does it require knowledge
the interface does not supply? If two rules apply, state a priority or leave
the choice open; do not silently pick the method that flatters the candidate.

## Inspect knowledge and coordination

At the consequential steps, ask what must be known and where it comes from:

| Demand | Inspect | Design move to test |
|---|---|---|
| Recognize the right action | Label, identity, scope, location, enabled state | Make the object and its action perceptually related |
| Predict the result | Current state, defaults, transformation, output boundary | Show the consequence before commit when that decision matters |
| Hold context | What must be remembered across steps: values, provenance, query, comparison, unfinished intention | Keep a visible reference or restore context on return; count items held in mind, not buttons |
| Choose a method | Preconditions and competing goals | Put the deciding information where the choice happens |
| Coordinate with the system | What is running, blocking, cancellable, or settled | Distinguish input acknowledgment from the resulting state |
| Recover | What survived, what failed, what Retry repeats | Restore the useful work and give an actionable route back |

These are analytical questions, not measurements of memory or load. A pause
can be reading, checking, waiting, reflection, distraction, or a capture gap;
[task observation](task-observation.md) keeps interpretations apart from events.

Divide the work explicitly among person, application, background worker,
external record, and collaborators. Find where the software makes someone
relay a dependency it could manage itself, and where automation would remove a
valuable choice or hide a consequence. "Fewer clicks" cannot settle that; see
[Project Ernestine](goms.md#dependencies-and-overlap).

For interruption, record the suspended goal, what context persists, what
changes while away, and the cues at return. Model error recovery as its own
method. That exposes missing recovery routes; it does not predict how often
errors happen.

## Walk first use

GOMS covers practiced, routine work. For a first or infrequent use, run a
cognitive walkthrough (Wharton, Rieman, Lewis & Polson, 1994): take the correct
action sequence for the task instance and ask, at every step:

1. Will the person be trying to achieve this step's effect at all?
2. Will they notice that the right action is available?
3. Will they connect that action with the effect they want?
4. After acting, will they see progress toward their goal?

A "no" names a missing cue, a step the person has no reason to want, or
feedback that does not report progress. A mandatory "Prepare video" step fails
question 1 for anyone who just wants the video. The walkthrough is an analyst
method; it finds candidate problems, and people confirm them.

## Change the method

Compare the current procedure with a candidate before polishing either:

- Can a subgoal disappear because the representation carries the information?
- Can the system do a routine handoff instead of making the person relay it?
- Can a branch depend on the person's intent, rather than being a pipeline
  stage every user must acknowledge?
- Can useful inspection stay available without being compulsory?
- What new search, recall, learning, verification, or recovery work does the
  candidate add?

Method changes move controls and add indicators. Check the result against
[continuity across states](interaction-contracts.md#continuity-across-states):
the next action stays put, one indicator per quantity, results carry their
revision. The [worked cases](task-analysis-cases.md) run this analysis on source
review and media export.

## Choose analytical depth

| Decision | Next step |
|---|---|
| Which work should the interface support? | Goal and method analysis here; consult people or domain evidence for uncertain requirements |
| Which routes exist, and when is each right? | Explicit methods and selection rules; formalize with [GOMS](goms.md) if needed |
| Can a first-time user find their way? | [Walk first use](#walk-first-use), then observe representative first use |
| Which specified routine is faster in practiced use? | [KLM or CPM-GOMS](goms.md), with stated assumptions and sensitivity |
| Does overlap or repeated information access change the routine? | [Microstrategies](microstrategies.md); CPM-GOMS when dependencies are defensible |
| Does the result support judgment, play, learning, or expression? | Build a probe and evaluate that outcome directly |
| Does the implementation hold the intended procedure? | [Interaction contracts](interaction-contracts.md); for a jury review, seat the [Walker](jury.md#the-roster) |

Task analysis is broader than GOMS. It exposes missing information, goals,
dependencies, and alternatives before a routine is fixed; GOMS models specified
routine behavior. Do not relabel a task narrative as a performance model.

## Carry the model into proof

Turn each consequential branch into an acceptance journey that starts in the
person's initial context and ends at the outcome, including return or
delivery. Assert state, representation, and consequences through canonical
product state, and write tests around invariants so that several valid action
sequences can pass.

Label each claim by its source: analysis, model prediction, artifact check,
human observation, or acceptance by the person responsible. An agent
walkthrough, including the Walker seat, is an artifact check, not a usability
result. Tracking evidence for the guidance itself is covered in
[task-analysis evaluation](task-analysis-evaluation.md).

Record only the fields that change the decision:

```text
Task instance, goal source, relevant user and input conditions
Start → observable outcome; what must survive
Current method, supported alternatives, candidate method and selection rules
Knowledge needed at the consequential choices, and where it is available
Failure, interruption, recovery, return
Model and assumptions, if predicting
Acceptance journeys; what still needs people
```

## Sources

- Wharton, C., Rieman, J., Lewis, C., and Polson, P. (1994). The cognitive
  walkthrough method: A practitioner's guide. In J. Nielsen and R. L. Mack
  (Eds.), *Usability Inspection Methods*. Wiley.
- GOMS sources are in [GOMS](goms.md#sources); observation sources in
  [task observation](task-observation.md#research-lineage).
