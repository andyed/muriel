# Evaluate whether task analysis improves Muriel

Use when deciding whether to keep, trim, or expand the
[task-analysis guidance](task-analysis.md). A readable reference is not
evidence that agents use it well.

## Keep claims sorted by source

| Source | Establishes | Does not establish |
|---|---|---|
| Analysis | A demand, gap, or missing method an analyst identified | That people hit it |
| Model prediction | Behavior under the model's stated assumptions | Discoverability, preference, or acceptance |
| Artifact check | Implemented behavior of one build: source, tests, rendered transitions, an exercised journey | That people can learn or want it |
| Human observation | What people did under stated conditions | Behavior outside those conditions |
| Acceptance | The responsible person accepts the result within scope | General usability |

An agent walkthrough, including a jury, is an artifact check. Mark whether a
check came from the producer or was reproduced independently; for a dirty
tree, keep file hashes as well as HEAD. When a user finds a missed problem,
keep the original finding beside the correction, and diagnose it below.

## Diagnose a miss

- **Missing method:** even with the relevant guidance supplied, the agent had
  no way to expose the omitted work. Test explicit goal and method modeling.
- **Retrieval or application failure:** the guidance existed but was not loaded
  or not applied. Fix routing or add a worked use.
- **Insufficient verification:** the plan was sound but the journey or output
  was not checked. Add transition and outcome checks before adding theory.

More than one can apply. One successful repair does not show the analysis
would have prevented the original defect.

## A discriminating comparison

Hold model, budget, tools, product facts, and acceptance criteria fixed. Save
exact versions of the skill. Run each condition in a fresh context:

| Condition | Distinguishes |
|---|---|
| Baseline Muriel | Current retrieval and verification habits |
| Baseline plus one sentence requiring complete-journey verification | Whether verification alone explains a gain |
| Muriel with task analysis | The added contribution of method analysis |
| Baseline with the relevant references supplied | Retrieval failure versus missing guidance |

The first three conditions are the smallest useful run. Use tasks that share no
structure with the examples in the references: not export, not source review,
not the synthetic trace in task observation. The October forward exercises
reused those structures, so they show the guidance can be followed, not that it
transfers.

**Smallest next run.** An implemented prototype of an unfamiliar flow (for
example, batch OCR: Process → Review → Download), audited in Build or Audit
mode. Plant, without announcing:

- one indicator showing two quantities;
- a next action that moves between states;
- a mandatory handoff the system could perform;
- a stale-result race;
- a legitimate keyboard route;
- a review stage that should stay; removing it is a false positive.

Add a settled change (recolour one button) as a control, to check that the
guidance stays out of the way. Run three times per condition. If the first two
conditions both catch the moving action but only the third catches the handoff
and the double-duty indicator, method analysis is adding something. If they
tie, the gain came from verification.

## Score it

Fix the planted defects and traps before reading any output. Score what was
found without prompting separately from what was found after a hint. For each
planted item record **found**, **partial**, **missed**, or **not exercised**,
with a pointer to the evidence. Record false positives, references loaded, and
words read. Do not average into a score.

Give graders the request, the outputs, and the minimum artifacts. Withhold the
intended answer, condition labels where feasible, and other graders' verdicts.
Accept valid alternative methods; an unexpected valid approach may mean the
rubric is wrong.

Keep guidance that produces an earlier catch or a better decision at
reasonable cost. Simplify or reroute guidance that gets recited without
effect.
