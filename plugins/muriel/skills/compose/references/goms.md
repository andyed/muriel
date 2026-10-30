# GOMS — make procedural assumptions inspectable

Load after [task analysis](task-analysis.md) when explicit methods, procedural
consistency, or a performance comparison can change the design. Do not
manufacture a timing exercise for every interface.

## Contents

- [Select the model](#select-the-model)
- [Construct a useful analysis](#construct-a-useful-analysis)
- [KLM comparison](#klm-comparison)
- [Knowledge and learning](#knowledge-and-learning)
- [Dependencies and overlap](#dependencies-and-overlap)
- [Report and test predictions](#report-and-test-predictions)
- [Sources](#sources)

## Select the model

GOMS describes goals, operators, methods, and selection rules. John and Kieras
(1996) distinguish four variants. All four estimate execution time; they differ
in what they represent and what else they predict.

| Model | Represents | Also predicts | Use when |
|---|---|---|---|
| CMN-GOMS | Goal hierarchy, methods, selection rules, operators | The operator sequence for a task instance | Comparing how procedures are structured and where methods diverge |
| KLM | One analyst-supplied sequence of keystroke-level operators; no goals, methods, or selection rules | — | Quick comparison of specified routine methods |
| NGOMSL | Methods in a program-like form, including what must be remembered | Operator sequence, relative learning time for the procedures, working-memory demands, benefits of consistency | Comparing learnability, consistency, or memory load of procedures |
| CPM-GOMS | Parallel cognitive, perceptual, and motor operators with dependencies | Which activities lie on the critical path | Skilled work where overlap decides the answer |

All four assume practiced, error-free, routine performance. For first or
infrequent use, run a [cognitive walkthrough](task-analysis.md#walk-first-use)
instead. Predictions are conditional on the modeled task, methods, users, and
parameters; they are legitimate engineering evidence, but they do not establish
discoverability, creative quality, or acceptance.

## Construct a useful analysis

1. Fix the task instance and completion criterion first, including initial
   focus, open context, data, and system availability. Do not give only the
   favored design a convenient start.
2. Write the competing procedures and the information used to choose between
   them. Say whether each method is permitted, taught, observed, or
   hypothesized.
3. Keep operator grain comparable. "Select the right source" is fine for a
   hierarchy; in a timing comparison it hides search.
4. Put unresolved judgment, learning, or missing prerequisites on the record
   instead of hiding them inside a mental operator.
5. Analyze the difference between designs. Shared work cancels only if its
   conditions really are unchanged; say so.
6. Check sensitivity to assumptions and alternate methods. Keep a failed
   prediction as diagnostic evidence.

For formal models, follow the technique's own construction rules and tools;
this reference is not an NGOMSL interpreter.

## KLM comparison

Card, Moran, and Newell's KLM estimates skilled, error-free execution of a
specified method. Operators: keystroke (K), pointing (P), homing (H), drawing
(D), mental preparation (M), and system response (R). It excludes the time to
acquire the task. M is placed by heuristic rules over the method, not added as
a fixed cost per click, and R counts only when the user actually waits.
[Original paper, §§2–3](https://frankritter.com/hcdd331/cardMN80.pdf).

Keep an operator ledger: occurrence, operator, parameter, unit, source, and
assumption. State where each M goes and whether each response blocks. Mark
published parameters versus local estimates. If pointing is modeled
geometrically, state device, distance, target width, and calibration.

**Symbolic example, not a calibrated prediction.** An evidence panel requires
opening a source list before opening the only source. A candidate adds a direct
link. For the same known-source task:

```text
List route:   M + P(list) + K + R(reveal) + [M] + P(source) + K + shared reading/return
Direct route: M + P(source) + K + shared reading/return
```

`[M]` depends on the placement rules: is locating the source in the revealed
list anticipated, or a new decision? State which rule you applied. The
candidate removes a blocking reveal and possibly an M. It still loses if the direct target is
hard to find or reach, or if skipping the list removes needed context. No
numerical advantage follows until parameters are supplied. If the task requires
comparing several sources, this is the wrong task instance.

For a numerical analysis, publish the operator table, equation, units,
parameter sources, and a plausible sensitivity range. If the ranking flips
within that range, report the uncertainty, not a speed claim.

## Knowledge and learning

NGOMSL learning estimates cover the methods in the model and the long-term
knowledge they require; use them for relative comparisons between designs.
They mislead for walk-up-and-use systems: a method consisting of one unlabeled
key predicts almost no learning time, even if nobody can discover the key.

Record the knowledge a design assumes even when no learning model is justified.
Must the person know that an eight-second take can yield a shorter loop, that a
preview is not the encoded file, or that a progress bar can also seek? Decide
which facts belong in the representation, a control, feedback, or help, then
test them in first use. Do not call a procedure intuitive because the analyst
can complete it.

## Dependencies and overlap

Project Ernestine is the standard lesson. A new telephone-operator workstation
removed about one keystroke per call and was expected to be faster, by one
estimate up to four seconds per call. CPM-GOMS models predicted it would be
slower; the field trial agreed, measuring 0.65 s slower per call. The faster
features were off the critical path, and on some calls the procedure with fewer
keystrokes took longer (Gray, John & Atwood, 1993). Count what is on the
critical path, not the steps removed.

Use [microstrategies](microstrategies.md) to inspect information access and
the coordination of action. Formalize with CPM-GOMS when plausible overlap
changes the answer. Two activities run concurrently only when both their
information dependencies and their resources allow it; "the user can think
while waiting" is not a dependency analysis. Label an informal dependency
sketch as such.

Overlapping system work raises product-state questions before timing ones: if
encoding runs during preview and the user changes the crop, the old result must
not become the current Download. Those rules live in
[continuity across states](interaction-contracts.md#continuity-across-states).

## Report and test predictions

Name the task, variant, skill level, methods, operator sources, and
exclusions. Fitting parameters and checking predictions on the same data
supports a weaker claim than predicting new tasks or people.

Compare at the grain the model addresses. A total-time match can hide a wrong
method or compensating errors; inspect sequence, branching, and latency before
adjusting parameters, and never tune away a mismatch to protect a preferred
design.

Keep execution time, errors and recovery, task correctness, learning,
enjoyment, and expressive range separate; they have no common currency. A
recovery procedure can be modeled once specified; that does not predict how
often errors occur or whether people find the recovery.

## Sources

- Card, S. K., Moran, T. P., and Newell, A. (1980). The keystroke-level model
  for user performance time with interactive systems. *Communications of the
  ACM*, 23(7), 396–410. [DOI](https://doi.org/10.1145/358886.358895).
- John, B. E., and Kieras, D. E. (1996). Using GOMS for user interface design
  and evaluation: Which technique? *ACM TOCHI*, 3(4), 287–319.
  [Full paper](https://people.eecs.berkeley.edu/~jfc/hcc/courseSP05/lecs/Cognitive%20Models/p287-john.pdf).
- John, B. E., and Kieras, D. E. (1996). The GOMS family of user interface
  analysis techniques: Comparison and contrast. *ACM TOCHI*, 3(4), 320–351.
  [DOI](https://doi.org/10.1145/235833.236054).
- Gray, W. D., John, B. E., and Atwood, M. E. (1993). Project Ernestine:
  Validating a GOMS analysis for predicting and explaining real-world task
  performance. *Human-Computer Interaction*, 8(3), 237–309.
  [DOI](https://doi.org/10.1207/s15327051hci0803_3).

The wider literature intake is in the repository's
`research/interaction-models-review.md`.
