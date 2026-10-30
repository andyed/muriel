# Task-analysis cases — source review and creative export

Two flows from local application reviews on 29 October 2026, both of which
passed review before a user found problems. Each case runs the
[task analysis](task-analysis.md) forward from the flow as it stood before the
correction and marks which line of the analysis exposes each problem. Whether
the analysis would have caught them without the user is untested; see
[task-analysis evaluation](task-analysis-evaluation.md).

## Case 1: resume work from a session record

**Flow as reviewed.** A session-history list. Each row's content expanded only
through a small icon. One row could stand for several similar items, and
previews were capped.

**Goal.** Establish what changed, check the supporting source, and get back to
the object to keep working. Expanding a row is a means, not the goal.

```text
Method: inspect a single source
  Acquire the row's one primary action; open the source; check it
  Return with query, object, and position preserved

Method: inspect one of several sources
  Reveal the members; tell them apart; choose one
  Continue with the single-source method

Selection rule: one source → direct; several → member selection; none → say so
```

| Analysis line | What it exposes | Repair |
|---|---|---|
| Acquire the row's one primary action | The whole row is the target, but only the icon responded | Whole-row activation |
| Reveal the members | A similar-items disclosure that revealed nothing | Make the disclosure list the actual members |
| Several sources → member selection | Capped previews with no route to the rest | Add a continuation to the remaining members |
| Return with query, object, position | Back must restore all three | Test Back and close for each input route |
| Recover a failed read | Retry must target the same source | Retry scoped to that source; ignore stale responses |

**What happened.** The user found the icon-only target. Whole-row activation
was repaired and reported by the implementing agent; it was not independently
re-run. That agent's tests caught a Back regression. A later sweep found the
inert disclosure and the capped previews; at intake those were proposals, not
repairs.

**What it shows.** Muriel already had target-acquisition guidance; it was not
applied. The method model adds the member-selection branch, which is where the
two later findings sit.

## Case 2: keep a creative moment as a usable video

**Flow as reviewed.** Record an eight-second take → preview a generated loop →
press Prepare video → wait → press Download. One progress bar showed playback
position during preview and job completion during preparation. Record,
Prepare, and Download each appeared in a different place.

**Goal.** "Keep this moment as a video I can use." A still and a loop are
different goal branches.

```text
Method as built
  Record take; wait for capture
  Inspect preview loop            (bar = playback position)
  Find and press Prepare video    ← person relays a pipeline stage
  Wait                            (same bar = job completion)
  Find Download                   ← target has moved
  Download                        ← no check of the file
```

| Analysis line | What it exposes | Candidate |
|---|---|---|
| Can the system do a routine handoff? (Change the method) | Prepare video is a stage every user must trigger; nothing about their intent decides it. Walkthrough question 1 fails for anyone who just wants the video | Prepare automatically while the preview plays; keep the preview for inspecting and refining |
| Coordinate with the system (knowledge table) | One bar means two things; the person cannot tell whether dragging it seeks the loop | Separate, labelled playback and job indicators |
| Walk the sequence ([continuity](interaction-contracts.md#continuity-across-states)) | The next action moves at every state | One action area; Record becomes Download in place, guarded across the change |
| Selection rules | Changing crop or loop mode while preparing creates competing results | Tag the result with its settings revision; only the current one becomes Download |
| Recover | A failed preparation must not cost the take | Keep the take; Retry repeats only preparation |
| Completion criterion | Download activation is not a delivered file | Check crop, duration, and playback at the destination |

**What happened.** A generalist critique asked for revision; three AI jury
lenses passed the flow, and that split is kept as recorded. The review judged
individual states and a partial journey, no seat was responsible for the
sequence, and the observer stopped before downloading. The user then reported the double-duty bar, the manual handoff,
and the moving actions. The implementation agent proposed separate indicators,
a fixed action area, and automatic preparation. At intake those were proposed
repairs, not verified behavior, and the agent's separate claim to have fixed
export flashing was not checked.

**What it shows.** The questions existed in Muriel. Interaction contracts
already asked which branches reflect real user decisions, and layout stability
was already a rule. They were not applied to the sequence, and no review step
looked at it. Most of this miss is retrieval and verification, which the
continuity checks and the [Walker](jury.md#the-roster) seat now target. The
method model adds the explicit handoff line.
